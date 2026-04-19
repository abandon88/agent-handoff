# agent-handoff

> **AI 会忘，仓库不会。**
>
> 把 AI 协作的交接状态留在仓库里，让它在换电脑、换线程、隔一天之后，仍然能接着干活。
>
> **AI forgets. Your repo doesn't.**
>
> Put your AI handoff state inside the repo, so work can continue across machines, threads, and time.

你可能并不缺代码同步。

你缺的是另一种东西:

- 昨天做到哪了
- 为什么这么做
- 哪些决定已经拍板
- 下一步最该干什么

代码可以在 GitHub 里同步，协作状态却经常死在聊天窗口里。

换一台电脑，AI 又要你重新解释一遍。  
开一个新线程，背景又像没发生过。  
一次明明很高质量的会话，隔天还是得重讲。

`agent-handoff` 解决的就是这个问题。

*If your code survives across machines but your AI context does not, this skill is built for that gap.*

---

## 它是什么

`agent-handoff` 是一个把“项目交接状态”写进仓库的技能。

它不是聊天记录导出器，也不是幻想让模型自己永远记住一切。它做的事情很务实:

- 在仓库里建立固定的交接入口
- 把当前目标、待办、决定和最近进展稳定落盘
- 让下一次恢复工作时，有一条明确、可重复的入口
- 用脚本校验和重建，避免交接文件越用越乱

实际发布的技能内容位于 [`dist/agent-handoff`](dist/agent-handoff)。

*`agent-handoff` turns handoff state into repo-owned project context: durable, readable, and resumable.*

---

## 为什么它比“再解释一遍背景”更靠谱

**状态留在仓库里**

不是留在某个临时线程，不是留在某台机器，也不是指望模型碰巧还记得。

**恢复入口固定**

下次继续之前，先看同一套交接文件，而不是每次都靠人脑回忆。

**重要事项会留下来**

当前目标、活跃待办、关键决定、最近进展，会被整理成稳定结构，而不是散成聊天碎片。

**能校验，也能重建**

交接文件不是“写了就听天由命”。如果展示文件乱了，可以重新生成；如果状态不一致，可以先检查再继续。

*The point is not magic memory. The point is a repeatable handoff workflow you can trust.*

---

## 快速开始

### 1. 准备条件

- Python 3.11+
- `PyYAML`
- 对目标仓库有读写权限

### 2. 使用这个仓库里的发布内容

这个仓库真正要拿去用的，是 [`dist/agent-handoff`](dist/agent-handoff) 这一份目录。

把它作为 `agent-handoff` 技能放进你的技能目录后，再执行下面这些命令。

### 3. 最常用命令

```bash
python scripts/handoff.py init <repo-root>
python scripts/handoff.py resume <repo-root>
python scripts/handoff.py close-session <repo-root> [update-request.json]
python scripts/handoff.py validate <repo-root>
python scripts/handoff.py rebuild <repo-root>
```

它们分别对应:

- `init`: 初始化仓库内的交接结构
- `resume`: 恢复当前上下文，快速接上工作
- `close-session`: 给这次会话收尾，把更新正式写进交接状态
- `validate`: 检查当前交接状态有没有问题
- `rebuild`: 按真源重新生成展示文件

*Use the published skill folder in `dist/agent-handoff/`, then run the handoff commands from the installed skill directory.*

---

## 一个最常见的工作流

### 第一次接入

在目标仓库里初始化一次:

```bash
python scripts/handoff.py init <repo-root>
```

### 下一次继续

不管你是换了电脑，还是新开了一个线程，先恢复上下文:

```bash
python scripts/handoff.py resume <repo-root>
```

### 结束这轮工作

把这次进展收尾，再做一次检查:

```bash
python scripts/handoff.py close-session <repo-root> [update-request.json]
python scripts/handoff.py validate <repo-root>
```

这套流程的重点不是“多一个命令”，而是把“交接”本身变成项目的一部分。

*Initialize once, resume before continuing, close the session when you stop. That rhythm is the product.*

---

## 它适合谁

- 经常在两台电脑之间切换的人
- 经常会新开 AI 会话的人
- 想把协作上下文跟着仓库走的人
- 不想每次都重新讲项目背景的人
- 希望 AI 协作更稳，而不是更玄学的人

---

## 它不做什么

- 不保存整段聊天记录
- 不替代 Git 或版本控制
- 不保证模型“永久记忆”
- 不替你决定哪些内容值得长期保留

它解决的是一件更具体、也更实际的事:

**把项目交接状态留在仓库里，让下一次继续工作时有地方可接。**

*This skill is about durable handoff state, not about pretending chat history is the same thing as project memory.*

---

## 仓库里有什么

- [`dist/agent-handoff`](dist/agent-handoff): 实际发布的技能内容
- [`dist/agent-handoff/SKILL.md`](dist/agent-handoff/SKILL.md): 技能说明
- [`dist/agent-handoff/scripts/handoff.py`](dist/agent-handoff/scripts/handoff.py): 命令入口
- [`dist/agent-handoff/schemas/update-request.schema.yaml`](dist/agent-handoff/schemas/update-request.schema.yaml): 更新单结构
- [`dist/agent-handoff/evals/evals.json`](dist/agent-handoff/evals/evals.json): 回归评估

如果你想看更偏内部的设计推演，这个仓库也保留了相应文档；但第一次接触时，你不需要先理解那些细节。

---

## 一句话总结

如果你想让 AI 协作别再被“换设备、换线程、隔天继续”这类事不断打断，`agent-handoff` 就是在仓库里给你补上这条断掉的线。
