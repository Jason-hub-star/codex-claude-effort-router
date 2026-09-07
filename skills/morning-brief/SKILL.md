---
name: morning-brief
description: Open a work session by checking the previous handoff, recent commits, uncommitted work, failed checks, and the single best next action. Use for “morning”, “start the day”, “what did I leave yesterday?”, “아침”, or “시작하자”.
---

# Morning Brief

Start from evidence left by the previous session. This is read-only unless the user separately asks to clean or archive files.

## Workflow

1. Read the nearest project instructions and one current status or handoff document.
2. Inspect recent commits and working-tree changes without modifying them.
3. Find the most recent recorded verification result. Missing evidence means unknown, not pass.
4. Identify one blocker or red signal that could invalidate today’s work.
5. Recommend exactly one next action.

## Output

- Previous result: last known completed outcome
- Red signal: failed, missing, or stale evidence
- Uncommitted work: concise status
- Blocker: one, or none
- Next action: exactly one

Do not automatically archive, delete, reset, or commit anything.

## Next

If the desired outcome still needs comparison with the code, use `aim-before-build`.
