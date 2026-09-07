#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT
CODEX_ROOT="$TMP_ROOT/codex"
CLAUDE_ROOT="$TMP_ROOT/claude"
mkdir -p "$CODEX_ROOT" "$CLAUDE_ROOT"

router_command="python3 \"$CODEX_ROOT/hooks/effort-router.py\""
jq -nc --arg command "$router_command" '{hooks:{UserPromptSubmit:[{hooks:[{type:"command",command:"keep-me",timeout:9},{type:"wrong",command:$command,timeout:99}]}]}}' > "$CODEX_ROOT/hooks.json"
printf '{"hooks":{}}\n' > "$CLAUDE_ROOT/settings.json"

run_install() {
  EFFORT_ROUTER_CODEX_HOME="$CODEX_ROOT" EFFORT_ROUTER_CLAUDE_HOME="$CLAUDE_ROOT" bash "$ROOT/install.sh" "$@" >/dev/null
}

bash "$ROOT/install.sh" --help | grep -q '^Usage:'
DRY_CODEX="$TMP_ROOT/dry run/codex"
DRY_CLAUDE="$TMP_ROOT/dry run/claude"
EFFORT_ROUTER_CODEX_HOME="$DRY_CODEX" EFFORT_ROUTER_CLAUDE_HOME="$DRY_CLAUDE" bash "$ROOT/install.sh" --dry-run --starter | grep -q '^Workflow skills:'
[[ ! -e "$DRY_CODEX" ]]
[[ ! -e "$DRY_CLAUDE" ]]

run_install
[[ ! -d "$CODEX_ROOT/skills" ]]
[[ ! -d "$CLAUDE_ROOT/skills" ]]
first_hash="$(shasum -a 256 "$CODEX_ROOT/hooks.json" "$CLAUDE_ROOT/settings.json")"
run_install
second_hash="$(shasum -a 256 "$CODEX_ROOT/hooks.json" "$CLAUDE_ROOT/settings.json")"
[[ "$first_hash" == "$second_hash" ]]

jq -e --arg command "$router_command" '
  ([.hooks.UserPromptSubmit[]?.hooks[]? | select(.command == $command and .type == "command" and .timeout == 2 and .additionalContextLimit == 1200)] | length == 1)
  and any(.hooks.UserPromptSubmit[]?.hooks[]?; .command == "keep-me")
' "$CODEX_ROOT/hooks.json" >/dev/null

claude_command="python3 \"$CLAUDE_ROOT/hooks/effort-router.py\""
jq -e --arg command "$claude_command" '
  [.hooks.UserPromptSubmit[]?.hooks[]? | select(.command == $command and .type == "command" and .timeout == 2)] | length == 1
' "$CLAUDE_ROOT/settings.json" >/dev/null

[[ -f "$CODEX_ROOT/hooks.json.effort-router.bak" ]]
[[ -f "$CLAUDE_ROOT/settings.json.effort-router.bak" ]]
printf 'null' | python3 "$CODEX_ROOT/hooks/effort-router.py" >/dev/null

skills_list="$(bash "$ROOT/install.sh" --list-skills)"
[[ "$(printf '%s\n' "$skills_list" | wc -l | tr -d ' ')" == "7" ]]
grep -qx 'agent-starter' <<< "$skills_list"
grep -qx 'phase-loop' <<< "$skills_list"

mkdir -p "$CODEX_ROOT/skills/aim-before-build" "$CLAUDE_ROOT/skills/aim-before-build"
printf 'previous codex skill\n' > "$CODEX_ROOT/skills/aim-before-build/SKILL.md"
printf 'previous claude skill\n' > "$CLAUDE_ROOT/skills/aim-before-build/SKILL.md"
run_install --skills 'aim-before-build, goal-contract'
for skill in aim-before-build goal-contract; do
  [[ -f "$CODEX_ROOT/skills/$skill/SKILL.md" ]]
  [[ -f "$CLAUDE_ROOT/skills/$skill/SKILL.md" ]]
done
grep -qx 'previous codex skill' "$CODEX_ROOT/skills/aim-before-build/SKILL.md.effort-router.bak"
grep -qx 'previous claude skill' "$CLAUDE_ROOT/skills/aim-before-build/SKILL.md.effort-router.bak"
[[ ! -e "$CODEX_ROOT/skills/phase-loop/SKILL.md" ]]

