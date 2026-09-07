---
name: agent-starter
description: Guide people who are new to coding agents through the next appropriate workflow stage, or help experienced users select and remix the included morning, aim, decision-sheet, converge, goal, phase-loop, audit, absorb, and harness-audit skills. Use for “what should I do next?”, “help me start with agents”, “에이전트 처음”, or “뭐부터 하지?”.
---

# Agent Starter

Choose one next stage. Do not run the whole chain by default.

## Route

1. Beginning a work session with existing repository history → `morning-brief`.
2. A desired outcome exists, but current implementation status is unclear → `aim-before-build`.
3. The target is still fuzzy and several decisions are open → `decision-sheet`.
4. A costly or hard-to-reverse plan is still uncertain → `converge-plan`.
5. Work needs multiple turns and an evidence-based finish line → `goal-contract`.
6. An approved plan has three or more implementation phases → `phase-loop`.
7. Work is ready to review or share → `evidence-audit`.
8. Too many skills, or a skill never triggers → `harness-audit`; an external source to evaluate → `absorb`.

Simple questions and one-line edits need none of these. Handle them directly.

## Shared habits

- Treat runtime behavior and direct measurements as stronger evidence than old documentation.
- Read the nearest project instructions and current status before editing.
- Search for existing code, standard features, dependencies, and installed skills before creating anything.
- Use the lowest effort that can close the task reliably.
- Delegate only independent, bounded work; keep one writer unless paths are disjoint.
- Never treat an empty result as proof that nothing exists.
- Finish non-trivial work with one runnable check and an explicit remaining-risk statement.

## Output

Return the selected stage, why it fits, the first artifact or check to inspect, and one next action.

## Next

Hand off to the selected stage and stop; the chain continues from that stage's own `## Next`.
