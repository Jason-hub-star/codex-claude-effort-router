#!/usr/bin/env python3
"""Deterministic prompt-to-effort routing shared by every supported agent runtime.

Runtimes: Codex, Claude Code (shell hooks) and OpenCode, OpenClaw, Hermes (thin plugins
that call this file with ``--classify --json``). The classifier never executes user text,
never blocks a prompt, and fails open on malformed input or malformed configuration.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CONFIG_NAME = ".effort-lanes.json"
GLOBAL_CONFIG = Path(os.environ.get("EFFORT_LANES_CONFIG") or (Path.home() / ".config" / "effort-lanes" / "config.json"))
LANE_ORDER = ("fast", "daily", "deep", "critical")
RUNTIMES = ("hook", "codex", "claude", "opencode", "openclaw", "hermes", "generic")


@dataclass(frozen=True)
class Route:
    lane: str
    reason: str
    context: str
    effort: str
    targets: dict[str, str]


# Lane -> effort level plus per-runtime starting points. These are defaults, not benchmarks.
LANES: dict[str, dict[str, str]] = {
    "fast": {
        "effort": "medium",
        "codex": "Luna/medium", "codex_agent": "explorer",
        "claude": "Haiku/medium", "claude_agent": "effort-fast",
    },
    "daily": {
        "effort": "medium",
        "codex": "Terra/medium", "codex_agent": "explorer",
        "claude": "Sonnet/medium", "claude_agent": "effort-daily",
    },
    "deep": {
        "effort": "high",
        "codex": "Sol/high", "codex_agent": "worker",
        "claude": "Sonnet/high", "claude_agent": "effort-deep",
    },
    "critical": {
        "effort": "high",
        "codex": "Astra/high", "codex_agent": "default",
        "claude": "Opus/high", "claude_agent": "effort-critical",
    },
}

KEYWORDS: dict[str, tuple[str, ...]] = {
    "critical": (
        "production deploy", "deploy to production", "운영 배포", "프로덕션 배포",
        "security", "보안", "vulnerability", "취약점", "credential", "secret",
        "payment", "결제", "drop table", "irreversible", "복구 불가", "live robot",
        "실제 로봇", "실기기", "safety", "안전", "architecture decision", "최종 판정",
        "two failed attempts", "두 번 실패", "repeatedly failed", "계속 실패",
    ),
    "deep": (
        "implement", "build", "refactor", "fix", "debug", "root cause", "end-to-end",
        "integration", "e2e", "automate", "구현", "만들어", "리팩터", "고쳐",
        "디버그", "근본 원인", "통합", "자동화", "테스트해", "검증해", "재현",
    ),
    "daily": (
        "research", "review", "analyze", "explain", "compare", "summarize", "docs",
        "조사", "검토", "분석", "설명", "비교", "요약", "문서", "상태 확인",
    ),
    "fast": (
        "find", "list", "count", "version", "filename", "format", "typo", "찾아",
        "목록", "개수", "버전", "파일명", "한 줄", "오탈자", "정렬", "조회",
    ),
}

GUIDANCE = (
    "The current parent model is unchanged; never claim it switched. "
    "Do trivial work directly. Delegate only when at least two substantial tracks are independent and bounded. "
    "Use one writer unless paths are explicitly disjoint, and keep final verification with the parent. "
    "User instructions and the nearest project rules always win."
)


# --- configuration -----------------------------------------------------------------

def _read_json(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _project_config_path(cwd: str) -> Path | None:
    try:
        current = Path(cwd).resolve()
    except (OSError, RuntimeError):
        return None
    for directory in (current, *current.parents):
        candidate = directory / CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None


def load_config(cwd: str | None) -> dict[str, object]:
    """Merge the global config with the nearest project config. Malformed files are ignored."""
    merged: dict[str, object] = {}
    sources = [GLOBAL_CONFIG]
    project = _project_config_path(cwd or os.getcwd())
    if project is not None:
        sources.append(project)
    for path in sources:
        for key, value in _read_json(path).items():
            if key == "keywords" and isinstance(value, dict):
                existing = dict(merged.get("keywords", {}))  # type: ignore[arg-type]
                for lane, terms in value.items():
                    if lane in LANES and isinstance(terms, list):
                        existing[lane] = list(existing.get(lane, ())) + [str(t) for t in terms]
                merged["keywords"] = existing
            elif key == "lanes" and isinstance(value, dict):
                existing_lanes = dict(merged.get("lanes", {}))  # type: ignore[arg-type]
                for lane, fields in value.items():
                    if lane in LANES and isinstance(fields, dict):
                        existing_lanes[lane] = {**existing_lanes.get(lane, {}), **{str(k): str(v) for k, v in fields.items()}}
                merged["lanes"] = existing_lanes
            else:
                merged[key] = value
    return merged


def _lane_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value in LANES else None


# --- classification ----------------------------------------------------------------

def _contains(text: str, terms: tuple[str, ...] | list[str]) -> bool:
    return any(term.casefold() in text for term in terms)


def _explicit_lane(text: str) -> str | None:
    for lane in LANES:
        if re.search(rf"(?:effort-|lane\s*[=:]\s*|모드\s*){lane}\b", text):
            return lane
    return None


def _raise_to_floor(lane: str, floor: str | None) -> str:
    if floor is None or LANE_ORDER.index(lane) >= LANE_ORDER.index(floor):
        return lane
    return floor


def classify(prompt: str, cwd: str | None = None, config: dict[str, object] | None = None) -> Route:
    cfg = load_config(cwd) if config is None else config
    text = prompt.casefold()
    extra = cfg.get("keywords", {}) if isinstance(cfg.get("keywords"), dict) else {}

    def terms(lane: str) -> tuple[str, ...]:
        return KEYWORDS[lane] + tuple(extra.get(lane, ()))  # type: ignore[arg-type]

    default_lane = _lane_or_none(cfg.get("default_lane")) or "daily"
    floor = _lane_or_none(cfg.get("floor"))
    fast_max = cfg.get("fast_max_chars", 140)
    fast_max = fast_max if isinstance(fast_max, int) and fast_max > 0 else 140

    if _contains(text, terms("critical")):
        lane, reason = "critical", "safety, production, security, irreversible, or repeated-failure signal"
    elif explicit := _explicit_lane(text):
        lane, reason = explicit, "explicit lane request"
    elif _contains(text, terms("deep")):
        lane, reason = "deep", "implementation or end-to-end verification signal"
    elif len(prompt.strip()) <= fast_max and _contains(text, terms("fast")):
        lane, reason = "fast", "short exact or mechanical request"
    elif _contains(text, terms("daily")):
        lane, reason = "daily", "read-heavy analysis or explanation signal"
    else:
        lane, reason = default_lane, "balanced default for an ambiguous task"

    if reason != "explicit lane request":
        raised = _raise_to_floor(lane, floor)
        if raised != lane:
            lane, reason = raised, "project floor"

    targets = dict(LANES[lane])
    overrides = cfg.get("lanes", {})
    if isinstance(overrides, dict) and isinstance(overrides.get(lane), dict):
        targets.update({str(k): str(v) for k, v in overrides[lane].items()})
    effort = targets.pop("effort", LANES[lane]["effort"])
    context = render_context(lane, reason, effort, targets, runtime="hook")
    return Route(lane=lane, reason=reason, context=context, effort=effort, targets=targets)


def render_context(lane: str, reason: str, effort: str, targets: dict[str, str], runtime: str) -> str:
    head = f"[EFFORT LANES] lane={lane.upper()}; reason={reason}; effort={effort}. "
    if runtime in ("hook", "codex", "claude"):
        body = (
            f"Codex target={targets['codex']}, verified built-in agent={targets['codex_agent']}; "
            f"Claude target={targets['claude']}, subagent={targets['claude_agent']}. "
        )
    else:
        model = targets.get(runtime)
        body = f"Suggested {runtime} model={model}. " if model else ""
    return head + body + GUIDANCE


# --- hook + CLI ----------------------------------------------------------------------

def hook(payload: dict[str, object]) -> dict[str, object] | None:
    """Shell-hook entry point.

    - Codex / Claude Code: ``UserPromptSubmit`` → ``hookSpecificOutput.additionalContext``.
    - Hermes shell hooks: ``pre_llm_call`` (prompt under ``extra.user_message``) → ``{"context": ...}``.
    """
    event = payload.get("hook_event_name")
    cwd = payload.get("cwd")
    cwd = cwd if isinstance(cwd, str) else None
    if event == "UserPromptSubmit":
        route = classify(str(payload.get("prompt", "")), cwd=cwd)
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": route.context,
            }
        }
    if event == "pre_llm_call":
        extra = payload.get("extra")
        message = extra.get("user_message") if isinstance(extra, dict) else payload.get("user_message")
        text = message if isinstance(message, str) else str(message or "")
        if not text.strip():
            return None
        route = classify(text, cwd=cwd)
        return {"context": render_context(route.lane, route.reason, route.effort, route.targets, "hermes")}
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classify", action="store_true", help="classify --prompt instead of reading hook JSON")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--cwd", default=None, help="project directory used to locate .effort-lanes.json")
    parser.add_argument("--runtime", default="hook", choices=RUNTIMES, help="shape the context string for a runtime")
    parser.add_argument("--json", action="store_true", help="emit lane, reason, effort, targets, and context")
    args = parser.parse_args()

    if args.classify:
        route = classify(args.prompt, cwd=args.cwd)
        context = render_context(route.lane, route.reason, route.effort, route.targets, args.runtime)
        if args.json:
            print(json.dumps({
                "lane": route.lane, "reason": route.reason, "effort": route.effort,
                "targets": route.targets, "context": context,
            }, ensure_ascii=False))
        else:
            print(json.dumps({"lane": route.lane, "reason": route.reason}, ensure_ascii=False))
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0
    output = hook(payload)
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
