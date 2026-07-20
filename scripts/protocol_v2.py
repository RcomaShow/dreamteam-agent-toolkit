#!/usr/bin/env python3
"""CLI wrapper for DreamTeam DCP/2 and CHP/2 validation."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dreamteam.ledger import RunLedger
from dreamteam.protocol import contract_hash, escape_field, protocol_identity, split_record, validate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--hash", action="store_true")
    parser.add_argument("--require-anchors", action="store_true")
    parser.add_argument("--require-contract-hash", action="store_true")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--expected-run-id")
    parser.add_argument("--expected-task-id")
    parser.add_argument("--expected-contract-hash")
    parser.add_argument("--author-agent-id")
    parser.add_argument("--reviewer-agent-id")
    parser.add_argument("--bind", action="store_true", help="register a valid DCP/2 in the SQLite ledger")
    parser.add_argument("--ledger", type=Path, help="ledger path; defaults to CLAUDE_PLUGIN_DATA/ledger.sqlite")
    args = parser.parse_args()
    text = args.file.read_text(encoding="utf-8")
    errors = validate(
        text,
        require_anchors=args.require_anchors,
        require_contract_hash=args.require_contract_hash,
        repo_root=args.repo_root,
        expected_run_id=args.expected_run_id,
        expected_task_id=args.expected_task_id,
        expected_contract_hash=args.expected_contract_hash,
        author_agent_id=args.author_agent_id,
        reviewer_agent_id=args.reviewer_agent_id,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("valid")
    is_dcp = text.lstrip().startswith("DCP|2")
    digest = contract_hash(text) if is_dcp else None
    if args.hash and digest is not None:
        print(digest)
    if args.bind:
        if not is_dcp or digest is None:
            raise SystemExit("--bind requires a valid DCP/2 contract")
        identity = protocol_identity(text)
        if args.expected_run_id is not None and identity.run_id != args.expected_run_id:
            raise SystemExit("DCP RUN does not match --expected-run-id")
        if args.expected_task_id is not None and identity.task_id != args.expected_task_id:
            raise SystemExit("DCP TASK does not match --expected-task-id")
        ledger_path = args.ledger
        if ledger_path is None:
            data_dir = Path(os.environ.get("CLAUDE_PLUGIN_DATA", ".dreamteam"))
            ledger_path = data_dir / "ledger.sqlite"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger = RunLedger(ledger_path)
        try:
            if not ledger.bind_contract(
                identity.run_id,
                identity.task_id,
                digest,
                author_agent_id=args.author_agent_id,
                reviewer_agent_id=args.reviewer_agent_id,
            ):
                raise SystemExit("DCP binding conflicts with an existing immutable binding")
        finally:
            ledger.close()
        print(f"bound {identity.run_id}/{identity.task_id} {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

__all__ = ["contract_hash", "escape_field", "split_record", "validate"]
