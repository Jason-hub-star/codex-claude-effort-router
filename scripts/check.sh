#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v jq >/dev/null
command -v python3 >/dev/null

python3 -m unittest discover -s "$ROOT/tests" -p 'test_*.py'
bash "$ROOT/tests/test_installer.sh"

for file in \
  README.md README.ko.md LICENSE SECURITY.md \
  docs/COMPARISON.md docs/VIDEO-ASSESSMENT.ko.md docs/effort-routing.workflow.json docs/effort-routing.html \
  evidence/VALIDATION.md assets/effort-routing.svg assets/effort-router-demo.mp4 \
  router/effort_router.py install.sh; do
  test -f "$ROOT/$file"
done

for lane in fast daily deep critical; do
  test -f "$ROOT/codex/profiles/effort-$lane.config.toml"
  test -f "$ROOT/claude/agents/effort-$lane.md"
done
for agent in scout explorer builder architect; do
  file="$ROOT/codex/agents/effort-$agent.toml"
  test -f "$file"
  grep -q '^name = "effort_' "$file"
  grep -q '^developer_instructions = ' "$file"
done

grep -q '<svg' "$ROOT/assets/effort-routing.svg"
grep -q 'One Prompt, Right-Sized Effort' "$ROOT/docs/effort-routing.html"

echo "Repository checks passed."
