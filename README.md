# agent-handoff

> **AI 会失忆，仓库不会。**
> 
> 把项目交接状态留在仓库里，让 Codex 或 Claude Code 在换电脑、换线程、隔一天之后，还是知道怎么继续干活。
> 
> **AI forgets. Your repo doesn't.**
> 
> Keep your project handoff state in the repo, so Codex or Claude Code can continue across machines, threads, and time.

好记性不如烂笔头。放到 AI 协作里也是一样：别赌模型记性，把交接写进仓库。

---

## 你到底怎么用

这东西的主用法，其实很简单。

把这个仓库链接发给 Codex 或 Claude Code，让它安装 `agent-handoff`。  
然后用 `/+` 选中这个 skill。  
接下来，直接像跟同事说话一样开口就行。

你最常用的就是这四句：

- `初始化项目交接`
- `读取交接状态并继续工作`
- `更新交接状态并收尾`
- `查看当前交接状态`

先把 skill 装上，然后直接说人话。

---

## 它解决什么问题

你可能已经把代码同步好了。

真正总在掉的，是这些东西：

- 昨天做到哪了
- 为什么这么改
- 哪些决定已经定了
- 下一步最该接什么

换一台电脑，AI 不记得了。  
新开一个线程，背景又像从零开始。  
明明昨天聊得很完整，今天还是得重讲一遍。

`agent-handoff` 就是专门补这条断线的。

---

## 它到底是什么

`agent-handoff` 是一个把项目交接状态写进仓库里的 skill。

它不是聊天记录导出器，也不是假装“模型会永久记住一切”的幻想工具。它做的是更实在的事：

- 在仓库里建立固定的交接入口
- 把当前目标、待办、决定和最近进展留在仓库里
- 让下一次恢复工作时，有一条稳定的入口可接
- 用规则、校验和重建，尽量避免交接状态越用越乱

真正发布的 skill 内容在 [`dist/agent-handoff`](dist/agent-handoff)。

---

## 为什么它顺手

**不用先背命令**

装上 skill 以后，主用法就是自然语言触发，不是先去记一套脚本参数。

**状态跟着仓库走**

代码在仓库里，交接状态也在仓库里，不再散落在某个临时聊天窗口里。

**换设备也能接上**

你换电脑、换线程、隔一天再回来，至少还有一个明确入口，而不是全靠回忆。

**长期用也不容易乱**

它不是随便写几段 Markdown 就完事了，背后有校验和重建逻辑，坏了还能拉回来。

---

## 一个最常见的使用方式

1. 把这个仓库链接发给 Codex 或 Claude Code
2. 让它安装 `agent-handoff`
3. 用 `/+` 选中这个 skill
4. 直接说你现在要做哪一类事

例如：

- “初始化项目交接”
- “读取交接状态并继续工作”
- “更新交接状态并收尾”
- “查看当前交接状态”

这就是它最自然的工作流。

---

## 如果你更喜欢手动跑

虽然首页主打法不是命令行，但它也保留了手动入口。

如果你已经把 `agent-handoff` 安装进自己的 skills 目录里，也可以在安装后的 skill 目录手动运行：

```bash
python scripts/handoff.py init <repo-root>
python scripts/handoff.py resume <repo-root>
python scripts/handoff.py close-session <repo-root> [update-request.json]
python scripts/handoff.py validate <repo-root>
python scripts/handoff.py rebuild <repo-root>
```

这些命令分别对应初始化、恢复、收尾、校验和重建。

---

## 它不做什么

- 不保存整段聊天记录
- 不替代 Git 或版本控制
- 不保证模型“永久记忆”
- 不替你判断所有内容是不是都值得长期保留

它解决的是更具体、也更有用的一件事：

**把项目交接状态留在仓库里，让下一次继续工作时有地方可接。**

---

## 仓库里有什么

- [`dist/agent-handoff`](dist/agent-handoff): 实际发布的 skill 内容
- [`dist/agent-handoff/SKILL.md`](dist/agent-handoff/SKILL.md): skill 说明
- [`dist/agent-handoff/scripts/handoff.py`](dist/agent-handoff/scripts/handoff.py): 命令入口
- [`dist/agent-handoff/schemas/update-request.schema.yaml`](dist/agent-handoff/schemas/update-request.schema.yaml): 更新单结构
- [`dist/agent-handoff/evals/evals.json`](dist/agent-handoff/evals/evals.json): 回归评估

---

## 一句话总结

如果你不想每次换设备、换线程、隔天继续时，都重新给 AI 补一遍背景，`agent-handoff` 就是在仓库里替你留下那份交接。
