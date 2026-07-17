"""Parse and validate DreamTeam DCP/2 and CHP/2 records."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Iterable

from .anchors import SourceAnchor, verify_anchor_file


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class Record:
    kind: str
    fields: tuple[str, ...]
    line: int


@dataclass(frozen=True)
class ContractBudget:
    files: int
    deep_reads: int
    turns: int
    records: int
    retries: int


@dataclass(frozen=True)
class ProtocolIdentity:
    run_id: str
    task_id: str
    contract_hash: str | None = None


_DCP_SINGLETONS = {"DCP", "RUN", "TASK", "CONST", "PROFILE", "G", "B", "O"}
_DCP_ALLOWED = _DCP_SINGLETONS | {"S+", "S-", "E+", "E-", "I", "K", "T", "R", "V"}
_CHP_SINGLETONS = {"CHP", "RUN", "TASK", "CONTRACT", "S", "N"}
_CHP_ALLOWED = _CHP_SINGLETONS | {"E", "C", "H", "V", "W"}
_VALID_PROFILES = {"economy", "balanced", "offload", "quality"}
_BUDGET_KEYS = ("files", "deep_reads", "turns", "records", "retries")
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")
_WORKER_OWNER_RE = re.compile(r"^WORKER:[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


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
        if not fields[0]:
            raise ProtocolError(f"line {number}: empty record kind")
        records.append(Record(fields[0], tuple(fields[1:]), number))
    if not records:
        raise ProtocolError("empty protocol")
    return records


def normalized(text: str) -> str:
    return "\n".join(
        "|".join([record.kind, *(escape_field(field) for field in record.fields)])
        for record in parse(text)
    ) + "\n"


def contract_hash(text: str) -> str:
    return "sha256:" + sha256(normalized(text).encode("utf-8")).hexdigest()


def parse_budget(value: str) -> ContractBudget:
    items: dict[str, int] = {}
    for chunk in value.split(";"):
        if "=" not in chunk:
            raise ProtocolError("budget entries must use key=value")
        key, raw = chunk.split("=", 1)
        if key not in _BUDGET_KEYS:
            raise ProtocolError(f"unsupported budget key: {key}")
        if key in items:
            raise ProtocolError(f"duplicate budget key: {key}")
        try:
            parsed = int(raw)
        except ValueError as exc:
            raise ProtocolError(f"budget {key} must be an integer") from exc
        if parsed < 0:
            raise ProtocolError(f"budget {key} must be non-negative")
        items[key] = parsed
    missing = set(_BUDGET_KEYS) - set(items)
    if missing:
        raise ProtocolError(f"missing budget keys: {sorted(missing)}")
    return ContractBudget(**items)


def _singletons(records: Iterable[Record], kinds: set[str]) -> tuple[dict[str, Record], list[str]]:
    found: dict[str, Record] = {}
    errors: list[str] = []
    for record in records:
        if record.kind not in kinds:
            continue
        if record.kind in found:
            errors.append(f"line {record.line}: duplicate {record.kind}")
        else:
            found[record.kind] = record
    return found, errors


def _field_count(record: Record, expected: int, errors: list[str]) -> None:
    if len(record.fields) != expected:
        errors.append(f"line {record.line}: {record.kind} requires {expected} fields")


def validate_dcp(records: list[Record]) -> list[str]:
    errors: list[str] = []
    if records[0].kind != "DCP" or records[0].fields != ("2",):
        errors.append("first record must be DCP|2")
    singletons, duplicate_errors = _singletons(records, _DCP_SINGLETONS)
    errors.extend(duplicate_errors)
    for record in records:
        if record.kind not in _DCP_ALLOWED:
            errors.append(f"line {record.line}: invalid DCP record {record.kind}")
            continue
        if record.kind == "DCP":
            _field_count(record, 1, errors)
        else:
            _field_count(record, 1, errors)
        if record.fields and not record.fields[0]:
            errors.append(f"line {record.line}: {record.kind} may not be empty")
    for required in ("RUN", "TASK", "CONST", "PROFILE", "G", "T", "B", "O"):
        if required not in singletons and not any(record.kind == required for record in records):
            errors.append(f"missing {required}")
    const = singletons.get("CONST")
    if const and const.fields != ("DT-C1",):
        errors.append(f"line {const.line}: CONST must be DT-C1")
    profile = singletons.get("PROFILE")
    if profile and (len(profile.fields) != 1 or profile.fields[0] not in _VALID_PROFILES):
        errors.append(f"line {profile.line}: invalid PROFILE")
    output = singletons.get("O")
    if output and output.fields != ("CHP/2",):
        errors.append(f"line {output.line}: O must be CHP/2")
    budget = singletons.get("B")
    if budget and len(budget.fields) == 1:
        try:
            parsed = parse_budget(budget.fields[0])
            if parsed.records < len(records):
                errors.append(
                    f"line {budget.line}: record count {len(records)} exceeds budget {parsed.records}"
                )
        except ProtocolError as exc:
            errors.append(f"line {budget.line}: {exc}")
    return errors


def validate_chp(
    records: list[Record],
    *,
    require_anchors: bool = False,
    require_contract_hash: bool = False,
    repo_root: Path | None = None,
    expected_run_id: str | None = None,
    expected_task_id: str | None = None,
    expected_contract_hash: str | None = None,
    author_agent_id: str | None = None,
    reviewer_agent_id: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if records[0].kind != "CHP" or records[0].fields != ("2",):
        errors.append("first record must be CHP|2")
    singletons, duplicate_errors = _singletons(records, _CHP_SINGLETONS)
    errors.extend(duplicate_errors)
    ids: set[str] = set()
    evidence_ids: set[str] = set()
    deductions: list[tuple[int, str]] = []
    handoffs = 0
    status: str | None = None

    for record in records:
        if record.kind not in _CHP_ALLOWED:
            errors.append(f"line {record.line}: invalid CHP record {record.kind}")
            continue
        if any(not field for field in record.fields):
            errors.append(f"line {record.line}: {record.kind} fields may not be empty")
        if record.kind in {"CHP", "RUN", "TASK", "CONTRACT"}:
            _field_count(record, 1, errors)
        if record.kind == "N":
            _field_count(record, 2, errors)
        if record.kind == "S":
            _field_count(record, 2, errors)
        if record.kind in {"E", "C", "H", "V", "W"}:
            if not record.fields or not record.fields[0]:
                errors.append(f"line {record.line}: missing record id")
                continue
            record_id = record.fields[0]
            if not _ID_RE.fullmatch(record_id):
                errors.append(f"line {record.line}: invalid record id {record_id}")
            if record_id in ids:
                errors.append(f"line {record.line}: duplicate id {record_id}")
            ids.add(record_id)
        if record.kind == "E":
            _field_count(record, 4, errors)
            if len(record.fields) == 4:
                evidence_ids.add(record.fields[0])
                evidence_type = record.fields[1]
                source = record.fields[2]
                if evidence_type == "DEDUCTION":
                    deductions.append((record.line, source))
                elif evidence_type not in {"FACT", "ASSUMPTION", "UNKNOWN"}:
                    errors.append(f"line {record.line}: invalid evidence type")
                if evidence_type == "FACT" and require_anchors:
                    errors.extend(_validate_anchor(source, record.line, repo_root))
        if record.kind == "C":
            _field_count(record, 3, errors)
        if record.kind == "H":
            handoffs += 1
            _field_count(record, 5, errors)
        if record.kind == "S" and record.fields:
            if record.fields[0] not in {"DONE", "PARTIAL", "BLOCKED", "FAILED"}:
                errors.append(f"line {record.line}: invalid status")
            else:
                status = record.fields[0]
        if record.kind == "V":
            _field_count(record, 4, errors)
            if len(record.fields) >= 2 and record.fields[1] not in {"PASS", "FAIL", "NR"}:
                errors.append(f"line {record.line}: invalid verification status")
        if record.kind == "W":
            _field_count(record, 3, errors)
        if record.kind == "N" and record.fields:
            owner = record.fields[0]
            if owner != "ORCHESTRATOR" and not _WORKER_OWNER_RE.fullmatch(owner):
                errors.append(f"line {record.line}: invalid next owner")

    for line, support in deductions:
        references = [reference.strip() for reference in support.split(",") if reference.strip()]
        if not references:
            errors.append(f"line {line}: DEDUCTION requires supporting evidence ids")
        for reference in references:
            if reference not in evidence_ids:
                errors.append(f"line {line}: unknown supporting evidence {reference}")

    if status == "DONE" and handoffs:
        errors.append("DONE cannot contain unresolved H records")
    for required in ("RUN", "TASK", "CONTRACT", "S", "N"):
        if required not in singletons:
            errors.append(f"missing {required}")

    run = singletons.get("RUN")
    task = singletons.get("TASK")
    contract = singletons.get("CONTRACT")
    if expected_run_id is not None and run and run.fields != (expected_run_id,):
        errors.append("RUN does not match dispatched contract")
    if expected_task_id is not None and task and task.fields != (expected_task_id,):
        errors.append("TASK does not match dispatched contract")
    if contract:
        value = contract.fields[0] if len(contract.fields) == 1 else ""
        if require_contract_hash and value == "UNAVAILABLE":
            errors.append("CONTRACT may not be UNAVAILABLE in strict mode")
        if value != "UNAVAILABLE" and not _HASH_RE.fullmatch(value):
            errors.append(f"line {contract.line}: invalid CONTRACT hash")
        if expected_contract_hash is not None and value != expected_contract_hash:
            errors.append("CONTRACT hash does not match dispatched DCP")
    if author_agent_id and reviewer_agent_id and author_agent_id == reviewer_agent_id:
        errors.append("writer and reviewer must be different agents")
    return errors


def _validate_anchor(source: str, line: int, repo_root: Path | None) -> list[str]:
    try:
        anchor = SourceAnchor.decode(source)
    except ValueError as exc:
        return [f"line {line}: FACT requires valid source anchor: {exc}"]
    if repo_root is None:
        return [f"line {line}: repo_root is required when anchors are enforced"]
    if not verify_anchor_file(anchor, repo_root):
        return [f"line {line}: source anchor is stale or invalid: {source}"]
    return []


def protocol_identity(text: str) -> ProtocolIdentity:
    records = parse(text)
    header = records[0].kind
    if header not in {"DCP", "CHP"}:
        raise ProtocolError("unknown protocol header")
    relevant = {"RUN", "TASK"}
    if header == "CHP":
        relevant.add("CONTRACT")
    singletons, errors = _singletons(records, relevant)
    if errors:
        raise ProtocolError("; ".join(errors))
    missing = [kind for kind in ("RUN", "TASK") if kind not in singletons]
    if header == "CHP" and "CONTRACT" not in singletons:
        missing.append("CONTRACT")
    if missing:
        raise ProtocolError(f"missing identity records: {missing}")
    for kind, record in singletons.items():
        if len(record.fields) != 1 or not record.fields[0]:
            raise ProtocolError(f"line {record.line}: invalid {kind} identity record")
    contract = singletons.get("CONTRACT")
    return ProtocolIdentity(
        run_id=singletons["RUN"].fields[0],
        task_id=singletons["TASK"].fields[0],
        contract_hash=None if contract is None else contract.fields[0],
    )


def validate(
    text: str,
    *,
    require_anchors: bool = False,
    require_contract_hash: bool = False,
    repo_root: Path | None = None,
    expected_run_id: str | None = None,
    expected_task_id: str | None = None,
    expected_contract_hash: str | None = None,
    author_agent_id: str | None = None,
    reviewer_agent_id: str | None = None,
) -> list[str]:
    records = parse(text)
    if records[0].kind == "DCP":
        return validate_dcp(records)
    if records[0].kind == "CHP":
        return validate_chp(
            records,
            require_anchors=require_anchors,
            require_contract_hash=require_contract_hash,
            repo_root=repo_root,
            expected_run_id=expected_run_id,
            expected_task_id=expected_task_id,
            expected_contract_hash=expected_contract_hash,
            author_agent_id=author_agent_id,
            reviewer_agent_id=reviewer_agent_id,
        )
    return ["unknown protocol header"]
