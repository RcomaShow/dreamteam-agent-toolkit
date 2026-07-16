# Worker Design

Add a worker only when all are true:

1. the task recurs;
2. it has a distinct tool and risk boundary;
3. a narrow contract materially improves reliability;
4. routing can distinguish it from existing workers;
5. its output can be verified.

A worker should not be created solely for a technology name. Prefer capability roles such as `structure-builder` over `java-dto-agent`.

Every worker requires:

- purpose;
- trigger;
- required inputs;
- tools;
- hard boundaries;
- budget;
- handoff schema;
- known failure modes;
- evaluation fixtures.
