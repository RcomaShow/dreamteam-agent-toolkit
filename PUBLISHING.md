# Publishing DreamTeam 0.3

Run from the repository root:

```bash
python scripts/sync_claude_adapter.py
git diff --exit-code
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/measure_v03.py
python -m compileall dreamteam adapters/claude-code/plugins/dreamteam
python scripts/build_release.py
python scripts/smoke_plugin_artifact.py dist/dreamteam-claude-code-plugin-0.3.0.zip
```

The release branch must contain no bootstrap/remediation payload. Publish one reviewable commit. Do not claim empirical savings unless paired benchmark artifacts satisfy the publication gate.
