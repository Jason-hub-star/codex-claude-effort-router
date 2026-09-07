# Codex + Claude Effort Router

[![test](https://github.com/Jason-hub-star/codex-claude-effort-router/actions/workflows/test.yml/badge.svg)](https://github.com/Jason-hub-star/codex-claude-effort-router/actions/workflows/test.yml)
[![MIT](https://img.shields.io/badge/license-MIT-7C3AED.svg)](LICENSE)
[![stdlib only](https://img.shields.io/badge/router-stdlib%20only-10B981.svg)](router/effort_router.py)

One deterministic prompt classifier for **Codex and Claude Code**. It routes work into four effort lanes, installs matching profiles and agent definitions, preserves existing hooks, and fails open when hook input is invalid.

> Honest boundary: a prompt hook cannot secretly hot-swap the model of the active parent session. This project adds routing context, provides explicit next-session profiles, and routes Codex delegation through verified built-in agents (`explorer`, `worker`, `default`).

![15-second effort router demo](assets/effort-router-demo.gif)

## Why this exists

Using maximum reasoning for every task is slow and wasteful. Using minimum reasoning for risky work is fragile. The router applies a small, inspectable policy:

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
git clone https://github.com/Jason-hub-star/codex-claude-effort-router.git
cd codex-claude-effort-router
bash install.sh
```

Restart active Codex and Claude Code sessions after installation so newly installed agent definitions can be discovered. Codex custom-agent exposure varies by client/runtime; the automatic hint therefore uses built-in agents and treats the included custom TOML files as opt-in examples.

The installer creates one-time `*.effort-router.bak` backups, preserves unrelated hook handlers, and converges its own handler to exactly one canonical entry.

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

The automated suite covers 32 English/Korean prompts, the hook output contract, malformed and non-object JSON, safety overrides, installation backups, unrelated-hook preservation, duplicate repair, and idempotency. See [validation evidence](evidence/VALIDATION.md).

## Architecture

![Effort routing workflow](assets/effort-routing.svg)

The editable [Archify source](docs/effort-routing.workflow.json), interactive [HTML diagram](docs/effort-routing.html), and [Remotion promo source](promo/remotion/) are included.

## Prior art and scope

The closest project found was [`claude-model-router-hook`](https://github.com/tzachbon/claude-model-router-hook), which focuses on Claude Code prompt/tool routing. Broader harnesses such as [`madebywild/agent-harness`](https://github.com/madebywild/agent-harness) and [`claudex5-engineering-harness`](https://github.com/woongjaejung/claudex5-engineering-harness) solve larger orchestration/setup problems. This repository stays deliberately narrow: shared Codex + Claude effort classification, transparent limitations, and reproducible regression evidence. See the [comparison](docs/COMPARISON.md).

## Safety

- Hook parsing fails open: invalid input exits successfully without blocking the prompt.
- The router never executes user-supplied text.
- Installed agent files are fixed repository assets, not generated from prompts.
- Review any third-party hook before installing it; hooks run with your local user permissions.

See [SECURITY.md](SECURITY.md) for reporting.

## License

MIT

[한국어 README](README.ko.md) · [15-second MP4](assets/effort-router-demo.mp4)
