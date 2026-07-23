# Git 协作流程参考

## 目录

- 先判断是否真的需要
- 给新手的默认选择
- 选择流程
- branch 与 worktree
- 推荐的最小流程
- 自动部署项目
- 并行 agent 任务
- 从直接修改 main 迁移
- 文档归属

## 先判断是否真的需要

检查：

- 有多少人或 coding agent 会同时修改仓库。
- `main` 是否触发自动部署。
- 是否存在测试、预发布和生产等多个环境。
- 发布是持续进行还是按固定版本窗口进行。
- 是否需要同时维护多个生产版本。
- 是否经常出现长周期功能与紧急修复并行。
- 团队是否具备维护复杂流程的能力。

不要因为“专业团队都这样做”就增加 branch 层级。流程必须解决已经存在或很快会出现的问题。

## 给新手的默认选择

不需要先学会所有 Git 工作流再开始：

- 一个人、一次只做一个任务、`main` 不会自动部署：保留一个稳定的 `main`，每个任务创建一个短期 branch；PR 可以按需要使用。
- 一个人或小团队、`main` 会自动部署：使用 GitHub Flow，通过短期 branch、PR 和 CI 合并，避免直接在 `main` 试验。
- 只有两个写入任务确实需要同时进行时才使用 worktree。
- 只有固定发布周期、多个环境或多个生产版本确实存在时，才考虑传统 Git Flow。

如果项目还没有 Git、只是一次性学习脚本，先做好备份和清晰提交即可，不要为了形式搭建复杂流程。

## 选择流程

| 情况 | 优先选择 | 特点 |
|---|---|---|
| 单人或小团队、`main` 持续部署、任务周期短 | GitHub Flow | 一个长期 `main`，任务使用短期 branch，通过 PR 和 CI 合并 |
| 团队成熟、提交很小、CI 完整、依赖 feature flag | trunk-based development | 频繁合并主干，branch 生命周期极短 |
| 固定发布周期、多个环境、同时维护多个版本 | 传统 Git Flow | 使用 `develop`、`release/*`、`hotfix/*`，管理成本较高 |
| 一次性实验或不会继续维护的脚本 | 简单 branch 或不增加流程 | 保持最低成本，但仍保留可恢复提交 |

自动部署到生产环境的单人 vibecoding 项目，默认优先 GitHub Flow，不要直接引入传统 Git Flow。

## branch 与 worktree

- branch 是独立的版本线，用来隔离任务和保留可审查的提交历史。
- worktree 是独立的文件目录，让多个 branch 可以同时保持检出状态。
- 串行完成一个任务时，只需要 branch，不一定需要 worktree。
- 两个任务并行、线上 hotfix 与未完成功能并行、多个 agent 任务同时运行时，使用不同 worktree。
- 不要让多个写入型 agent 任务直接修改同一个工作目录。

手动创建示例：

```bash
git worktree add ../project-worktrees/task-name -b codex/task-name
```

遵循仓库已有 branch 前缀。工具或团队存在默认约定时使用对应前缀，例如 Codex 可使用 `codex/`；不要把某个工具的前缀强制用于所有项目。

## 推荐的最小流程

```text
从最新 main 创建短期任务 branch
        ↓
修改代码、配置、测试和文档
        ↓
运行本地验证并提交
        ↓
推送并创建 PR
        ↓
CI 通过后合并 main
        ↓
部署和生产验证
        ↓
打 tag（需要发布版本时）
        ↓
删除 branch 和 worktree
```

建议规则：

- `main` 始终保持可部署。
- 一个独立目标对应一个短期 branch。
- branch 名说明目的，例如 `feat-search`、`fix-login`、`docs-structure`。已有工具或团队前缀时继续沿用。
- commit 应围绕一个可说明的变化，不混入无关文件。
- 即使只有一名开发者，也可以用 PR 集中检查 diff、CI 和部署内容。
- 小团队优先 squash merge，除非项目需要保留分支中的完整提交结构。
- 合并并验证后及时清理短期 branch 和 worktree。

## 自动部署项目

当 push 到 `main` 会部署生产环境时：

- 禁止把 `main` 当作试验区。
- 要求 CI 通过后才能合并。
- 禁止 force push。
- 默认通过 PR 合并；紧急流程也要留下可追踪 commit。
- 部署失败时必须明确回滚代码、依赖、配置、数据和资源分别怎样处理。
- 部署成功后再创建 release tag，不能只修改文档中的版本文字。

不要只在文档中写 branch protection。应检查 GitHub 或其他托管平台中的真实设置；无法访问时明确列为待配置项。

## 并行 agent 任务

- 创建任务前先判断它是否会写文件。
- 多个只读审计任务可以共享仓库；多个写入任务必须隔离。
- 每个并行写入任务使用独立 branch 和 worktree。
- 创建 worktree 时明确从默认 branch、现有 branch 还是当前 working tree 开始。
- 未提交修改不会自动出现在普通新 worktree 中，不要假设状态已经带过去。
- 合并前检查不同任务是否修改了相同文件或同一业务约束。

## 从直接修改 main 迁移

仓库已有未提交修改时：

1. 先运行 `git status`，区分本次修改、用户修改和临时文件。
2. 不要为了“清理”而丢弃或覆盖现有修改。
3. 内容属于同一目标时，可以在当前状态创建新的任务 branch，让修改随 working tree 进入该 branch。
4. 无关修改应保留在原处、分别提交或由用户决定归属，不能混入同一 commit。
5. 完成验证和第一个稳定提交后，再开始创建并行 worktree。
6. 配置 `main` 保护和 CI 后，才把新流程描述为已经落地。

## 文档归属

- `CONTRIBUTING.md`：面向人的 branch、commit、PR 和 review 流程。
- `AGENTS.md`：coding agent 必须遵守的隔离、命名、验证和文档同步规则。
- 运维文档：合并后部署、tag、回滚和生产验证。
- README：只保留协作入口链接，不复制整套流程。

小项目可以把简短规则放进 `AGENTS.md` 或运维文档，不必为了形式强行创建 `CONTRIBUTING.md`。
