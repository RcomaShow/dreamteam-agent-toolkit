# Codex Adapter — Planned

This directory will map DreamTeam core concepts to Codex capabilities.

A conforming adapter must define:

- orchestrator entry point;
- worker registration and invocation;
- tool restrictions;
- model/cost-tier mapping;
- continuation or resume behavior;
- DCP/1 input rendering;
- CHP/1 output rendering;
- quality-gate verification;
- install, update, and security model.

Do not copy Claude Code-specific fields into this adapter. Reuse `core/` and `workers/` semantics.
