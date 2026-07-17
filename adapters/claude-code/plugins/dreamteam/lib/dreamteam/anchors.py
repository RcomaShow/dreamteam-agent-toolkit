"""Stable source anchors with formal parsing and fail-closed verification."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
import re
import subprocess

_ANCHOR_RE = re.compile(
    r"^file:(?P<path>.+):L(?P<start>[1-9][0-9]*)-L(?P<end>[1-9][0-9]*)@blob:(?P<blob>[0-9a-fA-F]{7,64})#sha256:(?P<hash>[0-9a-f]{64})$"
)


@dataclass(frozen=True)
class SourceAnchor:
    path: str
    start_line: int
    end_line: int
    blob_id: str
    slice_hash: str

    def __post_init__(self) -> None:
        validate_relative_path(self.path)
        if self.start_line < 1 or self.end_line < self.start_line:
            raise ValueError("invalid line range")
        if not re.fullmatch(r"[0-9a-fA-F]{7,64}", self.blob_id):
            raise ValueError("invalid blob id")
        if not re.fullmatch(r"[0-9a-f]{64}", self.slice_hash):
            raise ValueError("invalid SHA-256")

    def encode(self) -> str:
        return f"file:{self.path}:L{self.start_line}-L{self.end_line}@blob:{self.blob_id}#sha256:{self.slice_hash}"

    @classmethod
    def decode(cls, value: str) -> "SourceAnchor":
        match = _ANCHOR_RE.fullmatch(value)
        if match is None:
            raise ValueError("invalid source anchor syntax")
        return cls(
            path=match.group("path"),
            start_line=int(match.group("start")),
            end_line=int(match.group("end")),
            blob_id=match.group("blob").lower(),
            slice_hash=match.group("hash"),
        )


def validate_relative_path(path: str) -> None:
    pure = PurePosixPath(path.replace("\\", "/"))
    if not path or pure.is_absolute() or ".." in pure.parts:
        raise ValueError("anchor path must be repository-relative without traversal")


def make_anchor(path: str, text: str, start_line: int, end_line: int, blob_id: str) -> SourceAnchor:
    validate_relative_path(path)
    lines = text.splitlines(keepends=True)
    if start_line < 1 or end_line < start_line or end_line > len(lines):
        raise ValueError("invalid line range")
    fragment = "".join(lines[start_line - 1 : end_line]).encode("utf-8")
    return SourceAnchor(path, start_line, end_line, blob_id.lower(), sha256(fragment).hexdigest())


def verify_anchor(anchor: SourceAnchor, text: str, blob_id: str) -> bool:
    if blob_id.lower() != anchor.blob_id:
        return False
    try:
        candidate = make_anchor(anchor.path, text, anchor.start_line, anchor.end_line, blob_id)
    except ValueError:
        return False
    return candidate.slice_hash == anchor.slice_hash


def current_git_blob_id(repo_root: str | Path, relative_path: str) -> str:
    validate_relative_path(relative_path)
    root = Path(repo_root).resolve()
    target = (root / relative_path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("anchor resolves outside repository") from exc
    if not target.is_file():
        raise FileNotFoundError(relative_path)
    result = subprocess.run(
        ["git", "-C", str(root), "hash-object", "--", relative_path],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git hash-object failed")
    return result.stdout.strip().lower()


def make_file_anchor(repo_root: str | Path, relative_path: str, start_line: int, end_line: int) -> SourceAnchor:
    root = Path(repo_root).resolve()
    validate_relative_path(relative_path)
    text = (root / relative_path).read_text(encoding="utf-8")
    return make_anchor(relative_path, text, start_line, end_line, current_git_blob_id(root, relative_path))


def verify_anchor_file(anchor: SourceAnchor, repo_root: str | Path) -> bool:
    root = Path(repo_root).resolve()
    try:
        text = (root / anchor.path).read_text(encoding="utf-8")
        blob = current_git_blob_id(root, anchor.path)
    except (OSError, ValueError, RuntimeError):
        return False
    return verify_anchor(anchor, text, blob)
