#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_ROOT="${EFFORT_ROUTER_CODEX_HOME:-$HOME/.codex}"
CLAUDE_ROOT="${EFFORT_ROUTER_CLAUDE_HOME:-$HOME/.claude}"

command -v jq >/dev/null || { echo "ERROR: jq is required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 is required" >&2; exit 1; }

install_file() {
  local source="$1" target="$2"
  mkdir -p "$(dirname "$target")"
  if [[ -e "$target" && ! -e "$target.effort-router.bak" ]]; then
    cp -p "$target" "$target.effort-router.bak"
  fi
  cp "$source" "$target"
}

merge_hook() {
  local settings="$1" command="$2" platform="$3" handler temp
  mkdir -p "$(dirname "$settings")"
  [[ -e "$settings" ]] || printf '{"hooks":{}}\n' > "$settings"
  jq -e . "$settings" >/dev/null
  [[ -e "$settings.effort-router.bak" ]] || cp -p "$settings" "$settings.effort-router.bak"

  if [[ "$platform" == "codex" ]]; then
    handler="$(jq -nc --arg command "$command" '{type:"command",command:$command,timeout:2,statusMessage:"Routing task effort",additionalContextLimit:1200}')"
  else
    handler="$(jq -nc --arg command "$command" '{type:"command",command:$command,timeout:2,statusMessage:"Routing task effort"}')"
  fi

  temp="$(mktemp "$(dirname "$settings")/.effort-router.XXXXXX")"
  jq --arg command "$command" --argjson handler "$handler" '
    .hooks = (.hooks // {})
    | .hooks.UserPromptSubmit = (.hooks.UserPromptSubmit // [])
    | .hooks.UserPromptSubmit = [
        .hooks.UserPromptSubmit[]?
        | .hooks = [ .hooks[]? | select(.command != $command) ]
        | select((.hooks | length) > 0)
      ]
    | .hooks.UserPromptSubmit += [{"hooks": [$handler]}]
  ' "$settings" > "$temp"
  chmod 600 "$temp"
  mv "$temp" "$settings"
}

install_file "$ROOT/router/effort_router.py" "$CODEX_ROOT/hooks/effort-router.py"
for source in "$ROOT"/codex/agents/*.toml; do
  install_file "$source" "$CODEX_ROOT/agents/$(basename "$source")"
done
for source in "$ROOT"/codex/profiles/*.config.toml; do
  install_file "$source" "$CODEX_ROOT/$(basename "$source")"
done
merge_hook "$CODEX_ROOT/hooks.json" "python3 \"$CODEX_ROOT/hooks/effort-router.py\"" codex

install_file "$ROOT/router/effort_router.py" "$CLAUDE_ROOT/hooks/effort-router.py"
for source in "$ROOT"/claude/agents/*.md; do
  install_file "$source" "$CLAUDE_ROOT/agents/$(basename "$source")"
done
merge_hook "$CLAUDE_ROOT/settings.json" "python3 \"$CLAUDE_ROOT/hooks/effort-router.py\"" claude

echo "Installed effort router for Codex and Claude Code. Restart active sessions to load new custom agents."