run_install --starter
for skill in $skills_list; do
  [[ -f "$CODEX_ROOT/skills/$skill/SKILL.md" ]]
  [[ -f "$CLAUDE_ROOT/skills/$skill/SKILL.md" ]]
done
starter_hash="$(find "$CODEX_ROOT/skills" "$CLAUDE_ROOT/skills" -type f -name SKILL.md -exec shasum -a 256 {} + | sort)"
run_install --starter
starter_second_hash="$(find "$CODEX_ROOT/skills" "$CLAUDE_ROOT/skills" -type f -name SKILL.md -exec shasum -a 256 {} + | sort)"
[[ "$starter_hash" == "$starter_second_hash" ]]

dedupe_output="$(EFFORT_ROUTER_CODEX_HOME="$CODEX_ROOT" EFFORT_ROUTER_CLAUDE_HOME="$CLAUDE_ROOT" bash "$ROOT/install.sh" --skills aim-before-build,aim-before-build)"
grep -q 'and 1 starter skill(s)' <<< "$dedupe_output"

if run_install --skills not-a-skill 2>/dev/null; then
  echo "Expected an unknown skill to fail" >&2
  exit 1
fi
if run_install --skills aim-before-build, 2>/dev/null; then
  echo "Expected an empty skill name to fail" >&2
  exit 1
fi

BROKEN_ROOT="$TMP_ROOT/broken"
mkdir -p "$BROKEN_ROOT/codex"
printf '{broken' > "$BROKEN_ROOT/codex/hooks.json"
if EFFORT_ROUTER_CODEX_HOME="$BROKEN_ROOT/codex" EFFORT_ROUTER_CLAUDE_HOME="$BROKEN_ROOT/claude" bash "$ROOT/install.sh" --starter >/dev/null 2>&1; then
  echo "Expected malformed settings to fail" >&2
  exit 1
fi
[[ "$(find "$BROKEN_ROOT" -type f | wc -l | tr -d ' ')" == "1" ]]

HALF_ROOT="$TMP_ROOT/half"
mkdir -p "$HALF_ROOT/codex"
printf 'not-a-directory\n' > "$HALF_ROOT/claude"
if EFFORT_ROUTER_CODEX_HOME="$HALF_ROOT/codex" EFFORT_ROUTER_CLAUDE_HOME="$HALF_ROOT/claude" bash "$ROOT/install.sh" --starter >/dev/null 2>&1; then
  echo "Expected a non-directory runtime home to fail" >&2
  exit 1
fi
[[ -z "$(find "$HALF_ROOT/codex" -mindepth 1 -print -quit)" ]]

SPACE_ROOT="$TMP_ROOT/path with spaces"
EFFORT_ROUTER_CODEX_HOME="$SPACE_ROOT/codex home" EFFORT_ROUTER_CLAUDE_HOME="$SPACE_ROOT/claude home" bash "$ROOT/install.sh" --skills morning-brief >/dev/null
[[ -f "$SPACE_ROOT/codex home/skills/morning-brief/SKILL.md" ]]
[[ -f "$SPACE_ROOT/claude home/skills/morning-brief/SKILL.md" ]]

NO_JQ_BIN="$TMP_ROOT/no-jq-bin"
mkdir -p "$NO_JQ_BIN"
ln -s "$(command -v dirname)" "$NO_JQ_BIN/dirname"
ln -s "$(command -v python3)" "$NO_JQ_BIN/python3"
if PATH="$NO_JQ_BIN" /bin/bash "$ROOT/install.sh" --dry-run > /dev/null 2> "$TMP_ROOT/no-jq.err"; then
  echo "Expected missing jq to fail" >&2
  exit 1
fi
grep -q 'ERROR: jq is required' "$TMP_ROOT/no-jq.err"

NO_PYTHON_BIN="$TMP_ROOT/no-python-bin"
mkdir -p "$NO_PYTHON_BIN"
ln -s "$(command -v dirname)" "$NO_PYTHON_BIN/dirname"
ln -s "$(command -v jq)" "$NO_PYTHON_BIN/jq"
if PATH="$NO_PYTHON_BIN" /bin/bash "$ROOT/install.sh" --dry-run > /dev/null 2> "$TMP_ROOT/no-python.err"; then
  echo "Expected missing python3 to fail" >&2
  exit 1
fi
grep -q 'ERROR: python3 is required' "$TMP_ROOT/no-python.err"

echo "Installer test OK: help/dry-run, preflight, paths with spaces, dependencies, selective/starter skills, idempotent, fail-open"
