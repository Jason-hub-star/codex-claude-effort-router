---
name: goal-contract
description: Convert multi-turn work into a runtime-neutral goal brief whose completion is decided by evidence. Use for “write a goal”, “goal brief”, “골”, performance work, flaky-test investigations, migrations, or any task requiring repeated verified passes—not simple one-turn requests.
---

# Goal Contract

Create one brief that Codex, Claude Code, or another agent can execute without changing the finish line.

## Required contract

1. **Outcome** — measurable state that must become true.
2. **Verification** — runnable commands or inspectable artifacts that prove it.
3. **Constraints** — behavior or quality that must not regress.
4. **Boundaries** — allowed and forbidden files, systems, data, and actions.
5. **Iteration policy** — how failed passes choose the next smallest change.
6. **Blocked stop** — when the agent must stop and report instead of guessing.

Human taste or approval belongs between goals, not inside an automated completion check.

## Output

Write a compact one-line goal plus a Markdown brief containing the six fields and an execution log. Use shell-runnable verification when possible; do not make an internal agent tool the only proof of success.

## Next

Use `phase-loop` when the goal becomes three or more ordered implementation phases. If verification cannot be written, return to `converge-plan`.
