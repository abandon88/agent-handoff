from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

MANAGED_BLOCK = """<!-- AGENT-HANDOFF:START -->
如果用户要求继续之前的工作、从上次中断处恢复，或读取交接状态，先查看 `.agent-handoff/START-HERE.md`，再按交接文件的顺序继续。
<!-- AGENT-HANDOFF:END -->
"""

START_HERE = """# 交接入口

## 读取顺序
1. STATE.yaml
2. CURRENT.md
3. TASKS.md
4. DECISIONS.md
5. SESSION-LOG.md
6. DAILY-LOG.md
7. HANDOFF-RULES.md

## 常用触发语
- 初始化项目交接
- 读取交接状态并继续工作
- 更新交接状态并收尾
- 查看当前交接状态
"""

HANDOFF_RULES = """# 交接规则

## 默认视为阶段变化的情况
- 一个主要任务完成
- 当前主线的下一步发生变化
- 新阻塞出现或旧阻塞解除
- 有新的明确决定已经拍板
- 工作范围明显扩大或缩小

## 更新单与内部中转区
- 收尾更新单默认放到 `.agent-handoff/_tmp/`。
- `_tmp/` 只存放脚本中转文件，不属于正式状态或长期归档。
- `close-session` 成功后只保留最近 10 份中转文件。

## 待办边界
- 会跨会话延续的事项，应该进入正式待办。
- 改变规则、结构、流程边界的重要事项，即使本轮做完，也可以记入已完成事项。
- 查看、试跑、顺手整理等零碎动作，只写入本轮进展，不单独建待办。
"""

TMP_DIR_NAME = "_tmp"
CLOSE_SESSION_PREFIX = "close-session-"
TMP_REQUEST_KEEP_LIMIT = 10
MODULE_SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT_PARTS = (".agent-handoff", "runtime", "agent-handoff")
RUNTIME_REQUIRED_FILES = (
    "requirements.txt",
    "RUNTIME-INFO.json",
    "scripts/handoff.py",
    "skill_impl/__init__.py",
    "skill_impl/handoff.py",
    "schemas/update-request.schema.yaml",
)


def _now_pair() -> tuple[str, str]:
    now = datetime.now().astimezone()
    return now.isoformat(timespec="seconds"), now.strftime("%Y-%m-%d %H:%M:%S %z")


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _ensure_agents_block(path: Path) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if "<!-- AGENT-HANDOFF:START -->" in existing and "<!-- AGENT-HANDOFF:END -->" in existing:
            start = existing.index("<!-- AGENT-HANDOFF:START -->")
            end = existing.index("<!-- AGENT-HANDOFF:END -->") + len("<!-- AGENT-HANDOFF:END -->")
            updated = existing[:start] + MANAGED_BLOCK + existing[end:]
        else:
            suffix = "" if existing.endswith("\n") or not existing else "\n\n"
            updated = existing + suffix + MANAGED_BLOCK
    else:
        updated = MANAGED_BLOCK
    path.write_text(updated, encoding="utf-8")


def _handoff_dir(root: Path) -> Path:
    return Path(root) / ".agent-handoff"


def _runtime_root(root: Path) -> Path:
    return Path(root).joinpath(*RUNTIME_ROOT_PARTS)


def _runtime_required_paths(root: Path) -> list[Path]:
    runtime_root = _runtime_root(root)
    return [runtime_root / relative for relative in RUNTIME_REQUIRED_FILES]


def _tmp_dir(root: Path) -> Path:
    tmp_dir = _handoff_dir(root) / TMP_DIR_NAME
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir


def _close_session_request_files(root: Path) -> list[Path]:
    return sorted(_tmp_dir(root).glob(f"{CLOSE_SESSION_PREFIX}*.json"))


def _latest_close_session_request(root: Path) -> Path:
    candidates = _close_session_request_files(root)
    if not candidates:
        raise FileNotFoundError(f"no close-session update request found in {_tmp_dir(root)}")
    return candidates[-1]


def _prune_close_session_requests(root: Path, keep: int = TMP_REQUEST_KEEP_LIMIT) -> None:
    candidates = _close_session_request_files(root)
    for stale in candidates[:-keep]:
        stale.unlink()


def _sync_static_handoff_files(root: Path) -> None:
    handoff_dir = _handoff_dir(root)
    _tmp_dir(root)
    (handoff_dir / "START-HERE.md").write_text(START_HERE, encoding="utf-8")
    (handoff_dir / "HANDOFF-RULES.md").write_text(HANDOFF_RULES, encoding="utf-8")


