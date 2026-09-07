#!/usr/bin/env python3
"""Deterministic prompt-to-effort routing for Codex and Claude Code hooks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    lane: str
    reason: str
    context: str


LANES = {
    "fast": ("Luna/medium", "Haiku/medium", "explorer", "effort-fast"),
    "daily": ("Terra/medium", "Sonnet/medium", "explorer", "effort-daily"),
    "deep": ("Sol/high", "Sonnet/high", "worker", "effort-deep"),
    "critical": ("Astra/high", "Opus/high", "default", "effort-critical"),
}

CRITICAL = (
    "production deploy", "deploy to production", "운영 배포", "프로덕션 배포",
    "security", "보안", "vulnerability", "취약점", "credential", "secret",
    "payment", "결제", "drop table", "irreversible", "복구 불가", "live robot",
    "실제 로봇", "실기기", "safety", "안전", "architecture decision", "최종 판정",
    "two failed attempts", "두 번 실패", "repeatedly failed", "계속 실패",
)
DEEP = (
    "implement", "build", "refactor", "fix", "debug", "root cause", "end-to-end",
    "integration", "e2e", "automate", "구현", "만들어", "리팩터", "고쳐",
    "디버그", "근본 원인", "통합", "자동화", "테스트해", "검증해", "재현",
)
DAILY = (
    "research", "review", "analyze", "explain", "compare", "summarize", "docs",
    "조사", "검토", "분석", "설명", "비교", "요약", "문서", "상태 확인",
)
FAST = (
    "find", "list", "count", "version", "filename", "format", "typo", "찾아",
    "목록", "개수", "버전", "파일명", "한 줄", "오탈자", "정렬", "조회",
)


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _explicit_lane(text: str) -> str | None:
    for lane in LANES:
        if re.search(rf"(?:effort-|lane\s*[=:]\s*|모드\s*){lane}\b", text):
            return lane
    return None


def classify(prompt: str) -> Route:
    text = prompt.casefold()

    if _contains(text, CRITICAL):
        lane, reason = "critical", "safety, production, security, irreversible, or repeated-failure signal"
    elif explicit := _explicit_lane(text):
        lane, reason = explicit, "explicit lane request"
    elif _contains(text, DEEP):
        lane, reason = "deep", "implementation or end-to-end verification signal"
    elif len(prompt.strip()) <= 140 and _contains(text, FAST):
        lane, reason = "fast", "short exact or mechanical request"
    elif _contains(text, DAILY):
        lane, reason = "daily", "read-heavy analysis or explanation signal"
    else:
        lane, reason = "daily", "balanced default for an ambiguous task"

    codex_model, claude_model, codex_agent, claude_agent = LANES[lane]
    context = (
        f"[EFFORT ROUTER] lane={lane.upper()}; reason={reason}. "
        f"Codex target={codex_model}, verified built-in agent={codex_agent}; "
        f"Claude target={claude_model}, subagent={claude_agent}. "
        "The current parent model is unchanged; never claim it switched. "
        "Do trivial work directly. Delegate only when at least two substantial tracks are independent and bounded. "
        "Use one writer unless paths are explicitly disjoint, and keep final verification with the parent. "
        "User instructions and the nearest project rules always win."
    )
    return Route(lane=lane, reason=reason, context=context)


def hook(payload: dict[str, object]) -> dict[str, object] | None:
    if payload.get("hook_event_name") != "UserPromptSubmit":
        return None
    route = classify(str(payload.get("prompt", "")))
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": route.context,
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classify", action="store_true")
    parser.add_argument("--prompt", default="")
    args = parser.parse_args()

    if args.classify:
        route = classify(args.prompt)
        print(json.dumps({"lane": route.lane, "reason": route.reason}, ensure_ascii=False))
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    output = hook(payload)
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
