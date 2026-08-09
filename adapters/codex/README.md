# DreamTeam for Codex — 0.5

DreamTeam 0.5 adds a usable Codex-native adapter without pretending that Claude Code hooks or model names are portable primitives.

The adapter has two surfaces:

- `AGENTS.md` — project-scoped DreamTeam operating instructions using Codex's native repository guidance mechanism;
- `skills/dreamteam-run/SKILL.md` — a user-installable Codex skill for explicit DreamTeam runs.

## Project install

From the DreamTeam repository:

```bash
python scripts/install_codex_adapter.py --scope project --project-root /path/to/project
```

The installer refuses to overwrite an existing `AGENTS.md`. Review and merge `adapters/codex/AGENTS.md` manually when the project already has instructions. `--force` is deliberately explicit.

Preview without writing:

```bash
python scripts/install_codex_adapter.py --scope project --project-root /path/to/project --dry-run
```

## User skill install

```bash
python scripts/install_codex_adapter.py --scope user
```

By default this installs to `~/.codex/skills/dreamteam-run/SKILL.md`. Use `--codex-home` for a different Codex home.

## Runtime behavior

Codex remains the root owner. If the active Codex runtime exposes child/subagent execution, DreamTeam may delegate bounded M0/L1 work with DCP/2 and receive compact CHP/2 deltas. If delegation is unavailable, the adapter remains `MAIN_DIRECT` while still applying minimal-capsule, reread, verification, and measurement discipline.

0.5 does **not** hardcode a GPT model hierarchy. Model availability and names are provider/runtime facts; the platform-independent core reasons in terms of root/main versus bounded worker capability. A future provider executor can map those capability tiers to pinned model snapshots and real usage data.

## Measurement contract

The Codex adapter keeps these dimensions separate when the runtime exposes them:

- API-equivalent cost;
- total provider tokens;
- root/main-model tokens;
- normalized payload bytes;
- handoff overhead;
- reread bytes;
- retries, escalations, failures, and latency;
- quality-oracle result.

Unavailable metrics are `NR`, never silently estimated. Savings claims still require a paired direct baseline with the same repository commit, task, tools, timeout, and quality oracle.
