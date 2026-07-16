# Escalation Policy

Escalation means returning decision ownership, not silently choosing a stronger model.

Escalate when:

- a reserved decision is required;
- evidence conflicts;
- scope must expand;
- a public contract may change;
- security, transaction, concurrency, idempotency, or distributed consistency is involved;
- two bounded attempts fail on the same cause;
- required information is unavailable;
- verification contradicts the assumed behavior.

An escalation record includes location, evidence, decision required, blocked work, and recommended next owner.
