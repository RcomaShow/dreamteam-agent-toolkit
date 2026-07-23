from __future__ import annotations

import json
from pathlib import Path


def write_fixture_plugin(root: Path) -> None:
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin/plugin.json").write_text(
        json.dumps({"name": "dreamteam", "version": "0.4.5"}),
        encoding="utf-8",
    )
    (root / "agents").mkdir()
    (root / "agents/discovery-symbol-locator.md").write_text(
        "---\nname: discovery-symbol-locator\n---\n\nAgent.\n",
        encoding="utf-8",
    )
    (root / "lib/dreamteam").mkdir(parents=True)
    (root / "lib/dreamteam/runtime.py").write_text(
        'VALUE = 1\nNEXT = "/dreamteam:doctor"\n',
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts/hook.py").write_text("print('hook')\n", encoding="utf-8")
    (root / "skills/init/references").mkdir(parents=True)
    (root / "skills/init/SKILL.md").write_text(
        "---\n"
        "name: init\n"
        "description: Initialize DreamTeam.\n"
        "---\n\n"
        "Run `python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/hook.py\"`.\n"
        "Next: /dreamteam:doctor\n",
        encoding="utf-8",
    )
    (root / "skills/init/references/note.md").write_text(
        "Use /dreamteam:run.\n", encoding="utf-8"
    )
    (root / "skills/doctor").mkdir(parents=True)
    (root / "skills/doctor/SKILL.md").write_text(
        "---\n"
        "name: doctor\n"
        "description: Inspect DreamTeam.\n"
        "---\n\n"
        "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/hook.py\" doctor "
        "--plugin-root \"${CLAUDE_PLUGIN_ROOT}\" --hooks-available\n",
        encoding="utf-8",
    )
    (root / "hooks").mkdir()
    (root / "hooks/hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Read",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": (
                                        "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/"
                                        "hook.py\" pre"
                                    ),
                                }
                            ],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    (root / "README.md").write_text("DreamTeam fixture\n", encoding="utf-8")
