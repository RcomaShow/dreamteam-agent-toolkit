"""Metadata-only SQLite ledger with exact spans and durable budget accounting."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable

_ALLOWED_OWNERS = {"main", "worker"}
_ALLOWED_REASONS = {"explore", "verify", "decision", "contradiction", "c3", "gate", "tool", "test"}
_ALLOWED_STATES = {"PENDING", "RUNNING", "DONE", "FAILED", "BLOCKED", "CANCELLED"}
_TERMINAL_STATES = {"DONE", "FAILED", "BLOCKED", "CANCELLED"}


@dataclass(frozen=True)
class ReadEvent:
    run_id: str
    agent_id: str
    owner: str
    path: str
    blob_id: str
    start_offset: int
    end_offset: int
    reason: str

    def __post_init__(self) -> None:
        if self.owner not in _ALLOWED_OWNERS:
            raise ValueError("owner must be main or worker")
        if not self.run_id or not self.agent_id or not self.path or not self.blob_id:
            raise ValueError("run_id, agent_id, path, and blob_id are required")
        if self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise ValueError("invalid byte range")
        if self.reason not in _ALLOWED_REASONS:
            raise ValueError(f"unsupported read reason: {self.reason}")

    @property
    def byte_count(self) -> int:
        return self.end_offset - self.start_offset


class RunLedger:
    def __init__(self, database: str | Path = ":memory:") -> None:
        self.database = str(database)
        self.connection = sqlite3.connect(
            self.database,
            timeout=5,
            isolation_level=None,
            check_same_thread=False,
        )
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA busy_timeout=5000")
        if self.database != ":memory:":
            self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS reads(
              id INTEGER PRIMARY KEY,
              run_id TEXT NOT NULL,
              agent_id TEXT NOT NULL,
              owner TEXT NOT NULL,
              path TEXT NOT NULL,
              blob_id TEXT NOT NULL,
              start_offset INTEGER NOT NULL,
              end_offset INTEGER NOT NULL,
              reason TEXT NOT NULL,
              UNIQUE(run_id,agent_id,path,blob_id,start_offset,end_offset,reason)
            );
            CREATE TABLE IF NOT EXISTS pending_reads(
              run_id TEXT NOT NULL,
              tool_use_id TEXT NOT NULL,
              agent_id TEXT NOT NULL,
              owner TEXT NOT NULL,
              path TEXT NOT NULL,
              blob_id TEXT NOT NULL,
              start_offset INTEGER NOT NULL,
              end_offset INTEGER NOT NULL,
              reason TEXT NOT NULL,
              PRIMARY KEY(run_id,tool_use_id)
            );
            CREATE TABLE IF NOT EXISTS checkpoints(
              run_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              state TEXT NOT NULL,
              result_hash TEXT,
              PRIMARY KEY(run_id,node_id)
            );
            CREATE TABLE IF NOT EXISTS reservations(
              run_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              usd_micros INTEGER NOT NULL CHECK(usd_micros >= 0),
              PRIMARY KEY(run_id,node_id)
            );
            CREATE TABLE IF NOT EXISTS charges(
              run_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              usd_micros INTEGER NOT NULL CHECK(usd_micros >= 0),
              PRIMARY KEY(run_id,node_id)
            );
            CREATE TABLE IF NOT EXISTS permits(
              run_id TEXT NOT NULL,
              agent_id TEXT NOT NULL,
              path TEXT NOT NULL,
              reason TEXT NOT NULL,
              remaining_uses INTEGER NOT NULL CHECK(remaining_uses >= 0),
              PRIMARY KEY(run_id,agent_id,path,reason)
            );
            CREATE TABLE IF NOT EXISTS invalidations(
              id INTEGER PRIMARY KEY,
              run_id TEXT NOT NULL,
              agent_id TEXT NOT NULL,
              category TEXT NOT NULL,
              detail TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tool_events_v04(
              id INTEGER PRIMARY KEY,
              run_id TEXT NOT NULL,
              agent_id TEXT NOT NULL,
              tool_use_id TEXT NOT NULL,
              tool_name TEXT NOT NULL,
              status TEXT NOT NULL,
              metadata_hash TEXT NOT NULL,
              UNIQUE(run_id,tool_use_id,status)
            );
            CREATE TABLE IF NOT EXISTS run_metadata(
              run_id TEXT PRIMARY KEY,
              config_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contract_bindings(
              run_id TEXT NOT NULL,
              task_id TEXT NOT NULL,
              contract_hash TEXT NOT NULL,
              author_agent_id TEXT,
              reviewer_agent_id TEXT,
              PRIMARY KEY(run_id,task_id)
            );
            """
        )

    def close(self) -> None:
        self.connection.close()

    def bind_config(self, run_id: str, config_hash: str) -> bool:
        if not run_id or not config_hash:
            raise ValueError("run_id and config_hash are required")
        self.connection.execute(
            "INSERT OR IGNORE INTO run_metadata(run_id,config_hash) VALUES(?,?)",
            (run_id, config_hash),
        )
        row = self.connection.execute(
            "SELECT config_hash FROM run_metadata WHERE run_id=?",
            (run_id,),
        ).fetchone()
        return bool(row and row[0] == config_hash)

    def config_hash_for_run(self, run_id: str) -> str | None:
        if not run_id:
            raise ValueError("run_id is required")
        row = self.connection.execute(
            "SELECT config_hash FROM run_metadata WHERE run_id=?",
            (run_id,),
        ).fetchone()
        return None if row is None else str(row[0])

    def bind_contract(
        self,
        run_id: str,
        task_id: str,
        contract_hash: str,
        *,
        author_agent_id: str | None = None,
        reviewer_agent_id: str | None = None,
    ) -> bool:
        if not run_id or not task_id or not contract_hash:
            raise ValueError("run_id, task_id, and contract_hash are required")
        for name, value in (
            ("author_agent_id", author_agent_id),
            ("reviewer_agent_id", reviewer_agent_id),
        ):
            if value is not None and (not isinstance(value, str) or not value):
                raise TypeError(f"{name} must be a non-empty string")
        if (
            author_agent_id is not None
            and reviewer_agent_id is not None
            and author_agent_id == reviewer_agent_id
        ):
            raise ValueError("writer and reviewer must be different agents")
        self.connection.execute(
            """INSERT OR IGNORE INTO contract_bindings
            (run_id,task_id,contract_hash,author_agent_id,reviewer_agent_id)
            VALUES(?,?,?,?,?)""",
            (run_id, task_id, contract_hash, author_agent_id, reviewer_agent_id),
        )
        row = self.connection.execute(
            """SELECT contract_hash,author_agent_id,reviewer_agent_id
               FROM contract_bindings WHERE run_id=? AND task_id=?""",
            (run_id, task_id),
        ).fetchone()
        return bool(
            row
            and row[0] == contract_hash
            and row[1] == author_agent_id
            and row[2] == reviewer_agent_id
        )

    def contract_binding(
        self, run_id: str, task_id: str
    ) -> tuple[str, str | None, str | None] | None:
        if not run_id or not task_id:
            raise ValueError("run_id and task_id are required")
        row = self.connection.execute(
            """SELECT contract_hash,author_agent_id,reviewer_agent_id
               FROM contract_bindings WHERE run_id=? AND task_id=?""",
            (run_id, task_id),
        ).fetchone()
        if row is None:
            return None
        return str(row[0]), row[1], row[2]

    def claim_contract_identity(
        self,
        run_id: str,
        task_id: str,
        *,
        role: str,
        agent_id: str,
    ) -> bool:
        if role not in {"author", "reviewer"}:
            raise ValueError("role must be author or reviewer")
        if not run_id or not task_id or not agent_id:
            raise ValueError("run_id, task_id, and agent_id are required")
        column = "author_agent_id" if role == "author" else "reviewer_agent_id"
        other = "reviewer_agent_id" if role == "author" else "author_agent_id"
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute(
                f"SELECT {column},{other} FROM contract_bindings WHERE run_id=? AND task_id=?",
                (run_id, task_id),
            ).fetchone()
            if row is None or (row[1] is not None and row[1] == agent_id):
                self.connection.execute("ROLLBACK")
                return False
            if row[0] is None:
                self.connection.execute(
                    f"UPDATE contract_bindings SET {column}=? WHERE run_id=? AND task_id=?",
                    (agent_id, run_id, task_id),
                )
                self.connection.execute("COMMIT")
                return True
            self.connection.execute("COMMIT")
            return row[0] == agent_id
        except Exception:
            self.connection.execute("ROLLBACK")
            raise

    def record_read(self, event: ReadEvent) -> bool:
        cursor = self.connection.execute(
            """INSERT OR IGNORE INTO reads
            (run_id,agent_id,owner,path,blob_id,start_offset,end_offset,reason)
            VALUES(?,?,?,?,?,?,?,?)""",
            (
                event.run_id,
                event.agent_id,
                event.owner,
                event.path,
                event.blob_id,
                event.start_offset,
                event.end_offset,
                event.reason,
            ),
        )
        return cursor.rowcount == 1

    def stage_read(self, tool_use_id: str, event: ReadEvent) -> None:
        if not tool_use_id:
            raise ValueError("tool_use_id is required")
        self.connection.execute(
            """INSERT INTO pending_reads
            (run_id,tool_use_id,agent_id,owner,path,blob_id,start_offset,end_offset,reason)
            VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(run_id,tool_use_id) DO UPDATE SET
              agent_id=excluded.agent_id, owner=excluded.owner, path=excluded.path,
              blob_id=excluded.blob_id, start_offset=excluded.start_offset,
              end_offset=excluded.end_offset, reason=excluded.reason""",
            (
                event.run_id,
                tool_use_id,
                event.agent_id,
                event.owner,
                event.path,
                event.blob_id,
                event.start_offset,
                event.end_offset,
                event.reason,
            ),
        )

    def pending_read(self, run_id: str, tool_use_id: str) -> ReadEvent | None:
        row = self.connection.execute(
            """SELECT agent_id,owner,path,blob_id,start_offset,end_offset,reason
               FROM pending_reads WHERE run_id=? AND tool_use_id=?""",
            (run_id, tool_use_id),
        ).fetchone()
        if row is None:
            return None
        return ReadEvent(run_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6])

    def commit_staged_read(
        self,
        run_id: str,
        tool_use_id: str,
        *,
        current_blob_id: str,
    ) -> bool:
        if not current_blob_id:
            raise ValueError("current_blob_id is required")
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute(
                """SELECT agent_id,owner,path,blob_id,start_offset,end_offset,reason
                   FROM pending_reads WHERE run_id=? AND tool_use_id=?""",
                (run_id, tool_use_id),
            ).fetchone()
            if row is None:
                self.connection.execute("ROLLBACK")
                return False
            if row[3] != current_blob_id:
                self.connection.execute(
                    "DELETE FROM pending_reads WHERE run_id=? AND tool_use_id=?",
                    (run_id, tool_use_id),
                )
                self.connection.execute("COMMIT")
                return False
            self.connection.execute(
                """INSERT OR IGNORE INTO reads
                (run_id,agent_id,owner,path,blob_id,start_offset,end_offset,reason)
                VALUES(?,?,?,?,?,?,?,?)""",
                (run_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6]),
            )
            self.connection.execute(
                "DELETE FROM pending_reads WHERE run_id=? AND tool_use_id=?",
                (run_id, tool_use_id),
            )
            self.connection.execute("COMMIT")
            return True
        except Exception:
            self.connection.execute("ROLLBACK")
            raise

    def discard_staged_read(self, run_id: str, tool_use_id: str) -> None:
        self.connection.execute(
            "DELETE FROM pending_reads WHERE run_id=? AND tool_use_id=?",
            (run_id, tool_use_id),
        )

    def record_tool_event(
        self,
        run_id: str,
        agent_id: str,
        tool_use_id: str,
        tool_name: str,
        status: str,
        metadata_hash: str,
    ) -> bool:
        if status not in {"requested", "completed", "failed"}:
            raise ValueError("invalid tool event status")
        if not all((run_id, agent_id, tool_use_id, tool_name, metadata_hash)):
            raise ValueError("tool event fields are required")
        cursor = self.connection.execute(
            """INSERT OR IGNORE INTO tool_events_v04
            (run_id,agent_id,tool_use_id,tool_name,status,metadata_hash)
            VALUES(?,?,?,?,?,?)""",
            (run_id, agent_id, tool_use_id, tool_name, status, metadata_hash),
        )
        return cursor.rowcount == 1

    def main_reread_ratio(self, run_id: str, additional_main: ReadEvent | None = None) -> float:
        rows = self.connection.execute(
            "SELECT owner,path,blob_id,start_offset,end_offset FROM reads WHERE run_id=?",
            (run_id,),
        ).fetchall()
        worker: dict[tuple[str, str], list[tuple[int, int]]] = {}
        main: dict[tuple[str, str], list[tuple[int, int]]] = {}
        for owner, path, blob_id, start, end in rows:
            target = worker if owner == "worker" else main
            target.setdefault((path, blob_id), []).append((start, end))
        if additional_main is not None:
            main.setdefault((additional_main.path, additional_main.blob_id), []).append(
                (additional_main.start_offset, additional_main.end_offset)
            )
        worker_total = 0
        overlap_total = 0
        for key, spans in worker.items():
            worker_union = merge_spans(spans)
            worker_total += span_length(worker_union)
            main_union = merge_spans(main.get(key, []))
            overlap_total += intersection_length(worker_union, main_union)
        if worker_total == 0:
            return 0.0
        return overlap_total / worker_total

    def checkpoint(
        self,
        run_id: str,
        node_id: str,
        state: str,
        result_hash: str | None = None,
    ) -> None:
        if state not in _ALLOWED_STATES:
            raise ValueError("invalid checkpoint state")
        if not run_id or not node_id:
            raise ValueError("run_id and node_id are required")
        current_row = self.connection.execute(
            "SELECT state FROM checkpoints WHERE run_id=? AND node_id=?",
            (run_id, node_id),
        ).fetchone()
        current = None if current_row is None else current_row[0]
        if current in _TERMINAL_STATES and state != current:
            raise ValueError(f"terminal checkpoint {current} cannot transition to {state}")
        if current == "RUNNING" and state == "PENDING":
            raise ValueError("RUNNING checkpoint cannot return to PENDING")
        self.connection.execute(
            """INSERT INTO checkpoints(run_id,node_id,state,result_hash) VALUES(?,?,?,?)
               ON CONFLICT(run_id,node_id) DO UPDATE SET
                 state=excluded.state,
                 result_hash=excluded.result_hash""",
            (run_id, node_id, state, result_hash),
        )

    def active_workers(self, run_id: str) -> int:
        return self.connection.execute(
            """SELECT COUNT(*) FROM checkpoints
               WHERE run_id=? AND state IN ('PENDING','RUNNING')""",
            (run_id,),
        ).fetchone()[0]

    def completed(self, run_id: str, node_id: str) -> bool:
        row = self.connection.execute(
            "SELECT state FROM checkpoints WHERE run_id=? AND node_id=?",
            (run_id, node_id),
        ).fetchone()
        return bool(row and row[0] == "DONE")

    def reserve(
        self,
        run_id: str,
        node_id: str,
        usd_micros: int,
        limit_micros: int,
        *,
        max_active_reservations: int | None = None,
    ) -> bool:
        _budget_values(usd_micros, limit_micros)
        if max_active_reservations is not None:
            if type(max_active_reservations) is not int or max_active_reservations < 1:
                raise ValueError("max_active_reservations must be a positive integer")
        if not run_id or not node_id:
            raise ValueError("run_id and node_id are required")
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            committed = self.connection.execute(
                "SELECT COALESCE(SUM(usd_micros),0) FROM charges WHERE run_id=?",
                (run_id,),
            ).fetchone()[0]
            reserved = self.connection.execute(
                "SELECT COALESCE(SUM(usd_micros),0) FROM reservations WHERE run_id=?",
                (run_id,),
            ).fetchone()[0]
            previous_row = self.connection.execute(
                "SELECT usd_micros FROM reservations WHERE run_id=? AND node_id=?",
                (run_id, node_id),
            ).fetchone()
            previous = 0 if previous_row is None else previous_row[0]
            if max_active_reservations is not None and previous_row is None:
                active = self.connection.execute(
                    "SELECT COUNT(*) FROM reservations WHERE run_id=?",
                    (run_id,),
                ).fetchone()[0]
                if active >= max_active_reservations:
                    self.connection.execute("ROLLBACK")
                    return False
            if committed + reserved - previous + usd_micros > limit_micros:
                self.connection.execute("ROLLBACK")
                return False
            self.connection.execute(
                """INSERT INTO reservations(run_id,node_id,usd_micros) VALUES(?,?,?)
                   ON CONFLICT(run_id,node_id) DO UPDATE SET usd_micros=excluded.usd_micros""",
                (run_id, node_id, usd_micros),
            )
            self.connection.execute("COMMIT")
            return True
        except Exception:
            self.connection.execute("ROLLBACK")
            raise

    def release(self, run_id: str, node_id: str) -> None:
        self.connection.execute(
            "DELETE FROM reservations WHERE run_id=? AND node_id=?",
            (run_id, node_id),
        )

    def commit_reservation(self, run_id: str, node_id: str) -> bool:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute(
                "SELECT usd_micros FROM reservations WHERE run_id=? AND node_id=?",
                (run_id, node_id),
            ).fetchone()
            if row is None:
                self.connection.execute("ROLLBACK")
                return False
            self.connection.execute(
                """INSERT INTO charges(run_id,node_id,usd_micros) VALUES(?,?,?)
                   ON CONFLICT(run_id,node_id) DO UPDATE SET usd_micros=excluded.usd_micros""",
                (run_id, node_id, row[0]),
            )
            self.connection.execute(
                "DELETE FROM reservations WHERE run_id=? AND node_id=?",
                (run_id, node_id),
            )
            self.connection.execute("COMMIT")
            return True
        except Exception:
            self.connection.execute("ROLLBACK")
            raise

    def reconcile(self, run_id: str, node_id: str, actual_usd_micros: int, limit_micros: int) -> bool:
        _budget_values(actual_usd_micros, limit_micros)
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            other_charges = self.connection.execute(
                """SELECT COALESCE(SUM(usd_micros),0) FROM charges
                   WHERE run_id=? AND node_id<>?""",
                (run_id, node_id),
            ).fetchone()[0]
            other_reservations = self.connection.execute(
                """SELECT COALESCE(SUM(usd_micros),0) FROM reservations
                   WHERE run_id=? AND node_id<>?""",
                (run_id, node_id),
            ).fetchone()[0]
            self.connection.execute(
                """INSERT INTO charges(run_id,node_id,usd_micros) VALUES(?,?,?)
                   ON CONFLICT(run_id,node_id) DO UPDATE SET usd_micros=excluded.usd_micros""",
                (run_id, node_id, actual_usd_micros),
            )
            self.connection.execute(
                "DELETE FROM reservations WHERE run_id=? AND node_id=?",
                (run_id, node_id),
            )
            self.connection.execute("COMMIT")
            return other_charges + other_reservations + actual_usd_micros <= limit_micros
        except Exception:
            self.connection.execute("ROLLBACK")
            raise

    def remaining(self, run_id: str, limit_micros: int) -> int:
        _budget_values(0, limit_micros)
        charged = self.connection.execute(
            "SELECT COALESCE(SUM(usd_micros),0) FROM charges WHERE run_id=?",
            (run_id,),
        ).fetchone()[0]
        reserved = self.connection.execute(
            "SELECT COALESCE(SUM(usd_micros),0) FROM reservations WHERE run_id=?",
            (run_id,),
        ).fetchone()[0]
        return max(0, limit_micros - charged - reserved)

    def charged(self, run_id: str) -> int:
        return self.connection.execute(
            "SELECT COALESCE(SUM(usd_micros),0) FROM charges WHERE run_id=?",
            (run_id,),
        ).fetchone()[0]

    def active_reservations(self, run_id: str) -> int:
        return self.connection.execute(
            "SELECT COUNT(*) FROM reservations WHERE run_id=?",
            (run_id,),
        ).fetchone()[0]

    def grant_permit(self, run_id: str, agent_id: str, path: str, reason: str, uses: int = 1) -> None:
        if reason not in {"decision", "contradiction", "c3", "gate"}:
            raise ValueError("permit reason is not decision-critical")
        if type(uses) is not int or uses < 1:
            raise ValueError("uses must be a positive integer")
        self.connection.execute(
            """INSERT INTO permits(run_id,agent_id,path,reason,remaining_uses) VALUES(?,?,?,?,?)
               ON CONFLICT(run_id,agent_id,path,reason)
               DO UPDATE SET remaining_uses=excluded.remaining_uses""",
            (run_id, agent_id, path, reason, uses),
        )

    def consume_permit(self, run_id: str, agent_id: str, path: str) -> bool:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute(
                """SELECT reason,remaining_uses FROM permits
                   WHERE run_id=? AND agent_id=? AND path=? AND remaining_uses>0
                   ORDER BY reason LIMIT 1""",
                (run_id, agent_id, path),
            ).fetchone()
            if row is None:
                self.connection.execute("ROLLBACK")
                return False
            reason, uses = row
            self.connection.execute(
                """UPDATE permits SET remaining_uses=?
                   WHERE run_id=? AND agent_id=? AND path=? AND reason=?""",
                (uses - 1, run_id, agent_id, path, reason),
            )
            self.connection.execute("COMMIT")
            return True
        except Exception:
            self.connection.execute("ROLLBACK")
            raise

    def invalidate(self, run_id: str, agent_id: str, category: str, detail: str) -> None:
        if not all((run_id, agent_id, category, detail)):
            raise ValueError("invalidation fields are required")
        self.connection.execute(
            "INSERT INTO invalidations(run_id,agent_id,category,detail) VALUES(?,?,?,?)",
            (run_id, agent_id, category, detail),
        )


