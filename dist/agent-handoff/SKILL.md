---
name: agent-handoff
description: 当用户希望在仓库内初始化交接状态、在另一台设备上续接之前的工作、更新本次会话进度，或在继续之前查看可持久保存的项目交接文件时使用。
compatibility: 需要 Python 3.8+ 与 PyYAML 6.0.2，并且对目标仓库内文件有读写权限。
---

# 项目交接技能

当用户希望把跨设备延续工作的交接信息持久化保存在仓库内时，使用这个技能。

## 必用命令

- 初始化：`python scripts/handoff.py init <repo-root>`
- 恢复上下文：`python scripts/handoff.py resume <repo-root>`
- 会话收尾：`python scripts/handoff.py close-session <repo-root> [update-request.json]`
- 校验状态：`python scripts/handoff.py validate <repo-root>`
- 重建展示文件：`python scripts/handoff.py rebuild <repo-root>`

## 规则

- 全局 skill 负责触发和说明，实际记录工作优先使用仓库内的 `.agent-handoff/runtime/agent-handoff/scripts/handoff.py`。
- 如果仓库内运行副本还不存在，或看起来不完整，先用全局安装目录里的 `scripts/handoff.py` 补齐，再继续后续命令。
- 仓库内运行副本只保留运行必需文件，不保留第二份 `SKILL.md`。
- 不要直接手改生成出来的交接 Markdown 文件。
- 收尾更新单默认写到 `.agent-handoff/_tmp/close-session-YYYYMMDD-HHMMSS.json`。
- 会跨会话延续的事项，应该进入正式待办。
- 改变规则、结构、流程边界的重要事项，即使本轮做完，也可以通过 `tasks_to_add_and_complete` 直接记入已完成事项。
- 查看、试跑、顺手整理等零碎动作，只写进本轮进展，不单独建待办。
- 在变更任务状态或决策状态之前，先准备明确的更新请求。
- 如果目标仓库还没有初始化，`resume`、`close-session`、`validate`、`rebuild` 会先自动初始化再继续。
- 继续之前的工作前，优先执行 `resume`。
- 执行完 `close-session` 后，补跑一次 `validate`。
