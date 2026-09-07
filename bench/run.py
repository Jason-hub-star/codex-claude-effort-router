#!/usr/bin/env python3
"""Routing-axis benchmark: same tasks, same model, one axis changed — the routing condition.

Conditions
  none         OpenCode with external plugins disabled (--pure); provider default effort
  always-high  --pure plus reasoningEffort=high on every call (OPENCODE_CONFIG_CONTENT)
  advisory     effort-lanes plugin loaded, enforcement off (context injection only)
  enforce      effort-lanes plugin loaded, EFFORT_LANES_ENFORCE=1 (reasoningEffort per lane)

Each run copies the fixture into a fresh temp directory, runs `opencode run --format json`,
sums step tokens/cost from the event stream, then executes verify/<task>.py against the
result. Rows are appended to a JSONL file; `summarize` turns a file into a table and checks
the predictions written in README.md before the first run.
"""

from __future__ import annotations

import argparse
import json
import os
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
    "none": {"pure": True},
    "always-high": {"pure": True, "effort": "high"},
    "advisory": {"pure": False},
    "enforce": {"pure": False, "env": {"EFFORT_LANES_ENFORCE": "1"}},
}


def config_content(model: str, effort: str) -> str:
    provider, model_id = model.split("/", 1)
    return json.dumps({"provider": {provider: {"models": {model_id: {"options": {"reasoningEffort": effort}}}}}})


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
    if spec.get("effort"):
        env["OPENCODE_CONFIG_CONTENT"] = config_content(model, spec["effort"])
    cmd = [OPENCODE, "run", "--format", "json", "-m", model, "--dir", str(work), "--title", f"bench {task['id']} {cond}"]
    if spec.get("pure"):
        cmd.append("--pure")
    cmd.append(task["prompt"])

    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(cmd, cwd=work, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
        out = proc.stdout
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        raw = exc.stdout or b""
        out = raw.decode(errors="ignore") if isinstance(raw, bytes) else raw
    wall = time.time() - started

    tokens, cost, steps, answer, errors = parse_events(out)
    answer_file = work / ".bench_answer.txt"
    answer_file.write_text(answer)
    verify = subprocess.run(
        [sys.executable, str(HERE / "verify" / f"{task['id']}.py")], cwd=HERE / "verify",
        env={**env, "WORKDIR": str(work), "ANSWER_FILE": str(answer_file)},
        capture_output=True, text=True, timeout=120,
    )
    return {
        "task": task["id"], "lane_expected": task["lane"], "lane_routed": routed_lane(debug),
        "condition": cond, "model": model, "pass": verify.returncode == 0 and not timed_out,
        "verify": (verify.stdout + verify.stderr).strip()[-160:],
        "tokens": tokens, "cost": round(cost, 5), "wall_s": round(wall, 1), "steps": steps,
        "errors": errors, "timed_out": timed_out, "workdir": str(work), "time": int(started),
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
                    print(f"[{done}/{total}] {task['id']:3} {cond:12} pass={row['pass']!s:5} lane={row['lane_routed']} "
                          f"in={row['tokens']['input']}+cache{row['tokens']['cache_read']} out={row['tokens']['output']} reason={row['tokens']['reasoning']} "
                          f"cost={row['cost']} wall={row['wall_s']}s", flush=True)
    print(f"results: {out}")
    return 0


def mean(values: list[float]) -> float:
    return round(statistics.mean(values), 1) if values else 0.0


def cmd_summarize(args: argparse.Namespace) -> int:
    rows = [json.loads(l) for l in Path(args.file).read_text().splitlines() if l.strip()]
    if not rows:
        print("no rows")
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
    summ = sub.add_parser("summarize")
    summ.add_argument("file")
    summ.set_defaults(func=cmd_summarize)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
