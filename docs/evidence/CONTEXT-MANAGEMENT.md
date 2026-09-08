# Context management evidence

Last updated: 2026-09-08 (Asia/Seoul).

## Decision

Do **not** auto-compact or auto-clear when a workflow says it is finished.

- A compact operation has its own summarization cost. It can reduce later requests only when the same thread continues.
- A clear/new thread is the right boundary for unrelated work, but conversational-only details are intentionally dropped.
- The portable action at finish is to persist decisions, evidence, blockers, and the next action. Context disposal remains a runtime or user decision.

This is a `PARTIAL` aim-before-build result: runtime compaction already exists and works, while a cross-runtime finish hook that safely decides whether future work is related does not.

## Claude Code conditions

Checked with Claude Code 2.1.258 on 2026-09-08.

- `claude --help` exposes `--autocompact auto|100k–1M`.
- Auto-compact is on by default. Claude first clears older tool outputs and then summarizes the conversation as the context window approaches its limit.
- `/compact` triggers it manually and can include a focus. `/clear` starts fresh; the previous conversation remains available through `/resume`.
- `PreCompact` and `PostCompact` hooks can observe the `manual` or `auto` trigger. `PreCompact` can block an operation; neither hook is a command that initiates compaction.
- A `SessionEnd` hook can observe `reason: clear` only after `/clear` happened. It cannot turn an ordinary finish into `/clear`.

Primary references: [Claude Code context window](https://code.claude.com/docs/en/context-window), [hooks reference](https://code.claude.com/docs/en/hooks), and [best practices](https://code.claude.com/docs/en/best-practices).

## Local Codex observation

Checked with Codex CLI 0.153.4. The private transcript was not copied; only counters and completion status were read.

One long thread contained nine `compacted` events. The event format does not say whether each was manual or automatic, so this sample proves compaction behavior but not the trigger mix.

| Measure | Before compact | First model call after | Change |
|---|---:|---:|---:|
| Median input tokens | 228,079 | 23,392 | **-89.7%** |
| Range | 218,053–238,775 | 21,226–36,026 | — |

The recorded effective context window was 258,400 tokens. Pre-compact calls occupied 84.4–92.4% of that window (median 88.3%). All nine next tasks reached `task_complete` with no recorded error.

That last result is an operational continuity signal, **not** a fact-retention score. A controlled retention benchmark would need seeded decisions, hidden recall checks, and three conditions: continue, compact, and clear plus a persisted handoff.

OpenAI's Responses guidance likewise recommends compaction for long tool-heavy workflows and after major milestones, not every turn: [official compaction guidance](https://developers.openai.com/api/docs/guides/latest-model#4-compaction-extending-effective-context).

## Practical rule

1. Same feature and healthy context: do nothing.
2. Same feature and crowded context: write the checkpoint, then compact with a preservation focus.
3. Different feature: write the checkpoint, then clear or start a new thread.
4. Do not claim cost savings from the `-89.7%` input figure. The compact pass has a cost, much of the pre-compact input was cached, and this sample did not record a billing comparison.
