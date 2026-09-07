---
name: phase-loop
description: Execute an approved implementation plan with three or more phases, running a project-specific gate after every phase, advancing automatically on pass, and stopping on failure. Use for “run the phases”, “phase loop”, or “페이즈루프”; avoid for one small change or a pure test-fix loop.
---

# Phase Loop

## Before starting

Each phase must name its outcome, owned paths, verification, and any domain-specific invariant. If those are missing, stop and repair the plan.

## For each phase

1. Read the relevant code path and current project rules.
2. Make the smallest complete change within the phase boundary.
3. Run the declared focused check plus applicable type, build, or security gates.
4. Check documentation drift and whether any fact blocks the next phase.
5. Record `PASS`, `CONDITIONAL_PASS`, or `FAIL` with direct evidence.
6. Advance automatically only on pass. Fix a bounded failure inside the phase; otherwise stop and report.

Use one writer by default. Parallelize read-only checks or explicitly disjoint paths, never competing edits to a shared hub file.

## Stop conditions

- The plan’s ordering or assumptions are wrong.
- Required authorization, data, or external state is missing.
- The same serious failure repeats without a new hypothesis.
- A phase would cross its declared boundary.

## Next

After all phases pass, use `evidence-audit`. If the plan itself failed, return to `converge-plan`.
