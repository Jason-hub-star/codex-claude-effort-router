---
name: evidence-audit
description: Audit work before it is shared or called complete, choosing a light decision review, a multi-lens defect search, or a deep high-risk review. Use for “audit”, “red team”, “final review”, “감사”, security and resilience checks, or release readiness. Finding issues is read-only unless fixes are explicitly requested.
---

# Evidence Audit

Choose one depth; do not run all three automatically.

- **Light:** challenge one design decision with evidence and a counterexample.
- **Standard:** inspect independent lenses such as security, state consistency, user-journey gaps, and operational recovery.
- **Deep:** examine an irreversible architecture, security, safety, or migration decision from primary evidence.

## Workflow

1. Define scope and success criteria. Split lenses or file clusters so they do not overlap unnecessarily.
2. Gather candidate findings with exact source locations, a concrete failure scenario, and a proposed decisive check.
3. Treat delegated findings as `CANDIDATE`, `LIKELY`, or `REFUTED`; only the parent can mark a high-severity finding `CONFIRMED` after reopening the source.
4. Report confirmed findings by severity and include useful refutations so safe paths are visible.
5. If fixes were explicitly requested, assign disjoint paths, keep shared index/manifest files under one owner, then rerun the real project checks.

## Completion verdict

Return `NOT_READY`, `READY_FOR_REVIEW`, or `READY_TO_SHARE`, followed by executed checks, assumptions, and remaining risk. No evidence means `NOT_READY`.

## Next

Fix confirmed findings and rerun this audit. Capture a reusable lesson only after it has repeated in more than one real task.
