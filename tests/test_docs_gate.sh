#!/usr/bin/env bash
# Break tests for the docs gate: a gate that only passes is not a gate.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATE="$ROOT/scaffold/scripts/check-docs.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fresh() {
  rm -rf "$TMP/p"
  mkdir -p "$TMP/p"
  cp -R "$ROOT/scaffold/docs" "$TMP/p/docs"
  echo "# readme" > "$TMP/p/README.md"
}

expect_pass() {
  local out
  out="$(bash "$GATE" "$TMP/p" 2>&1)" || { echo "expected PASS, got:"; echo "$out"; exit 1; }
}

expect_fail() {
  local needle="$1" out
  if out="$(bash "$GATE" "$TMP/p" 2>&1)"; then echo "expected FAIL ($needle), gate passed"; exit 1; fi
  grep -qF -- "$needle" <<<"$out" || { echo "expected message '$needle', got:"; echo "$out"; exit 1; }
}

fresh; expect_pass
fresh; echo x > "$TMP/p/docs/stray.md"; expect_fail "root clutter: stray.md"
fresh; echo x > "$TMP/p/docs/archive/old-notes.md"; expect_fail "archive name rule: old-notes.md"
fresh; echo x > "$TMP/p/docs/archive/old-notes-superseded-2026-09-07.md"; expect_fail "not in ARCHIVE-INDEX.md"
fresh; echo x > "$TMP/p/docs/archive/old-notes-superseded-2026-09-07.md"
printf '| `old-notes-superseded-2026-09-07.md` | replaced | INDEX.md |\n' >> "$TMP/p/docs/archive/ARCHIVE-INDEX.md"; expect_pass
fresh; rm "$TMP/p/README.md"; expect_fail "source truth missing: README.md"
fresh; rm "$TMP/p/docs/status/DOC-SYNC-MATRIX.md"; expect_fail "missing"
fresh; for i in $(seq 1 19); do mkdir -p "$TMP/p/.claude/skills/s$i"; echo "---" > "$TMP/p/.claude/skills/s$i/SKILL.md"; done
expect_fail "19 skills installed; cap is 18"
fresh; mkdir -p "$TMP/p/.claude/skills/_archive/dead"; echo "---" > "$TMP/p/.claude/skills/_archive/dead/SKILL.md"; expect_pass

echo "Docs gate break tests OK"
