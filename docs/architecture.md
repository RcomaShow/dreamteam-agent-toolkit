# Architecture 0.2

DreamTeam uses a hub-and-spoke model with one final orchestrator. Workers never call each other.

## Stable layers

- constitution: common authority, evidence, scope, and ownership principles;
- routing: code criticality and execution routes;
- protocols: closed delegation and compact handoff;
- worker charters: narrow roles and tool boundaries;
- adapters: runtime-specific model, tools, files, and invocation syntax.

## Ownership

Every task declares read owner, edit owner, and review owner. Every code region has one active edit owner. M0/L1 are worker-eligible; L2 uses hybrid ownership; C3 remains orchestrator-owned.
