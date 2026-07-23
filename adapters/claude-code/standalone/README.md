# DreamTeam standalone Claude Code adapter

This adapter projects the canonical DreamTeam Claude Code package into standard
user-level or project-level Claude directories. It is generated at install time
from `../plugins/dreamteam`, so the plugin package remains the single source of
adapter runtime, skills, agents, and hooks.

## Project installation

Run from the repository root:

```bash
python scripts/install_claude_standalone.py install \
  --scope project \
  --project-root .
```

This installs:

```text
.claude/
├── agents/dreamteam-*.md
├── skills/dreamteam-*/
└── dreamteam/
    ├── .claude-plugin/
    ├── agents/
    ├── hooks/
    ├── lib/
    ├── scripts/
    ├── skills/
    ├── adapter.json
    └── install-state.json
```

The standalone skill names are:

```text
/dreamteam-init
/dreamteam-doctor
/dreamteam-status
/dreamteam-run
/dreamteam-review
/dreamteam-measure
```

## User installation

```bash
python scripts/install_claude_standalone.py install --scope user
```

User scope writes under `~/.claude`. Project scope writes under
`<project>/.claude`.

## Optional hooks

Hook installation is explicit:

```bash
python scripts/install_claude_standalone.py install \
  --scope project \
  --project-root . \
  --enable-hooks
```

When requested, the installer merges DreamTeam hook entries into the existing
`settings.json` without replacing unrelated settings or hook events. Expected
hook entries and entries actually added by the installer are tracked separately,
so pre-existing identical hooks remain user-owned. The current Python executable
is written into generated commands; `--python-command` can select another stable
executable.

## Inspect and remove

```bash
python scripts/install_claude_standalone.py doctor \
  --scope project \
  --project-root .

python scripts/install_claude_standalone.py uninstall \
  --scope project \
  --project-root .
```

The install state records every generated file hash and every hook entry managed
by the adapter. Upgrade and uninstall stop when tracked files or managed hooks
have changed. Existing destination files are never adopted implicitly. `--force`
is available for an intentional replacement or removal, and `--dry-run` reports
the planned operation without writing files.
