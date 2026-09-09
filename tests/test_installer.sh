#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT
LANES_HOME="$TMP_ROOT/lanes"
CODEX_ROOT="$TMP_ROOT/codex"
CLAUDE_ROOT="$TMP_ROOT/claude"
OPENCODE_ROOT="$TMP_ROOT/opencode"
OPENCLAW_ROOT="$TMP_ROOT/openclaw"
HERMES_ROOT="$TMP_ROOT/hermes"
mkdir -p "$CODEX_ROOT" "$CLAUDE_ROOT"
ALL="codex,claude,opencode,openclaw,hermes"

router_command="python3 \"$CODEX_ROOT/hooks/model-orchestrator.py\""
jq -nc --arg command "$router_command" '{hooks:{UserPromptSubmit:[{hooks:[{type:"command",command:"keep-me",timeout:9},{type:"wrong",command:$command,timeout:99}]}]}}' > "$CODEX_ROOT/hooks.json"
printf '{"hooks":{}}\n' > "$CLAUDE_ROOT/settings.json"

with_homes() {
  MODEL_ORCHESTRATOR_HOME="$LANES_HOME" MODEL_ORCHESTRATOR_CODEX_HOME="$CODEX_ROOT" MODEL_ORCHESTRATOR_CLAUDE_HOME="$CLAUDE_ROOT" \
  MODEL_ORCHESTRATOR_OPENCODE_HOME="$OPENCODE_ROOT" MODEL_ORCHESTRATOR_OPENCLAW_HOME="$OPENCLAW_ROOT" MODEL_ORCHESTRATOR_HERMES_HOME="$HERMES_ROOT" "$@"
}
run_install() { with_homes bash "$ROOT/install.sh" --runtimes "$ALL" "$@" >/dev/null; }

bash "$ROOT/install.sh" --help | grep -q '^Usage:'
DRY="$TMP_ROOT/dry run"
MODEL_ORCHESTRATOR_HOME="$DRY/lanes" MODEL_ORCHESTRATOR_CODEX_HOME="$DRY/codex" MODEL_ORCHESTRATOR_CLAUDE_HOME="$DRY/claude" \
  bash "$ROOT/install.sh" --runtimes codex,claude --dry-run --starter | grep -q '^Workflow skills:'
[[ ! -e "$DRY" ]]

# core install for every runtime, twice, must converge
run_install
[[ -f "$LANES_HOME/model_orchestrator.py" ]]
[[ -f "$LANES_HOME/config.example.json" ]]
[[ -f "$OPENCODE_ROOT/plugins/model-orchestrator.js" ]]
[[ -f "$OPENCLAW_ROOT/extensions/model-orchestrator/openclaw.plugin.json" ]]
[[ -f "$HERMES_ROOT/plugins/model-orchestrator/plugin.yaml" ]]
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
claude_command="python3 \"$CLAUDE_ROOT/hooks/model-orchestrator.py\""
jq -e --arg command "$claude_command" '
  [.hooks.UserPromptSubmit[]?.hooks[]? | select(.command == $command and .type == "command" and .timeout == 2)] | length == 1
' "$CLAUDE_ROOT/settings.json" >/dev/null
[[ -f "$CODEX_ROOT/hooks.json.model-orchestrator.bak" ]]
[[ -f "$CLAUDE_ROOT/settings.json.model-orchestrator.bak" ]]
printf 'null' | python3 "$CODEX_ROOT/hooks/model-orchestrator.py" >/dev/null

# the installed plugins find the shared router without any env var
MODEL_ORCHESTRATOR_ROUTER="$LANES_HOME/model_orchestrator.py" node -e "
import('$OPENCODE_ROOT/plugins/model-orchestrator.js').then(async (m) => {
  const h = await m.ModelOrchestratorPlugin({ directory: '$TMP_ROOT' });
  const out = { message: { id: 'm' }, parts: [{ type: 'text', text: 'count files' }] };
  await h['chat.message']({ sessionID: 's' }, out);
  if (out.parts.length !== 2 || !/lane=FAST/.test(out.parts[1].text)) { console.error(out); process.exit(1); }
});"

# skills
skills_list="$(bash "$ROOT/install.sh" --list-skills)"
[[ "$(printf '%s\n' "$skills_list" | wc -l | tr -d ' ')" == "10" ]]
grep -qx 'agent-starter' <<< "$skills_list"
grep -qx 'decision-sheet' <<< "$skills_list"

