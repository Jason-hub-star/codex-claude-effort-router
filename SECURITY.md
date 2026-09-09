# Security policy

Please report vulnerabilities privately through GitHub Security Advisories for this repository.

Before installing, review `install.sh` and `router/model_orchestrator.py`. Hooks execute as your local user. The installer only writes named files under the configured Codex and Claude homes, creates one-time backups, and preserves unrelated handlers.

Never add secrets, tokens, credentials, or captured private prompts to issues or validation evidence.
