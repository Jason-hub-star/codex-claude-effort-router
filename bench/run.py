#!/usr/bin/env python3
"""Routing-axis benchmark: same tasks, same model, one axis changed — the routing condition.

Conditions
  none         OpenCode with external plugins disabled (--pure); provider default effort
  always-low   --pure plus reasoningEffort=low on every call
  always-high  --pure plus reasoningEffort=high on every call (OPENCODE_CONFIG_CONTENT)
  advisory     effort-lanes plugin loaded, enforcement off (context injection only)
  enforce      effort-lanes plugin loaded, EFFORT_LANES_ENFORCE=1 (reasoningEffort per lane)
  enforce-low  enforce plus a config override that changes only the fast lane to low

Each run copies the fixture into a fresh temp directory, runs `opencode run --format json`,
sums step tokens/cost from the event stream, then executes verify/<task>.py against the
result. Rows are appended to a JSONL file; `summarize` turns a file into a table and checks
the predictions written in README.md before the first run.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import signal
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPENCODE = os.environ.get("OPENCODE_BIN", "opencode")
PLUGIN = Path.home() / ".config" / "opencode" / "plugins" / "effort-lanes.js"
LANES = ("fast", "daily", "deep", "critical")
CONDITIONS = {
    # pure = external plugins disabled; effort = reasoningEffort forced for every call;
    # lane_config = a config file the router reads, so a single lane's effort can change.
    "none": {"pure": True},
    "always-low": {"pure": True, "effort": "low"},
    "always-high": {"pure": True, "effort": "high"},
    "advisory": {"pure": False},
    "enforce": {"pure": False, "env": {"EFFORT_LANES_ENFORCE": "1"}},
    "enforce-low": {"pure": False, "env": {"EFFORT_LANES_ENFORCE": "1"},
                    "lane_config": {"lanes": {"fast": {"effort": "low"}}}},
}


def config_content(model: str, effort: str) -> str:
    provider, model_id = model.split("/", 1)
    return json.dumps({"provider": {provider: {"models": {model_id: {"options": {"reasoningEffort": effort}}}}}})


FATAL_STATUS = (401, 402, 403)


def fatal_error(out: str) -> str | None:
    """An account-level provider failure: retrying the other 74 runs cannot help."""
    for line in out.splitlines():
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") != "error":
            continue
        data = (event.get("error") or {}).get("data") or {}
        if data.get("statusCode") in FATAL_STATUS:
            return f"HTTP {data['statusCode']}: {str(data.get('message', ''))[:200]}"
    return None


def parse_events(out: str) -> tuple[dict, float, int, str, int]:
    tokens = {"input": 0, "output": 0, "reasoning": 0, "cache_read": 0, "cache_write": 0}
    cost, steps, errors = 0.0, 0, 0
    texts: dict[str, str] = {}
    for line in out.splitlines():
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        part = event.get("part") or {}
        kind = event.get("type")
        if kind == "step_finish":
            steps += 1
            tk = part.get("tokens") or {}
            for key in ("input", "output", "reasoning"):
                tokens[key] += int(tk.get(key, 0) or 0)
            tokens["cache_read"] += int((tk.get("cache") or {}).get("read", 0) or 0)
            tokens["cache_write"] += int((tk.get("cache") or {}).get("write", 0) or 0)
            cost += float(part.get("cost") or 0)
        elif kind == "text" and part.get("type") == "text" and not part.get("synthetic"):
            texts[part.get("id", str(len(texts)))] = part.get("text", "")
        elif kind == "error":
            errors += 1
    return tokens, cost, steps, "\n".join(texts.values()), errors


def routed_lane(debug: Path) -> str | None:
    lane = None
    if debug.exists():
        for line in debug.read_text().splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if record.get("hook") == "chat.message" and record.get("lane"):
                lane = record["lane"]
    return lane


def routed_effort(debug: Path) -> str | None:
    """The effort actually applied to the API call, read back from the plugin's own log.

    The plugin logs the lane's effort on every turn but only applies it when enforcement is
    on, so an advisory turn must report None rather than the value it would have used.
    """
    effort = None
    if debug.exists():
        for line in debug.read_text().splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if record.get("hook") == "chat.params" and record.get("effort") and record.get("enforce"):
                effort = record["effort"]
    return effort


def run_one(task: dict, cond: str, model: str, timeout: int) -> dict:
    spec = CONDITIONS[cond]
    work = Path(tempfile.mkdtemp(prefix=f"bench-{task['id']}-{cond}-"))
    shutil.copytree(HERE / "fixtures" / "todo", work, dirs_exist_ok=True)
    env = dict(os.environ)
    env.pop("EFFORT_LANES_ENFORCE", None)
    env.pop("OPENCODE_CONFIG_CONTENT", None)
    env.update(spec.get("env", {}))
    debug = work / ".bench_lanes.jsonl"
    env["EFFORT_LANES_DEBUG"] = str(debug)
    # isolate the router from this machine's personal config and test the repository's router, not an installed copy
    lane_config = spec.get("lane_config")
    config_path = work / ".effort-lanes-config.json"
    if lane_config:
        config_path.write_text(json.dumps(lane_config))
    env["EFFORT_LANES_CONFIG"] = str(config_path) if lane_config else str(work / ".no-global-config.json")
    env["EFFORT_LANES_ROUTER"] = str(HERE.parent / "router" / "effort_router.py")
    if spec.get("effort"):
        env["OPENCODE_CONFIG_CONTENT"] = config_content(model, spec["effort"])
    cmd = [OPENCODE, "run", "--format", "json", "-m", model, "--dir", str(work), "--title", f"bench {task['id']} {cond}"]
    if spec.get("pure"):
        cmd.append("--pure")
    cmd.append(task["prompt"])

    # Never capture through a pipe: OpenCode leaves a server process holding the inherited
    # stdout, so subprocess.run(capture_output=True, timeout=...) blocks past its own deadline
    # (measured: two runs sat for ~54 minutes against a 300 s timeout). Redirect to a file and
    # kill the whole process group instead.
    started = time.time()
    timed_out = False
    run_log = work / ".bench_run.log"
    with run_log.open("w") as sink:
        proc = subprocess.Popen(cmd, cwd=work, env=env, stdin=subprocess.DEVNULL,
                                stdout=sink, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=30)
    wall = time.time() - started
    out = run_log.read_text(errors="ignore")

    tokens, cost, steps, answer, errors = parse_events(out)
    fatal = fatal_error(out)
    answer_file = work / ".bench_answer.txt"
    answer_file.write_text(answer)
    verify = subprocess.run(
        [sys.executable, str(HERE / "verify" / f"{task['id']}.py")], cwd=HERE / "verify",
        env={**env, "WORKDIR": str(work), "ANSWER_FILE": str(answer_file)},
        capture_output=True, text=True, timeout=120,
    )
    return {
        "task": task["id"], "lane_expected": task["lane"], "lane_routed": routed_lane(debug),
        "effort_applied": routed_effort(debug),
        "condition": cond, "model": model, "pass": verify.returncode == 0 and not timed_out,
        "verify": (verify.stdout + verify.stderr).strip()[-160:],
        "tokens": tokens, "cost": round(cost, 5), "wall_s": round(wall, 1), "steps": steps,
        "errors": errors, "timed_out": timed_out, "fatal": fatal, "log": str(run_log),
        "workdir": str(work), "time": int(started),
    }


def cmd_run(args: argparse.Namespace) -> int:
    tasks = json.loads((HERE / "tasks.json").read_text())
    wanted = set(args.tasks.split(",")) if args.tasks else None
    tasks = [t for t in tasks if wanted is None or t["id"] in wanted]
    conds = args.conditions.split(",")
    for cond in conds:
        if cond not in CONDITIONS:
            print(f"unknown condition: {cond}", file=sys.stderr)
            return 1
        if not CONDITIONS[cond]["pure"] and not PLUGIN.exists():
            print(f"condition {cond} needs the OpenCode plugin at {PLUGIN}; run install.sh --runtimes opencode", file=sys.stderr)
            return 1
    out = Path(args.out) if args.out else HERE / "results" / f"{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    total = len(tasks) * len(conds) * args.repeat
    done = 0
    with out.open("a") as fh:
        for rep in range(args.repeat):
            for task in tasks:
                for cond in conds:
                    row = run_one(task, cond, args.model, args.timeout)
                    row["repeat"] = rep
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                    done += 1
                    if row["fatal"]:
                        print(f"ABORT after {done} run(s): {row['fatal']}", file=sys.stderr)
                        print(f"  runtime log: {row['log']}", file=sys.stderr)
                        print(f"results: {out}")
                        return 2
                    print(f"[{done}/{total}] {task['id']:3} {cond:12} pass={row['pass']!s:5} lane={row['lane_routed']} "
                          f"in={row['tokens']['input']}+cache{row['tokens']['cache_read']} out={row['tokens']['output']} reason={row['tokens']['reasoning']} "
                          f"effort={row['effort_applied']} cost={row['cost']} wall={row['wall_s']}s", flush=True)
    print(f"results: {out}")
    return 0


def mean(values: list[float]) -> float:
    return round(statistics.mean(values), 1) if values else 0.0


def load_rows(path: str) -> tuple[list[dict], int]:
    """Rows usable for comparison, plus how many were dropped as infrastructure failures."""
    all_rows = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    rows = [r for r in all_rows if not r.get("timed_out") and not r.get("fatal")]
    return rows, len(all_rows) - len(rows)


def cmd_summarize(args: argparse.Namespace) -> int:
    rows, dropped = load_rows(args.file)
    if dropped:
        print(f"note: {dropped} run(s) excluded as infrastructure failures (timeout or provider error)\n")
    if not rows:
        print("no usable rows")
        return 1
    conds = [c for c in CONDITIONS if any(r["condition"] == c for r in rows)]
    print(f"model: {sorted({r['model'] for r in rows})}  rows: {len(rows)}\n")
    print("| lane | condition | n | pass | input+cache | output | reasoning | cost $ | wall s |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    cell: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        cell.setdefault((r["lane_expected"], r["condition"]), []).append(r)
    for lane in LANES:
        for cond in conds:
            group = cell.get((lane, cond), [])
            if not group:
                continue
            print(f"| {lane} | {cond} | {len(group)} | {sum(r['pass'] for r in group)}/{len(group)} | "
                  f"{mean([r['tokens']['input'] + r['tokens']['cache_read'] for r in group])} | {mean([r['tokens']['output'] for r in group])} | "
                  f"{mean([r['tokens']['reasoning'] for r in group])} | {round(statistics.mean([r['cost'] for r in group]), 4)} | "
                  f"{mean([r['wall_s'] for r in group])} |")

    def stat(lane: str, cond: str, key):
        group = cell.get((lane, cond), [])
        return (statistics.mean([key(r) for r in group]) if group else None), len(group)

    print("\nPredictions (from README.md):")
    def verdict(name: str, ok: bool | None, detail: str) -> None:
        print(f"  {'PASS' if ok else 'FAIL' if ok is False else 'INCONCLUSIVE'}  {name}: {detail}")

    for lane in ("fast", "daily"):
        hi, n1 = stat(lane, "always-high", lambda r: r["tokens"]["reasoning"])
        en, n2 = stat(lane, "enforce", lambda r: r["tokens"]["reasoning"])
        if hi is None or en is None:
            verdict(f"P1 {lane}: enforce reasons less than always-high", None, "missing condition")
        else:
            verdict(f"P1 {lane}: enforce reasons less than always-high", en < hi, f"enforce={en:.0f} always-high={hi:.0f} (n={n2},{n1})")
    for lane in ("fast", "deep", "critical"):
        ps = {c: stat(lane, c, lambda r: 1.0 if r["pass"] else 0.0)[0] for c in conds}
        present = {c: v for c, v in ps.items() if v is not None}
        if len(present) < 2:
            verdict(f"P2 {lane}: pass rate does not drop under enforce", None, "need two conditions")
        else:
            en = present.get("enforce")
            best = max(present.values())
            verdict(f"P2 {lane}: pass rate does not drop under enforce", None if en is None else en >= best - 0.2,
                    " ".join(f"{c}={v:.0%}" for c, v in present.items()))
    routed = [r for r in rows if r["condition"] in ("advisory", "enforce")]
    if routed:
        agree = sum(r["lane_routed"] == r["lane_expected"] for r in routed)
        verdict("P3 routed lane agrees with the task label", agree / len(routed) >= 0.85, f"{agree}/{len(routed)}")
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    """Offline: does the router send each task prompt to its labeled lane? No model runs."""
    tasks = json.loads((HERE / "tasks.json").read_text())
    env = {**os.environ, "EFFORT_LANES_CONFIG": str(HERE / "results" / ".no-global-config.json")}
    agree = 0
    for task in tasks:
        result = subprocess.run([sys.executable, str(HERE.parent / "router" / "effort_router.py"), "--classify",
                                 "--prompt", task["prompt"], "--cwd", str(HERE / "fixtures" / "todo")],
                                capture_output=True, text=True, env=env, check=True)
        lane = json.loads(result.stdout)["lane"]
        mark = "ok  " if lane == task["lane"] else "MISS"
        agree += lane == task["lane"]
        print(f"{mark} {task['id']:3} {task['lane']:8} -> {lane:8} {task['prompt'][:60]}")
    print(f"agreement: {agree}/{len(tasks)}")
    return 0 if agree == len(tasks) else 1


def cmd_decide(args: argparse.Namespace) -> int:
    """Apply the sealed decision rule from docs/goals/GOAL-fast-lane-effort.md to a results file.

    Order matters and resolves an ambiguity in the sealed table: C (pass-rate loss) is checked
    first, then B (difference inside the 15% noise band), then A (a reduction beyond that band).
    A therefore means "clearly lower", not merely "lower".
    """
    rows, dropped = load_rows(args.file)
    if dropped:
        print(f"note: {dropped} run(s) excluded as infrastructure failures (timeout or provider error)\n")
    fast = [r for r in rows if r["lane_expected"] == "fast"]
    if not fast:
        print("no fast-lane rows")
        return 1

    def group(cond: str) -> list[dict]:
        return [r for r in fast if r["condition"] == cond]

    def reasoning(cond: str) -> float | None:
        g = group(cond)
        return statistics.mean([r["tokens"]["reasoning"] for r in g]) if g else None

    def passes(cond: str) -> tuple[int, int]:
        g = group(cond)
        return sum(r["pass"] for r in g), len(g)

    enforce, low = reasoning("enforce"), reasoning("enforce-low")
    none_r, adv, always_low = reasoning("none"), reasoning("advisory"), reasoning("always-low")
    ep, en = passes("enforce")
    lp, ln = passes("enforce-low")

    print("fast lane, mean reasoning tokens:")
    for cond in ("none", "always-low", "always-high", "advisory", "enforce", "enforce-low"):
        value, (p, n) = reasoning(cond), passes(cond)
        if value is not None:
            print(f"  {cond:12} {value:7.1f}   pass {p}/{n}")

    if enforce is None or low is None:
        print("\nINCONCLUSIVE: need both enforce and enforce-low")
        return 1

    delta = (low - enforce) / enforce if enforce else 0.0
    if lp <= ep - 2:
        case, action = "C", "keep medium; enforce-low lost pass rate"
    elif abs(delta) <= 0.15:
        case, action = "B", "keep medium; the effort knob is not the cause (inside the 15% noise band)"
    elif low < enforce:
        case, action = "A", "fast lane default becomes low"
    else:
        case, action = "C*", "keep medium; enforce-low was worse (case outside the sealed table)"
    print(f"\ncase {case}: {action}")
    print(f"  enforce={enforce:.1f} enforce-low={low:.1f} delta={delta:+.0%} pass {ep}/{en} vs {lp}/{ln}")

    if none_r is not None and adv is not None:
        excess = (adv - none_r) / none_r if none_r else float("inf")
        print(f"case D: advisory vs none {excess:+.0%} -> " +
              ("the injected context is itself the cost on fast prompts" if excess > 0.25 else "context cost is not dominant"))
    if none_r is not None and always_low is not None:
        print(f"case E: always-low vs none {always_low:.1f} vs {none_r:.1f} -> " +
              ("provider default sits above low" if always_low < none_r else "provider default is already at or below low"))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--model", default="opencode-go/gpt-5.6-luna")
    run.add_argument("--conditions", default=",".join(CONDITIONS))
    run.add_argument("--tasks", default="", help="comma-separated task ids (default: all)")
    run.add_argument("--repeat", type=int, default=1)
    run.add_argument("--timeout", type=int, default=600)
    run.add_argument("--out", default="")
    run.set_defaults(func=cmd_run)
    route = sub.add_parser("route", help="offline routing agreement for tasks.json")
    route.set_defaults(func=cmd_route)
    dec = sub.add_parser("decide", help="apply the sealed fast-lane decision rule to a results file")
    dec.add_argument("file")
    dec.set_defaults(func=cmd_decide)
    summ = sub.add_parser("summarize")
    summ.add_argument("file")
    summ.set_defaults(func=cmd_summarize)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
