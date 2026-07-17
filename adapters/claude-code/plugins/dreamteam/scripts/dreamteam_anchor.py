#!/usr/bin/env python3
"""Create or verify repository source anchors."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "lib"))
from dreamteam.anchors import SourceAnchor, make_file_anchor, verify_anchor_file


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("repo", type=Path)
    create.add_argument("path")
    create.add_argument("start_line", type=int)
    create.add_argument("end_line", type=int)
    verify = sub.add_parser("verify")
    verify.add_argument("repo", type=Path)
    verify.add_argument("anchor")
    args = parser.parse_args()
    if args.command == "create":
        print(make_file_anchor(args.repo, args.path, args.start_line, args.end_line).encode())
        return 0
    return 0 if verify_anchor_file(SourceAnchor.decode(args.anchor), args.repo) else 1


if __name__ == "__main__":
    raise SystemExit(main())
