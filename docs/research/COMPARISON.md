# Similar harness review

Checked on 2026-09-07. Star counts are snapshots, not quality scores.

| Project | Snapshot | Primary scope | Difference here |
|---|---:|---|---|
| [tzachbon/claude-model-router-hook](https://github.com/tzachbon/claude-model-router-hook) | 79 stars | Claude Code model routing with hook lifecycle coverage | This project shares one classifier across Codex and Claude and emphasizes cross-runtime evidence |
| [madebywild/agent-harness](https://github.com/madebywild/agent-harness) | 13 stars | Multi-provider agent framework | This project is a smaller effort-routing layer, not a framework |
| [Pierry/harness-kit](https://github.com/Pierry/harness-kit) | 3 stars | Claude-centered gated delivery pipeline | This project does not impose a delivery lifecycle |
| [sevenschulte/agentic-harness](https://github.com/sevenschulte/agentic-harness) | 2 stars | Reference harness and adapters | This project ships an executable classifier and installer regression suite |
| [cristian-robert/claude-code-harness](https://github.com/cristian-robert/claude-code-harness) | 1 star | PIV+E workflow and dual-target guidance | This project makes Codex routing executable rather than guidance-only |
| [woongjaejung/claudex5-engineering-harness](https://github.com/woongjaejung/claudex5-engineering-harness) | 0 stars | Broad global Codex/Claude orchestration | This project stays focused on effort choice and measurable installation behavior |

## Positioning decision

The useful gap is not “one more full agent harness.” It is a small shared policy that:

1. gives Codex and Claude Code the same task taxonomy;
2. states that the active parent model is unchanged;
3. fails open at the hook boundary;
4. preserves unrelated settings and converges duplicates;
5. includes both passing and failed validation history.

The project deliberately does not auto-star itself, rewrite arbitrary settings, or claim that one effort table is universally optimal.

## Adoption benchmark

The first review found the closest small routers. A second review compared the installation experience with four widely adopted workflow harnesses:

| Project | Stars on 2026-09-07 | Installation strength | Lesson applied here |
|---|---:|---|---|
| [obra/superpowers](https://github.com/obra/superpowers#installation) | 282,667 | Official Claude/Codex marketplace presence | Keep a single beginner entry point and explicit restart step |
| [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD/blob/main/docs/how-to/install-bmad.md) | 52,753 | Interactive module/tool selection plus `bmad-help` | Provide a starter router that chooses one next stage |
| [wshobson/agents](https://github.com/wshobson/agents/blob/main/docs/harnesses.md) | 39,466 | Plugin-level and individual-skill installation | Make every workflow stage independently installable |
| [Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin#install) | 24,930 | Native instructions across many agent hosts | Separate portable skills from runtime-specific hooks |

Stars are GitHub API snapshots, not quality scores. Full findings and local failure tests are in [INSTALL-UX-RESEARCH.ko.md](INSTALL-UX-RESEARCH.ko.md).

## Repositioning — 2026-09-08 (v0.3)

The "small shared policy, not one more harness" decision above was reversed deliberately after measuring where a prompt hook can actually change effort:

| Runtime | Can a hook change model/effort per prompt? | Seam |
|---|---|---|
| OpenCode | yes | `chat.params` options (`reasoningEffort`) |
| OpenClaw | yes | `before_model_resolve` → `modelOverride` / `providerOverride` |
| Hermes Agent | no (issues #23739, #7273 open) | `pre_llm_call` context only |
| Codex, Claude Code | no | `UserPromptSubmit` context only |

That asymmetry is the differentiator none of the compared projects have: one policy file, five runtimes, enforced where possible and honest where not. The widening also folds in the docs gate, the sync matrix, and the harness-audit recovery-rate measurement, because the adoption benchmark above showed the winning projects ship a workflow, not only a hook. What did not change: the classifier stays one dependency-free file, routing never calls an LLM, enforcement is opt-in, and every capability claim carries a recorded run in `docs/evidence/VALIDATION.md`.