mkdir -p "$CODEX_ROOT/skills/aim-before-build" "$CLAUDE_ROOT/skills/aim-before-build"
printf 'previous codex skill\n' > "$CODEX_ROOT/skills/aim-before-build/SKILL.md"
printf 'previous claude skill\n' > "$CLAUDE_ROOT/skills/aim-before-build/SKILL.md"
run_install --skills 'aim-before-build, harness-audit'
for skill in aim-before-build harness-audit; do
  [[ -f "$CODEX_ROOT/skills/$skill/SKILL.md" ]]
  [[ -f "$CLAUDE_ROOT/skills/$skill/SKILL.md" ]]
  [[ -f "$HERMES_ROOT/skills/$skill/SKILL.md" ]]
  [[ -f "$OPENCLAW_ROOT/skills/$skill/SKILL.md" ]]
done
[[ -f "$CLAUDE_ROOT/skills/harness-audit/scripts/audit.py" ]]   # whole skill tree, not only SKILL.md
[[ ! -d "$OPENCODE_ROOT/skills" ]]                                 # OpenCode reads ~/.claude/skills
grep -qx 'previous codex skill' "$CODEX_ROOT/skills/aim-before-build/SKILL.md.model-orchestrator.bak"
grep -qx 'previous claude skill' "$CLAUDE_ROOT/skills/aim-before-build/SKILL.md.model-orchestrator.bak"
[[ ! -e "$CODEX_ROOT/skills/phase-loop/SKILL.md" ]]

run_install --starter
for skill in $skills_list; do
  [[ -f "$CODEX_ROOT/skills/$skill/SKILL.md" ]]
  [[ -f "$CLAUDE_ROOT/skills/$skill/SKILL.md" ]]
done
starter_hash="$(find "$CODEX_ROOT/skills" "$CLAUDE_ROOT/skills" -type f -name SKILL.md -exec shasum -a 256 {} + | sort)"
run_install --starter
[[ "$starter_hash" == "$(find "$CODEX_ROOT/skills" "$CLAUDE_ROOT/skills" -type f -name SKILL.md -exec shasum -a 256 {} + | sort)" ]]

dedupe_output="$(with_homes bash "$ROOT/install.sh" --runtimes claude --skills aim-before-build,aim-before-build)"
grep -q 'and 1 starter skill(s)' <<< "$dedupe_output"

# scaffold never overwrites
PROJ="$TMP_ROOT/proj"
mkdir -p "$PROJ/docs"
printf '# mine\n' > "$PROJ/docs/INDEX.md"
printf '# readme\n' > "$PROJ/README.md"
with_homes bash "$ROOT/install.sh" --runtimes claude --scaffold "$PROJ" >/dev/null
grep -qx '# mine' "$PROJ/docs/INDEX.md"
[[ -f "$PROJ/docs/status/DOC-SYNC-MATRIX.md" && -f "$PROJ/scripts/check-docs.sh" && -d "$PROJ/docs/research" ]]
bash "$PROJ/scripts/check-docs.sh" "$PROJ" >/dev/null

# failures happen before any write
if run_install --skills not-a-skill 2>/dev/null; then echo "Expected an unknown skill to fail" >&2; exit 1; fi
if run_install --skills aim-before-build, 2>/dev/null; then echo "Expected an empty skill name to fail" >&2; exit 1; fi
if run_install --runtimes cursor 2>/dev/null; then echo "Expected an unknown runtime to fail" >&2; exit 1; fi

BROKEN_ROOT="$TMP_ROOT/broken"
mkdir -p "$BROKEN_ROOT/codex"
printf '{broken' > "$BROKEN_ROOT/codex/hooks.json"
if MODEL_ORCHESTRATOR_HOME="$BROKEN_ROOT/lanes" MODEL_ORCHESTRATOR_CODEX_HOME="$BROKEN_ROOT/codex" MODEL_ORCHESTRATOR_CLAUDE_HOME="$BROKEN_ROOT/claude" \
   bash "$ROOT/install.sh" --runtimes codex,claude --starter >/dev/null 2>&1; then
  echo "Expected malformed settings to fail" >&2; exit 1
fi
[[ "$(find "$BROKEN_ROOT" -type f | wc -l | tr -d ' ')" == "1" ]]

HALF_ROOT="$TMP_ROOT/half"
mkdir -p "$HALF_ROOT/codex"
printf 'not-a-directory\n' > "$HALF_ROOT/claude"
if MODEL_ORCHESTRATOR_HOME="$HALF_ROOT/lanes" MODEL_ORCHESTRATOR_CODEX_HOME="$HALF_ROOT/codex" MODEL_ORCHESTRATOR_CLAUDE_HOME="$HALF_ROOT/claude" \
   bash "$ROOT/install.sh" --runtimes codex,claude --starter >/dev/null 2>&1; then
  echo "Expected a non-directory runtime home to fail" >&2; exit 1
