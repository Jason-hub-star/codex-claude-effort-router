# Doc sync matrix

Maps each work unit to its source of truth, the documents that must change with it, and the check that proves it.

| Work unit | Source truth | Required docs | Verify |
|---|---|---|---|
| `example` | `README.md` | `docs/status/PROJECT-STATUS.md` | `bash scripts/check-docs.sh` |

Rules: source truth points at code or runtime facts, never at another status document. Required docs are the nearest documents that must change with the unit.
