# Architecture

DreamTeam uses a hub-and-spoke model.

- The orchestrator interprets requirements, owns decisions, reviews output, and verifies completion.
- Workers are specialized, bounded, and disposable or resumable depending on the runtime.
- Workers do not call each other.
- The compact handoff is the only required inter-worker interface.
- Adapters translate runtime-specific models, tools, permissions, files, and invocation syntax.

## Stable core vs adapters

Core stability allows a routing policy or worker prompt to be evaluated across platforms. Adapter code may change frequently as each agent runtime evolves.

## Extension points

- new worker role;
- new cost/quality profile;
- model mapping;
- alternative handoff serialization;
- persistent ledger;
- evaluation harness;
- platform adapter;
- optional deterministic validation or log filtering.
