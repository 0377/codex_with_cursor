# AI 安装说明

本文件是 `codex_with_cursor` 的仓库直装安装契约，给 AI 执行安装或更新时使用。安装源为本仓库 [https://github.com/0377/codex_with_cursor](https://github.com/0377/codex_with_cursor)，不经过插件市场。

## 默认交互策略

用户要求安装、集成或更新这套工作流时，默认零打扰执行：

1. 直接执行，不先把安装变成问答。
2. 如果检测到旧版脚本安装残留或旧版 `codex-with-cc` 插件，先清理再继续直装。
3. 默认执行用户级安装，除非用户明确要求项目级。
4. 如果宿主环境还没有安装 `codex` CLI，先自动安装官方 CLI，再继续后续步骤。
5. 如果还没有 `agent`（Cursor Agent CLI），先安装 Cursor CLI，再继续后续步骤。
6. 插件安装失败时停止并报告，不复制仓库文件、不恢复旧脚本、不写旧目录。
7. 必要时提醒用户重载插件列表或重启宿主。

## 目标

把本仓库安装为用户级 Codex 插件 `codex-with-cursor`，使所有 child-agent、subagent、sub-agent、child-thread、 subthread、delegation、worker-execution、子代理、子线程、多代理、委派、派工或执行层请求都触发 `$codex-with-cursor`。

Any user mention of child-agent, subagent, sub-agent, child-thread, subthread, delegation, worker-execution, or Chinese equivalents such as 子代理、子线程、多代理、委派、派工、执行层 is a workflow trigger.

触发后必须走：

```text
Codex 主线程 -> Codex spawn_agent 子线程 -> 已安装插件中的 delegate_to_cursor.* -> scripts/*.py -> Cursor Agent CLI
```

不要把 Codex 默认子代理流程、宿主内置 worker、直接运行 `agent`/`cursor`、或主线程直接执行 `delegate_to_cursor.*` 当作替代。

## 内部协议

插件 ID 为 `codex-with-cursor`。插件内部直接使用 workflow/task/run 协议：

- 每次用户请求对应一个 `WorkflowId`。
- 每个被拆出的子任务对应一个 `TaskId`。
- 每次 Cursor Agent 执行对应一个 `RunId`。
- 每个 worker 必须声明 `Role`，取值为 `planner`、`implementer`、`researcher`、`reviewer` 或 `final-verifier`。
- 当前 artifact schema 会生成 `workflow_<WorkflowId>.json`，用于聚合 task、run、scope、verification、review gate 和 final acceptance。
- 委派命令必须使用 task-file-only 形态：`-TaskFile`、`-WorkflowId`、`-TaskId`、`-Role`、`-SessionKey` 都是必填。
- TaskFile 必须包含 `Goal`、`Allowed Scope`、`Forbidden Actions`、`Acceptance Criteria`、`Verification`、`Report Requirements`。
- TaskFile 不能为空段、不能保留明显占位符，`Report Requirements` 必须列出完整报告标题；复杂任务派发前可先运行 `validate_delegate_task.*` 预检。
- 旧式 inline `-Task`、旧式 `-Mode`、隐式 session key fallback 都不保留。
- reviewer 必须额外传 `-ReviewForTaskId` 和 `-ReviewKind spec` 或 `-ReviewKind quality`。
- worker 报告必须使用 `Status / Role / Summary / Changed Files / Verification / Findings / Final Result / Risks Or Follow-ups`，并且 `Status` 与 `Final Result` 必须一致。
- 单次运行使用 `verify_delegate_run` 或 `verify_delegate_artifacts` 验证；整条工作流使用 `verify_delegate_workflow` 验证。
- implementer workflow 必须有 accepted `spec` reviewer、accepted `quality` reviewer 和 accepted `final-verifier`；非 dry-run 的 `DONE` 报告必须覆盖所有 `-Tests` 命令和结果；并行 implementer 的 `-Scope` 不能重叠。

### 三层命令参数（勿混用）

| 层级 | 入口 | 典型参数 | 是否 Cursor CLI |
|------|------|----------|-----------------|
| Codex 子线程 | `spawn_agent` | `model: gpt-5.4`, `reasoning_effort: medium`, `fork_context: false` | 否 |
| 委派包装器 | `delegate_to_cursor.*` | `-TaskFile`, `-WorkflowId`, `-TaskId`, `-Role`, `-SessionKey` 等 | 否 |
| Cursor 执行层 | `agent` | `--print`, `--output-format stream-json`, `--model`, `--resume`, `--yolo`, `--trust` | 是 |

- 未传 `-Model` 时，委派默认使用 `composer-2.5`（可用 `agent --list-models` 查看账号可用 ID 并覆盖）。
- `-Model` 仅映射为 `agent --model <id>`，与 Codex `spawn_agent` 的 `model` 无关。
- 运行时只解析 `agent` 命令，不回退到 `cursor` 可执行文件。
- 每次运行在 `config_<RunId>.json` 中记录 `lastCursorCliArgv` 便于排错。

插件声明 `./hooks/hooks.json`。宿主启用 Codex hooks 后，`SessionStart` 注入完整契约，`UserPromptSubmit` 遇到触发词时再次注入，`PreToolUse` 拦截直接 `agent`/`cursor`、主线程直接 `delegate_to_cursor.*`、缺少 `CODEX_CURSOR_CHILD_THREAD=1`、缺少 `-TaskFile`、缺少 workflow metadata、缺少 `-SessionKey`、旧式 `-Task`、旧式 `-Mode`、reviewer 缺少 review metadata、以及并行写任务无 `-Scope`。

## 分发源

唯一分发入口为本仓库（直装，不经过插件市场）：

```text
Repository: https://github.com/0377/codex_with_cursor
Plugin name: codex-with-cursor
```

## 旧版安装残留清理

安装前先检查并删除旧入口，避免旧插件与新插件同时存在。

### 1. 清理项目下旧安装产物

删除目标项目根目录下这些旧产物：

- `docs/codex_with_cc`
- `doc/codex_with_cc`
- `.codex/skills/codex-with-cc`
- `.codex/skills/codex-with-cursor`（若来自错误的手动复制且非插件安装）
- `AGENTS.md` 里的 `<!-- BEGIN CODEX_WITH_CC --> ... <!-- END CODEX_WITH_CC -->` 托管块

如果 `AGENTS.md` 删除托管块后变空，可以直接删除整个文件。

### 2. 清理用户级旧 skill 与旧插件

- 用户级旧 skill：`$HOME/.codex/skills/codex-with-cc`
- Windows：`$env:USERPROFILE\.codex\skills\codex-with-cc`
- 在 `~/.codex/config.toml` 中禁用或移除旧插件项 `codex-with-cc`、`codex-with-cc@aiskyhub`，以及仅为本插件添加的 aiskyhub 市场配置段

不要保留旧 skill 作为回退。

## Codex 安装协议

当前仓库只提供 Codex 插件入口。

### 1. 检查并安装 Codex CLI

先检查 `codex` 命令是否可用。

PowerShell：

```powershell
Get-Command codex -ErrorAction SilentlyContinue
```

macOS / Linux：

```bash
command -v codex
```

如果不存在：

```bash
npm i -g @openai/codex
```

安装完成后再次确认 `codex` 命令可用。若 `npm` 不存在或安装失败，直接报告失败并停止。

### 2. 检查并安装 Cursor Agent CLI

检查 `agent` 命令：

```bash
command -v agent
```

若不存在，按 Cursor 官方文档安装 CLI（例如 `curl https://cursor.com/install -fsS | bash`），并确认 `agent` 可用。无法安装则报告失败并停止。

### 3. 安装插件（本仓库直装）

按优先级选择一种方式（均安装插件 `codex-with-cursor`）：

**A. 已在当前仓库工作区**（目录内存在 `.codex-plugin/plugin.json`）：

```bash
codex plugin install "$(git -C /path/to/codex_with_cursor rev-parse --show-toplevel)" --scope user
```

将 `/path/to/codex_with_cursor` 换成实际 clone 路径；若命令就在仓库根目录执行，可用 `$(git rev-parse --show-toplevel)`。

**B. 从本仓库 GitHub 源安装：**

```bash
codex plugin install https://github.com/0377/codex_with_cursor --scope user
```

**C. 回退：clone 本仓库后本地路径安装：**

```bash
git clone https://github.com/0377/codex_with_cursor.git
codex plugin install /path/to/codex_with_cursor --scope user
```

检查 `~/.codex/config.toml` 是否包含并启用：

```toml
[plugins."codex-with-cursor"]
```

安装后如未即时生效，提示用户重载插件或重启 Codex。

### 4. 启用 Codex hooks 半硬门

```toml
[features]
codex_hooks = true
```

### 5. 定位已安装 workflow 根目录

`<installed-workflow-root>` 指已安装插件包内的 `skills/codex-with-cursor`，例如：

```text
<codex-home>/plugins/cache/.../skills/codex-with-cursor
```

### 6. 安装后自检

Windows：

```powershell
pwsh -NoProfile -File "<installed-workflow-root>\windows_scripts\test_delegate_runtime.ps1"
pwsh -NoProfile -File "<installed-workflow-root>\windows_scripts\test_delegate_session_pool.ps1"
```

macOS / Linux：

```bash
"<installed-workflow-root>/macos_scripts/test_delegate_runtime.sh"
"<installed-workflow-root>/macos_scripts/test_delegate_session_pool.sh"
```

dry-run 委派示例（项目内生成 `.codex/codex_with_cursor/cursor-delegate`）：

```powershell
$env:CODEX_CURSOR_CHILD_THREAD = '1'
pwsh -NoProfile -File "<installed-workflow-root>\windows_scripts\delegate_to_cursor.ps1" `
  -TaskFile .\.codex\codex_with_cursor\tasks\install-check\dry-run-install-verification.md `
  -WorkflowId install-check `
  -TaskId install-check-dry-run `
  -Role researcher `
  -SessionKey install-check `
  -Scope AGENTS.md `
  -DryRun
```

```bash
export CODEX_CURSOR_CHILD_THREAD=1
"<installed-workflow-root>/macos_scripts/delegate_to_cursor.sh" \
  -TaskFile ./.codex/codex_with_cursor/tasks/install-check/dry-run-install-verification.md \
  -WorkflowId install-check \
  -TaskId install-check-dry-run \
  -Role researcher \
  -SessionKey install-check \
  -Scope AGENTS.md \
  -DryRun
```

dry-run 成功后应看到 `config_<RunId>.json`、`status_<RunId>.json`、`prompt_<RunId>.md`、`cursor_<RunId>.md`、`workflow_install-check.json`。

可选：在仓库根目录执行 `python -m pytest tests/test_cursor_agent_cli_smoke.py -q`（需已安装 `pytest` 与 `agent`）做 Cursor CLI 冒烟校验。

## 失败处理

- 插件安装失败：直接报告并停止。
- 自检或 dry-run 失败：直接报告并停止。
- 不要复制仓库文件到 skill 目录作为回退。

## 安装或更新完成后告知用户

最终回复至少说明：

- 安装/更新是否成功。
- 是否清理了旧 `codex-with-cc` / marketplace 残留。
- `codex-with-cursor` 是否已安装并启用。
- 是否运行了 runtime 自检与 dry-run。
- 是否需要重载插件或重启 Codex。
- 未执行步骤须说明原因。

不要只说“好了”或“已完成”。

## 委派规则

```powershell
$env:CODEX_CURSOR_CHILD_THREAD = '1'
pwsh -NoProfile -File "<installed-workflow-root>\windows_scripts\delegate_to_cursor.ps1" `
  -TaskFile .\.codex\codex_with_cursor\tasks\<task-file>.md `
  -WorkflowId <workflow-id> `
  -TaskId <task-id> `
  -Role implementer `
  -SessionKey <stable-session-key> `
  -Scope <path> `
  -SessionMode PrimaryReuse `
  -BypassPermissions
```

```bash
export CODEX_CURSOR_CHILD_THREAD=1
"<installed-workflow-root>/macos_scripts/delegate_to_cursor.sh" \
  -TaskFile ./.codex/codex_with_cursor/tasks/<task-file>.md \
  -WorkflowId <workflow-id> \
  -TaskId <task-id> \
  -Role implementer \
  -SessionKey <stable-session-key> \
  -Scope <path> \
  -SessionMode PrimaryReuse \
  -BypassPermissions
```

reviewer 额外传 `-Role reviewer -ReviewForTaskId <id> -ReviewKind spec` 或 `quality`。

## 验证与产物

默认目录：

```text
.codex/codex_with_cursor/cursor-delegate
```

常见文件：`workflow_<WorkflowId>.json`、`cursor_<RunId>.md`、`status_<RunId>.json`、`config_<RunId>.json`、`prompt_<RunId>.md`、`stream_<RunId>.jsonl`、`trace_<RunId>.log`。

使用 `verify_delegate_run.*`、`verify_delegate_workflow.*`、`verify_delegate_chain.*` 验证。
