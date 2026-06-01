# 别只做用户，去写扩展

> Pi Agent 扩展开发手记——从理解架构到动手写出五个真实扩展  
> 老谭 · 2026-06

---

## 目录

1. [缘起](#1-缘起)
2. [全局速览：我做了什么](#2-全局速览我做了什么)
3. [第一步：多模型 / 多服务商配置](#3-第一步多模型--多服务商配置)
4. [扩展一：/chat ↔ /code 模式切换](#4-扩展一chat--code-模式切换)
5. [扩展二：/context 上下文用量可视化](#5-扩展二context-上下文用量可视化)
6. [扩展三：routinai 兼容补丁](#6-扩展三routinai-兼容补丁)
7. [扩展四：/flow 工具执行可视化面板](#7-扩展四flow-工具执行可视化面板)
8. [扩展五：subagent 多代理协作工具](#8-扩展五subagent-多代理协作工具)
9. [技能（Skills）塑形工作流](#9-技能skills塑形工作流)
10. [自定义 Agent：thinker + executor + vision](#10-自定义-agentthinker--executor--vision)
11. [端到端工作流：从论文到部署](#11-端到端工作流从论文到部署)
12. [会话分析：量化自己的使用模式](#12-会话分析量化自己的使用模式)
13. [踩坑实录](#13-踩坑实录)
14. [总结与感悟](#14-总结与感悟)

---

## 1. 缘起

[Pi Coding Agent](https://github.com/earendil-works/pi-coding-agent) 是一个极简主义的终端编码助手。

它和其他编码 Agent（Claude Code、Codex CLI）不同——**核心极小，一切皆可扩展**。没有内置 MCP、没有子 Agent、没有 Plan Mode、没有权限弹窗。这些功能如果有需要，都由 TypeScript 扩展来实现。

---

## 2. 全局速览：我做了什么

围绕 Pi Agent 做了以下实践和探索：

| 方面 | 具体产出 |
|------|----------|
| **模型配置** | 对接 3 个服务商 8+ 个模型：volcengine/ark-code-latest、routinai-api/gpt-5.x、opencode-go/deepseek-v4-flash/pro、minimax |
| **扩展开发 × 5** | chat-mode.ts、context.ts、routinai-compat.ts、agent-flow.ts、subagent（官方例子的引用） |
| **Skills** | 安装 arxiv-search、read-arxiv-paper；自建 deploy-notes、webwright |
| **自定义 Agent** | 配置 executor（代码执行）、thinker（深度分析）、vision（图片理解）3 个 agent |
| **研究产出** | Agent 架构文档、Agent Harness 综述、成本优化调研、工作流权衡分析、CDP 详解等多份技术报告 |
| **幻灯片制作** | 用 HTML PPT skill 制作数份演示文稿并部署到 GitHub Pages |
| **工具建设** | 会话 token 统计脚本、用户行为分析报告、工作空间组织规则 |
| **总对话量** | ~67 个会话，大量深度交互 |

---

## 3. 第一步：多模型 / 多服务商配置

Pi Agent 原生支持 31+ Provider。我配置了三个来源：

### 3.1 `settings.json`

```json
{
  "defaultProvider": "opencode-go",
  "defaultModel": "deepseek-v4-flash",
  "defaultThinkingLevel": "high"
}
```

### 3.2 `models.json` —— 手动添加 Provider

```json
{
  "providers": {
    "volcengine": {
      "api": "anthropic-messages",
      "baseUrl": "https://api.example-volcengine.com/v1",
      "models": [{ "id": "ark-code-latest" }]
    },
    "routinai": {
      "api": "openai-responses",
      "baseUrl": "https://api.example-routinai.com/v1",
      "compat": { "thinkingFormat": "reasoning_effort" },
      "models": [
        { "id": "gpt-5.5" },
        { "id": "gpt-5.4" },
        { "id": "gpt-5.4-mini" },
        { "id": "gpt-5.3-codex" }
      ]
    }
  }
}
```

### 3.3 `auth.json` —— API 密钥

密钥用 macOS Keychain 管理的（routinai），或者直接写在 auth.json 中但也足够安全——因为这个文件位于 `~/.pi/` 下，不会被 git 跟踪。

### 🌟 关键发现

- **opencode-go/deepseek-v4-flash** 是我的主力模型，性价比极高（~$0.0005/会话）
- 不用的 Provider 配置不对会导致启动报错（API key 缺失），在 `models.json` 中发现后修复即可
- `opencode-go` 是一个把多家国产模型包装成 OpenAI 兼容接口的 proxy，使用体验流畅

---

## 4. 扩展一：/chat ↔ /code 模式切换

这是第一个动手写的扩展。灵感：有时候我只是想闲聊或问个概念问题，但完整的编码工具链（read、bash、edit、write、grep、find、ls）会让 Agent 过度"主动"。

### 4.1 设计

两个命令：

- `/chat` → 只保留 bash 工具，注入极简系统提示
- `/code` → 恢复全部默认工具和编码提示

### 4.2 实现

```typescript
// 核心逻辑
pi.registerCommand("chat", {
  handler: async (_args, ctx) => {
    savedTools = pi.getActiveTools();   // 保存现有工具集
    pi.setActiveTools(["bash"]);        // 只留 bash
    persistState();                      // 持久化到 session
  }
});
```

关键 API：

- `pi.setActiveTools(names)` —— 动态切换可用工具集
- `pi.on("before_agent_start", ...)` —— 拦截系统提示注入
- `pi.appendEntry()` —— 状态持久化，跨 `/tree` 导航也保持

### 4.3 部署演进

先在项目级 `.pi/extensions/` 下开发验证，稳定后迁到用户级 `~/.pi/agent/extensions/`。

### 🌟 关键发现

- `setActiveTools()` 让 Agent 的"行为能力"可编程控制，是实现模式切换的基础
- 状态持久化到 session 分支上，确保 `/tree` 导航后不会丢失聊天状态
- 这个扩展只有 ~130 行，清晰展示了扩展的基本骨架

---

## 5. 扩展二：/context 上下文用量可视化

模仿 Claude Code 的 `/context` 命令，展示当前上下文窗口的 token 消耗。

### 5.1 解决的问题

Agent 经常不理解自己用了多少上下文。我想知道：

- 系统提示 / 工具定义 / skills / 消息 各占多少 token
- 还剩多少空间
- 模型是谁

### 5.2 实现

```typescript
pi.registerCommand("context", {
  handler: async (_args, ctx) => {
    const usage = ctx.getContextUsage();
    const systemPrompt = ctx.getSystemPrompt();
    const activeTools = pi.getActiveTools();
    // ... 逐个分类估算 token 用量
    // 用 ctx.ui.custom() 渲染自定义面板
  }
});
```

关键 API：

- `ctx.getContextUsage()` —— 获取当前上下文信息
- `ctx.getSystemPrompt()` —— 获取系统提示
- `pi.getActiveTools()` —— 获取当前活跃工具集
- `pi.getCommands()` —— 获取所有注册的命令（含 skills 和扩展）
- `ctx.ui.custom()` —— 自定义 UI 渲染

### 5.3 效果

```
┌──────────────────────────────────────────────┐
│  Context Usage — deepseek-v4-flash           │
│  19.5k/128k tokens (15.2%)                   │
│                                              │
│  Messages       ████████░░░░░░░  12.3k  9.6% │
│  System prompt  ██░░░░░░░░░░░░░   3.2k  2.5% │
│  Built-in tools █░░░░░░░░░░░░░░   1.8k  1.4% │
│  Skills         ░░░░░░░░░░░░░░░   0.5k  0.4% │
│  Free space     ███████████████ 108.5k 84.8% │
│                                              │
│  Skills: arxiv-search, deploy-notes          │
│  Messages: 3 entries                         │
│                                              │
│  Press Enter or Esc to close                 │
└──────────────────────────────────────────────┘
```

### 🌟 关键发现

- `ctx.ui.custom()` 是 TUI 的"画布 API"——可以绘制任何字符界面
- `matchesKey()` 用来处理键盘事件，做关闭面板等交互
- 扩展中还可以访问 `ctx.sessionManager.getBranch()` 来获取完整的会话分支数据

---

## 6. 扩展三：routinai 兼容补丁

### 6.1 背景

使用 routinai provider 时遇到一个问题：assistant 消息中的 thinking 块会包含 `thinkingSignature`（类似于 OpenAI 的 `rs_...` ID），但在多轮对话中，`pi` 会把这些 ID 嵌入到后续请求的 input 数组中。而 routinai 的后端实际上没有持久化这些 item，所以拒绝这些 ID。

### 6.2 解决方案

在 `message_end` 事件中，仅针对 routinai provider，剥离 `thinkingSignature`：

```typescript
pi.on("message_end", (event, _ctx) => {
  const msg = event.message;
  if (msg.role !== "assistant" || msg.provider !== "routinai") return;

  let modified = false;
  const newContent = msg.content.map((block: any) => {
    if (block.type === "thinking" && block.thinkingSignature) {
      modified = true;
      const { thinkingSignature, ...rest } = block;
      return rest;
    }
    return block;
  });

  if (modified) {
    return { message: { ...msg, content: newContent } };
  }
});
```

### 🌟 关键发现

- `pi.on("message_end")` 可以**返回修改后的消息对象**来拦截并修复消息
- provider 兼容问题是使用非主流服务商时必然会遇到的
- 这个补丁只有 ~50 行，但解决了核心的多轮对话崩溃问题
- 类似的模式未来可能扩展到其他非标准 provider

---

## 7. 扩展四：/flow 工具执行可视化面板

这是我目前写得最复杂的扩展，做一个**非劫持式侧边面板**显示 Agent 的工具执行过程。

### 7.1 设计目标

现在 pi Agent 执行时屏幕刷刷刷往上滚动，执行完只看到最终结果，中间过程不可视。想要一个侧边面板实时显示：

- 正在执行的工具 / 状态 / 耗时
- 并行执行的分组关系（用树形分支线表示）
- 不拦截键盘输入（与编辑器互不干扰）

### 7.2 核心实现

```typescript
// 生命周期事件
pi.on("session_start", async () => { reset(); closePanel(); });
pi.on("agent_start", async () => { agentPromptIndex++; });
pi.on("turn_start", async () => { currentTurnIndex++; requestRender(); });

pi.on("tool_execution_start", async (event) => {
  // 检测是否并行（同一 turn 中有多个 running 的工具）
  const runningInTurn = state.filter(
    (e) => e.turnIndex === currentTurnIndex && e.status === "running",
  );
  const isParallel = runningInTurn.length > 0;

  state.push({
    id: event.toolCallId,
    name: event.toolName,
    args: fmtArgs(event.toolName, event.args),
    status: "running",
    turnIndex: currentTurnIndex,
    batchId: isParallel ? (runningInTurn[0].batchId ?? ++nextBatchId) : null,
    startedAt: Date.now(),
    durationMs: null,
  });
});

pi.on("tool_execution_end", async (event) => {
  const entry = state.find((e) => e.id === event.toolCallId);
  if (entry) {
    entry.status = event.isError ? "error" : "done";
    entry.durationMs = Date.now() - entry.startedAt;
  }
  requestRender();
});
```

### 7.3 非劫持 Overlay 的技术挑战

最大难点是 `ctx.ui.custom()` 默认是**劫持式**——会捕获键盘输入。但我的侧面板只需要展示信息，输入应该穿透到编辑器。

解决方案（写了好几版才搞定）：

```typescript
ctx.ui.custom<void>((tui, theme, _kb, done) => {
  const capturedTui = tui;
  const capturedTheme = theme;
  done();  // 立即弹出 custom controller
  setTimeout(() => openPanel(capturedTui, capturedTheme), 0);
  return {
    render: () => [],
    invalidate: () => {},
    handleInput: () => {},
  };
}, {
  overlay: true,
  overlayOptions: { anchor: "top-right", width: 1, height: 1 },
});
```

关键技巧：

1. `done()` 立即弹出 custom controller
2. `setTimeout(..., 0)` 在下一个 tick 创建独面板——此时 controller 已消失
3. `tui.showOverlay()` 的 `nonCapturing: true` 让输入穿透
4. 返回空面板让用户看不到这个临时 overlay

### 7.4 显示效果

```
┌──────────────────────────────────────────┐
│ ◆ A3 T5  24/30  ◌1                      │
│  5 ├◌ 1.2s bash Install dependencies     │
│  5 ├✓ 0.8s read config.json              │
│  5 └✓ 0.3s write output.txt              │
│  6   ✓ 1.5s grep error patterns          │
│  7   ◌2.3s bash Run tests...             │
│                                          │
│ /flow off                                │
└──────────────────────────────────────────┘
```

还在迭代中（多屏滚动时的渲染问题），但框架已经跑通。

### 🌟 关键发现

- `tui.showOverlay()` 的 `nonCapturing` 选项是实现侧面板的关键
- `tool_execution_start/update/end` 事件流可以精确追踪每个工具的执行
- TUI 的 render 函数是纯函数式的——把状态映射为字符行数组即可
- 并行检测算法：同一 turn 中同时 running 的工具视为并行

---

## 8. 扩展五：subagent 多代理协作工具

这是我从 pi 官方 SDK 示例直接使用的扩展。安装方式是软链接：

```
~/.pi/agent/extensions/subagent/
├── index.ts  →  pi SDK examples/extensions/subagent/index.ts
└── agents.ts →  pi SDK examples/extensions/subagent/agents.ts
```

### 8.1 功能

注册了一个 `subagent` 工具，支持三种模式：

| 模式 | 用法 | 场景 |
|------|------|------|
| **Single** | `{ agent: "thinker", task: "..." }` | 把单个任务委托给专门 Agent |
| **Parallel** | `{ tasks: [{agent:"vision", task:"..."}, ...] }` | 并发处理多个独立子任务 |
| **Chain** | `{ chain: [{agent:"thinker", task:"..."}, ...] }` | 链式传递，前者输出给后者 |

### 8.2 实际使用

```typescript
// 用 vision agent 看截图
subagent({
  agent: "vision",
  task: "分析这张图片 /path/to/screenshot.png"
})

// 并行分析多个论文
subagent({
  tasks: [
    { agent: "thinker", task: "分析论文 A" },
    { agent: "thinker", task: "分析论文 B" }
  ],
  agentScope: "user"
})
```

### 🌟 关键发现

- 每个 subagent 启动独立 `pi` 进程，完全隔离的上下文窗口
- 支持 `agentScope: "both"` 来同时加载用户级和项目级 Agent
- Chain 模式中 `{previous}` 占位符自动替换为上一步输出
- 并发上限 `MAX_CONCURRENCY=4`，防止资源耗尽
- 显示结果时自带 token 统计、耗时、tool call 展开等 TUI 渲染

---

## 9. 技能（Skills）塑形工作流

### 9.1 安装的技能

| Skill | 来源 | 用途 |
|-------|------|------|
| `arxiv-search` | langchain-ai/deepagents | 搜索 arXiv 论文 |
| `read-arxiv-paper` | karpathy/nanochat | 读取并总结 arXiv 论文 |
| `webwright` | 内置 skill | 浏览器自动化（Playwright） |
| `deploy-notes` | 自建 | 部署 HTML/MD 到 GitHub Pages |
| `searxng-search` | 用户级 | 通过本地 SearXNG 搜索 |
| `html-ppt` | 用户级 | 制作 HTML 幻灯片 |

### 9.2 自建 deploy-notes skill

这是我唯一自建的 skill，解决了"做完东西怎么发布"的问题。

工作流：

```
本地 HTML/MD → cp 到 notes/ 子目录 → git commit & push → 更新 index.md
```

skill 核心是约 60 行的 SKILL.md，定义了三个部署场景：

```
情况 A：已有目录 → 直接复制目录
情况 B：单个文件 → 确认目录名后复制
情况 C：用户指定名称 → 直接使用
```

它和我的 Git Pages 仓库（`<username>/notes`）紧密绑定，域名做了 CNAME。

### 🌟 关键发现

- Skills 本质是**README 式的可消费文档**——给 AI 阅读的操作手册
- SKILL.md 比传统脚本更灵活：它描述了**什么时候做什么事**，而非固定的指令
- 写好 skill 后，只需 `pi` 会话中说"部署"就能触发

---

## 10. 自定义 Agent：thinker + executor + vision

我按照 pi 的 agent 规范定义了三个 agent，用 TypeScript frontmatter + Markdown body 描述行为和约束。

### 10.1 executor —— 日常代码执行

```markdown
---
name: executor
description: 日常代码编写、修改、调试、文件操作
tools: read, bash, edit, write, grep, find, ls
model: opencode-go/deepseek-v4-flash
---

你是代码执行助手，负责日常开发任务...
```

### 10.2 thinker —— 深度分析

```markdown
---
name: thinker
description: 复杂分析、架构设计、技术方案评审
tools: read, grep, find, ls
model: opencode-go/deepseek-v4-pro
---

你只能读取代码，不能修改。如果需要修改代码，把方案交给 executor 执行。
```

### 10.3 vision —— 图片理解

```markdown
---
name: vision
description: 图片理解、截图分析、OCR
tools: read
model: opencode-go/qwen3.6-plus
---
```

### 10.4 协作模式

一个实际工作流示例：

```
用户: "你看一下这张截图里的报错信息"

pi (Default Agent):
  → subagent({ agent: "vision", task: "分析截图 /path/to/error.png" })
  → vision 返回错误描述
  → subagent({ agent: "thinker", task: "分析根因并修复方案" })
  → thinker 返回分析报告
  → subagent({ agent: "executor", task: "按方案修改代码" })
```

这就是 thinker + executor 的协作模式：**强模型规划，弱模型执行**。

### 🌟 关键发现

- Agent 定义就是 Markdown + frontmatter，非常简单
- `tools` 字段限制 Agent 的能力边界（thinker 只能读不能写）
- 不同 Agent 可以绑定不同的模型（vision 用视觉模型、thinker 用推理模型）
- 协作通过 subagent 工具编排，天然支持链式传递

---

## 11. 端到端工作流：从论文到部署

这是我反复实践的核心工作流：

```
arXiv 搜索 → 下载 PDF → 阅读总结 → 写技术文档 → 做 HTML PPT → 部署到 GitHub Pages
```

### 11.1 一个典型例子

```
# 1. 找论文
"帮我找一篇关于 agent token 成本优化的论文"
→ arxiv-search skill 搜索 → 找到 arXiv:2605.23929

# 2. 读论文
"读一下这篇论文"
→ read-arxiv-paper skill → 下载 PDF → 生成详细总结

# 3. 写技术文档
"把论文内容写成技术文档"
→ 生成 markdown 文档 → 存储到 docs/ 或对应目录

# 4. 做 PPT
"把这篇论文做成 HTML 幻灯片"
→ html-ppt skill → 生成 reveal.js 风格的 HTML

# 5. 部署
"部署到 GitHub Pages"
→ deploy-notes skill → cp → git push
→ 访问 https://<your-domain>/notes/xxx/
```

### 11.2 产出物一览

| 主题 | 文档 | PPT | 已部署 |
|------|------|-----|--------|
| Pi Agent 入门 | ✅ `.md` 调研报告 | ✅ HTML | ✅ |
| Agent 架构设计 | ✅ `agent-architecture.md` | - | ✅ |
| Agent Harness 综述 | ✅ 详细报告（86+ 页） | - | ✅ |
| 成本优化调研（83 篇论文） | ✅ report | - | ✅ |
| LLM 工作流权衡（论文 2605.23929） | ✅ 总结 | ✅ HTML | ✅ |
| CDP 协议详解 | - | ✅ HTML | ✅ |
| OpenAI Response API | - | ✅ HTML | ✅ |
| Recurrent Context Compression | - | ✅ HTML | ✅ |

### 🌟 关键发现

- 这个端到端流水线完全由 Agent + Skills 驱动，只需要自然语言指令
- 每个环节（搜索 → 阅读 → 写作 → 演示 → 部署）对应一个 Skill 或自定义 Agent
- 产出物归档到 session 对应目录，保持工作空间整洁（`AGENTS.md` 约定的规则）

---

## 12. 会话分析：量化自己的使用模式

### 12.1 token 统计脚本

因为好奇自己的使用量，让 Agent 写了一个 Python 脚本来分析所有会话：

```python
# token-analysis/pi_token_stats.py
# 遍历 sessions 目录下的所有 .meta.json 文件
# 按天统计每个模型的 token 使用量、缓存命中率、费用
```

### 12.2 行为分析报告

进一步让 Agent 读自己的全部对话日志，生成了一份行为模式分析报告。我的一些特征：

- **重度使用者**：67 会话，交互密集
- **"先说原理再动手"**：先问"这是啥原理"，决定深入后再让动手
- **性价比敏感**：主力用 deepseek-v4-flash，但也积极尝试新模型
- **迭代式工作**：PPT 要改 3+ 轮以上才满意
- **喜欢可视化**：经常用 vision agent 看截图确认结果

---

## 13. 踩坑实录

### 13.1 ⚠️ routinai thinkingSignature 问题

- **现象**：多轮对话时报错，API 拒绝 `rs_...` ID
- **根因**：pi 的 openai-responses provider 会引用 reasoning item ID，但 routinai 未持久化
- **解决**：写 routinai-compat.ts 扩展，在 `message_end` 事件中剥离 thinkingSignature

### 13.2 ⚠️ /flow 面板劫持输入

- **现象**：面板一切换就捕获键盘，无法在保持面板可见时输入
- **迭代**：至少改了三版
  - 第一版：`ctx.ui.custom()` 劫持式 → 无法输入
  - 第二版：用 `done()` 弹出 controller 后创建 overlay → 有时崩溃
  - 第三版：`done()` 后 `setTimeout(..., 0)` 创建 `nonCapturing` overlay → 稳定工作

### 13.3 ⚠️ Skill 冲突

- **现象**：启动时提示 `[Skill conflicts]`
- **根因**：多个 skill 定义了同名的 prompt template 或命令
- **解决**：检查 `skills-lock.json`，移除重复源

### 13.4 ⚠️ Volcengine API key 问题

- **现象**：启动时报错 `models.json error: "apiKey" is required`
- **根因**：Provider 配置不完整或 API key 未正确关联
- **解决**：在 `models.json` 中补充正确的 Provider 配置

### 13.5 ⚠️ 多屏滚动渲染问题

- **现象**：/flow 面板在多屏滚动时渲染异常
- **状态**：正在调试中

---

## 14. 总结与感悟

### 14.1 Pi Agent 的设计哲学 —— 真的和别家不一样

| 方面 | Claude Code | Pi Agent |
|------|-------------|----------|
| 扩展方式 | MCP 外部服务器 | TypeScript Extension API |
| 工具集控制 | MCP 注册 | 动态 `setActiveTools()` |
| 代理协作 | 内置 Agent 模式 | subagent 扩展提供 |
| 会话管理 | 线性对话 | 树形分支 + 压缩 |
| Skills 体系 | CLAUDE.md 指令 | SKILL.md 生态文件 |
| TUI 可定制 | 无 | 全开放 overlay/panel |
| 生命周期钩子 | 无 | 事件系统全暴露 |
| Provider 生态 | 仅 Anthropic | 31+ Provider 切换 |
| 开箱即用 | ✅ 即装即用 | ⚡ 需自行配置 |
| 定制天花板 | 低 | 高 |

Pi 的设计是"给你积木，你来搭"——它不预设你的工作流。

### 14.2 我的经验总结

```
如果你想要一个开箱即用的编码助手 → 用 Claude Code
如果你想要一个可以深度定制的 Agent 平台 → 用 Pi

Pi 的学习曲线更陡，但天花板更高。

实践下来，我最大的收获不是写了多少代码，
而是理解了 AI Agent 不是"魔法黑箱"，而是一套可以编程控制的系统。
```

### 14.3 下一步想尝试的

1. 完成 `/flow` 面板的滚动渲染修复
2. 给 Agent 写一个更完善的上下文压缩机制（参考 RCC 论文）
3. 探索 Agent 的 Thinker + Executor 自动编排（不用手动指定，让系统自动判断）
4. 更多 Provider 的自定义兼容补丁
5. 试着写一个更复杂的 Package

---

*本文档由 Agent 协作生成，来源包括会话记录、扩展代码、项目产出物和用户口述。*  
*归档于 `pi-agent-practice/`，2026-06-01。*
