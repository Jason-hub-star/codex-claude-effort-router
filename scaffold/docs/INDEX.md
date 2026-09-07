# Docs index

Folders state what a document is and whether it may be cited as evidence.

| Folder | Holds | Cite as evidence? |
|---|---|---|
| `ref/` | The basis for the code: architecture, contracts, plans | Yes |
| `status/` | Current state, decisions, open gaps | Yes, for state only |
| `evidence/` | Dated verification records | Yes, for that date |
| `research/` | Pre-work investigation output | No |
| `archive/` | Superseded or abandoned documents | No |

Only entry documents live in this root. `bash scripts/check-docs.sh` enforces the layout.
