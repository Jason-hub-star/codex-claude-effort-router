# Contributing

Small, evidence-backed changes are welcome.

1. Add or update a prompt fixture in `tests/cases.json` when routing behavior changes.
2. Run `bash scripts/check.sh`.
3. Explain the behavior change and tradeoff in the pull request.

Avoid adding dependencies to the router itself. Promo tooling is isolated under `promo/`.
