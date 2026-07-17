#!/usr/bin/env python3
"""Parse and validate DreamTeam DCP/2 and CHP/2 records, including source anchors."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dreamteam.anchors import SourceAnchor, verify_anchor_file


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class Record:
    kind: str
    fields: tuple[str, ...]
    line: int


def split_record(line: str) -> list[str]:
    fields: list[str] = []
    current: list[str] = []
    escape = False
    for char in line.rstrip("\n"):
        if escape:
            decoded = {"n": "\n", "r": "\r", "|": "|", "\\": "\\"}.get(char)
            if decoded is None:
                raise ProtocolError(f"unsupported escape: \\{char}")
            current.append(decoded)
            escape = False
        elif char == "\\":
            escape = True
        elif char == "|":
            fields.append("".join(current))
            current = []
        else:
            current.append(char)
    if escape:
        raise ProtocolError("trailing escape")
    fields.append("".join(current))
    return fields


def escape_field(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", "\\r").replace("\n", "\\n")


def parse(text: str) -> list[Record]:
    records: list[Record] = []
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        fields = split_record(raw)
        records.append(Record(fields[0], tuple(fields[1:]), number))
    if not records:
        raise ProtocolError("empty protocol")
    return records


def normalized(text: str) -> str:
    return "\n".join("|".join([record.kind, *(escape_field(field) for field in record.fields)]) for record in parse(text)) + "\n"


def contract_hash(text: str) -> str:
    return "sha256:" + sha256(normalized(text).encode("utf-8")).hexdigest()


def validate_dcp(records: list[Record]) -> list[str]:
    errors: list[str] = []
    if records[0].kind != "DCP" or records[0].fields != ("2",):
        errors.append("first record must be DCP|2")
    singletons = {"DCP", "RUN", "TASK", "CONST", "PROFILE", "G", "B", "O"}
    allowed = singletons | {"S+", "S-", "E+", "E-", "I", "K", "T", "R", "V"}
    seen: dict[str, int] = {}
    for record in records:
        if record.kind not in allowed:
            errors.append(f"line {record.line}: invalid DCP record {record.kind}")
        if record.kind in singletons:
            seen[record.kind] = seen.get(record.kind, 0) + 1
            if seen[record.kind] > 1:
                errors.append(f"line {record.line}: duplicate {record.kind}")
    for required in ("RUN", "TASK", "CONST", "PROFILE", "G", "T", "B", "O"):
        if not any(record.kind == required for record in records):
            errors.append(f"missing {required}")
    return errors


def validate_chp(
    records: list[Record],
    *,
    require_anchors: bool = False,
    repo_root: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if records[0].kind != "CHP" or records[0].fields != ("2",):
        errors.append("first record must be CHP|2")
    allowed = {"CHP", "RUN", "TASK", "CONTRACT", "S", "E", "C", "H", "V", "W", "N"}
    ids: set[str] = set()
    evidence_ids: set[str] = set()
    deductions: list[tuple[int, str]] = []
    handoffs = 0
    status: str | None = None
    for record in records:
        if record.kind not in allowed:
            errors.append(f"line {record.line}: invalid CHP record {record.kind}")
        if record.kind in {"E", "C", "H", "V", "W"}:
            if not record.fields:
                errors.append(f"line {record.line}: missing record id")
                continue
            record_id = record.fields[0]
            if record_id in ids:
                errors.append(f"line {record.line}: duplicate id {record_id}")
            ids.add(record_id)
        if record.kind == "E":
            if len(record.fields) != 4:
                errors.append(f"line {record.line}: E requires 4 fields")
            else:
                evidence_ids.add(record.fields[0])
                evidence_type = record.fields[1]
                source = record.fields[2]
                if evidence_type == "DEDUCTION":
                    deductions.append((record.line, source))
                elif evidence_type not in {"FACT", "ASSUMPTION", "UNKNOWN"}:
                    errors.append(f"line {record.line}: invalid evidence type")
                if evidence_type == "FACT" and require_anchors:
                    errors.extend(_validate_anchor(source, record.line, repo_root))
        if record.kind == "H":
            handoffs += 1
        if record.kind == "S":
            if not record.fields or record.fields[0] not in {"DONE", "PARTIAL", "BLOCKED", "FAILED"}:
                errors.append(f"line {record.line}: invalid status")
            else:
                status = record.fields[0]
        if record.kind == "V" and len(record.fields) >= 2 and record.fields[1] not in {"PASS", "FAIL", "NR"}:
            errors.append(f"line {record.line}: invalid verification status")
    for line, support in deductions:
        for reference in filter(None, support.split(",")):
            if reference.strip() not in evidence_ids:
                errors.append(f"line {line}: unknown supporting evidence {reference.strip()}")
    if status == "DONE" and handoffs:
        errors.append("DONE cannot contain unresolved H records")
    for required in ("RUN", "TASK", "CONTRACT", "S", "N"):
        if not any(record.kind == required for record in records):
            errors.append(f"missing {required}")
    return errors


def _validate_anchor(source: str, line: int, repo_root: Path | None) -> list[str]:
    try:
        anchor = SourceAnchor.decode(source)
    except ValueError as exc:
        return [f"line {line}: FACT requires valid source anchor: {exc}"]
    if repo_root is None:
        return [f"line {line}: --repo-root is required when anchors are enforced"]
    if not verify_anchor_file(anchor, repo_root):
        return [f"line {line}: source anchor is stale or invalid: {source}"]
    return []


def validate(
    text: str,
    *,
    require_anchors: bool = False,
    repo_root: Path | None = None,
) -> list[str]:
    records = parse(text)
    if records[0].kind == "DCP":
        return validate_dcp(records)
    if records[0].kind == "CHP":
        return validate_chp(records, require_anchors=require_anchors, repo_root=repo_root)
    return ["unknown protocol header"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--hash", action="store_true")
    parser.add_argument("--require-anchors", action="store_true")
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args()
    text = args.file.read_text(encoding="utf-8")
    errors = validate(text, require_anchors=args.require_anchors, repo_root=args.repo_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("valid")
    if args.hash and text.lstrip().startswith("DCP|2"):
        print(contract_hash(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
