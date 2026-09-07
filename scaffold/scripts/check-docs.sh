#!/usr/bin/env bash
# Documentation gate: fails when the docs/ layout stops telling the truth.
#
#  1. docs/ root holds entry documents only; everything else lives in a folder that states its role.
#  2. docs/archive/ files carry <name>-<reason>-<YYYY-MM-DD>.<ext> and are listed in ARCHIVE-INDEX.md.
#  3. docs/status/DOC-SYNC-MATRIX.md exists and every "Source truth" path it names exists.
#  4. The project installs at most SKILL_CAP skills (recovery rate drops sharply above it).
#
# Usage: bash scripts/check-docs.sh [project-dir]
set -uo pipefail

ROOT="${1:-.}"
DOCS="$ROOT/docs"
ALLOWED_ROOT="${DOCS_ALLOWED_ROOT:-INDEX.md SESSION-START.md README.md}"
SKILL_CAP="${SKILL_CAP:-18}"
FAILURES=0

bad() { echo "FAIL $*"; FAILURES=$((FAILURES + 1)); }
ok() { echo "ok   $*"; }

[[ -d "$DOCS" ]] || { echo "FAIL docs/ missing: $DOCS"; exit 1; }

# 1. docs/ root
for f in "$DOCS"/*; do
  [[ -f "$f" ]] || continue
  b="$(basename "$f")"
  case " $ALLOWED_ROOT " in
    *" $b "*) ok "root entry: $b" ;;
    *) bad "docs/ root clutter: $b -> move to ref/ status/ evidence/ research/ archive/" ;;
  esac
done

# 2. archive naming + index
if [[ -d "$DOCS/archive" ]]; then
  index="$DOCS/archive/ARCHIVE-INDEX.md"
  for f in "$DOCS"/archive/*; do
    [[ -f "$f" ]] || continue
    b="$(basename "$f")"
    [[ "$b" == "ARCHIVE-INDEX.md" ]] && continue
    if printf '%s' "$b" | grep -qE -- '-(superseded|abandoned|legacy|progresslog)-[0-9]{4}-[0-9]{2}-[0-9]{2}\.[A-Za-z0-9]+$'; then
      if [[ -f "$index" ]] && grep -qF -- "$b" "$index"; then ok "archived: $b"; else bad "not in ARCHIVE-INDEX.md: $b"; fi
    else
      bad "archive name rule: $b -> <name>-<superseded|abandoned|legacy|progresslog>-<YYYY-MM-DD>.<ext>"
    fi
  done
fi

# 3. sync matrix
matrix="$DOCS/status/DOC-SYNC-MATRIX.md"
if [[ -f "$matrix" ]]; then
  ok "sync matrix present"
  # table rows: | `unit` | `source/path` | ... ; the second backticked cell is the source truth
  while IFS= read -r src; do
    [[ -z "$src" ]] && continue
    if [[ -e "$ROOT/$src" ]]; then ok "source truth exists: $src"; else bad "source truth missing: $src"; fi
  done < <(grep -E '^\| *`[^`]+` *\| *`[^`]+`' "$matrix" | sed -E 's/^\| *`[^`]+` *\| *`([^`]+)`.*/\1/')
else
  bad "missing $matrix"
fi

# 4. skill cap
count=0
for d in "$ROOT"/.claude/skills/*/ "$ROOT"/.codex/skills/*/ "$ROOT"/.agents/skills/*/; do
  [[ -f "$d/SKILL.md" ]] || continue
  [[ "$d" == *"/_archive/"* ]] && continue
  count=$((count + 1))
done
if (( count > SKILL_CAP )); then bad "$count skills installed; cap is $SKILL_CAP"; else ok "skills installed: $count/$SKILL_CAP"; fi

if (( FAILURES > 0 )); then echo "docs gate: $FAILURES failure(s)"; exit 1; fi
echo "docs gate: PASS"
