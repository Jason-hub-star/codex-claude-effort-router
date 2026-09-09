#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCHESTRATOR_HOME="${MODEL_ORCHESTRATOR_HOME:-$HOME/.config/model-orchestrator}"
CODEX_ROOT="${MODEL_ORCHESTRATOR_CODEX_HOME:-$HOME/.codex}"
CLAUDE_ROOT="${MODEL_ORCHESTRATOR_CLAUDE_HOME:-$HOME/.claude}"
OPENCODE_ROOT="${MODEL_ORCHESTRATOR_OPENCODE_HOME:-$HOME/.config/opencode}"
OPENCLAW_ROOT="${MODEL_ORCHESTRATOR_OPENCLAW_HOME:-$HOME/.openclaw}"
HERMES_ROOT="${MODEL_ORCHESTRATOR_HERMES_HOME:-$HOME/.hermes}"
ALL_RUNTIMES=(codex claude opencode openclaw hermes)
AVAILABLE_SKILLS=(
  absorb
  agent-starter
  aim-before-build
  converge-plan
  decision-sheet
  evidence-audit
  goal-contract
  harness-audit
  morning-brief
  phase-loop
)
SELECTED_SKILLS=()
HAS_SELECTED_SKILLS=0
SELECTED_RUNTIMES=()
HAS_SELECTED_RUNTIMES=0
DRY_RUN=0
SCAFFOLD_DIR=""
DO_SCAFFOLD=0

usage() {
  cat <<'USAGE'
Usage: bash install.sh [options]

Install Model Orchestrator for Codex, Claude Code, OpenCode, OpenClaw, and Hermes Agent.

Options:
  --runtimes LIST    Comma-separated subset of: codex,claude,opencode,openclaw,hermes
                     (default: every runtime detected on this machine)
  --starter          Also install all workflow skills
  --skills LIST      Install comma-separated skills; spaces after commas are OK
  --list-skills      Print available skill names without changing files
  --scaffold [DIR]   Copy the docs layout and docs gate into DIR (default: current
                     directory); existing files are never overwritten
  --dry-run          Validate inputs and print destinations without changing files
  -h, --help         Show this help

Examples:
  bash install.sh
  bash install.sh --runtimes claude,opencode --starter
  bash install.sh --skills decision-sheet,evidence-audit
  bash install.sh --scaffold ~/code/my-project
  bash install.sh --starter --dry-run

Existing files receive one-time .model-orchestrator.bak backups. Restart active
sessions after installation. Enforcement (OpenCode, OpenClaw) stays off until
you enable it; see README.
USAGE
}

list_skills() { printf '%s\n' "${AVAILABLE_SKILLS[@]}"; }

