# Effort Lanes

[![test](https://github.com/Jason-hub-star/effort-lanes/actions/workflows/test.yml/badge.svg)](https://github.com/Jason-hub-star/effort-lanes/actions/workflows/test.yml)
[![MIT](https://img.shields.io/badge/license-MIT-7C3AED.svg)](LICENSE)
[![router: stdlib only](https://img.shields.io/badge/router-stdlib%20only-10B981.svg)](router/effort_router.py)
[![runtimes: 5](https://img.shields.io/badge/runtimes-Codex%20%C2%B7%20Claude%20Code%20%C2%B7%20OpenCode%20%C2%B7%20OpenClaw%20%C2%B7%20Hermes-0EA5E9.svg)](#what-actually-changes-per-runtime)

One deterministic effort policy for five coding-agent runtimes, plus the working habits that keep an agent harness small enough to be used.

Use this when you work across these runtimes and want one deterministic per-prompt effort policy, not a full autonomous-agent framework.

Every prompt is classified into one of four lanes — **fast, daily, deep, critical** — by a single stdlib-only Python file. The same file runs as a shell hook in Codex and Claude Code, and behind thin plugins in OpenCode, OpenClaw, and Hermes Agent. Where a runtime lets a hook change the model or reasoning effort, Effort Lanes can enforce the lane; everywhere else it injects a routing hint and says so.

## Why

Maximum reasoning on every prompt is slow and expensive. Minimum reasoning on a production migration is how incidents start. Most people pick one setting and leave it. Effort Lanes makes the choice per prompt, deterministically. Malformed input or config emits no routing output, and the OpenCode/OpenClaw adapters cap classification at two seconds so a router failure does not block the turn.

| Lane | Signal | Effort | Codex default | Claude default |
|---|---|---|---|---|
| Fast | short exact lookups, counts, formatting | low | Luna / medium | Haiku / medium |
| Daily | research, review, explanation | medium | Terra / medium | Sonnet / medium |
| Deep | implement, refactor, debug, end-to-end | high | Sol / high | Sonnet / high |
| Critical | security, production, payments, safety, repeated failure | high | Astra / high | Opus / high |

Safety signals win over everything: `lane=fast audit security` still routes to Critical. Explicit lane requests (`lane=deep`, `effort-fast`) win over keyword matching. A project floor can raise but never lower a lane.

The effort column is the per-prompt value used by runtimes that can enforce it. Codex and Claude
profiles remain at medium until they have their own workload A/B; the low result below is from OpenCode.

## What actually changes per runtime

A prompt hook cannot secretly hot-swap the model of a running session. The verification column states the strongest evidence available for each runtime; limitations stay explicit in [validation evidence](docs/evidence/VALIDATION.md).

| Runtime | Hook | Injects routing context | Can change effort or model per prompt | Verified |
|---|---|---|---|---|
| Claude Code | `UserPromptSubmit` shell hook | yes | no — provides per-lane subagents and profiles instead | hook contract, installer, isolated local marketplace install |
| Codex | `UserPromptSubmit` shell hook | yes | no — profiles `codex -p effort-deep` for the next session | hook contract, installer, built-in agent delegation |
| **OpenCode** | plugin `chat.message` + `chat.params` | yes | **yes, opt-in** — sets the request's `reasoningEffort` | live context run; one-provider A/B benchmark |
| **OpenClaw** | plugin `before_prompt_build` + `before_model_resolve` | yes | **yes, opt-in** — returns a provider/model override per lane | local install/doctor; resolve hook observed; prompt hook contract-tested |
| Hermes Agent | plugin `pre_llm_call`, or a shell hook on the same event | yes | no — upstream issues #23739 / #7273 are open | `hermes plugins doctor` OK, `hermes hooks test` parsed the context |

Enforcement is off by default. Switching models mid-session invalidates prompt caches and surprises people, so you turn it on deliberately: `"enforce": {"opencode": true}` in the global config, or `enforce: true` in the OpenClaw plugin config.

## Quick start

| Selected runtime | Requirements |
|---|---|
| All | Python 3, Bash/POSIX userland |
| Codex or Claude Code | `jq` |
| OpenCode or OpenClaw | Node 22 or newer |

On Windows, run the installer inside **WSL 2** Ubuntu/Debian. Native Git Bash, PowerShell, and Command Prompt are not supported.

```bash
git clone https://github.com/Jason-hub-star/effort-lanes.git
cd effort-lanes
bash install.sh                 # every runtime detected on this machine, core only
bash install.sh --starter       # optional: add all ten workflow skills
bash install.sh --runtimes claude,opencode --skills decision-sheet,evidence-audit
bash install.sh --dry-run       # print targets, change nothing
```

Start core-only and add skills only when you need them. The installer copies one shared router to `~/.config/effort-lanes/effort_router.py`, merges its own hook entry without touching yours, converges duplicates to exactly one handler, makes one-time `*.effort-router.bak` backups, and validates runtime prerequisites and settings JSON before writing. Restart open sessions afterwards.

Other routes:

- **Claude Code plugin marketplace** — `/plugin marketplace add Jason-hub-star/effort-lanes`, then `/plugin install effort-lanes@effort-lanes`. Installs the hook, the four lane subagents, and the skills natively.
- **Skills only, any runtime** — `npx skills add Jason-hub-star/effort-lanes --list`.
- **OpenClaw** — `openclaw plugins install ./openclaw` (the installer runs this when selected). Add `effort-lanes` to `plugins.allow`, then restart OpenClaw.
- **Hermes** — the installer copies the plugin and runs non-interactive `hermes plugins enable effort-lanes`; restart Hermes afterwards. Prefer a subprocess boundary? Add a shell hook instead:

  ```yaml
  # ~/.hermes/config.yaml
  hooks:
    pre_llm_call:
      - command: "python3 ~/.config/effort-lanes/effort_router.py"
        timeout: 5
  ```

## Configure

Drop `.effort-lanes.json` in a project (found by walking up from the working directory) or `~/.config/effort-lanes/config.json` globally. Project values win; keyword lists merge. Every key is optional and a malformed file is ignored.

```json
{
  "floor": "deep",
  "default_lane": "daily",
  "keywords": { "critical": ["movej", "joint motion"] },
  "lanes": { "critical": { "opencode": "anthropic/claude-opus-5", "openclaw": "anthropic/claude-opus-5" } },
  "enforce": { "opencode": false }
}
```

`floor` is for repositories where a wrong guess is expensive (hardware, production infrastructure): every prompt starts at that lane. `lanes.<lane>.<runtime>` sets the model a runtime should use for that lane; enforcement reads it. See [`router/config.example.json`](router/config.example.json).

Ask for a lane explicitly whenever you want:

```text
lane=fast list the changed files
effort-deep implement and test this change
effort-critical audit this production migration
```

## Workflow skills

Ten optional portable `SKILL.md` stages distilled from one operator's repeated habits. They are a menu, not a ceremony; `agent-starter` picks exactly one for a beginner.

```text
morning-brief → aim-before-build → decision-sheet? → converge-plan? → goal-contract? → phase-loop? → evidence-audit
                                   harness-audit ⇄ absorb   (maintenance: keep the set small)
```

- `aim-before-build` (`조준`) — the cheapest outcome is discovering nothing needs building.
- `decision-sheet` (`그릴미`) — every question ships with a recommended answer; a blank reply means "agreed". A file-round-trip variant of Matt Pocock's `grill-me`.
- `converge-plan` (`수렴`) — sealed rubric, adversarial rounds, ends with the cheapest experiment that could kill the plan.
- `goal-contract` (`골`) — outcome, verification, constraints, boundaries, iteration policy, stop condition; runtime-neutral.
- `phase-loop` (`페이즈루프`) — a 3+ phase plan advances only through passing gates.
- `evidence-audit` (`감사`) — `NOT_READY` / `READY_FOR_REVIEW` / `READY_TO_SHARE`, from evidence only.
- `harness-audit` (`정비`) — measures which installed skills are actually invoked from session logs. Dead means zero calls **and** no entry point. Keeps a project at 18 skills or fewer: across 14 repositories, sets of ≤18 skills recovered 33–83% of them, sets of 26–27 recovered 19–30%.
- `absorb` (`흡수`) — classifies an external source as already-present / extend / new, and logs rejections so the same source is never re-evaluated.
- `morning-brief` (`아침`) — yesterday's baton and one next action.
- `agent-starter` — points a new coding-agent user at exactly one appropriate workflow stage.

Full table and install options in [skills/README.md](skills/README.md).

## Docs gate and scaffold

Conventions written down are not followed; conventions enforced by a failing script are. `scaffold/scripts/check-docs.sh` fails when:

1. anything other than entry documents sits in the `docs/` root;
2. an archived file lacks `<name>-<superseded|abandoned|legacy|progresslog>-<YYYY-MM-DD>.<ext>` or is missing from the archive index;
3. a "source truth" path in `docs/status/DOC-SYNC-MATRIX.md` does not exist;
4. a project installs more than 18 skills.

```bash
bash install.sh --scaffold ~/code/my-project     # docs/ layout + gate; never overwrites
bash scripts/check-docs.sh                        # run the gate
```

This repository runs the same gate on itself in CI. It caught a stray file on its first run.

## Verify

```bash
bash scripts/check.sh
python3 router/effort_router.py --classify --json --runtime opencode --prompt "fix the bug and test it"
```

The suite covers 47 English/Korean prompts, the hook contracts for both shell-hook shapes, malformed and hostile config, project floors, plugin contracts for OpenCode and OpenClaw under plain Node, the Hermes plugin, the installer across five runtime homes, and ten break tests for the docs gate. Live-runtime evidence and the failures kept on record are in [docs/evidence/VALIDATION.md](docs/evidence/VALIDATION.md).

## Benchmark

`bench/` measures the router the only way that means anything: same tasks, same model, one axis changed — how effort is chosen. Pilot 1 used four conditions; the runner now carries six, including the fast-lane low controls added for experiment 2. Hidden pass/fail checks stay invisible to the agent, and predictions are written before a run.

Pilot 1 (2026-09-08, `opencode-go/gpt-5.6-luna`, one repeat, 60 runs):

| Finding | Number |
|---|---|
| Critical tasks under `enforce` matched `always-high` on pass rate (5/5) at lower cost | 4% cheaper on that lane |
| `enforce` versus no router: fixed the one critical miss | +13% cost on critical, +13% overall |
| Fast tasks: the router **cost** reasoning tokens instead of saving them on this provider | 46 → 153 reasoning tokens |
| Keyword tables missed short English prompts before the fix | 10/15 → 15/15 offline after |

Two predictions failed and both changed the code or the roadmap; the table, the failures, and the next single-axis experiment are in [bench/results/pilot-1.md](bench/results/pilot-1.md).

Experiment 2 then isolated the fast effort setting: 5 tasks × 5 conditions × 3 repeats, 75/75 passed.
`enforce-low` cut mean reasoning tokens from 60.3 to 30.3 versus the previous `enforce=medium`
(-49.8%) with no pass loss, so the sealed rule changed the fast per-prompt default to `low`. Total
cost moved only -1.9%; this is one provider and not a universal model claim. See
[experiment 2](bench/results/exp2-fastlane-20260908.md).

```bash
python3 bench/run.py route                       # offline: does each task reach its labeled lane?
python3 bench/run.py run --repeat 3              # 270 model runs (15 tasks × 6 conditions × 3)
python3 bench/run.py summarize bench/results/<file>.jsonl
```

## Architecture

![Effort routing workflow](assets/effort-routing.svg)

![Optional starter workflow](assets/starter-workflow.svg)

Editable diagram sources live in [docs/ref/diagrams](docs/ref/diagrams/); the Remotion promo source is in [promo/remotion](promo/remotion/).

## Positioning and prior art

Until v0.2 this project was deliberately a narrow router for Codex and Claude Code. v0.3 widened it to a cross-runtime harness after measuring where hooks can actually change effort. The closest routers and the widely adopted harnesses it learned from (Superpowers, BMad, wshobson/agents, Compound Engineering) are compared in [docs/research/COMPARISON.md](docs/research/COMPARISON.md). What stays deliberate: one classifier file, no LLM in the routing path, no auto-enforcement, and claims linked to evidence with explicit limits.

## Safety

- Hook parsing fails open: invalid input or config exits successfully without blocking the prompt.
- The router never executes user-supplied text. Plugins pass the prompt to it as a process argument, never through a shell.
- Installed agent, profile, plugin, and skill files are fixed repository assets, not generated from prompts.
- OpenClaw and OpenCode plugins run in-process with the runtime's own trust level; read them before installing, and add `effort-lanes` to OpenClaw's `plugins.allow`.

See [SECURITY.md](SECURITY.md) for reporting.

## License

MIT.

[한국어 README](README.ko.md)
