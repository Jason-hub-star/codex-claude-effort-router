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
  EFFORT_ROUTER_CODEX_HOME="$CODEX_ROOT" EFFORT_ROUTER_CLAUDE_HOME="$CLAUDE_ROOT" bash "$ROOT/install.sh" >/dev/null
}

run_install
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
echo "Installer test OK: preserved unrelated hook, repaired duplicate, idempotent, fail-open"
