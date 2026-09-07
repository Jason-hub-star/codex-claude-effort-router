---
name: absorb
description: Extract only the changes worth porting from an external source (article, release notes, competing harness, thread) by comparing it against the current inventory and classifying each idea as already present, an addition to an existing asset, or genuinely new. Use for “what can we learn from this repo”, “should we adopt this”, “review these release notes”, “흡수”. Unlike a harness audit, this judges what to bring in, not what to remove.
---

# Absorb

Most tool announcements describe something you already have under a new name. This stage answers one question: *does this source contain anything we lack that can be attached today?*

## Principles

- **Never say "we don't have that" before checking the inventory.** Comparison is the whole job. Tool-level features (subagents, worktrees, scheduling) live in the runtime's tool list, not only in files.
- **Numbers from the source are quotes, not evidence.** Benchmarks measure their model plus their harness; they do not reproduce elsewhere. Adopt on mechanism ("why this structure removes waste"), never on a score.
- **Adoption means it works in this runtime today.** Features bound to the other side's private infrastructure keep only their idea.
- **No diff, no proposal.** Each candidate names a file and what changes in it. "Change the culture" dies here.
- **Record rejections.** Without a reason, the same source triggers the same meeting next month.

## Workflow

1. Obtain the source. While reading, separate claims from structural facts; only facts become candidates.
2. Dump the inventory: skills, commands, rule sections, and the runtime's tool list.
3. Classify each candidate:

| Class | Meaning | Output |
|---|---|---|
| Already present | Same capability, different name | Name of the matching asset |
| Extend | One line or section added to an existing asset | Target file plus the sentence to add |
| New | Nothing comparable exists | New file path plus a minimal skeleton |

Extend beats new: every new file lowers the recovery rate of the whole set.

4. Gate each candidate with four questions; one "no" rejects it:
   1. Nothing in the inventory covers it?
   2. Buildable with the tools and files that exist now?
   3. Can you name the file and lines to change?
   4. Can you cite one real incident where its absence cost something?

   Question 4 rejects the most. Hypothetical benefit is not a reason.

5. Report: adopted (at most three, with class, file, change, incident), deferred (correct but not now, with the condition), rejected (candidate plus the failed gate number).

## Reading the result

| Signal | Meaning |
|---|---|
| Zero adopted | Normal; most sources end here. Keep the rejection log |
| Five or more adopted | Over-adoption; the inventory check was skipped |
| Everything classified "new" | The comparison was not done |
| "Already present" with zero usage | The asset exists but is never invoked — run `harness-audit` |

The last row is the most common real finding: the problem was not a missing asset but an unused one.

## Next

Adopted items are complete only after their entry point is verified (the skill appears in the list, or a command names it). "Already present but unused" goes to `harness-audit`. Zero adoptions is a valid end.
