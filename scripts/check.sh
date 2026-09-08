#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v jq >/dev/null
command -v python3 >/dev/null
command -v node >/dev/null

python3 -m unittest discover -s "$ROOT/tests" -p 'test_*.py'
node "$ROOT/tests/test_opencode_plugin.mjs"
node "$ROOT/tests/test_openclaw_plugin.mjs"
bash "$ROOT/tests/test_installer.sh"
bash "$ROOT/tests/test_docs_gate.sh"
bash "$ROOT/scripts/check-docs.sh" "$ROOT" >/dev/null
cmp "$ROOT/scripts/check-docs.sh" "$ROOT/scaffold/scripts/check-docs.sh"

for file in \
  README.md README.ko.md LICENSE SECURITY.md CHANGELOG.md CONTRIBUTING.md \
  docs/INDEX.md docs/status/PROJECT-STATUS.md docs/status/DOC-SYNC-MATRIX.md docs/archive/ARCHIVE-INDEX.md \
  docs/research/COMPARISON.md docs/research/INSTALL-UX-RESEARCH.ko.md docs/research/VIDEO-ASSESSMENT.ko.md \
  docs/ref/diagrams/effort-routing.workflow.json docs/ref/diagrams/effort-routing.html \
  docs/ref/diagrams/starter-workflow.lifecycle.json docs/ref/diagrams/starter-workflow.html \
  docs/evidence/VALIDATION.md docs/evidence/CONTEXT-MANAGEMENT.md assets/effort-routing.svg assets/starter-workflow.svg assets/effort-router-demo.mp4 \
  router/effort_router.py router/config.example.json install.sh \
  opencode/effort-lanes.js opencode/package.json \
  openclaw/index.js openclaw/openclaw.plugin.json openclaw/package.json \
  hermes/effort-lanes/__init__.py hermes/effort-lanes/plugin.yaml \
  scaffold/scripts/check-docs.sh scaffold/docs/INDEX.md scaffold/docs/status/DOC-SYNC-MATRIX.md \
  .claude-plugin/plugin.json .claude-plugin/marketplace.json hooks/hooks.json tests/test_wsl_container.sh; do
  test -f "$ROOT/$file"
done
grep -q 'WSL 2' "$ROOT/README.md"
grep -q 'Git Bash, PowerShell, and Command Prompt are not supported' "$ROOT/README.md"
grep -q 'WSL 2' "$ROOT/README.ko.md"
for json in router/config.example.json opencode/package.json openclaw/openclaw.plugin.json openclaw/package.json \
  .claude-plugin/plugin.json .claude-plugin/marketplace.json hooks/hooks.json; do
  jq -e . "$ROOT/$json" >/dev/null
done
jq -e '(has("agents") | not) and (has("hooks") | not)' "$ROOT/.claude-plugin/plugin.json" >/dev/null  # standard paths auto-discover both
[[ "$(jq -r .name "$ROOT/openclaw/package.json")" == "$(jq -r .id "$ROOT/openclaw/openclaw.plugin.json")" ]]  # OpenClaw id hint

for lane in fast daily deep critical; do
  test -f "$ROOT/codex/profiles/effort-$lane.config.toml"
  test -f "$ROOT/agents/effort-$lane.md"
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
  # OpenClaw's parser accepts frontmatter `metadata` only as a single-line JSON object
  if grep -q '^metadata:' "$skill_file"; then grep -qE '^metadata: *\{.*\} *$' "$skill_file"; fi
  grep -q '^## Next' "$skill_file"   # every stage hands the baton to the next one
  skill_count=$((skill_count + 1))
done
[[ "$skill_count" -eq 10 ]]
[[ "$(bash "$ROOT/install.sh" --list-skills | wc -l | tr -d ' ')" == "$skill_count" ]]
grep -q 'grill-me' "$ROOT/skills/decision-sheet/SKILL.md"   # prior art stays credited

grep -q '<svg' "$ROOT/assets/effort-routing.svg"
grep -q '<svg' "$ROOT/assets/starter-workflow.svg"
grep -q 'One Prompt, Right-Sized Effort' "$ROOT/docs/ref/diagrams/effort-routing.html"
grep -q 'Remixable Agent Work Lifecycle' "$ROOT/docs/ref/diagrams/starter-workflow.html"

case_count="$(jq length "$ROOT/tests/cases.json")"
grep -q "$case_count English/Korean prompts" "$ROOT/README.md"
grep -q "프롬프트 ${case_count}개" "$ROOT/README.ko.md"
grep -q "$case_count English/Korean prompts" "$ROOT/docs/evidence/VALIDATION.md"
grep -q "$case_count English and Korean classification cases" "$ROOT/docs/ref/diagrams/effort-routing.workflow.json"
grep -q "$case_count English and Korean classification cases" "$ROOT/docs/ref/diagrams/effort-routing.html"
grep -q "$case_count routing cases" "$ROOT/promo/remotion/src/root.tsx"
grep -q '>effort-lanes</div>' "$ROOT/promo/remotion/src/root.tsx"
! grep -Eq '200-line|under 50 ms|effort-router-demo\.(gif|mp4)' "$ROOT/README.md"
! grep -Eq '50ms 안|effort-router-demo\.(gif|mp4)' "$ROOT/README.ko.md"
grep -q 'Input + cache read' "$ROOT/README.md"
grep -q '입력+캐시 읽기' "$ROOT/README.ko.md"
for value in '-6.2%' '-11.7%' '-49.8%' '-1.9%' '+17.7%' '+15.4%' '-34.7%' '+3.8%'; do
  grep -Fq -- "$value" "$ROOT/README.md"
  grep -Fq -- "$value" "$ROOT/README.ko.md"
done
grep -q 'No automatic finish hook was added' "$ROOT/docs/evidence/VALIDATION.md"

echo "Repository checks passed."