def merge_spans(spans: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    ordered = sorted((start, end) for start, end in spans if end > start)
    merged: list[list[int]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def span_length(spans: Iterable[tuple[int, int]]) -> int:
    return sum(end - start for start, end in spans)


def intersection_length(left: Iterable[tuple[int, int]], right: Iterable[tuple[int, int]]) -> int:
    a = list(left)
    b = list(right)
    i = j = total = 0
    while i < len(a) and j < len(b):
        start = max(a[i][0], b[j][0])
        end = min(a[i][1], b[j][1])
        if end > start:
            total += end - start
        if a[i][1] <= b[j][1]:
            i += 1
        else:
            j += 1
    return total


def line_range_to_offsets(text: str, start_line: int, end_line: int) -> tuple[int, int]:
    if start_line < 1 or end_line < start_line:
        raise ValueError("invalid line range")
    lines = text.splitlines(keepends=True)
    if end_line > len(lines):
        raise ValueError("line range exceeds source")
    start = len("".join(lines[: start_line - 1]).encode("utf-8"))
    end = len("".join(lines[:end_line]).encode("utf-8"))
    return start, end


def _budget_values(value: int, limit: int) -> None:
    for name, item in (("value", value), ("limit", limit)):
        if type(item) is not int:
            raise TypeError(f"{name} must be an integer")
        if item < 0:
            raise ValueError(f"{name} must be non-negative")
