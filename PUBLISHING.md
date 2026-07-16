# Publishing

## Pre-release checks

Run the platform-independent validation suite:

```bash
python scripts/sync_claude_adapter.py
python scripts/validate.py
python -m unittest discover -s tests -v
```

Validate representative DCP/2 and CHP/2 files with:

```bash
python scripts/protocol_v2.py path/to/contract.dcp2 --hash
python scripts/protocol_v2.py path/to/handoff.chp2
```

When Claude Code is installed, also validate the adapter and marketplace:

```bash
claude plugin validate ./adapters/claude-code/plugins/dreamteam --strict
claude plugin validate .
```

## Release process

1. Update the plugin version and `CHANGELOG.md`.
2. Synchronize the Claude Code adapter from the core worker definitions.
3. Run all validation commands.
4. Build release archives:

```bash
python scripts/build_release.py
```

5. Commit on a release branch, review the generated worker catalog and protocol changes, merge, tag the release, and publish the archives from `dist/`.

## Marketplace

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
```
