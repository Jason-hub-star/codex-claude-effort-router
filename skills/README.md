# Workflow skills

Ten portable `SKILL.md` stages. Names are English; descriptions keep the original Korean aliases so either triggers.

**Build axis** (a menu, not a ceremony — question marks mean "only when needed"):

```text
morning-brief → aim-before-build → decision-sheet? → converge-plan? → goal-contract? → phase-loop? → evidence-audit
```

**Maintenance axis** (keeps the set small enough to be recovered):

```text
harness-audit ⇄ absorb
```

| Skill | Alias | One line |
|---|---|---|
| `morning-brief` | 아침 | Recover yesterday's state and one next action |
| `aim-before-build` | 조준 | Classify a goal as done / partial / not started / conflicting before touching code |
| `decision-sheet` | 그릴미 | Question file with pre-filled recommended answers; blank means agree (file-round-trip variant of Matt Pocock's grill-me) |
| `converge-plan` | 수렴 | Score, attack, and converge a risky plan; end with the cheapest kill experiment |
| `goal-contract` | 골 | Six-part goal brief whose completion is decided by evidence |
| `phase-loop` | 페이즈루프 | Advance a 3+ phase plan only through passing gates |
| `evidence-audit` | 감사 | Release-readiness verdict from direct evidence |
| `absorb` | 흡수 | Bring in only what an external source adds; log rejections |
| `harness-audit` | 정비 | Measure which installed skills are actually invoked; archive the dead; keep ≤18 |
| `agent-starter` | — | Pick exactly one stage for a beginner |

## Install

```bash
bash install.sh --starter                                  # all ten, every detected runtime
bash install.sh --skills decision-sheet,evidence-audit     # a subset
bash install.sh --list-skills
npx skills add Jason-hub-star/effort-lanes --skill harness-audit -g -a codex -a claude-code
```

Skill folders are copied whole, so `harness-audit/scripts/audit.py` travels with its SKILL.md. OpenCode reads `~/.claude/skills` directly and needs no separate copy. OpenClaw requires frontmatter `metadata` to be a single-line JSON object and rejects symlinked skill directories; `scripts/check.sh` enforces the first rule.
