#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v jq >/dev/null
command -v python3 >/dev/null

python3 -m unittest discover -s "$ROOT/tests" -p 'test_*.py'
bash "$ROOT/tests/test_installer.sh"

for file in \
  README.md README.ko.md LICENSE SECURITY.md \
  docs/COMPARISON.md docs/FINAL-EVALUATION.ko.md docs/INSTALL-UX-RESEARCH.ko.md docs/VIDEO-ASSESSMENT.ko.md \
  docs/effort-routing.workflow.json docs/effort-routing.html docs/starter-workflow.lifecycle.json docs/starter-workflow.html \
  evidence/VALIDATION.md assets/effort-routing.svg assets/starter-workflow.svg assets/effort-router-demo.mp4 \
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

skill_count=0
for skill_dir in "$ROOT"/skills/*; do
  [[ -d "$skill_dir" ]] || continue
  skill="$(basename "$skill_dir")"
  skill_file="$skill_dir/SKILL.md"
  test -f "$skill_file"
  grep -qx -- '---' "$skill_file"
  grep -q "^name: $skill$" "$skill_file"
  grep -q '^description: ' "$skill_file"
  ! grep -q 'TODO' "$skill_file"
  skill_count=$((skill_count + 1))
done
[[ "$skill_count" -eq 7 ]]

grep -q '<svg' "$ROOT/assets/effort-routing.svg"
grep -q '<svg' "$ROOT/assets/starter-workflow.svg"
grep -q 'One Prompt, Right-Sized Effort' "$ROOT/docs/effort-routing.html"
grep -q 'Remixable Agent Work Lifecycle' "$ROOT/docs/starter-workflow.html"

echo "Repository checks passed."
