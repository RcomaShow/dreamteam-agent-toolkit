# Publishing DreamTeam 0.4.2

Run from a clean repository root:

```bash
python scripts/sync_claude_adapter.py
git diff --exit-code
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/measure.py
python -m compileall dreamteam adapters/claude-code/plugins/dreamteam
python scripts/build_release.py
python scripts/smoke_plugin_artifact.py dist/dreamteam-claude-code-plugin-0.4.2.zip
```

Equivalent developer shortcuts:

```bash
make check
make release
```

The build refuses dirty working trees and symlinks, obtains its allowlist from `git ls-files`, writes a commit-bound source manifest, and emits SHA-256 checksums. Publish one reviewable release commit. Do not claim empirical savings unless paired benchmark artifacts satisfy every quality and economic bucket gate.
