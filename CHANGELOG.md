# Changelog

## Unreleased

- Fast lane default effort is now `low`. In the sealed 75-run experiment, `enforce-low` kept 15/15 passes while reducing mean reasoning tokens 49.8% versus `enforce=medium`; total cost changed -1.9%. Codex and Claude profile targets remain medium because the result covers one OpenCode provider.
- Benchmark (`bench/`): fixture with seeded defects, 15 tasks with hidden checks, four routing conditions, predictions before runs, offline `route` check. Pilot 1 results and two failed predictions recorded in `bench/results/pilot-1.md`.
- Router: `EFFORT_LANES_CONFIG` relocates the global config; fast keywords `how many`, `which file`, `what is the`; deep keywords for bug reports and "add a test"; a short typo request is fast even when it says "fix". Matrix grew to 47 cases.
- Platform boundary: Windows is supported through WSL 2 Ubuntu/Debian with Node 22, Python 3, `jq`, and Bash. Git Bash, PowerShell, and Command Prompt are explicitly unsupported. Added a reproducible clean-container regression.

## 0.3.0 — 2026-09-08

Repositioned from a Codex + Claude Code router to a cross-runtime harness; repository renamed to `effort-lanes`.

- Router: project config `.effort-lanes.json` (walk-up discovery) merged over `~/.config/effort-lanes/config.json`; `floor`, `default_lane`, keyword extensions, per-lane per-runtime targets, `fast_max_chars`. `--json --runtime <name>` output for plugins. Hermes `pre_llm_call` shell-hook shape supported next to `UserPromptSubmit`. Context tag is now `[EFFORT LANES]` and includes `effort=`.
- OpenCode plugin (`opencode/effort-lanes.js`): injects the routing context as a synthetic part; opt-in `reasoningEffort` enforcement via `chat.params`. Live-verified: the model echoed `LANE=FAST EFFORT=MEDIUM`.
- OpenClaw plugin (`openclaw/`): `before_prompt_build` context, opt-in `before_model_resolve` provider/model override. `openclaw plugins doctor` clean; hook fired in a live local turn.
- Hermes plugin (`hermes/effort-lanes/`): `pre_llm_call` context injection; `hermes plugins doctor` passes; shell-hook route verified with `hermes hooks test`.
- Skills: `decision-sheet` (file-round-trip variant of grill-me, credited), `absorb`, `harness-audit` with a session-log recovery-rate script and the 18-skill cap. Skill folders are now installed whole.
- Docs gate (`scaffold/scripts/check-docs.sh`) with ten break tests, and `install.sh --scaffold` for the docs layout. This repository's own `docs/` was restructured to pass it.
- Installer: `--runtimes`, auto-detection of five runtimes, shared router at `~/.config/effort-lanes/`, `--scaffold`, env overrides `EFFORT_LANES_*_HOME` (legacy `EFFORT_ROUTER_*` still accepted).
- Distribution: Claude Code plugin manifest and marketplace (`.claude-plugin/`, `hooks/hooks.json`), npm-ready `opencode/package.json`, OpenClaw `openclaw.plugin.json`.
- Fixed: loading the router via `importlib` on Python 3.14 failed inside `@dataclass` unless the module was registered in `sys.modules` (Hermes plugin loader).

## 0.2.0 — 2026-09-07

- Added seven optional, runtime-neutral workflow skills distilled from repeated `아침`, `조준`, `수렴`, `골`, `페이즈루프`, and `감사` habits.
- Added core-only, selective (`--skills`), full starter (`--starter`), and read-only listing (`--list-skills`) installation modes.
- Added installer regression coverage for both Codex and Claude Code skill locations.
- Added a dual-theme Archify starter-workflow diagram and refreshed the Remotion promo.
- Reframed the README for beginners, trend explorers, and experienced harness remixers.

## 0.1.0 — 2026-09-07

- Added one deterministic four-lane classifier for Codex and Claude Code.
- Added Codex profiles/custom agents and Claude Code subagents.
- Added preserving, convergent installer with one-time backups.
- Added 32-case multilingual routing tests and malformed-input regression tests.
- Added Archify workflow source, interactive HTML, dual-theme SVG, and Remotion promo assets.
- Published failed-trial evidence and explicit product limitations.
