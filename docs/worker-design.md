# Worker Design 0.4

Create a worker only when at least two of these differ: tool set, risk, stop condition, output shape, model tier, verification, or decision authority.

DreamTeam 0.4 contains discovery, execution, coordination, and verification families: thirteen Haiku roles and three Sonnet roles. Each role has a compact constitutional projection, closed scope, maximum turns, least-privilege tools, no Agent tool, and bound CHP/2 output. `execution-sonnet-lead` supports explicit Opus → Sonnet work without silently inserting Haiku.

More available roles do not imply more workers per task. The router selects one concrete primary role, at most one Frontier support role, and an independent reviewer only for writing paths.