def sync_runtime_copy(root: Path, source_skill_root: Path | None = None) -> Path:
    root = Path(root)
    source_root = Path(source_skill_root) if source_skill_root else MODULE_SKILL_ROOT
    runtime_root = _runtime_root(root)
    runtime_root.mkdir(parents=True, exist_ok=True)

    for relative in RUNTIME_REQUIRED_FILES:
        source = source_root / relative
        target = runtime_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() == target.resolve():
            continue
        shutil.copy2(source, target)

    return runtime_root


def init_repository(root: Path) -> None:
    root = Path(root)
    handoff_dir = _handoff_dir(root)
    state_dir = handoff_dir / "_state"
    schemas_dir = handoff_dir / "schemas"
    archive_dir = handoff_dir / "archive"
    state_dir.mkdir(parents=True, exist_ok=True)
    schemas_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    _tmp_dir(root)

    created_at, display_at = _now_pair()

    _write_yaml(
        state_dir / "project.yaml",
        {
            "version": 1,
            "project": root.name or "agent-handoff-project",
            "created_at": created_at,
            "updated_at": created_at,
            "last_resumed_at": "",
            "current_phase": "unstarted",
            "current_goal": "",
            "summary": "",
            "next_step": "",
            "blockers": [],
        },
    )
    _write_yaml(state_dir / "tasks.yaml", {"active": [], "completed": []})
    _write_yaml(state_dir / "decisions.yaml", {"items": []})
    (state_dir / "sessions.jsonl").write_text("", encoding="utf-8")

    _sync_static_handoff_files(root)
    (handoff_dir / "CURRENT.md").write_text(f"# 当前状态\n\n- 最近更新时间：{display_at}\n", encoding="utf-8")
    (handoff_dir / "TASKS.md").write_text("# 当前待办\n", encoding="utf-8")
    (handoff_dir / "COMPLETED.md").write_text("# 已完成事项\n", encoding="utf-8")
    (handoff_dir / "DECISIONS.md").write_text("# 已定决策\n", encoding="utf-8")
    (handoff_dir / "SESSION-LOG.md").write_text("# 会话记录\n", encoding="utf-8")
    (handoff_dir / "DAILY-LOG.md").write_text("# 每日工作日志\n\n- 无\n", encoding="utf-8")
    (handoff_dir / "STATE.yaml").write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "project": root.name or "agent-handoff-project",
                "created_at": display_at,
                "updated_at": display_at,
                "last_resumed_at": "",
                "current_phase": "unstarted",
                "current_goal": "",
                "next_step": "",
                "blockers": [],
                "key_files": [".agent-handoff/START-HERE.md", ".agent-handoff/CURRENT.md"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    _ensure_agents_block(root / "AGENTS.md")
    sync_runtime_copy(root)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def _display_time(iso_value: str) -> str:
    if not iso_value:
        return ""
    stamp = datetime.fromisoformat(iso_value)
    return stamp.strftime("%Y-%m-%d %H:%M:%S %z")


def _load_truth(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    state_dir = Path(root) / ".agent-handoff" / "_state"
    project = _read_yaml(state_dir / "project.yaml")
    tasks = _read_yaml(state_dir / "tasks.yaml")
    decisions = _read_yaml(state_dir / "decisions.yaml")
    sessions = []
    sessions_path = state_dir / "sessions.jsonl"
    if sessions_path.exists():
        for line in sessions_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                sessions.append(json.loads(line))
    return project, tasks, decisions, sessions


def _render_state_yaml(project: dict[str, Any]) -> str:
    payload = {
        "version": project["version"],
        "project": project["project"],
        "created_at": _display_time(project["created_at"]),
        "updated_at": _display_time(project["updated_at"]),
        "last_resumed_at": _display_time(project["last_resumed_at"]),
        "current_phase": project["current_phase"],
        "current_goal": project["current_goal"],
        "next_step": project["next_step"],
        "blockers": project["blockers"],
        "key_files": [
            ".agent-handoff/START-HERE.md",
            ".agent-handoff/CURRENT.md",
            ".agent-handoff/TASKS.md",
        ],
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def _render_current_md(project: dict[str, Any], tasks: dict[str, Any]) -> str:
    completed = tasks.get("completed", [])[-3:]
    completed_lines = "\n".join(f"- {item['task_id']}: {item['title']}" for item in completed) or "- 无"
    blockers = "\n".join(f"- {item}" for item in project.get("blockers", [])) or "- 无"
    return f"""# 当前状态

- 最近更新时间：{_display_time(project['updated_at'])}
- 当前阶段：{project['current_phase']}
- 当前目标：{project['current_goal']}
- 当前摘要：{project['summary']}

## 已完成进展
{completed_lines}

## 下一步建议
- {project['next_step']}

## 当前阻塞
{blockers}
"""


def _render_tasks_md(tasks: dict[str, Any]) -> str:
    active = tasks.get("active", [])
    lines = ["# 当前待办", "", "## 进行中"]
    if not active:
        lines.append("- 无")
    for item in active:
        lines.extend(
            [
                f"- [ ] {item['task_id']}: {item['title']}",
                f"  详情：{item['details']}",
                f"  状态：{item['status']}",
                f"  创建时间：{_display_time(item['created_at'])}",
                f"  更新时间：{_display_time(item['updated_at'])}",
            ]
        )
    return "\n".join(lines) + "\n"


def _render_completed_md(tasks: dict[str, Any]) -> str:
    completed = tasks.get("completed", [])
    lines = ["# 已完成事项", ""]
    if not completed:
        lines.append("- 无")
    for item in completed:
        lines.extend(
            [
                f"- {item['task_id']}: {item['title']}",
                f"  完成时间：{_display_time(item['completed_at'])}",
                f"  备注：{item.get('notes', '') or '无'}",
            ]
        )
    return "\n".join(lines) + "\n"


def _render_decisions_md(decisions: dict[str, Any]) -> str:
    items = decisions.get("items", [])
    lines = ["# 已定决策", ""]
    if not items:
        lines.append("- 无")
    for item in items:
        lines.extend(
            [
                f"- {item['decision_id']}: {item['summary']}",
                f"  时间：{_display_time(item['time'])}",
                f"  原因：{item['rationale']}",
            ]
        )
    return "\n".join(lines) + "\n"


def _render_sessions_md(sessions: list[dict[str, Any]]) -> str:
    lines = ["# 会话记录", ""]
    if not sessions:
        lines.append("- 无")
    for session in sessions[-10:]:
        progress_lines = [f"- {item}" for item in session.get("progress", [])] or ["- 无"]
        file_lines = [f"- {item}" for item in session.get("files_touched", [])] or ["- 无"]
        risk_lines = [f"- {item}" for item in session.get("risks", [])] or ["- 无"]
        lines.extend(
            [
                "## 一次会话",
                f"- 开始时间：{_display_time(session['started_at'])}",
                f"- 结束时间：{_display_time(session['ended_at'])}",
                f"- 本次焦点：{session['focus']}",
                "",
                "### 本次进展",
                *progress_lines,
                "",
                "### 涉及文件",
                *file_lines,
                "",
                "### 下次恢复点",
                f"- {session['resume_hint']}",
                "",
                "### 风险与备注",
                *risk_lines,
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _session_date(session: dict[str, Any]) -> str:
    stamp = session.get("ended_at") or session.get("started_at") or ""
    if not stamp:
        return "未知日期"
    return datetime.fromisoformat(stamp).date().isoformat()


def _session_sort_stamp(session: dict[str, Any]) -> str:
    return session.get("ended_at") or session.get("started_at") or ""


def _render_daily_log_md(sessions: list[dict[str, Any]]) -> str:
    lines = ["# 每日工作日志", ""]
    if not sessions:
        lines.append("- 无")
        return "\n".join(lines) + "\n"

    grouped: dict[str, list[dict[str, Any]]] = {}
    for session in sessions:
        grouped.setdefault(_session_date(session), []).append(session)

    for day in sorted(grouped.keys(), reverse=True):
        lines.extend(["---", "", f"## {day}", ""])
        for session in sorted(grouped[day], key=_session_sort_stamp):
            progress_lines = [f"- {item}" for item in session.get("progress", [])] or ["- 无"]
            risk_items = session.get("risks", [])
            lines.extend([f"### {session['focus']}", *progress_lines])
            if risk_items:
                lines.extend(["", "#### 风险与备注", *[f"- {item}" for item in risk_items]])
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def rebuild_views(root: Path) -> None:
    root = Path(root)
    handoff_dir = root / ".agent-handoff"
    _sync_static_handoff_files(root)
    project, tasks, decisions, sessions = _load_truth(root)
    (handoff_dir / "STATE.yaml").write_text(_render_state_yaml(project), encoding="utf-8")
    (handoff_dir / "CURRENT.md").write_text(_render_current_md(project, tasks), encoding="utf-8")
    (handoff_dir / "TASKS.md").write_text(_render_tasks_md(tasks), encoding="utf-8")
    (handoff_dir / "COMPLETED.md").write_text(_render_completed_md(tasks), encoding="utf-8")
    (handoff_dir / "DECISIONS.md").write_text(_render_decisions_md(decisions), encoding="utf-8")
    (handoff_dir / "SESSION-LOG.md").write_text(_render_sessions_md(sessions), encoding="utf-8")
    (handoff_dir / "DAILY-LOG.md").write_text(_render_daily_log_md(sessions), encoding="utf-8")


def _save_truth(
    root: Path,
    project: dict[str, Any],
    tasks: dict[str, Any],
    decisions: dict[str, Any],
    sessions: list[dict[str, Any]],
) -> None:
    state_dir = Path(root) / ".agent-handoff" / "_state"
    _write_yaml(state_dir / "project.yaml", project)
    _write_yaml(state_dir / "tasks.yaml", tasks)
    _write_yaml(state_dir / "decisions.yaml", decisions)
    session_lines = [json.dumps(item, ensure_ascii=False) for item in sessions]
    (state_dir / "sessions.jsonl").write_text("\n".join(session_lines) + ("\n" if session_lines else ""), encoding="utf-8")


def _next_task_id(tasks: dict[str, Any]) -> str:
    items = tasks.get("active", []) + tasks.get("completed", [])
    if not items:
        return "TASK-001"
    last_number = max(int(item["task_id"].split("-")[1]) for item in items)
    return f"TASK-{last_number + 1:03d}"


def _next_decision_id(decisions: dict[str, Any]) -> str:
    items = decisions.get("items", [])
    if not items:
        return "DEC-001"
    last_number = max(int(item["decision_id"].split("-")[1]) for item in items)
    return f"DEC-{last_number + 1:03d}"


def _task_record(
    *,
    task_id: str,
    title: str,
    details: str,
    priority: str,
    status: str,
    created_at: str,
    updated_at: str,
    completed_at: str = "",
    notes: str = "",
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "title": title,
        "details": details,
        "priority": priority,
        "status": status,
        "created_at": created_at,
        "updated_at": updated_at,
        "completed_at": completed_at,
        "notes": notes,
    }


def _require_update_keys(update_request: dict[str, Any]) -> None:
    required = {
        "session",
        "current_status",
        "tasks_to_add",
        "tasks_to_update",
        "tasks_to_complete",
        "tasks_to_add_and_complete",
        "decisions_to_add",
        "session_log",
        "resume_hint",
    }
    missing = sorted(required - set(update_request.keys()))
    if missing:
        raise ValueError(f"update request missing keys: {', '.join(missing)}")


def apply_update_request(root: Path, update_request: dict[str, Any]) -> None:
    _require_update_keys(update_request)
    project, tasks, decisions, sessions = _load_truth(root)
    now_iso, _ = _now_pair()

    active = tasks.setdefault("active", [])
    completed = tasks.setdefault("completed", [])
    active_by_id = {item["task_id"]: item for item in active}

    for item in update_request["tasks_to_add"]:
        active.append(
            _task_record(
                task_id=_next_task_id(tasks),
                title=item["title"],
                details=item["details"],
                priority=item["priority"],
                status="pending",
                created_at=now_iso,
                updated_at=now_iso,
            )
        )
        active_by_id = {entry["task_id"]: entry for entry in active}

    for item in update_request["tasks_to_add_and_complete"]:
        completed.append(
            _task_record(
                task_id=_next_task_id(tasks),
                title=item["title"],
                details=item["details"],
                priority=item["priority"],
                status="completed",
                created_at=now_iso,
                updated_at=now_iso,
                completed_at=now_iso,
                notes=item["notes"],
            )
        )

    for item in update_request["tasks_to_update"]:
        if item["task_id"] not in active_by_id:
            raise ValueError(f"unknown active task id: {item['task_id']}")
        active_item = active_by_id[item["task_id"]]
        active_item["title"] = item["title"]
        active_item["details"] = item["details"]
        active_item["priority"] = item["priority"]
        active_item["updated_at"] = now_iso
        active_item["status"] = "in_progress"

    for item in update_request["tasks_to_complete"]:
        if item["task_id"] not in active_by_id:
            raise ValueError(f"unknown active task id: {item['task_id']}")
        finished = active_by_id[item["task_id"]]
        active.remove(finished)
        finished["status"] = "completed"
        finished["updated_at"] = now_iso
        finished["completed_at"] = now_iso
        finished["notes"] = item.get("notes", "")
        completed.append(finished)
        active_by_id = {entry["task_id"]: entry for entry in active}

    for item in update_request["decisions_to_add"]:
        decisions.setdefault("items", []).append(
            {
                "decision_id": _next_decision_id(decisions),
                "summary": item["summary"],
                "rationale": item["rationale"],
                "time": now_iso,
            }
        )

    project["updated_at"] = update_request["session"]["ended_at"]
    project["current_phase"] = update_request["current_status"]["phase"]
    project["current_goal"] = update_request["current_status"]["goal"]
    project["summary"] = update_request["current_status"]["summary"]
    project["next_step"] = update_request["current_status"]["next_step"]
    project["blockers"] = update_request["current_status"]["blockers"]

    sessions.append(
        {
            "started_at": update_request["session"]["started_at"],
            "ended_at": update_request["session"]["ended_at"],
            "focus": update_request["session"]["focus"],
            "progress": update_request["session_log"]["progress"],
            "files_touched": update_request["session_log"]["files_touched"],
            "resume_hint": update_request["resume_hint"]["text"],
            "risks": update_request["session_log"]["risks"],
        }
    )

    _save_truth(root, project, tasks, decisions, sessions)
    rebuild_views(root)


def close_session(root: Path, update_request_path: Path | None = None) -> Path:
    root = Path(root)
    request_path = Path(update_request_path) if update_request_path is not None else _latest_close_session_request(root)
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    apply_update_request(root, payload)
    _prune_close_session_requests(root)
    return request_path


def validate_repository(root: Path) -> list[str]:
    root = Path(root)
    handoff_dir = _handoff_dir(root)
    problems = []
    required_directories = [
        handoff_dir / "_state",
        handoff_dir / "archive",
        handoff_dir / TMP_DIR_NAME,
    ]
    required_files = [
        handoff_dir / "_state" / "project.yaml",
        handoff_dir / "_state" / "tasks.yaml",
        handoff_dir / "_state" / "decisions.yaml",
        handoff_dir / "_state" / "sessions.jsonl",
        handoff_dir / "STATE.yaml",
        handoff_dir / "CURRENT.md",
        handoff_dir / "TASKS.md",
        handoff_dir / "COMPLETED.md",
        handoff_dir / "DECISIONS.md",
        handoff_dir / "SESSION-LOG.md",
        handoff_dir / "DAILY-LOG.md",
    ]
    for path in required_directories:
        if not path.is_dir():
            problems.append(f"missing directory: {path}")

    for path in required_files:
        if not path.exists():
            problems.append(f"missing file: {path}")

    for path in _runtime_required_paths(root):
        if not path.exists():
            problems.append(f"missing runtime file: {path}")

    _, tasks, _, _ = _load_truth(root)
    ids = [item["task_id"] for item in tasks.get("active", []) + tasks.get("completed", [])]
    if len(ids) != len(set(ids)):
        problems.append("duplicate task ids detected")

    active_ids = {item["task_id"] for item in tasks.get("active", [])}
    completed_ids = {item["task_id"] for item in tasks.get("completed", [])}
    if active_ids & completed_ids:
        problems.append("task ids appear in both active and completed")

    return problems


def build_resume_summary(root: Path) -> dict[str, Any]:
    root = Path(root)
    project, tasks, decisions, sessions = _load_truth(root)
    project["last_resumed_at"] = _now_pair()[0]
    _save_truth(root, project, tasks, decisions, sessions)
    rebuild_views(root)
    return {
        "phase": project["current_phase"],
        "goal": project["current_goal"],
        "summary": project["summary"],
        "next_step": project["next_step"],
        "blockers": project["blockers"],
        "active_task_ids": [item["task_id"] for item in tasks.get("active", [])],
        "decision_ids": [item["decision_id"] for item in decisions.get("items", [])],
    }
