# JunJie Project Guide

面向缺少工程经验的开发者，帮助你看懂项目、建立文档，并安全使用 AI 编程助手。

## 适合什么场景

- 项目是通过 vibe coding 快速搭建的，缺少清晰说明。
- 新手不知道项目怎样启动、修改和验证。
- 需要整理 README、AGENTS、架构、业务、配置、运维或用户文档。
- 需要逐步学习 Git、AI 协作、权限、自动化和排障。

## 主要内容

- `SKILL.md`：Skill 的核心执行流程。
- `references/documentation-system.md`：项目文档如何分层和维护。
- `references/templates.md`：README、协作说明和主题文档大纲。
- `references/git-workflow.md`：根据项目规模选择最小 Git 流程。
- `references/agent-collaboration.md`：面向新手的 AI 编程助手协作入门。
- `scripts/audit_docs.py`：检查本地 Markdown 链接和环境变量文档覆盖。

## 使用方式

将本目录安装到你使用的 coding agent 的 Skill 目录，然后调用：

```text
$junjie-project-guide
```

使用时先从简单任务开始：让 agent 只读检查项目、解释现状、提出方案，再确认是否修改。涉及架构、数据、安全、部署或其他高影响选择时，应先讨论方案和利弊。

## 设计原则

先解决“看懂、跑起来、改得动、验得过”这几个基本问题，再按真实需要增加 Git workflow、CI、worktree、Skill、Hook 或 automation。不要为了显得专业而给小项目增加无法维护的流程。

## 来源说明

部分通用方法参考并重新整理自 [CodexGuide 进阶教程](https://github.com/freestylefly/CodexGuide/tree/main/docs/advanced)。原项目作者为 canghe，采用 [MIT License](https://github.com/freestylefly/CodexGuide/blob/main/LICENSE)。本仓库中的 Skill 结构和内容经过重新设计，产品行为请以对应工具的官方文档为准。

## 本地验证

```powershell
python scripts/audit_docs.py . --no-env
```
