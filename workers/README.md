# Generic Worker Library

Each worker has:

- `specification.md`: responsibilities, boundaries, inputs, outputs;
- `prompt.md`: compact platform-independent instructions suitable for adaptation.

Adapters should preserve the boundaries, but may translate tool names, model selectors, continuation mechanisms, and invocation syntax.
