#!/usr/bin/env python3
"""Parse and validate DreamTeam DCP/2 and CHP/2 records."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable
import argparse

class ProtocolError(ValueError):
    pass

@dataclass(frozen=True)
class Record:
    kind: str
    fields: tuple[str, ...]
    line: int


def split_record(line: str) -> list[str]:
    fields, current = [], []
    escape = False
    for char in line.rstrip("\n"):
        if escape:
            current.append({"n":"\n", "r":"\r", "|":"|", "\\":"\\"}.get(char, "\0"))
            if current[-1] == "\0":
                raise ProtocolError(f"unsupported escape: \\{char}")
            escape = False
        elif char == "\\":
            escape = True
        elif char == "|":
            fields.append("".join(current)); current = []
        else:
            current.append(char)
    if escape:
        raise ProtocolError("trailing escape")
    fields.append("".join(current))
    return fields


def escape_field(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", "\\r").replace("\n", "\\n")


def parse(text: str) -> list[Record]:
    records = []
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        fields = split_record(raw)
        records.append(Record(fields[0], tuple(fields[1:]), number))
    if not records:
        raise ProtocolError("empty protocol")
    return records


def normalized(text: str) -> str:
    return "\n".join("|".join([r.kind, *(escape_field(f) for f in r.fields)]) for r in parse(text)) + "\n"


def contract_hash(text: str) -> str:
    return "sha256:" + sha256(normalized(text).encode()).hexdigest()


def validate_dcp(records: list[Record]) -> list[str]:
    errors = []
    if records[0].kind != "DCP" or records[0].fields != ("2",):
        errors.append("first record must be DCP|2")
    singletons = {"DCP","RUN","TASK","CONST","PROFILE","G","B","O"}
    seen = {}
    allowed = singletons | {"S+","S-","E+","E-","I","K","T","R","V"}
    for r in records:
        if r.kind not in allowed: errors.append(f"line {r.line}: invalid DCP record {r.kind}")
        if r.kind in singletons:
            seen[r.kind] = seen.get(r.kind, 0) + 1
            if seen[r.kind] > 1: errors.append(f"line {r.line}: duplicate {r.kind}")
    for required in ("RUN","TASK","CONST","PROFILE","G","T","B","O"):
        if not any(r.kind == required for r in records): errors.append(f"missing {required}")
    return errors


def validate_chp(records: list[Record]) -> list[str]:
    errors = []
    if records[0].kind != "CHP" or records[0].fields != ("2",):
        errors.append("first record must be CHP|2")
    allowed = {"CHP","RUN","TASK","CONTRACT","S","E","C","H","V","W","N"}
    ids, evidence_ids, deductions, handoffs = set(), set(), [], 0
    status = None
    for r in records:
        if r.kind not in allowed: errors.append(f"line {r.line}: invalid CHP record {r.kind}")
        if r.kind in {"E","C","H","V","W"}:
            if not r.fields: errors.append(f"line {r.line}: missing record id"); continue
            rid = r.fields[0]
            if rid in ids: errors.append(f"line {r.line}: duplicate id {rid}")
            ids.add(rid)
        if r.kind == "E":
            if len(r.fields) != 4: errors.append(f"line {r.line}: E requires 4 fields")
            else:
                evidence_ids.add(r.fields[0])
                if r.fields[1] == "DEDUCTION": deductions.append((r.line, r.fields[2]))
                elif r.fields[1] not in {"FACT","ASSUMPTION","UNKNOWN"}: errors.append(f"line {r.line}: invalid evidence type")
        if r.kind == "H": handoffs += 1
        if r.kind == "S":
            if len(r.fields) < 1 or r.fields[0] not in {"DONE","PARTIAL","BLOCKED","FAILED"}: errors.append(f"line {r.line}: invalid status")
            else: status = r.fields[0]
        if r.kind == "V" and len(r.fields) >= 2 and r.fields[1] not in {"PASS","FAIL","NR"}: errors.append(f"line {r.line}: invalid verification status")
    for line, support in deductions:
        for ref in filter(None, support.split(',')):
            if ref.strip() not in evidence_ids: errors.append(f"line {line}: unknown supporting evidence {ref.strip()}")
    if status == "DONE" and handoffs: errors.append("DONE cannot contain unresolved H records")
    for required in ("RUN","TASK","CONTRACT","S","N"):
        if not any(r.kind == required for r in records): errors.append(f"missing {required}")
    return errors


def validate(text: str) -> list[str]:
    records = parse(text)
    if records[0].kind == "DCP": return validate_dcp(records)
    if records[0].kind == "CHP": return validate_chp(records)
    return ["unknown protocol header"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--hash", action="store_true")
    args = parser.parse_args()
    text = args.file.read_text(encoding="utf-8")
    errors = validate(text)
    if errors:
        for e in errors: print(f"ERROR: {e}")
        return 1
    print("valid")
    if args.hash and text.lstrip().startswith("DCP|2"): print(contract_hash(text))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
