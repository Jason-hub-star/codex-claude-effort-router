# Doc sync matrix

| Work unit | Source truth | Required docs | Verify |
|---|---|---|---|
| `router` | `router/effort_router.py` | `README.md`, `README.ko.md`, `docs/evidence/VALIDATION.md` | `python3 -m unittest discover -s tests` |
| `installer` | `install.sh` | `README.md`, `README.ko.md`, `docs/evidence/VALIDATION.md` | `bash tests/test_installer.sh` |
| `claude-plugin` | `.claude-plugin/plugin.json` | `README.md`, `README.ko.md`, `docs/evidence/VALIDATION.md` | `claude plugin validate --strict .` |
| `opencode-plugin` | `opencode/effort-lanes.js` | `README.md`, `README.ko.md` | `node tests/test_opencode_plugin.mjs` |
| `openclaw-plugin` | `openclaw/index.js` | `README.md`, `README.ko.md` | `node tests/test_openclaw_plugin.mjs` |
| `hermes-plugin` | `hermes/effort-lanes/__init__.py` | `README.md`, `README.ko.md` | `python3 -m unittest tests/test_hermes_plugin.py` |
| `skills` | `skills/` | `skills/README.md`, `README.md`, `README.ko.md` | `bash scripts/check.sh` |
| `docs-gate` | `scaffold/scripts/check-docs.sh` | `docs/INDEX.md` | `bash tests/test_docs_gate.sh` |
| `bench` | `bench/run.py` | `bench/README.md`, `README.md`, `README.ko.md`, `docs/evidence/VALIDATION.md` | `python3 -m unittest discover -s tests -p 'test_bench.py'` |

Rules: source truth points at code, never at another status document. `scripts/check-docs.sh` must stay byte-identical to the scaffold copy; `scripts/check.sh` enforces that.
