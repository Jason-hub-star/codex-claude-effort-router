# Codex + Claude Effort Router

[![test](https://github.com/Jason-hub-star/codex-claude-effort-router/actions/workflows/test.yml/badge.svg)](https://github.com/Jason-hub-star/codex-claude-effort-router/actions/workflows/test.yml)
[![MIT](https://img.shields.io/badge/license-MIT-7C3AED.svg)](LICENSE)
[![stdlib only](https://img.shields.io/badge/router-stdlib%20only-10B981.svg)](router/effort_router.py)

One deterministic prompt classifier for **Codex and Claude Code**, plus an optional, remixable starter workflow. It routes work into four effort lanes, installs matching profiles and agent definitions, preserves existing hooks, and fails open when hook input is invalid.

> Honest boundary: a prompt hook cannot secretly hot-swap the model of the active parent session. This project adds routing context, provides explicit next-session profiles, and routes Codex delegation through verified built-in agents (`explorer`, `worker`, `default`).

![15-second effort router demo](assets/effort-router-demo.gif)

## Why this exists

Using maximum reasoning for every task is slow and wasteful. Using minimum reasoning for risky work is fragile. Beginners also need a clear next step, while experienced users need pieces they can mix into an existing harness. The core router stays small; the workflow skills are opt-in.

| Lane | Codex default | Claude default | Best fit |
|---|---|---|---|
| Fast | Luna / medium | Haiku / medium | exact lookup, inventory, formatting |
| Daily | Terra / medium | Sonnet / medium | exploration, review, explanation |
| Deep | Sol / high | Sonnet / high | implementation, integration, debugging |
| Critical | Astra / high | Opus / high | security, safety, irreversible decisions |

These mappings are starting points, not benchmarks. Model availability and the best effort level vary by account, release, and workload. Edit the small TOML/Markdown files to fit your environment.

## Install

Requirements: Python 3 and `jq`.

```bash
python3 --version
jq --version
```

If either command is missing, install it with your operating system's package manager before continuing. `--help` and `--list-skills` work without those dependencies; installation and `--dry-run` require both.

For the seven portable skills only, use the open Agent Skills CLI without cloning this repository:

```bash
npx skills add Jason-hub-star/codex-claude-effort-router --list
npx skills add Jason-hub-star/codex-claude-effort-router --skill agent-starter -g -a codex -a claude-code
```

That route does **not** install the effort-routing hooks or Codex profiles. For the complete cross-runtime harness:

```bash
git clone https://github.com/Jason-hub-star/codex-claude-effort-router.git
cd codex-claude-effort-router
bash install.sh
```

Preview the full starter installation first if you prefer:

```bash
bash install.sh --starter --dry-run
bash install.sh --starter
```

Restart active Codex and Claude Code sessions after installation so newly installed agent definitions can be discovered. Codex custom-agent exposure varies by client/runtime; the automatic hint therefore uses built-in agents and treats the included custom TOML files as opt-in examples.

The default install is core-only. The installer creates one-time `*.effort-router.bak` backups, preserves unrelated hook handlers, and converges its own handler to exactly one canonical entry.

There is no automatic core uninstaller yet. Do not delete an entire Codex or Claude directory. Restore only the specific `*.effort-router.bak` files after inspecting them, or use `npx skills remove` for skills installed through the external Agent Skills CLI.

## Pick your path

| You are… | Start here | What gets installed |
|---|---|---|
| New to coding agents | `bash install.sh --starter` | Core router + all seven workflow skills |
| Trying current harness ideas | `bash install.sh --skills morning-brief,evidence-audit` | Core + only the experiments you name |
| Mixing into an existing harness | `bash install.sh --list-skills` | Nothing; inspect and copy/select individual skill folders |

The starter workflow is a menu, not a mandatory ceremony:

```text
Morning → Aim → [Converge if risky] → Goal → [Phase loop if 3+ phases] → Audit
```

- `morning-brief` (`아침`) recovers the last known state and one next action.
- `aim-before-build` (`조준`) checks whether the work is conflicting, done, partial, or absent.
- `converge-plan` (`수렴`) stress-tests expensive decisions and ends with a falsifiable experiment.
- `goal-contract` (`골`) freezes an evidence-based finish line for multi-turn work.
- `phase-loop` (`페이즈루프`) advances an approved multi-phase plan only when each gate passes.
- `evidence-audit` (`감사`) assigns a release-readiness verdict from direct evidence.
- `agent-starter` chooses exactly one of those stages for a beginner.

Run `bash install.sh --help` or read [skills/README.md](skills/README.md) for selective installation and remixing guidance.

## Use

Normal prompts are classified automatically. You can also request a lane explicitly:

```text
lane=fast list the changed files
effort-daily review the API boundary
effort-deep implement and test this change
effort-critical audit this production migration
```

Safety signals raise the floor, so `effort-fast audit security` still routes to Critical.

To launch Codex directly with a profile:

```bash
codex -p effort-fast
codex -p effort-daily
codex -p effort-deep
codex -p effort-critical
```

## Verify

```bash
bash scripts/check.sh
python3 router/effort_router.py --classify --prompt "fix the bug and test it"
```

The automated suite covers 32 English/Korean prompts, the hook output contract, malformed and non-object JSON, safety overrides, installation backups, unrelated-hook preservation, duplicate repair, core-only/selective/starter installs, and idempotency. See [validation evidence](evidence/VALIDATION.md).

## Architecture

![Effort routing workflow](assets/effort-routing.svg)

![Optional starter workflow](assets/starter-workflow.svg)

Editable Archify sources and interactive diagrams are included for both [effort routing](docs/effort-routing.workflow.json) and the [starter workflow](docs/starter-workflow.lifecycle.json). The [Remotion promo source](promo/remotion/) is included too.

## Prior art and scope

The closest project found was [`claude-model-router-hook`](https://github.com/tzachbon/claude-model-router-hook), which focuses on Claude Code prompt/tool routing. Broader harnesses such as [`madebywild/agent-harness`](https://github.com/madebywild/agent-harness) and [`claudex5-engineering-harness`](https://github.com/woongjaejung/claudex5-engineering-harness) solve larger orchestration/setup problems. This repository stays deliberately narrow: shared Codex + Claude effort classification, transparent limitations, and reproducible regression evidence. See the [comparison](docs/COMPARISON.md).

An additional [installation UX benchmark](docs/INSTALL-UX-RESEARCH.ko.md) compares this project with Superpowers, BMad, wshobson/agents, and Compound Engineering. The [v0.2 final evaluation](docs/FINAL-EVALUATION.ko.md) records the release verdict and remaining risks. Current verdict: suitable for technical beginners and remixers, but not yet as discoverable or update-friendly as a native marketplace plugin.

## Safety

- Hook parsing fails open: invalid input exits successfully without blocking the prompt.
- The router never executes user-supplied text.
- Installed agent files are fixed repository assets, not generated from prompts.
- Review any third-party hook before installing it; hooks run with your local user permissions.

See [SECURITY.md](SECURITY.md) for reporting.

## License

MIT. The workflow skills are portable extracts of one operator's repeated habits, not claims that every task needs process.

[한국어 README](README.ko.md) · [15-second MP4](assets/effort-router-demo.mp4)
