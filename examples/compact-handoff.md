# Compact CHP/2 Handoff

```text
CHP|2
RUN|dt-42
TASK|map-status
CONTRACT|sha256:example
S|PARTIAL|mapping implemented; unknown status semantics reserved
E|E1|FACT|StatusMapper#map|ACTIVE maps to ENABLED
C|C1|StatusMapper#map|implemented approved mappings
H|H1|business|StatusMapper#map|define NEW status mapping|one branch and test
V|V1|PASS|StatusMapperTest|4 approved cases passed
N|ORCHESTRATOR|decide H1 and review bounded logic
```
