# Starter skills

The starter pack is a progressive workflow, not a mandatory ceremony:

```text
morning-brief → aim-before-build → converge-plan? → goal-contract? → phase-loop? → evidence-audit
```

Question marks mean “only when the task needs it.” `agent-starter` selects one stage for beginners. Experienced users can install or copy any skill independently.

```bash
bash install.sh --starter
bash install.sh --skills aim-before-build,goal-contract,evidence-audit
bash install.sh --list-skills
bash install.sh --starter --dry-run
```

The same `SKILL.md` files are installed for Codex and Claude Code. Names are English for portability; descriptions include the original Korean aliases.

For skills without the router, profiles, or hooks:

```bash
npx skills add Jason-hub-star/codex-claude-effort-router --list
npx skills add Jason-hub-star/codex-claude-effort-router --skill evidence-audit -g -a codex -a claude-code
```

The repository follows the common `skills/<name>/SKILL.md` layout. The bundled Bash installer copies files and makes one-time backups; the external Agent Skills CLI manages its own links/copies, updates, and removal.
