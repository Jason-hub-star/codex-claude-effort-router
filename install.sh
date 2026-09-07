#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_ROOT="${EFFORT_ROUTER_CODEX_HOME:-$HOME/.codex}"
CLAUDE_ROOT="${EFFORT_ROUTER_CLAUDE_HOME:-$HOME/.claude}"
AVAILABLE_SKILLS=(
  agent-starter
  aim-before-build
  converge-plan
  evidence-audit
  goal-contract
  morning-brief
  phase-loop
)
SELECTED_SKILLS=()
HAS_SELECTED_SKILLS=0
DRY_RUN=0

usage() {
  cat <<'USAGE'
Usage: bash install.sh [options]

Install the effort router for both Codex and Claude Code.

Options:
  --starter          Also install all seven workflow skills
  --skills LIST      Install comma-separated skills; spaces after commas are OK
  --list-skills      Print available skill names without changing files
  --dry-run          Validate inputs and print destinations without changing files
  -h, --help         Show this help

Examples:
  bash install.sh
  bash install.sh --starter
  bash install.sh --skills morning-brief,evidence-audit
  bash install.sh --starter --dry-run

Existing files receive one-time .effort-router.bak backups. Restart active
Codex and Claude Code sessions after installation.
USAGE
}

list_skills() {
  printf '%s\n' "${AVAILABLE_SKILLS[@]}"
}

skill_exists() {
  local wanted="$1" skill
  for skill in "${AVAILABLE_SKILLS[@]}"; do
    [[ "$skill" == "$wanted" ]] && return 0
  done
  return 1
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

add_skill() {
  local wanted="$1" selected
  if [[ "$HAS_SELECTED_SKILLS" -eq 1 ]]; then
    for selected in "${SELECTED_SKILLS[@]}"; do
      [[ "$selected" == "$wanted" ]] && return 0
    done
  fi
  SELECTED_SKILLS+=("$wanted")
  HAS_SELECTED_SKILLS=1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --list-skills)
      list_skills
      exit 0
      ;;
    --starter)
      SELECTED_SKILLS=("${AVAILABLE_SKILLS[@]}")
      HAS_SELECTED_SKILLS=1
      shift
      ;;
    --skills)
      [[ $# -ge 2 && -n "$2" ]] || { echo "ERROR: --skills requires a comma-separated list" >&2; exit 1; }
      [[ "$2" != ,* && "$2" != *, && "$2" != *,,* ]] || { echo "ERROR: --skills contains an empty name" >&2; exit 1; }
      IFS=',' read -r -a requested_skills <<< "$2"
      for requested_skill in "${requested_skills[@]}"; do
        add_skill "$(trim "$requested_skill")"
      done
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "$HAS_SELECTED_SKILLS" -eq 1 ]]; then
  for skill in "${SELECTED_SKILLS[@]}"; do
    skill_exists "$skill" || { echo "ERROR: unknown skill: $skill" >&2; exit 1; }
  done
fi

command -v jq >/dev/null || { echo "ERROR: jq is required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 is required" >&2; exit 1; }

for source in \
  "$ROOT/router/effort_router.py" \
  "$ROOT"/codex/agents/*.toml \
  "$ROOT"/codex/profiles/*.config.toml \
  "$ROOT"/claude/agents/*.md; do
  [[ -f "$source" ]] || { echo "ERROR: missing installer source: $source" >&2; exit 1; }
done
[[ ! -e "$CODEX_ROOT" || -d "$CODEX_ROOT" ]] || { echo "ERROR: Codex home is not a directory: $CODEX_ROOT" >&2; exit 1; }
[[ ! -e "$CLAUDE_ROOT" || -d "$CLAUDE_ROOT" ]] || { echo "ERROR: Claude home is not a directory: $CLAUDE_ROOT" >&2; exit 1; }
for settings in "$CODEX_ROOT/hooks.json" "$CLAUDE_ROOT/settings.json"; do
  if [[ -e "$settings" ]]; then
    [[ -f "$settings" ]] || { echo "ERROR: settings path is not a file: $settings" >&2; exit 1; }
    jq -e . "$settings" >/dev/null || { echo "ERROR: invalid JSON settings: $settings" >&2; exit 1; }
  fi
done
if [[ "$HAS_SELECTED_SKILLS" -eq 1 ]]; then
  for skill in "${SELECTED_SKILLS[@]}"; do
    [[ -f "$ROOT/skills/$skill/SKILL.md" ]] || { echo "ERROR: missing skill source: $skill" >&2; exit 1; }
  done
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run OK. Codex target: $CODEX_ROOT"
  echo "Dry run OK. Claude target: $CLAUDE_ROOT"
  if [[ "$HAS_SELECTED_SKILLS" -eq 1 ]]; then
    echo "Workflow skills: ${SELECTED_SKILLS[*]}"
  else
    echo "Workflow skills: none (core-only)"
  fi
  exit 0
fi

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

if [[ "$HAS_SELECTED_SKILLS" -eq 1 ]]; then
  for skill in "${SELECTED_SKILLS[@]}"; do
    install_file "$ROOT/skills/$skill/SKILL.md" "$CODEX_ROOT/skills/$skill/SKILL.md"
    install_file "$ROOT/skills/$skill/SKILL.md" "$CLAUDE_ROOT/skills/$skill/SKILL.md"
  done
  echo "Installed effort router and ${#SELECTED_SKILLS[@]} starter skill(s) for Codex and Claude Code. Restart active sessions to load them."
else
  echo "Installed effort router for Codex and Claude Code. Restart active sessions to load new custom agents."
fi