in_list() {
  local wanted="$1" item; shift
  for item in "$@"; do [[ "$item" == "$wanted" ]] && return 0; done
  return 1
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

add_skill() {
  local wanted="$1"
  if [[ "$HAS_SELECTED_SKILLS" -eq 1 ]] && in_list "$wanted" "${SELECTED_SKILLS[@]}"; then return 0; fi
  SELECTED_SKILLS+=("$wanted"); HAS_SELECTED_SKILLS=1
}

add_runtime() {
  local wanted="$1"
  if [[ "$HAS_SELECTED_RUNTIMES" -eq 1 ]] && in_list "$wanted" "${SELECTED_RUNTIMES[@]}"; then return 0; fi
  SELECTED_RUNTIMES+=("$wanted"); HAS_SELECTED_RUNTIMES=1
}

split_list() {
  local raw="$2" item
  [[ -n "$raw" ]] || { echo "ERROR: $1 requires a comma-separated list" >&2; exit 1; }
  [[ "$raw" != ,* && "$raw" != *, && "$raw" != *,,* ]] || { echo "ERROR: $1 contains an empty name" >&2; exit 1; }
  IFS=',' read -r -a __items <<< "$raw"
  for item in "${__items[@]}"; do printf '%s\n' "$(trim "$item")"; done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --list-skills) list_skills; exit 0 ;;
    --starter) SELECTED_SKILLS=("${AVAILABLE_SKILLS[@]}"); HAS_SELECTED_SKILLS=1; shift ;;
    --skills)
      [[ $# -ge 2 ]] || { echo "ERROR: --skills requires a comma-separated list" >&2; exit 1; }
      parsed="$(split_list --skills "$2")"
      while IFS= read -r s; do add_skill "$s"; done <<< "$parsed"
      shift 2 ;;
    --runtimes)
      [[ $# -ge 2 ]] || { echo "ERROR: --runtimes requires a comma-separated list" >&2; exit 1; }
      parsed="$(split_list --runtimes "$2")"
      while IFS= read -r r; do add_runtime "$r"; done <<< "$parsed"
      shift 2 ;;
    --scaffold)
      DO_SCAFFOLD=1
      if [[ $# -ge 2 && "$2" != -* ]]; then SCAFFOLD_DIR="$2"; shift 2; else SCAFFOLD_DIR="$PWD"; shift; fi ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "ERROR: unknown argument: $1" >&2; exit 1 ;;
  esac
done

# --- validation -------------------------------------------------------------------------

if [[ "$HAS_SELECTED_SKILLS" -eq 1 ]]; then
  for skill in "${SELECTED_SKILLS[@]}"; do
    in_list "$skill" "${AVAILABLE_SKILLS[@]}" || { echo "ERROR: unknown skill: $skill" >&2; exit 1; }
    [[ -f "$ROOT/skills/$skill/SKILL.md" ]] || { echo "ERROR: missing skill source: $skill" >&2; exit 1; }
  done
fi
if [[ "$HAS_SELECTED_RUNTIMES" -eq 1 ]]; then
  for rt in "${SELECTED_RUNTIMES[@]}"; do
    in_list "$rt" "${ALL_RUNTIMES[@]}" || { echo "ERROR: unknown runtime: $rt (choose from ${ALL_RUNTIMES[*]})" >&2; exit 1; }
  done
else
  [[ -d "$CODEX_ROOT" || -n "$(command -v codex 2>/dev/null)" ]] && add_runtime codex
  [[ -d "$CLAUDE_ROOT" || -n "$(command -v claude 2>/dev/null)" ]] && add_runtime claude
  [[ -d "$OPENCODE_ROOT" || -n "$(command -v opencode 2>/dev/null)" ]] && add_runtime opencode
  [[ -n "$(command -v openclaw 2>/dev/null)" ]] && add_runtime openclaw
  [[ -d "$HERMES_ROOT" || -n "$(command -v hermes 2>/dev/null)" ]] && add_runtime hermes
  [[ "$HAS_SELECTED_RUNTIMES" -eq 1 ]] || { echo "ERROR: no supported runtime detected; pass --runtimes" >&2; exit 1; }
fi

want() { [[ "$HAS_SELECTED_RUNTIMES" -eq 1 ]] && in_list "$1" "${SELECTED_RUNTIMES[@]}"; }

command -v python3 >/dev/null || { echo "ERROR: python3 is required" >&2; exit 1; }
if want codex || want claude; then
  command -v jq >/dev/null || { echo "ERROR: jq is required" >&2; exit 1; }
fi
if want opencode || want openclaw; then
  command -v node >/dev/null || { echo "ERROR: Node 22 or newer is required for OpenCode/OpenClaw" >&2; exit 1; }
  node_major="$(node -p 'Number(process.versions.node.split(".")[0])' 2>/dev/null || true)"
  [[ "$node_major" =~ ^[0-9]+$ && "$node_major" -ge 22 ]] || {
    echo "ERROR: Node 22 or newer is required for OpenCode/OpenClaw (found ${node_major:-unknown})" >&2
    exit 1
  }
fi

for home in "$ORCHESTRATOR_HOME" "$CODEX_ROOT" "$CLAUDE_ROOT" "$OPENCODE_ROOT" "$HERMES_ROOT"; do
  [[ ! -e "$home" || -d "$home" ]] || { echo "ERROR: runtime home is not a directory: $home" >&2; exit 1; }
done
for settings in "$CODEX_ROOT/hooks.json" "$CLAUDE_ROOT/settings.json"; do
  if [[ -e "$settings" ]]; then
    [[ -f "$settings" ]] || { echo "ERROR: settings path is not a file: $settings" >&2; exit 1; }
    jq -e . "$settings" >/dev/null || { echo "ERROR: invalid JSON settings: $settings" >&2; exit 1; }
  fi
done
if [[ "$DO_SCAFFOLD" -eq 1 ]]; then
  [[ ! -e "$SCAFFOLD_DIR" || -d "$SCAFFOLD_DIR" ]] || { echo "ERROR: scaffold target is not a directory: $SCAFFOLD_DIR" >&2; exit 1; }
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run OK. Shared router: $ORCHESTRATOR_HOME/model_orchestrator.py"
  echo "Runtimes: ${SELECTED_RUNTIMES[*]}"
  want codex && echo "Dry run OK. Codex target: $CODEX_ROOT"
  want claude && echo "Dry run OK. Claude target: $CLAUDE_ROOT"
  want opencode && echo "Dry run OK. OpenCode target: $OPENCODE_ROOT/plugins/model-orchestrator.js"
  want openclaw && echo "Dry run OK. OpenClaw target: openclaw plugins install $ROOT/openclaw"
  want hermes && echo "Dry run OK. Hermes target: $HERMES_ROOT/plugins/model-orchestrator"
  if [[ "$HAS_SELECTED_SKILLS" -eq 1 ]]; then echo "Workflow skills: ${SELECTED_SKILLS[*]}"; else echo "Workflow skills: none (core-only)"; fi
  [[ "$DO_SCAFFOLD" -eq 1 ]] && echo "Scaffold target: $SCAFFOLD_DIR"
  exit 0
fi

# --- helpers ----------------------------------------------------------------------------

install_file() {
  local source="$1" target="$2"
  mkdir -p "$(dirname "$target")"
  if [[ -e "$target" && ! -e "$target.model-orchestrator.bak" ]]; then cp -p "$target" "$target.model-orchestrator.bak"; fi
  cp "$source" "$target"
}

install_tree() {
  # copy every file under $1 into $2, one-time backup per existing file
  local source="$1" target="$2" file rel
  while IFS= read -r -d '' file; do
    rel="${file#"$source"/}"
    install_file "$file" "$target/$rel"
  done < <(find "$source" -type f -print0)
}

merge_hook() {
  local settings="$1" command="$2" platform="$3" handler temp
  mkdir -p "$(dirname "$settings")"
  [[ -e "$settings" ]] || printf '{"hooks":{}}\n' > "$settings"
  jq -e . "$settings" >/dev/null
  [[ -e "$settings.model-orchestrator.bak" ]] || cp -p "$settings" "$settings.model-orchestrator.bak"
  if [[ "$platform" == "codex" ]]; then
    handler="$(jq -nc --arg command "$command" '{type:"command",command:$command,timeout:2,statusMessage:"Routing task effort",additionalContextLimit:1200}')"
  else
    handler="$(jq -nc --arg command "$command" '{type:"command",command:$command,timeout:2,statusMessage:"Routing task effort"}')"
  fi
  temp="$(mktemp "$(dirname "$settings")/.model-orchestrator.XXXXXX")"
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

install_skills_into() {
  local base="$1" skill
  [[ "$HAS_SELECTED_SKILLS" -eq 1 ]] || return 0
  for skill in "${SELECTED_SKILLS[@]}"; do install_tree "$ROOT/skills/$skill" "$base/$skill"; done
}

# --- install ----------------------------------------------------------------------------

NOTES=()
install_file "$ROOT/router/model_orchestrator.py" "$ORCHESTRATOR_HOME/model_orchestrator.py"
[[ -e "$ORCHESTRATOR_HOME/config.example.json" ]] || cp "$ROOT/router/config.example.json" "$ORCHESTRATOR_HOME/config.example.json"

if want codex; then
  install_file "$ROOT/router/model_orchestrator.py" "$CODEX_ROOT/hooks/model-orchestrator.py"
  for source in "$ROOT"/codex/agents/*.toml; do install_file "$source" "$CODEX_ROOT/agents/$(basename "$source")"; done
  for source in "$ROOT"/codex/profiles/*.config.toml; do install_file "$source" "$CODEX_ROOT/$(basename "$source")"; done
  merge_hook "$CODEX_ROOT/hooks.json" "python3 \"$CODEX_ROOT/hooks/model-orchestrator.py\"" codex
  install_skills_into "$CODEX_ROOT/skills"
fi

if want claude; then
  install_file "$ROOT/router/model_orchestrator.py" "$CLAUDE_ROOT/hooks/model-orchestrator.py"
  for source in "$ROOT"/agents/*.md; do install_file "$source" "$CLAUDE_ROOT/agents/$(basename "$source")"; done
  merge_hook "$CLAUDE_ROOT/settings.json" "python3 \"$CLAUDE_ROOT/hooks/model-orchestrator.py\"" claude
  install_skills_into "$CLAUDE_ROOT/skills"
fi

if want opencode; then
  install_file "$ROOT/opencode/model-orchestrator.js" "$OPENCODE_ROOT/plugins/model-orchestrator.js"
  if want claude; then
    NOTES+=("OpenCode reads skills from ~/.claude/skills, so no separate OpenCode skill copy was made.")
  else
    install_skills_into "$OPENCODE_ROOT/skills"
  fi
fi

if want openclaw; then
  if [[ -n "${MODEL_ORCHESTRATOR_OPENCLAW_HOME:-}" ]]; then
    install_tree "$ROOT/openclaw" "$OPENCLAW_ROOT/extensions/model-orchestrator"
  elif command -v openclaw >/dev/null; then
    openclaw plugins install "$ROOT/openclaw" >/dev/null 2>&1 || NOTES+=("OpenClaw plugin install failed; run: openclaw plugins install $ROOT/openclaw")
    NOTES+=("OpenClaw: restart the gateway, and add \"model-orchestrator\" to plugins.allow to silence the trust warning.")
  else
    NOTES+=("OpenClaw CLI not found; skipped. Install it, then run: openclaw plugins install $ROOT/openclaw")
  fi
  install_skills_into "$OPENCLAW_ROOT/skills"
fi

if want hermes; then
  install_tree "$ROOT/hermes/model-orchestrator" "$HERMES_ROOT/plugins/model-orchestrator"
  install_skills_into "$HERMES_ROOT/skills"
  if [[ -z "${MODEL_ORCHESTRATOR_HERMES_HOME:-}" ]] && command -v hermes >/dev/null; then
    # stdin closed: the enable command can prompt for capability grants and would otherwise hang
    hermes plugins enable model-orchestrator </dev/null >/dev/null 2>&1 || NOTES+=("Run: hermes plugins enable model-orchestrator")
  else
    NOTES+=("Hermes: run 'hermes plugins enable model-orchestrator' (or add a pre_llm_call shell hook; see README).")
  fi
fi

if [[ "$DO_SCAFFOLD" -eq 1 ]]; then
  copied=0
  while IFS= read -r -d '' file; do
    rel="${file#"$ROOT/scaffold"/}"
    [[ "$(basename "$file")" == ".gitkeep" ]] && { mkdir -p "$SCAFFOLD_DIR/$(dirname "$rel")"; continue; }
    if [[ -e "$SCAFFOLD_DIR/$rel" ]]; then continue; fi
    mkdir -p "$SCAFFOLD_DIR/$(dirname "$rel")"
    cp "$file" "$SCAFFOLD_DIR/$rel"
    copied=$((copied + 1))
  done < <(find "$ROOT/scaffold" -type f -print0)
  echo "Scaffolded $copied file(s) into $SCAFFOLD_DIR (existing files untouched). Gate: bash scripts/check-docs.sh"
fi

skill_note="core only"
[[ "$HAS_SELECTED_SKILLS" -eq 1 ]] && skill_note="and ${#SELECTED_SKILLS[@]} starter skill(s)"
echo "Installed Model Orchestrator for: ${SELECTED_RUNTIMES[*]} ($skill_note). Restart active sessions."
if [[ ${#NOTES[@]} -gt 0 ]]; then printf '  note: %s\n' "${NOTES[@]}"; fi