fi
[[ -z "$(find "$HALF_ROOT/codex" -mindepth 1 -print -quit)" ]]

SPACE_ROOT="$TMP_ROOT/path with spaces"
MODEL_ORCHESTRATOR_HOME="$SPACE_ROOT/lanes" MODEL_ORCHESTRATOR_CODEX_HOME="$SPACE_ROOT/codex home" MODEL_ORCHESTRATOR_CLAUDE_HOME="$SPACE_ROOT/claude home" \
  bash "$ROOT/install.sh" --runtimes codex,claude --skills morning-brief >/dev/null
[[ -f "$SPACE_ROOT/codex home/skills/morning-brief/SKILL.md" ]]
[[ -f "$SPACE_ROOT/claude home/skills/morning-brief/SKILL.md" ]]

NO_JQ_BIN="$TMP_ROOT/no-jq-bin"
mkdir -p "$NO_JQ_BIN"
ln -s "$(command -v dirname)" "$NO_JQ_BIN/dirname"
ln -s "$(command -v python3)" "$NO_JQ_BIN/python3"
if PATH="$NO_JQ_BIN" /bin/bash "$ROOT/install.sh" --runtimes claude --dry-run > /dev/null 2> "$TMP_ROOT/no-jq.err"; then
  echo "Expected missing jq to fail" >&2; exit 1
fi
grep -q 'ERROR: jq is required' "$TMP_ROOT/no-jq.err"

NO_PYTHON_BIN="$TMP_ROOT/no-python-bin"
mkdir -p "$NO_PYTHON_BIN"
ln -s "$(command -v dirname)" "$NO_PYTHON_BIN/dirname"
ln -s "$(command -v jq)" "$NO_PYTHON_BIN/jq"
if PATH="$NO_PYTHON_BIN" /bin/bash "$ROOT/install.sh" --runtimes claude --dry-run > /dev/null 2> "$TMP_ROOT/no-python.err"; then
  echo "Expected missing python3 to fail" >&2; exit 1
fi
grep -q 'ERROR: python3 is required' "$TMP_ROOT/no-python.err"

NO_NODE_ROOT="$TMP_ROOT/no-node-root"
NO_NODE_BIN="$TMP_ROOT/no-node-bin"
mkdir -p "$NO_NODE_BIN"
ln -s "$(command -v dirname)" "$NO_NODE_BIN/dirname"
ln -s "$(command -v python3)" "$NO_NODE_BIN/python3"
if PATH="$NO_NODE_BIN" MODEL_ORCHESTRATOR_HOME="$NO_NODE_ROOT/lanes" MODEL_ORCHESTRATOR_OPENCODE_HOME="$NO_NODE_ROOT/opencode" \
   /bin/bash "$ROOT/install.sh" --runtimes opencode --dry-run > /dev/null 2> "$TMP_ROOT/no-node.err"; then
  echo "Expected missing Node to fail" >&2; exit 1
fi
grep -q 'ERROR: Node 22 or newer is required' "$TMP_ROOT/no-node.err"
[[ ! -e "$NO_NODE_ROOT" ]]

OLD_NODE_ROOT="$TMP_ROOT/old-node-root"
OLD_NODE_BIN="$TMP_ROOT/old-node-bin"
mkdir -p "$OLD_NODE_BIN"
ln -s "$(command -v dirname)" "$OLD_NODE_BIN/dirname"
ln -s "$(command -v python3)" "$OLD_NODE_BIN/python3"
printf '#!/bin/sh\nprintf "18\\n"\n' > "$OLD_NODE_BIN/node"
chmod +x "$OLD_NODE_BIN/node"
if PATH="$OLD_NODE_BIN" MODEL_ORCHESTRATOR_HOME="$OLD_NODE_ROOT/lanes" MODEL_ORCHESTRATOR_OPENCLAW_HOME="$OLD_NODE_ROOT/openclaw" \
   /bin/bash "$ROOT/install.sh" --runtimes openclaw --dry-run > /dev/null 2> "$TMP_ROOT/old-node.err"; then
  echo "Expected Node 18 to fail" >&2; exit 1
fi
grep -q 'ERROR: Node 22 or newer is required for OpenCode/OpenClaw (found 18)' "$TMP_ROOT/old-node.err"
[[ ! -e "$OLD_NODE_ROOT" ]]

echo "Installer test OK: five runtimes, shared router, plugin resolution, skill trees, scaffold, preflight, idempotent, fail-open"
