# Validation evidence

Last updated: 2026-09-07 (Asia/Seoul)

## Passing checks

| Check | Result | Evidence |
|---|---|---|
| Classification matrix | PASS | 32 English/Korean prompts across four lanes |
| Hook contract | PASS | `UserPromptSubmit` returns `additionalContext`; other events emit nothing |
| Fail-open boundary | PASS | malformed JSON, `null`, string, array, and empty object exit 0 without output |
| Safety floor | PASS | a Fast request containing a security signal becomes Critical |
| Installer preservation | PASS | unrelated hook remains after install |
| Installer convergence | PASS | a malformed duplicate is replaced by exactly one canonical handler |
| Installer idempotency | PASS | settings hashes are unchanged after a second install |
| Optional skill schemas | PASS | all seven `SKILL.md` folders pass the official Codex skill validator |
| Install modes | PASS | default installs no skills; selective and starter modes copy the expected skills to both runtimes |
| Invalid skill boundary | PASS | an unknown requested skill exits non-zero before changing either runtime |
| Preflight boundary | PASS | invalid settings and a non-directory runtime home stop before either runtime is modified |
| Beginner install edges | PASS | dependency errors, paths with spaces, comma whitespace, duplicates, and prior-skill backups |
| Remote skill discovery | PASS | public GitHub shorthand exposes seven skills through `npx skills` |
| Remote selective install | PASS | `agent-starter` copied into a clean temporary project with an exact source match and lock entry |
| Archify schema/render | PASS | finite SVG, orthogonal arrows, legend clearance, browser visual inspection |
| Remotion render | PASS | v0.1 artifact retained: 450 frames, 1280×720, 30 fps, 15.06 s, H.264 output |
| Built-in Codex delegation | PASS | `explorer` spawned and returned `BUILTIN_EXPLORER_OK` |
| Daily Codex profile | PASS | persisted thread reports `gpt-5.6-terra` / `medium` |
| Deep Codex profile | PASS | persisted thread reports `gpt-5.6-sol` / `high` |

Run all repository checks with:

```bash
bash scripts/check.sh
```

## Failures kept as evidence

1. The first live large-task trial selected Critical and attempted the configured `jason_architect` custom agent. That running CLI session reported the role unavailable, then successfully created two built-in fallback agents. The run was manually interrupted after roughly five minutes because its audit did not converge within the intended bound.
2. Fresh CLI and parent-session smoke tests repeated the custom-role failure even though the TOML matched the official schema. Built-in `explorer` succeeded immediately. Automatic Codex hints now use built-in roles; custom TOML files remain optional examples until the active runtime exposes them.
3. That trial revealed non-object JSON could crash the original hook, duplicate malformed hook handlers could survive installation, and the checker could accept one good handler beside a bad duplicate. All three defects now have regression coverage.
4. The first Archify layout failed because two arrows crossed nodes and one label overlapped a component. The redundant arrows were removed, the label was shortened, and the second render passed structural and visual checks.

## What this does not prove

- It does not prove that the recommended model/effort mapping is optimal for every workload.
- It does not prove that a hook changes the active parent model; it does not.
- Static agent files do not prove that a client already running before installation has loaded them. Restart and verify in a fresh session.

Future measurements should record task fixture, model version, effort, wall time, token use, pass/fail rubric, and repeated trials.

The v0.2 candidate passed [GitHub Actions run 34126285413](https://github.com/Jason-hub-star/codex-claude-effort-router/actions/runs/34126285413) on Ubuntu after the starter workflow and installer-edge tests were pushed.
