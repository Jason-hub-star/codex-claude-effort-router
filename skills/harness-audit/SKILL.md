---
name: harness-audit
description: Measure whether installed harness assets (skills, commands, templates) are actually invoked, using session logs rather than opinions, then archive dead assets, harvest improvements back to the template, and keep the installed set under the recovery-rate cap. Use for “which skills are unused”, “too many skills”, “harness check”, “why doesn't this skill trigger”, “정비”. Unlike absorb, this removes and consolidates what exists.
---

# Harness Audit

Creating assets is easy; removing them is what nobody does. This stage checks one thing: **were the assets we installed ever called?**

## Principles

- **Dead means zero invocations AND no entry point.** Both conditions. A skill with no log hits can still be alive if a command names it or a living skill links to it; moving it breaks that path. Catalog listings (README, INDEX) do not count as entry points.
- **Two invocation paths.** The model's `Skill` tool calls and the user's typed slash commands. Counting only one produces false deaths.
- **Modification time is not usage.** Good skills are invoked for months without edits, and checkouts overwrite mtime anyway.
- **Templates are warehouses, not workers.** Scaffold and template directories are expected to have zero invocations; measure recovery only in projects that do real work.
- **Read recovery rate together with session count.** Zero sessions means the project is resting, not that its skills are dead.
- **Fewer installed assets recover better.** One operator's measurement across 14 repositories (August 2026): projects holding 18 or fewer skills recovered 33–83% of them; projects holding 26–27 recovered 19–30%. This stage keeps the per-project set at 18 or fewer.

## Run

```bash
python3 scripts/audit.py                 # current project against Claude Code session logs
python3 scripts/audit.py --root ~/code   # every project under a root
python3 scripts/audit.py --json
```

The script reports, per project: sessions, installed skills, invocations per skill (tool calls plus slash commands), entry points found in commands and other skills, and a verdict per skill (`ALIVE`, `LINKED`, `DEAD`). Session logs are read from `~/.claude/projects/**/*.jsonl`; other runtimes need an adapter.

## Reading the result

| Signal | Meaning | Action |
|---|---|---|
| Recovery below 20% | Skills compete and matching collapsed | Archive dead ones first |
| Dead but zero sessions | Project is idle | Do nothing |
| Global invocations far exceed local | The real workers are global skills | Stop adding project skills |
| Copies of one skill differ across projects | Someone fixed only one copy | Restore the canonical one |

## Actions

1. **Archive** dead skills with `git mv` into `_archive/`; never delete. Record the recovery numbers in the commit message.
2. **Harvest** project-side improvements back into the shared template.
3. **Promote** assets that exist identically in three or more projects into the template.
4. **Install selectively.** Never push the whole template into a project; pick the shared commands plus what that project will actually call.

## Pitfalls

- A new check produces false positives first. Open three samples by hand before reporting a number; a false alarm hides the real ones.
- Verdicts are only valid for the period the logs cover. A fresh machine makes everything look dead — the session column is the guard.
- Logs can be gigabytes. Run wide audits in the background.

## Next

A dead asset with no replacement goes to `absorb`. A dead asset that died because nobody knew when to call it needs an entry point (a `## Next` baton or a command), not a rewrite.
