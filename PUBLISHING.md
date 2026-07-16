# Publishing

## Pre-release checks

Run the platform-independent validation suite:

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
```

When Claude Code is installed, also validate the adapter and marketplace:

```bash
claude plugin validate ./adapters/claude-code/plugins/dreamteam --strict
claude plugin validate .
```

## Release process

1. Update the version in `adapters/claude-code/plugins/dreamteam/.claude-plugin/plugin.json`.
2. Add the release notes to `CHANGELOG.md`.
3. Run the validation commands above.
4. Build the repository and plugin archives:

```bash
python scripts/build_release.py
```

5. Commit the release changes, create a matching Git tag, and publish the generated archives from `dist/` as release assets.

## Claude Code marketplace

Users can add this repository as a marketplace and install the adapter with:

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
```

After publishing updates, increment the plugin version so clients can distinguish releases reliably.
