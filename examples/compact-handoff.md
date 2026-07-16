# Compact Handoff Example

```text
S|PARTIAL|Scaffold implemented; error semantics reserved
C|C1|OutputActivationRequest.java|Created record
C|C2|OutputActivationResource.java|Added POST and service delegation
F|F1|ExistingResource#start|Project uses constructor injection
D|D1|F1|New resource follows constructor injection convention
H|H1|contract|OutputActivationResource#activate|Choose 409 or idempotent 200|Error mapper and two tests
V|V1|NR|compile|Builder has no shell tool
N|ORCHESTRATOR|Resolve H1, inspect C1-C2, compile
```
