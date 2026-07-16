# Boilerplate Generation

After deciding the API contract, delegate:

```text
G|Create activation request, response, mapper, and resource skeleton
S+|src/main/java/com/acme/output/api;src/main/java/com/acme/output/mapper
S-|pom.xml;application.properties
I|ExistingImportResource.java;ExistingImportMapper.java
K|POST /output-activations;request fields processId requestedBy type;response fields processId status
T|Create structures and simple service delegation
R|Validation;errors;Kafka;idempotency;transactions
V|NR
B|files=6;deep_reads=3;turns=8;records=25;retries=1
O|CHP/1
```

The orchestrator then resolves the reserved behavior, reviews the diff, and compiles.
