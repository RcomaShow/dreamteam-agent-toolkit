# Publishing DreamTeam 0.5.0

Run from a clean repository root:

```bash
python scripts/sync_claude_adapter.py
git diff --exit-code
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/measure.py
python -m compileall dreamteam adapters/claude-code/plugins/dreamteam adapters/codex scripts/install_codex_adapter.py
python scripts/build_release.py
python scripts/smoke_plugin_artifact.py dist/dreamteam-claude-code-plugin-0.5.0.zip
```

Equivalent developer shortcuts:

```bash
make check
make release
```

The build refuses dirty working trees and symlinks, obtains its allowlist from `git ls-files`, writes a commit-bound source manifest, deterministic SBOM, and SHA-256 checksums.

## 0.5 claim policy

Publish cost, token, normalized-payload, and combined efficiency claims separately. A cheaper model is not evidence of token savings. General efficiency claims require paired quality parity and the configured sample, median, and positive lower-tail gates for every reported bucket.

Token routing thresholds remain shadow policy until representative paired provider benchmarks calibrate them. The current strict ledger enforces forecast reservations; without authoritative provider usage callbacks it is not a provider-side spending hard cap.
