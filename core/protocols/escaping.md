# DCP/2 and CHP/2 Escaping

Protocols use `|` as a field separator.

Within a field encode:

```text
\\  -> backslash
\|  -> literal pipe
\n  -> newline
\r  -> carriage return
```

Unknown escape sequences are invalid. Records are UTF-8 and one physical line each. Empty trailing fields are preserved. Parsers must reject unsupported versions, duplicate evidence/change/handoff IDs, invalid references, and malformed status records.
