# Doc sync matrix

| Work unit | Source truth | Required docs | Verify |
|---|---|---|---|
| `router` | `router/effort_router.py` | `README.md`, `docs/evidence/VALIDATION.md` | `python3 -m unittest discover -s tests` |
| `installer` | `install.sh` | `README.md` | `bash tests/test_installer.sh` |
| `opencode-plugin` | `opencode/effort-lanes.js` | `README.md` | `node tests/test_opencode_plugin.mjs` |
| `openclaw-plugin` | `openclaw/index.js` | `README.md` | `node tests/test_openclaw_plugin.mjs` |
| `hermes-plugin` | `hermes/effort-lanes/__init__.py` | `README.md` | `python3 -m unittest tests/test_hermes_plugin.py` |
| `skills` | `skills/` | `skills/README.md`, `README.md` | `bash scripts/check.sh` |
| `docs-gate` | `scaffold/scripts/check-docs.sh` | `docs/INDEX.md` | `bash tests/test_docs_gate.sh` |

Rules: source truth points at code, never at another status document. `scripts/check-docs.sh` must stay byte-identical to the scaffold copy; `scripts/check.sh` enforces that.
