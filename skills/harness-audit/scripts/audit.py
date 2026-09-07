#!/usr/bin/env python3
"""Recovery-rate audit for installed skills, measured from Claude Code session logs.

A skill is DEAD only when it has zero invocations AND no entry point (no command or other
skill names it). Logs live in ~/.claude/projects/<encoded-cwd>/*.jsonl; a project's logs are
every directory whose encoded name starts with the project's encoded path (subdirectory
sessions belong to the project).
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

LOG_ROOT = Path.home() / ".claude" / "projects"
CAP = 18


def encode(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(path.resolve()))


def skills_of(project: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for base in (project / ".claude" / "skills", project / ".codex" / "skills", project / ".agents" / "skills"):
        if not base.is_dir():
            continue
        for skill_md in base.glob("*/SKILL.md"):
            if "_archive" in skill_md.parts:
                continue
            found[skill_md.parent.name] = skill_md
    return found


def entry_points(project: Path, skills: dict[str, Path]) -> dict[str, set[str]]:
    """Names referenced by commands or by *other* skills' bodies."""
    refs: dict[str, set[str]] = {name: set() for name in skills}
    sources: list[tuple[str, Path]] = []
    for cmd in (project / ".claude" / "commands").glob("*.md"):
        sources.append((f"command:{cmd.stem}", cmd))
    for name, path in skills.items():
        sources.append((f"skill:{name}", path))
    for label, path in sources:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name in skills:
            if label == f"skill:{name}":
                continue
            if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text):
                refs[name].add(label)
    return refs


def invocations(project: Path, skills: dict[str, Path]) -> tuple[int, Counter[str]]:
    prefix = encode(project)
    counts: Counter[str] = Counter()
    sessions = 0
    if not LOG_ROOT.is_dir():
        return 0, counts
    for log_dir in LOG_ROOT.iterdir():
        if not log_dir.is_dir() or not log_dir.name.startswith(prefix):
            continue
        for log in log_dir.glob("*.jsonl"):
            sessions += 1
            try:
                text = log.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for name in skills:
                # model-invoked Skill tool calls and user-typed slash commands
                counts[name] += len(re.findall(rf'"skill":\s*"{re.escape(name)}"', text))
                counts[name] += len(re.findall(rf"<command-name>/?{re.escape(name)}</command-name>", text))
    return sessions, counts


def audit(project: Path) -> dict[str, object]:
    skills = skills_of(project)
    sessions, counts = invocations(project, skills)
    refs = entry_points(project, skills)
    rows = []
    for name in sorted(skills):
        hits = counts[name]
        verdict = "ALIVE" if hits else ("LINKED" if refs[name] else "DEAD")
        rows.append({"skill": name, "invocations": hits, "entry_points": sorted(refs[name]), "verdict": verdict})
    alive = sum(1 for r in rows if r["invocations"])
    return {
        "project": str(project),
        "sessions": sessions,
        "installed": len(rows),
        "cap": CAP,
        "over_cap": len(rows) > CAP,
        "recovery_rate": round(alive / len(rows), 2) if rows else None,
        "skills": rows,
    }


def render(report: dict[str, object]) -> str:
    lines = [f"{report['project']}  sessions={report['sessions']}  installed={report['installed']}/{report['cap']}"
             f"  recovery={report['recovery_rate']}"]
    if report["over_cap"]:
        lines.append(f"  WARNING: more than {CAP} skills installed; recovery rate drops sharply above this")
    if report["sessions"] == 0:
        lines.append("  note: no sessions found; verdicts are not meaningful for an idle project")
    for row in report["skills"]:  # type: ignore[union-attr]
        refs = ", ".join(row["entry_points"]) or "-"
        lines.append(f"  {row['verdict']:6} {row['invocations']:4}  {row['skill']}  ({refs})")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="project directory (default: current)")
    parser.add_argument("--root", help="audit every git project directly under this root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.root:
        projects = sorted(p for p in Path(args.root).expanduser().iterdir() if (p / ".git").exists())
    else:
        projects = [Path(args.project).expanduser()]
    reports = [audit(p) for p in projects]
    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        print("\n\n".join(render(r) for r in reports))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
