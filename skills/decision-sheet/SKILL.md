---
name: decision-sheet
description: Turn an ambiguous plan into a decided spec before implementation by writing one question file where every question already carries a recommended answer, so the user only edits what is wrong. Use for “interrogate this plan”, “what do we need to decide”, “make this a spec”, “그릴미”, or any pre-build request where the target is still fuzzy. Not for code that already exists and needs fixing.
---

# Decision Sheet

A file-round-trip variant of Matt Pocock's `grill-me` interview. The original asks one question at a time in chat and needs the user present for the whole session; this stage writes all questions at once, **pre-fills a recommended answer for each**, and treats an empty answer as agreement. The user's job is editing, not writing.

## Principles

- **Read the code before asking.** Anything answerable from code, docs, or commits is not a question. It becomes a "confirm only" row with a file path as evidence.
- **Never hand over a blank.** Every question ships with a recommended answer and its reason.
- **Close upstream decisions first.** A decision whose answer changes the downstream questions is upstream. Round 1 asks 10–15 upstream decisions; round 2 asks the 25–35 downstream ones with round 1 fixed.
- **Sort by reversal cost.** Expensive-to-undo decisions (names, public surfaces, storage formats) come first; taste comes last.
- **Visual choices need a comparison artifact.** Colors, type, and layout asked as text produce fake agreement; attach a rendered comparison instead.
- **Done means zero open items**, not a question count.

## Workflow

1. Confirm this is pre-build work. If code already exists, use `aim-before-build` instead.
2. Scout the codebase for facts. Each fact becomes a confirm-only row.
3. Write `docs/status/DECISIONS-<topic>.md` (project root if `docs/` is absent):

```markdown
# Decisions — <topic> · round 1
> Leave the answer blank if the recommendation is right. Move the [x] to change it; two checked boxes count as unresolved.

## R1-01 · <area>  [upstream]
Q. <one-line decision>
- [x] <recommended> ← recommended. Evidence: `path/file.ts:41`
- [ ] <alternative A>
- [ ] <alternative B>
Answer:

## R1-02 · confirm only  [answered by code]
<what the code already does> (`path/file.ts:12`)
Leave blank to keep it; write here to change it:
```

4. When the user replies, read the file. Blank = recommendation adopted. `?` = unresolved: dig further or propose the cheapest experiment. A changed answer reopens its downstream branch, and the known cost of that choice is written next to it so the next session does not rediscover it.
5. When nothing is open, prepend a summary table (`decision · evidence · reversal cost`) to the same file. That file is the spec draft; do not write a second document. Archive it once the work ships.

## Reading the result

| Signal | Meaning | Action |
|---|---|---|
| Most answers blank | Recommendations fit | Proceed to round 2 |
| Over half changed | The plan was misread | Re-read before round 2 |
| More than five `?` | Not ready to decide | Run `converge-plan` first |
| Questions are all taste | Reversal-cost sort was skipped | Rewrite the questions |

## Next

Use `converge-plan` when a decision is expensive and still uncertain, `goal-contract` when the spec is settled and the work spans multiple turns, or implement directly for a small reversible change.
