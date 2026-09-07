---
name: aim-before-build
description: Compare a desired outcome with the real codebase before implementation and classify it as already done, partial, not started, or conflicting. Use for “check before building”, “is this already implemented?”, “조준”, or requests that combine a goal with status discovery.
---

# Aim Before Build

This stage is read-only. Its cheapest valid outcome is discovering that no implementation is needed.

## Workflow

1. Separate the requested target from the action verb. Resolve project-specific terms from code or current documentation.
2. Trace the relevant path end to end. Count completed behavior paths, not changed files.
3. Check decisions, archived attempts, and recent commits for conflicts or previously rejected approaches.
4. Return exactly one verdict:
   - `CONFLICTING`: the goal contradicts current architecture or a confirmed decision; do not start.
   - `ALREADY_DONE`: the behavior exists and is verified; stop.
   - `PARTIAL`: name the shortest missing end-to-end path.
   - `NOT_STARTED`: identify the first owned path and whether planning risk is high.

An index or search result can prove presence, but an empty result alone cannot prove absence.

## Output

Verdict, direct evidence, completed paths `n/m`, conflict history, and one next action.

## Next

Use `converge-plan` for an expensive uncertain decision, `goal-contract` for multi-turn work with a clear target, or direct implementation for a small reversible change.
