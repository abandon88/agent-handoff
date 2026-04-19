from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

from skill_impl.handoff import build_resume_summary, close_session, init_repository, rebuild_views, validate_repository


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="handoff")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("root")

    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("root")

    close_parser = subparsers.add_parser("close-session")
    close_parser.add_argument("root")
    close_parser.add_argument("update_request", nargs="?")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("root")

    rebuild_parser = subparsers.add_parser("rebuild")
    rebuild_parser.add_argument("root")

    args = parser.parse_args(argv)
    root = Path(args.root)

    if args.command == "init":
        init_repository(root)
        print(json.dumps({"status": "ok", "command": "init"}, ensure_ascii=False))
        return 0
    if args.command == "resume":
        print(json.dumps(build_resume_summary(root), ensure_ascii=False))
        return 0
    if args.command == "close-session":
        used_path = close_session(root, Path(args.update_request) if args.update_request else None)
        print(
            json.dumps(
                {"status": "ok", "command": "close-session", "used_update_request": str(used_path)},
                ensure_ascii=False,
            )
        )
        return 0
    if args.command == "validate":
        problems = validate_repository(root)
        print(json.dumps({"status": "ok" if not problems else "error", "problems": problems}, ensure_ascii=False))
        return 0 if not problems else 1

    rebuild_views(root)
    print(json.dumps({"status": "ok", "command": "rebuild"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
