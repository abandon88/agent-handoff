from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]
REPO_LOCAL_SUFFIX = (".agent-handoff", "runtime", "agent-handoff", "scripts", "handoff.py")


def _build_parser() -> argparse.ArgumentParser:
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
    return parser


def _load_runtime_info(skill_root: Path) -> Dict[str, object]:
    return json.loads((skill_root / "RUNTIME-INFO.json").read_text(encoding="utf-8"))


def _module_name_for_requirement(requirement: str) -> str:
    package_name = requirement.split("==")[0].split(">=")[0].strip()
    if package_name.lower() == "pyyaml":
        return "yaml"
    return package_name


def _installed_modules(runtime_info: Dict[str, object]) -> Dict[str, bool]:
    installed = {}
    for requirement in runtime_info.get("dependencies", []):
        module_name = _module_name_for_requirement(str(requirement))
        installed[module_name] = importlib.util.find_spec(module_name) is not None
    return installed


def _environment_diagnostics(
    runtime_info: Dict[str, object],
    version_info: Tuple[int, int, int],
    installed_modules: Dict[str, bool],
) -> Dict[str, object]:
    minimum_text = str(runtime_info["minimum_python"])
    minimum = tuple(int(part) for part in minimum_text.split("."))
    if version_info[:2] < minimum:
        return {
            "status": "error",
            "reason": "python version is too old",
            "current_python": ".".join(str(part) for part in version_info[:3]),
            "minimum_python": minimum_text,
        }

    missing = []
    for requirement in runtime_info.get("dependencies", []):
        module_name = _module_name_for_requirement(str(requirement))
        if not installed_modules.get(module_name, False):
            missing.append(str(requirement))

    if missing:
        return {
            "status": "error",
            "reason": "required dependency is missing",
            "current_python": ".".join(str(part) for part in version_info[:3]),
            "minimum_python": minimum_text,
            "missing_dependencies": missing,
        }

    return {"status": "ok"}


def _is_repo_local_script(script_path: Path) -> bool:
    return script_path.parts[-len(REPO_LOCAL_SUFFIX) :] == REPO_LOCAL_SUFFIX


def _assert_repo_local_script_location(script_path: Path) -> None:
    if not _is_repo_local_script(script_path):
        raise RuntimeError(
            "repo-local agent-handoff runner must live at .agent-handoff/runtime/agent-handoff/scripts/handoff.py"
        )


def _print_environment_error(runtime_info: Dict[str, object], diagnostics: Dict[str, object], skill_root: Path) -> int:
    payload = {
        "status": "error",
        "reason": diagnostics["reason"],
        "current_python": diagnostics["current_python"],
        "minimum_python": diagnostics["minimum_python"],
        "missing_dependencies": diagnostics.get("missing_dependencies", []),
        "next_step": f"python -m pip install -r {skill_root / 'requirements.txt'}",
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 1


def _runtime_script_for_root(root: Path, runtime_info: Dict[str, object]) -> Path:
    runtime_root = root / Path(str(runtime_info["runtime_root"]))
    return runtime_root / Path(str(runtime_info["entry_script"]))


def _argv_from_args(args: argparse.Namespace) -> List[str]:
    argv = [args.command, args.root]
    if args.command == "close-session" and args.update_request:
        argv.append(args.update_request)
    return argv


def _run_global_launcher(args: argparse.Namespace) -> int:
    runtime_info = _load_runtime_info(SKILL_ROOT)
    diagnostics = _environment_diagnostics(runtime_info, sys.version_info[:3], _installed_modules(runtime_info))
    if diagnostics["status"] != "ok":
        return _print_environment_error(runtime_info, diagnostics, SKILL_ROOT)

    sys.path.insert(0, str(SKILL_ROOT))
    from skill_impl.handoff import sync_runtime_copy

    root = Path(args.root)
    sync_runtime_copy(root, SKILL_ROOT)
    repo_local_script = _runtime_script_for_root(root, runtime_info)
    completed = subprocess.run([sys.executable, str(repo_local_script), *_argv_from_args(args)], check=False)
    return completed.returncode


def _ensure_repo_state(command: str, root: Path, init_repository) -> None:
    if command == "init":
        init_repository(root)
        return
    state_file = root / ".agent-handoff" / "_state" / "project.yaml"
    if not state_file.exists():
        init_repository(root)


def _run_repo_local(args: argparse.Namespace) -> int:
    _assert_repo_local_script_location(SCRIPT_PATH)
    runtime_info = _load_runtime_info(SKILL_ROOT)
    diagnostics = _environment_diagnostics(runtime_info, sys.version_info[:3], _installed_modules(runtime_info))
    if diagnostics["status"] != "ok":
        return _print_environment_error(runtime_info, diagnostics, SKILL_ROOT)

    sys.path.insert(0, str(SKILL_ROOT))
    from skill_impl.handoff import build_resume_summary, close_session, init_repository, rebuild_views, validate_repository

    root = Path(args.root)

    if args.command == "init":
        init_repository(root)
        print(json.dumps({"status": "ok", "command": "init"}, ensure_ascii=False))
        return 0

    _ensure_repo_state(args.command, root, init_repository)

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


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    if _is_repo_local_script(SCRIPT_PATH):
        return _run_repo_local(args)
    return _run_global_launcher(args)


if __name__ == "__main__":
    raise SystemExit(main())
