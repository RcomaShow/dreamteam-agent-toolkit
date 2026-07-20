# DCP/2 and CHP/2 Escaping

Protocols use `|` as a field separator. Within a field encode:

```text
\\  -> backslash
\|  -> literal pipe
\n  -> newline
\r  -> carriage return
```

Unknown escape sequences are invalid. Records are UTF-8 and one physical line each. Empty trailing fields are preserved. Parsers reject unsupported versions, duplicate singleton or item IDs, invalid references, invalid budgets, malformed status records, and mismatched contract bindings.
