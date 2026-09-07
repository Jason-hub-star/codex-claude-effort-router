---
name: converge-plan
description: Stress-test a costly or hard-to-reverse plan before implementation by freezing a rubric, iterating improvements and adversarial critique, and ending with one crux and the cheapest falsifiable experiment. Use for “converge this plan”, “수렴”, major architecture choices, or risky research bets—not routine edits.
---

# Converge Plan

Use this before implementation, not as a generic review after code exists.

## Workflow

1. Freeze a small rubric before round one. Suggested dimensions: feasibility, evidence, gap coverage, differentiation, cost realism, and falsifiability.
2. For each round: improve the largest weakness, score with evidence, attempt to refute the improvement, then record surviving new defects.
3. Stop after two consecutive rounds with no new surviving defect, two rounds with less than 5% improvement, or a hard cap of 6–8 rounds.
4. Do not declare convergence without at least one primary-source comparison and one direct check of the real system when those are available.

## Output

- Frozen rubric and score trajectory
- Accepted plan changes and rejected alternatives
- One irreversible crux
- One cheapest falsifiable experiment
- Stop reason and remaining uncertainty

Do not change the rubric mid-run or accept an improvement without trying to disprove it.

## Next

Turn the converged outcome into `goal-contract`. If the crux is unresolved, run only the cheapest experiment first.
