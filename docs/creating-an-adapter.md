# Creating an Adapter

An adapter maps DreamTeam core semantics to a platform.

## Required mapping

| DreamTeam concept | Adapter responsibility |
|---|---|
| Orchestrator | Main agent/session entry point |
| Worker | Subagent, subprocess, API call, or task |
| Cost tier | Platform model selector |
| Tool boundary | Runtime permissions/tool allowlist |
| DCP/1 | Worker prompt or structured input |
| CHP/1 | Parsed worker output |
| TLP/1 | Session or persistent state |
| Quality gate | Runtime command/check integration |
| Resume | Session continuation or rehydration |

## Conformance

- Core documents remain unchanged.
- Worker cannot silently exceed scope.
- Facts remain source-linked.
- Reserved decisions return to orchestrator.
- Verification states are explicit.
- Adapter documents security and update behavior.
