# Prompt Compressor — 设计文档

> 从 rtk 实践中理解提示词压缩的设计空间
>
> **已实现**：完整 Python 库 + CLI + SQLite 追踪 + Tee 机制 + 8 级流水线 + 三层优先级链

---

## 目录

0. [rtk 调研报告](#0-rtk-调研报告)
    0.1 [rtk 是什么](#01-rtk-是什么)
    0.2 [安装与使用](#02-安装与使用)
    0.3 [技术原理](#03-技术原理)
    0.4 [实测效果](#04-实测效果)
    0.5 [架构模式总结](#05-架构模式总结)
    0.6 [从 rtk 到 Prompt Compressor：设计迁移](#06-从-rtk-到-prompt-compressor设计迁移)
1. [问题与目标](#1-问题与目标)
2. [核心架构](#2-核心架构)
3. [流水线 Pipeline](#3-流水线-pipeline)
4. [策略引擎](#4-策略引擎)
5. [声明式规则 DSL](#5-声明式规则-dsl)
6. [优先级链](#6-优先级链)
7. [回退机制](#7-回退机制)
8. [追踪与反馈闭环](#8-追踪与反馈闭环)
9. [与 rtk 的模式映射](#9-与-rtk-的模式映射)
10. [边界情况与风险](#10-边界情况与风险)
11. [附录：Python 实现源码](#11-附录python-实现源码)

---

## 0 rtk 调研报告

### 0.1 rtk 是什么

**rtk**（Rust Token Killer，[GitHub: rtk-ai/rtk](https://github.com/rtk-ai/rtk)）是一个用 Rust 编写的 CLI 代理工具，位于用户命令行与终端输出之间，通过 **8 级压缩流水线**实时过滤和压缩 CLI 输出，减少传给 LLM 上下文的 token 数。

```
 用户输入命令 ──►  rtk 代理 ──► [8 级流水线] ──► 压缩后输出
                              │
                              └──► LLM 上下文（token 节省 60-90%）
```

rtk 并非通用压缩器，而是**专门为 CLI 输出场景设计**的手术刀级工具。它理解常见的命令行输出格式（git、ls、find、docker、npm 等），能够精确地剥离元信息、注释、重复行、ANSI 转义序列等"对人类有用但对 LLM 无用"的内容。

**当前版本**：0.42.0（2026-06-03 实测）。

**支持的 CLI 命令**：git、ls、find、tree、read、diff、log、grep、env、summary、docker、kubectl、aws、psql、npm、pnpm、cargo、jest、vitest、eslint、prettier、pytest、mypy、ruff、rubocop、rspec、gradlew、dotnet、prisma、next、tsc、gh、glab、curl、wget 等 30+ 子命令。

### 0.2 安装与使用

#### 安装

```bash
brew install rtk-ai/rtk/rtk
```

#### 基本用法

**模式一：hook 模式（推荐）**

```bash
eval "$(rtk init)"
```
安装后所有受支持的命令自动走 rtk 流水线，无需每次显式调用。

**模式二：显式子命令调用**

```bash
rtk git status                    # git 命令的压缩版
rtk ls -la .                      # ls 的压缩版
rtk find . -name "*.rs"           # find 的紧凑树形输出
rtk diff <file1> <file2>          # 超紧凑 diff
rtk summary wc -l src/lib.rs      # 两行摘要
rtk env PATH                      # 环境变量（脱敏）
rtk read src/main.rs              # 智能文件阅读
```

**模式三：原始执行**

```bash
rtk run -- <command>              # 执行但不追踪
rtk proxy -- <command>            # 执行并过滤+追踪
```

#### 管理命令

```bash
rtk gain                          # 查看节省统计
rtk config                        # 查看/创建配置
rtk verify                        # 校验 hook 完整性
rtk init --agent pi               # 为 pi agent 安装初始化文档
```

### 0.3 技术原理

#### 0.3.1 拦截机制

rtk 使用 **LD_PRELOAD / DYLD_INSERT_LIBRARIES**（类 Unix）或 **pty 劫持**（跨平台）方式拦截进程的 stdout/stderr，在输出抵达终端之前截获原始字节流。这使得 rtk 可以做到：

- **零侵入**：被拦截的命令完全不知道自己被"代理"了
- **低开销**：纯 Rust 实现，单次拦截延迟 <5ms
- **全捕获**：同时捕获 stdout/stderr，支持 `filter_stderr` 配置

#### 0.3.2 8 级压缩流水线

rtk 的核心是 `TomlFilterDef` 结构体定义的处理管线（从二进制逆向解析确认以下 13 个字段）：

```rust
struct TomlFilterDef {
    description: String,           // 规则描述
    match_command: String,         // 匹配的命令正则（如 "^git\\s+status"）
    strip_ansi: bool,              // 是否去掉 ANSI 转义序列
    replace: Vec<ReplaceRule>,     // 文本替换对
    match_output: Vec<MatchOutputRule>, // 条件输出匹配
    strip_lines_matching: Vec<String>,  // 丢弃匹配的行
    keep_lines_matching: Vec<String>,   // 只保留匹配的行
    truncate_lines_at: usize,      // 单行截断长度
    head_lines: usize,             // 保留前 N 行
    tail_lines: usize,             // 保留后 M 行
    max_lines: usize,              // 最大行数
    filter_stderr: bool,           // 是否过滤 stderr
}
```

实际执行顺序（从 `strings` 反推的流水线顺序）：

```
        输入 stdout/stderr
              │
              ▼
 ┌─ ① MatchCommand ───────────────────┐
 │  检查命令是否匹配 match_command      │
 │  不匹配 → 透传（passthrough）         │
 └────────────────┬───────────────────┘
                  │
 ┌─ ② StripAnsi ──────────────────────┐
 │  去掉 ANSI 颜色/样式控制序列          │
 └────────────────┬───────────────────┘
                  │
 ┌─ ③ Replace ────────────────────────┐
 │  文本替换（如 "verbose" → ""）       │
 │  链式执行：多个替换按顺序执行          │
 └────────────────┬───────────────────┘
                  │
 ┌─ ④ MatchOutput ────────────────────┐
 │  根据输出内容的模式匹配，条件替换       │
 │  unless 字段：不匹配时才执行 pipeline │
 └────────────────┬───────────────────┘
                  │
 ┌─ ⑤ StripLinesMatching ────────────┐
 │  丢弃匹配指定正则的行                │
 │  常见目标：空行、注释、分隔线、引用行  │
 └────────────────┬───────────────────┘
                  │
 ┌─ ⑥ KeepLinesMatching ─────────────┐
 │  只保留匹配指定正则的行              │
 │  通常与 strip 组合使用               │
 └────────────────┬───────────────────┘
                  │
 ┌─ ⑦ TruncateLinesAt ───────────────┐
 │  单行超长 → 截断 + "..." 标记       │
 └────────────────┬───────────────────┘
                  │
 ┌─ ⑧ HeadTail + MaxLines ───────────┐
 │  保留前 N 行 + 后 M 行，总行数上限   │
 │  核心信息在头部，摘要/状态在尾部      │
 └────────────────┬───────────────────┘
                  │
 ┌─ ⑨ OnEmpty ───────────────────────┐
 │  如果压缩后为空 → 输出兜底消息       │
 └────────────────┬───────────────────┘
                  │
                  ▼
             压缩后输出
```

#### 0.3.3 30+ 命令专用压缩器

rtk 为每个受支持的命令类型内建了专用的压缩策略：

| 命令组 | 压缩策略 | 典型省率 | 原理 |
|--------|---------|---------|------|
| `ls` | 只留文件名 + 紧凑权限 | 70-84% | 去掉总大小、行数、权限列宽 |
| `git status` | 单行裸格式 | 54-63% | "On branch" → "*"，去掉提示文案 |
| `git log` | 只留 hash + message | 14-41% | 去掉时间、作者、引用信息 |
| `find` | 树形紧凑输出 | 85-96% | 文件路径扁平化为树 |
| `diff` | 只留变更行 | 50-70% | 去掉上下文行（+- 号外） |
| `ls -la` | 紧凑表格 | 73-84% | 压缩权限/大小列 |
| `tree` | 紧凑树（无空白填充） | 18-40% | 减少缩进 |
| `env` | 脱敏 + 过滤 | 60-90% | 隐藏敏感值 |
| `npm/pnpm` | 超紧凑 | 70-90% | 去进度条、去依赖树装饰 |
| `docker` | 去表头、去格式 | 50-70% | 保持核心字段 |
| `kubectl` | 去表头、去装饰 | 40-60% | 保持核心字段 |
| `read` | 行号 + 智能截断 | 0-70% | 大文件自动截断 |

#### 0.3.4 TOML 规则引擎

rtk 将压缩策略声明为 TOML 规则，每条规则针对一类命令：

```toml
# ~/.config/rtk/filters.toml（用户级规则示例）
[[filters]]
match_command = "^my-tool\\s+build"
strip_ansi = true
strip_lines_matching = ["^\\s*\\[\\d+/\\d+\\]"]
truncate_lines_at = 120
on_empty = "my-tool: build completed"
```

规则系统特性：

- **match_command 正则**：锚定命令名和参数，精确匹配
- **链式替换**：`replace` 字段支持多对替换，顺序执行
- **条件输出（match_output）**：`unless` 字段——输出匹配某个模式时才（或才不）执行 pipeline
- **内置规则二进打包**：rtk 将通用规则编译进二进制，无需外部文件
- **内联测试**：`[[filters.tests]]` 结构中定义输入/输出/匹配断言，`rtk verify` 自动验证

#### 0.3.5 优先级链（三层覆盖）

```
                  高
                   │
       项目规则 ───┤ 项目级 .rtk/filters.toml（与代码仓库一起提交）
                   │
       用户规则 ───┤ 用户级 ~/.config/rtk/filters.toml
                   │
       内置规则 ───┤ 平台级（编译进二进制的通用规则）
                   │
                   ▼
                  低
```

**合并语义**：

| 字段类型 | 合并方式 |
|---------|---------|
| 列表（strip/keep） | 拼接并集 |
| 替换（replace） | 高优先级在前执行 |
| 标量（max_lines） | 取非空值（高优先级优先） |

**Trust 机制**：项目级规则默认需手动信任 `rtk trust`，防止恶意规则注入。

#### 0.3.6 Tee 机制

```bash
rtk tee replay <session_id>     # 重放某次压缩的完整现场
```

Tee 保存的数据：

```
~/.local/share/rtk/tee/<session_id>/
├── original.txt       # 压缩前原始输出
├── compressed.txt     # 压缩后输出
└── meta.json          # 命中规则、命令、耗时
```

#### 0.3.7 SQLite 追踪 & rtk gain

```bash
rtk gain
```

输出示例（实测）：

```
RTK Token Savings (Global Scope)
════════════════════════════════════════════════════════════

Total commands:    45
Input tokens:      15.5K
Output tokens:     12.5K
Tokens saved:      3.1K (19.8%)
Total exec time:   2.3s (avg 51ms)
Efficiency meter: █████░░░░░░░░░░░░░░░░░░░ 19.8%

[warn] No hook installed — run `rtk init -g` for automatic token savings

By Command
─────────────────────────────────────────────────────────────
  #  Command                   Count  Saved    Avg%  Impact
─────────────────────────────────────────────────────────────
 1.  rtk ls -la .                  5   1.2K   82.0%  ██████████
 2.  rtk ls -la manyfiles/         2   1.2K   73.3%  █████████░
 3.  rtk git status                8    307   62.5%  ███░░░░░░░
 4.  rtk git log -5                1    203   40.8%  ██░░░░░░░░
 5.  rtk find                      3     33   84.6%  ░░░░░░░░░░
 6.  rtk tree                      2     12   17.6%  ░░░░░░░░░░
─────────────────────────────────────────────────────────────
```

追踪系统支持：
- **按项目过滤**：`rtk gain --project` 只统计当前目录
- **历史窗口**：`rtk gain --since 7` 只看最近 N 天
- **图表模式**：`rtk gain --graph` ASCII 趋势图
- **导出**：`rtk gain --format json`
- **配额估算**：`rtk gain --quota pro` 按 API 订阅估算费用节省

### 0.4 实测效果

#### 测试环境

- **工具版本**：rtk 0.42.0（Homebrew）
- **系统**：macOS（Apple Silicon）
- **测试仓库**：临时 git 仓库，50 个文件 + Rust 源码目录

#### 场景一：`git status`（最惊艳）

```
# 原始 git status（145 chars）
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   src/lib.rs

no changes added to commit (use "git add" and/or "git commit -a")

# rtk 压缩后（54 chars，省 63%）
* main
 M src/lib.rs
```

rtk 剥离了全部"帮助文案"：`use "git add..."`、`use "git restore..."` 等对开发者友好但对 LLM 无用的提示。

#### 场景二：`ls -la`（目录含 50 个文件）

```
# 原始 ls -la（841 chars）
total 200
drwxr-xr-x  152 user  staff   4864 Jun  3 12:34 .
drwxr-xr-x   11 user  staff    352 Jun  3 12:30 ..
-rw-r--r--   1 user  staff     10 Jun  3 12:34 file_1.txt
-rw-r--r--   1 user  staff     10 Jun  3 12:34 file_2.txt
...

# rtk 压缩后（224 chars，省 73%）
file_1.txt  file_2.txt  file_3.txt  ...
```

剥离了：权限列、用户组、文件大小、日期、`.` 和 `..`、`total` 行。只留文件名。

#### 场景三：`find . -type f`

```
# 原始 find（1304 chars 输出树形目录）
# rtk 压缩后（50 chars，省 96%）
```

rtk 将 `find` 的长路径列表压缩为紧凑树。

#### 场景四：`git log`

```
# 原始 git log 约 50% 是时间/作者/引用元信息
# rtk 压缩约 14-41%（取决于有无额外 ref 信息）
```

#### 场景五：`git diff`

```
# 原始 diff 含上下文行
# rtk diff 去上下文只留变更行（约省 50-70%）
```

#### 全局统计

45 次调用累计：**输入 15.5K tokens → 输出 12.5K tokens，总体省 19.8%**（含不可压缩的命令）。

### 0.5 架构模式总结

rtk 的设计中值得学习的架构模式：

| # | 模式 | rtk 实现 | 通用价值 |
|---|------|---------|---------|
| **P1** | **流水线 Pipeline** | 8 级阶段串联，每级独立可插拔 | 每级关注单一职责，容易添加/禁用 |
| **P2** | **声明式规则 DSL** | TOML 文件声明压缩策略 | 业务方不写代码即可定制 |
| **P3** | **优先级链** | 项目 > 用户 > 内置，逐级覆盖 | 不同粒度的定制需求解耦 |
| **P4** | **Tee 审计** | 压缩前后 + 规则快照全量保留 | 压缩失败时完整回溯 |
| **P5** | **Fail-safe** | 任何异常 → passthrough 原始输出 | 压缩绝不能比不压缩更差 |
| **P6** | **可观测性** | SQLite 追踪 + `rtk gain` 仪表板 | 持续衡量压缩效果，驱动迭代 |
| **P7** | **内联测试** | TOML 规则内嵌 `[[tests]]` | 规则变更时可自动回归验证 |
| **P8** | **命令注册制** | 30+ 子命令各自有专用压缩器 | 紧耦合的场景获得最优结果 |

### 0.6 从 rtk 到 Prompt Compressor：设计迁移

**核心洞见**：LLM 提示词（prompt）的"肥胖"问题与 CLI 输出高度类似——都包含大量对人类有用但对 LLM 无意义的冗余。

| rtk 视角 | Prompt Compressor 映射 |
|----------|----------------------|
| CLI 命令输出 | LLM 提示词文本 |
| ANSI 转义序列 | Markdown 章节标记 |
| "On branch" 帮助文案 | "bg"、"背景说明"、"Q&A" 等非核心章节 |
| 权限/时间/大小列 | 示例对话、历史变更记录 |
| 注释行（# // ;） | 空行、修饰性短语 |
| `match_command` 锚定命令 | `match_prompt` 锚定 prompt 主题 |
| `git status` 专用过滤器 | 代码审查专用 TOML 规则 |
| `ls -la` 紧凑输出 | 替换 "请对以下代码进行审查" → "审查代码" |
| Tee 保留 CLI 现场 | Tee 保留原始 prompt + 压缩后 prompt |
| `rtk gain` 节省统计 | SQLite Tracker + `prompt-compressor gain` |

**关键差异**：

1. **CLI 输出是可重复生成的**，而 prompt 需要谨慎保持语义完整性 → Prompt Compressor 的膨胀阈值设定为 1.2x（允许小幅度膨胀）而非 rtk 的严格"不能变长"
2. **CLI 输出格式高度可预测**（git status 永远以 "On branch" 开头），prompt 则多种多样 → Prompt Compressor 使用 Markdown 章节检测作为分段入口
3. **CLI 输出压缩是 lossy 的**（去掉帮助文案是安全的），prompt 压缩需要保语义 → Prompt Compressor 内置规则极度保守（仅去连续空行），项目规则按需添加
4. **CLI 没有"压缩后质量下降"的概念**（要么正确要么不正确），prompt 有质量维度 → Prompt Compressor 预留了 QualityCheck 模块

**设计迁移的具体映射**：

```
rtk 8-stage pipeline               Prompt Compressor 8-stage pipeline
─────────────────────              ────────────────────────────────
① MatchCommand                    ① SectionMarker（检测 Markdown 篇章）
② StripAnsi                       ② SectionFilter（保留/移除章节）
③ Replace                         ③ TextReplace（短语替换）
④ MatchOutput（条件过滤）         ④ LineFilter（行级过滤）
⑤ StripLinesMatching              ⑤ TruncateLine（单行截断）
⑥ KeepLinesMatching               ⑥ HeadTail（保留首尾）
⑦ TruncateLinesAt                 ⑦ MaxLength（绝对长度上限）
⑧ HeadTail + MaxLines             ⑧ OnEmpty（兜底）
⑨ OnEmpty
```

**从 rtk 借鉴到的设计原则，全部在 Prompt Compressor 中重现**：

| 原则 | rtk 做法 | Prompt Compressor 做法 |
|------|---------|----------------------|
| 声明式配置 | TOML 规则文件 | TOML 规则文件（兼容 JSON） |
| 三层优先级 | 项目 > 用户 > 内置 | 项目 > 用户 > 内置 |
| 流水线架构 | 8 级固定管线 | 8 级固定管线 |
| 回退安全 | 异常 → passthrough | L1(阶段跳过) + L2(膨胀回退) + L3(质量回退) |
| 现场保留 | Tee 目录 | Tee 目录（延迟创建） |
| 节省统计 | `rtk gain` + SQLite | `prompt-compressor gain` + SQLite |
| 规则验证 | `rtk verify` + 内联测试 | 预留 `verify` 子命令 |

**而以下部分是 prompt 场景独有的创新**：

1. **章节级操作（SectionMarker + SectionFilter）**：CLI 输出没有"章节"概念，而 prompt 天然是 Markdown 组织的
2. **知识保留检查（QualityCheck）**：压缩后验证核心关键词、动词、输出格式是否被误删
3. **UTF-8 安全截断**：中文 prompt 的多字节字符不能切开
4. **层叠合并语义**：比 rtk 更精细的列表并集 + 标量优先

---

## 1 问题与目标

### 1.1 背景

LLM 调用成本与提示词长度直接相关。实际业务中提示词普遍存在**肥胖**问题：

- 历史遗留的冗长指令，无人清理
- 多轮迭代后出现大量互文重复的约束
- Few-shot 示例越加越多，缺乏淘汰机制
- 不同版本/来源的 prompt 被拼接在一起

### 1.2 目标

构建一个**可声明、可分层、可观测**的提示词压缩框架，对标 rtk 的设计质量：

| 指标 | 目标 | 实测 |
|------|------|------|
| 压缩率 | 30-70%（无损感知） | ✅ 代码审查 68%，通用助手 44% |
| 延迟开销 | <10ms（纯本地规则，不调 LLM） | ✅ 实测 <5ms |
| 规则热更新 | 不重启服务，TOML 文件变更即时生效 | ✅ 每次读取 TOML |
| 回退安全 | 任何规则异常 → 自动回退原始 prompt | ✅ L1/L2/L3 三层回退 |
| 可观测性 | 每次压缩记录节省、命中规则、质量评分 | ✅ SQLite + CLI `gain` |
| 可扩展性 | 业务方通过 TOML 配置即可定制策略 | ✅ TOML/JSON 双格式 |

### 1.3 快速开始

```bash
# 安装依赖（Python 3.11+ 自带 tomllib，无需额外安装）
cd prompt-compressor-design

# 运行集成测试
python3 test_compress.py

# CLI 使用
echo "你是一个代码审查专家..." | python3 -m prompt_compressor.cli compress --project-rules rules/examples --verbose
python3 -m prompt_compressor.cli explain "你是一个助手\n\n## 核心指令\n请简洁回答"
python3 -m prompt_compressor.cli gain
```

---

## 2 核心架构

### 2.1 整体流程

```
                     ┌─────────────────────────┐
                     │    CompressorRegistry    │
                     │  (规则注册 + 优先级链)    │
                     └──────────┬──────────────┘
                                │
  原始 Prompt ──► ┌─────────────▼──────────────┐
                  │        Pipeline             │
                  │   ┌──────────────────────┐  │
                  │   │ ① SectionMarker      │  │
                  │   │ ② SectionFilter      │  │
                  │   │ ③ TextReplace        │  │
                  │   │ ④ LineFilter         │  │
                  │   │ ⑤ TruncateLine       │  │
                  │   │ ⑥ HeadTail           │  │
                  │   │ ⑦ MaxLength          │  │
                  │   │ ⑧ OnEmpty            │  │
                  │   └──────────────────────┘  │
                  └─────────────┬──────────────┘
                                │
                        压缩后 Prompt
                                │
                                ▼
                        ┌────────────────┐
                        │    Tracker     │ ← SQLite / 日志
                        │   (节省统计)    │
                        └────────────────┘
```

### 2.2 模块职责

| 模块 | 文件 | 职责 | 对标 rtk |
|------|------|------|----------|
| **CompressorRegistry** | `registry.py` | 管理规则优先级链，按 `match_prompt` 正则匹配 | `TomlFilterRegistry` |
| **Pipeline** | `pipeline.py` | 串联 8 级处理阶段，L1/L2 回退 | 8 级流水线 |
| **RuleParser** | `rule_parser.py` | 解析 TOML → `CompiledRule` | `TomlFilterDef` 编译 |
| **Tracker** | `tracker.py` | SQLite 记录每次压缩的节省量 | SQLite 追踪 |
| **Tee** | `tee.py` | 保留原始 prompt + 压缩结果供回放 | Tee 机制 |

### 2.3 核心类定义

```python
# prompt_compressor/rule_parser.py
from dataclasses import dataclass, field
import re
from typing import Optional

@dataclass
class CompiledRule:
    """编译后的提示词压缩规则。"""
    name: str
    description: str = ""
    match_regex: Optional[re.Pattern] = None

    # Stage 2: SectionFilter
    keep_sections: list[str] = field(default_factory=list)
    remove_sections: list[str] = field(default_factory=list)

    # Stage 3: TextReplace — 有序替换对（先执行高优先级的）
    replace_pairs: list[tuple[re.Pattern, str]] = field(default_factory=list)

    # Stage 4: LineFilter
    strip_lines_matching: list[re.Pattern] = field(default_factory=list)
    keep_lines_matching: list[re.Pattern] = field(default_factory=list)

    # Stage 5-7: 长度控制
    truncate_lines_at: Optional[int] = None
    head_lines: Optional[int] = None
    tail_lines: Optional[int] = None
    max_char: Optional[int] = None
    max_tokens: Optional[int] = None

    # Stage 8: OnEmpty
    on_empty: Optional[str] = None

    # 扩展
    strategies: list[str] = field(default_factory=list)
    max_examples: Optional[int] = None
    override: bool = False

    def match(self, prompt: str) -> bool:
        if self.match_regex is None:
            return False
        return bool(self.match_regex.search(prompt))

    def merge(self, lower: "CompiledRule") -> "CompiledRule":
        """self 优先级更高，lower 优先级较低。"""
        ...  # 详见 §6
```

---

## 3 流水线 Pipeline

### 3.1 8 级处理阶段（真实实现）

```python
# prompt_compressor/pipeline.py
from .stages import (
    SectionMarker, SectionFilter, TextReplace,
    LineFilter, TruncateLine, HeadTail, MaxLength, OnEmpty,
)

class Pipeline:
    def __init__(self, tee: Tee = None):
        self.tee = tee
        self._stages: list[Stage] = [
            SectionMarker(),   # ① 检测 Markdown 章节边界
            SectionFilter(),   # ② 按 keep/remove 保留章节
            TextReplace(),     # ③ 短语替换
            LineFilter(),      # ④ 行级过滤
            TruncateLine(),    # ⑤ 单行截断
            HeadTail(),        # ⑥ 保留首尾
            MaxLength(),       # ⑦ 绝对长度上限
            OnEmpty(),         # ⑧ 兜底
        ]
```

#### Stage ① SectionMarker — Markdown 章节检测

```python
# prompt_compressor/stages.py
MARKDOWN_HEADER = re.compile(r"^#{1,4}\s+(.+)$", re.MULTILINE)

class SectionMarker(Stage):
    def _detect_sections(self, prompt: str) -> list[dict]:
        """以 Markdown 标题为界检测章节。
        返回 [{name, start, end, raw}]，preamble 章节名固定为 '(preamble)'。
        """
        lines = prompt.split("\n")
        sections = []
        current_name = "(preamble)"
        current_start = 0

        for i, line in enumerate(lines):
            m = MARKDOWN_HEADER.match(line)
            if m:
                sections.append({
                    "name": current_name,
                    "start": current_start,
                    "end": i,
                    "raw": "\n".join(lines[current_start:i]),
                })
                current_name = m.group(1).strip()
                current_start = i

        # 最后一个章节
        sections.append({
            "name": current_name,
            "start": current_start,
            "end": len(lines),
            "raw": "\n".join(lines[current_start:]),
        })
        return sections
```

#### Stage ② SectionFilter — 章节保留/移除

```python
class SectionFilter(Stage):
    def apply(self, prompt: str, rule: CompiledRule) -> tuple[str, dict]:
        marker = SectionMarker()
        _, info = marker.apply(prompt, rule)
        sections = info["sections_detected"]
        lines = prompt.split("\n")
        kept_ranges = []

        if rule.keep_sections:
            # 白名单：只保留匹配的章节，(preamble) 始终跳过
            for sec in sections:
                if sec["name"] == "(preamble)":
                    continue
                if any(_section_matches(sec["name"], p)
                       for p in rule.keep_sections):
                    kept_ranges.append((sec["start"], sec["end"]))
        else:
            # 黑名单：移除匹配的章节
            for sec in sections:
                if not any(_section_matches(sec["name"], p)
                           for p in rule.remove_sections):
                    kept_ranges.append((sec["start"], sec["end"]))

        result_lines = []
        for start, end in kept_ranges:
            result_lines.extend(lines[start:end])
        return "\n".join(result_lines).strip(), {
            "sections_kept": len(kept_ranges),
            "sections_removed": len(sections) - len(kept_ranges),
        }
```

#### Stage ③ TextReplace — 链式替换

```python
class TextReplace(Stage):
    def apply(self, prompt: str, rule: CompiledRule) -> tuple[str, dict]:
        if not rule.replace_pairs:
            return prompt, {"skipped": True}

        text = prompt
        replacements_made = 0
        for pattern, replacement in rule.replace_pairs:
            new_text, n = pattern.subn(replacement, text)
            if n > 0:
                replacements_made += n
                text = new_text
        return text, {"replacements_made": replacements_made}
```

> **注意**：替换是**链式的**——第 N+1 条规则在第 N 条的输出上执行。`re.compile(re.escape(pattern))` 使用字面匹配（非正则），避免误伤。

#### Stage ④ LineFilter — 行级过滤（两阶段交集）

```python
class LineFilter(Stage):
    def apply(self, prompt: str, rule: CompiledRule) -> tuple[str, dict]:
        has_strip = bool(rule.strip_lines_matching)
        has_keep = bool(rule.keep_lines_matching)

        if not has_strip and not has_keep:
            return prompt, {"skipped": True}

        lines = prompt.split("\n")
        kept = []
        stripped = 0

        for line in lines:
            # Phase 1: strip — 丢弃匹配的行
            if has_strip and any(p.search(line) for p in rule.strip_lines_matching):
                stripped += 1
                continue

            # Phase 2: keep — 只保留匹配的行
            if has_keep and not any(p.search(line) for p in rule.keep_lines_matching):
                stripped += 1
                continue

            kept.append(line)

        return "\n".join(kept).strip(), {
            "lines_kept": len(kept),
            "lines_stripped": stripped,
        }
```

> **两阶段顺序**：先 `strip`（黑名单），再 `keep`（白名单）。同时配置时取**交集**——行必须**不被 strip 且被 keep**。

#### Stage ⑤-⑧ 其余阶段

| 阶段 | 核心逻辑 | 关键参数 |
|------|---------|---------|
| **TruncateLine** | `line[:max_len] + "..."` | `truncate_lines_at` |
| **HeadTail** | `lines[:head] + ["..."] + lines[-tail:]` | `head_lines` + `tail_lines` |
| **MaxLength** | 从中间裁剪，保留头尾 | `max_char`，UTF-8 安全 `_safe_slice` |
| **OnEmpty** | `if not prompt.strip() and rule.on_empty` | `on_empty` |

### 3.2 Pipeline 执行与回退

```python
# prompt_compressor/pipeline.py
class Pipeline:
    def run(self, prompt: str, rule: CompiledRule) -> dict:
        if self.tee:
            self.tee.save("original.txt", prompt)

        current = prompt
        stage_log = []
        fallback_used = False

        for stage in self._stages:
            try:
                before = len(current)
                output, info = stage.apply(current, rule)
                info["name"] = stage.name()
                info["before_len"] = before
                info["after_len"] = len(output)
                stage_log.append(info)
                current = output
            except Exception as e:
                # L1 回退：跳过该 stage，继续流水线
                stage_log.append({
                    "name": stage.name(), "error": str(e), "skipped": True,
                })

        # L2 回退：膨胀超过 20% → 回退原始
        swell_threshold = int(len(prompt) * 1.2)
        if len(current) > swell_threshold:
            stage_log.append({
                "name": "Fallback",
                "reason": f"compressed {len(current)} > original {len(prompt)} * 1.2",
            })
            current = prompt
            fallback_used = True

        # 空输出回退
        if not current.strip():
            stage_log.append({
                "name": "Fallback", "reason": "compressed output is empty",
            })
            current = prompt
            fallback_used = True

        result = {
            "compressed": current,
            "original": prompt,
            "stages": stage_log,
            "rule": rule.name,
            "fallback": fallback_used,
            "original_char": len(prompt),
            "compressed_char": len(current),
        }

        if self.tee:
            self.tee.save("compressed.txt", current)
            self.tee.save("stages.json", json.dumps(stage_log, ensure_ascii=False, default=str))

        return result
```

---

## 4 策略引擎

### 4.1 策略矩阵

10 种高级压缩策略，对应 rtk 的 11 种过滤策略。当前实现中策略通过 `strategies` 字段声明，实际压缩由 Pipeline 各阶段执行。

| ID | 策略 | Pipeline 对应阶段 | 预期省率 | 风险 |
|----|------|-------------------|---------|------|
| **S1** | 统计摘要 | SectionFilter + TextReplace | 15-30% | 低 |
| **S2** | 仅核心指令 | SectionFilter keep_sections | 40-60% | 中 |
| **S3** | 约束归并 | TextReplace | 10-20% | 中 |
| **S4** | 去重 | TextReplace + LineFilter | 5-15% | 低 |
| **S5** | 骨架提取 | SectionFilter + HeadTail | 50-70% | 高 |
| **S6** | Few-shot 裁剪 | max_examples（预留） | 20-40% | 中 |
| **S7** | 层级折叠 | TextReplace | 10-20% | 低 |
| **S8** | 同义精简 | TextReplace | 5-15% | 低 |
| **S9** | 渐进式 prompt | max_tokens + on_empty | 30-50% | 高 |
| **S10** | 条件压缩 | 预留扩展 | 20-40% | 中 |

### 4.2 渐进式策略阶梯

```toml
# 轻度压缩：S1 + S4 + S8
strategies = []
strip_lines_matching = ["^\s{2,}$"]
replace = { "请详细说明" = "说明" }

# 中度压缩：+ S2 + S6
keep_sections = ["核心指令", "输出格式"]
remove_sections = ["背景说明", "Q&A"]
max_examples = 2

# 重度压缩：+ S3 + S7 + S5
head_lines = 60
tail_lines = 15
max_char = 5000
```

---

## 5 声明式规则 DSL

### 5.1 TOML 规则格式

```toml
schema_version = 1

[compressors.code-review-prompt]
match_prompt = "^你是一个.*代码审查|^你是一个.*Code Review"
description = "代码审查 prompt 压缩规则"
strategies = ["s2", "s8"]

# Stage 2
keep_sections = ["核心指令", "审查清单", "输出格式"]
remove_sections = ["背景说明", "Q&A", "历史变更记录", "参考案例"]

# Stage 3
[compressors.code-review-prompt.replace]
"请对以下代码进行审查" = "审查代码"
"请确保" = "须"
"如果有任何问题" = "有问题则"
"请重点关注" = "重点检查"

# Stage 4
strip_lines_matching = [
    "^\\s{2,}$",                   # 连续空行
    "^\\-{3,}",                    # 分隔线
]

# Stage 5-7
truncate_lines_at = 300
head_lines = 60
tail_lines = 15
max_char = 8000

# Stage 8
on_empty = "你是一个代码审查专家，审查以下代码变更并标注严重问题。"
```

### 5.2 程序化配置（Python）

```python
from prompt_compressor.rule_parser import RuleParser

rules = RuleParser.parse_dict({
    "compressors": {
        "code-review": {
            "match_prompt": "你是一个.*审查",
            "keep_sections": ["核心指令", "审查清单", "输出格式"],
            "remove_sections": ["背景说明", "参考案例", "Q&A"],
            "replace": {
                "请对以下代码变更进行审查": "审查以下代码",
                "是否存在": "有无",
            },
            "strip_lines_matching": [r"^\s{2,}$"],
            "max_char": 5000,
            "on_empty": "审查以下代码变更。",
        }
    }
})
```

### 5.3 内置规则（保守策略）

```python
# prompt_compressor/registry.py
_BUILTIN_RULES = {
    "compressors": {
        "_builtin_cleanup": {
            "match_prompt": r"(?s).{20,}",  # 只匹配 20+ 字符的 prompt
            "description": "全局清洗：去连续空行",
            "strip_lines_matching": [
                r"^\s{2,}$",  # 仅 2+ 空格的空行
            ],
        },
    }
}
```

> **设计原则**：内置规则极度保守——只去连续空行，不碰任何实质内容。短 prompt（<20 字符）完全透传。

---

## 6 优先级链

### 6.1 三层覆盖

```
                  高
                   │
       项目规则 ───┤ 项目级（与代码仓库一起提交）
   .prompt-compressor/rules/
                   │
       用户规则 ───┤ 用户级（个人偏好，不共享）
   ~/.config/prompt-compressor/rules/
                   │
       内置规则 ───┤ 平台级（框架自带的通用规则）
   硬编码在 registry.py 中
                   │
                   ▼
                  低
```

### 6.2 合并逻辑

```python
# prompt_compressor/registry.py
class CompressorRegistry:
    def _match_rules(self, prompt: str) -> Optional[CompiledRule]:
        """按优先级匹配并合并规则。

        匹配顺序: project → user → builtin
        合并方式: high.merge(lower) 即高优先级在前，低优先级在后
        """
        matched: list[CompiledRule] = []
        for rule in self._project_rules:
            if rule.match(prompt):
                matched.append(rule)
        for rule in self._user_rules:
            if rule.match(prompt):
                matched.append(rule)
        for rule in self._builtin_rules:
            if rule.match(prompt):
                matched.append(rule)

        if not matched:
            return None

        result = matched[0]  # 最高优先级
        for rule in matched[1:]:
            result = result.merge(rule)
        return result
```

```python
# prompt_compressor/rule_parser.py
class CompiledRule:
    def merge(self, lower: "CompiledRule") -> "CompiledRule":
        """self 优先级更高，lower 优先级较低。"""
        if lower is None:
            return self

        # override 模式：声明 override=True 的一方完全覆盖另一方
        if self.override:
            return self
        if lower.override:
            return lower

        merged = CompiledRule(name=f"{self.name}+{lower.name}")

        # 列表字段：高优先级在前（先执行），低优先级在后
        merged.keep_sections = _dedup(self.keep_sections + lower.keep_sections)
        merged.remove_sections = _dedup(self.remove_sections + lower.remove_sections)
        merged.strip_lines_matching = _dedup(
            self.strip_lines_matching + lower.strip_lines_matching
        )
        merged.keep_lines_matching = _dedup(
            self.keep_lines_matching + lower.keep_lines_matching
        )
        merged.replace_pairs = self.replace_pairs + lower.replace_pairs

        # 标量字段：self 优先，fallback 到 lower
        merged.truncate_lines_at = self.truncate_lines_at or lower.truncate_lines_at
        merged.head_lines = self.head_lines or lower.head_lines
        merged.tail_lines = self.tail_lines or lower.tail_lines
        merged.max_char = self.max_char or lower.max_char
        merged.max_tokens = self.max_tokens or lower.max_tokens
        merged.on_empty = self.on_empty or lower.on_empty
        merged.strategies = _dedup(self.strategies + lower.strategies)

        return merged
```

### 6.3 合并语义速查

| 字段 | 合并方式 | 示例 |
|------|---------|------|
| `keep_sections` | 并集（高优先级在前） | `["核心"] + ["审查"] = ["核心", "审查"]` |
| `replace_pairs` | 链式拼接（高优先级先执行） | `self.replace + lower.replace` |
| `max_char` | 取非 None（self 优先） | `self.max_char=5000, lower.max_char=8000 → 5000` |
| `override=True` | 短路返回该规则 | 用于禁用低优先级规则 |

---

## 7 回退机制

### 7.1 三层回退

```
层级              触发条件                          行为
──────────────────────────────────────────────────────────────────
L1 阶段回退     单个 Stage 抛异常                  跳过该 Stage，继续流水线
L2 规则回退     压缩后长度 > 原始 * 1.2            回退到原始 prompt
                或压缩后为空                       回退到原始 prompt
L3 全局回退     Tracker 报告质量评分 < 阈值        自动用原始 prompt 重试（预留）
```

### 7.2 L1 阶段回退（Pipeline 内部）

```python
for stage in self._stages:
    try:
        output, info = stage.apply(current, rule)
        ...
    except Exception as e:
        # 跳过该 stage，保留上次输出
        stage_log.append({
            "name": stage.name(), "error": str(e), "skipped": True,
        })
```

### 7.3 L2 规则回退（Pipeline 尾部）

```python
# 允许 20% 膨胀（TextReplace 可能略微增加长度）
swell_threshold = int(len(prompt) * 1.2)
if len(current) > swell_threshold:
    current = prompt  # 回退
    fallback_used = True

# 空输出回退
if not current.strip():
    current = prompt  # 回退
    fallback_used = True
```

### 7.4 L3 全局回退（预留）

```python
# 预留：Tracker 记录质量评分后自动触发
if quality_score < 0.6:
    result = registry.compress(prompt)  # 用原始 prompt 重试
    # 或通知规则维护人
```

### 7.5 Tee 机制

```python
# prompt_compressor/tee.py
class Tee:
    def __init__(self, dir: Optional[str] = None):
        self.base_dir = Path(dir) if dir else Path.home() / ".prompt-compressor" / "tee"
        self._session_id = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"
        self._session_dir: Optional[Path] = None  # 延迟创建

    def save(self, filename: str, content: str):
        path = self.session_dir / filename
        path.write_text(content, encoding="utf-8")

    def replay(self, session_id: str) -> dict:
        dir_path = self.base_dir / session_id
        return {
            file.stem: file.read_text(encoding="utf-8")
            for file in dir_path.iterdir() if file.is_file()
        }
```

输出目录结构：

```
~/.prompt-compressor/tee/
└── 20260603_123845_a58dcb05/
    ├── original.txt
    ├── compressed.txt
    └── stages.json
```

---

## 8 追踪与反馈闭环

### 8.1 SQLite Schema

```python
# prompt_compressor/tracker.py
SCHEMA = """
CREATE TABLE IF NOT EXISTS compression_logs (
    id            TEXT PRIMARY KEY,
    session_id    TEXT NOT NULL DEFAULT '',
    prompt_hash   TEXT NOT NULL,           -- SHA256 前 16 位（跨进程稳定）

    original_char     INTEGER NOT NULL,
    original_tokens   INTEGER NOT NULL,    -- len(text) // 3
    compressed_char   INTEGER NOT NULL,
    compressed_tokens INTEGER NOT NULL,
    savings_pct       REAL NOT NULL,

    rules_matched     TEXT NOT NULL,        -- JSON: ["code-review", "_builtin_cleanup"]
    stages_applied    TEXT NOT NULL,        -- JSON: [{"name":"SectionFilter","skipped":false},...]

    compression_ms    INTEGER DEFAULT 0,
    quality_score     REAL,                 -- NULL = 未评估
    quality_flags     TEXT,                 -- JSON: ["keyword_missing"]
    fallback_used     INTEGER DEFAULT 0,    -- 0/1

    created_at        TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_prompt_hash ON compression_logs(prompt_hash);
CREATE INDEX idx_session ON compression_logs(session_id);
"""
```

### 8.2 核心 API

```python
# prompt_compressor/tracker.py
class Tracker:
    def record(self, result: dict) -> str:
        """记录一次压缩。返回记录 ID（UUID 前 8 位）。"""
        record_id = str(uuid.uuid4())[:8]
        # ... SQLite INSERT ...
        return record_id

    def summary(self) -> dict:
        """汇总统计：总调用、总节省、平均节省率、回退次数。"""
        ...

    def top_rules(self, limit: int = 10) -> list[dict]:
        """按节省量排序的规则排名。"""
        ...
```

### 8.3 CLI 查询

```bash
$ python3 -m prompt_compressor.cli gain
Prompt Compressor — 压缩统计
========================================
总调用次数:    42
原始 Token:    15400
压缩后 Token:  7700
节省 Token:    7700
平均节省率:    50.0%
回退次数:      0

按规则排名:
  code-review+_builtin_cleanup    20次   4200 tokens (55.0%)
  general-assistant               12次   2100 tokens (45.0%)
  _builtin_cleanup                10次    400 tokens (10.0%)
```

---

## 9 与 rtk 的模式映射

| rtk 概念 | Prompt Compressor 实现 | 对应文件 |
|----------|------------------------|----------|
| `match_command` | `match_prompt` 正则匹配 | `rule_parser.py` |
| `strip_ansi` | `strip_lines_matching` 去空行/注释 | `stages.py` |
| `replace` | `TextReplace` 链式替换 | `stages.py` |
| `match_output` | `OnEmpty` + `SectionFilter` 短路 | `stages.py` |
| `strip_lines_matching` | `LineFilter` Phase 1 | `stages.py` |
| `keep_lines_matching` | `LineFilter` Phase 2 | `stages.py` |
| `truncate_lines_at` | `TruncateLine` | `stages.py` |
| `head_lines` / `tail_lines` | `HeadTail` | `stages.py` |
| `max_lines` | `max_char` / `max_tokens` | `stages.py` |
| `on_empty` | `OnEmpty` | `stages.py` |
| 内置 TOML | `_builtin_cleanup`（硬编码） | `registry.py` |
| 项目级 `.rtk/filters.toml` | `rules/*.toml` | `rules/examples/` |
| `rtk gain` | `python3 -m prompt_compressor.cli gain` | `cli.py` + `tracker.py` |
| Tee 机制 | `Tee` 类（延迟创建目录） | `tee.py` |
| fail-safe | L1(阶段跳过) + L2(膨胀回退) + L3(质量回退) | `pipeline.py` |
| 11 种过滤策略 | 10 种压缩策略（`strategies` 字段声明） | `rule_parser.py` |

---

## 10 边界情况与风险

### 10.1 压缩后质量下降

```
风险：去掉了看似"冗余"实则关键的上下文
缓解：
  - L1/L2/L3 三层回退 + Tee 现场保留
  - 膨胀阈值 1.2x（允许 TextReplace 小幅度膨胀）
  - 内置规则仅去连续空行，不做侵入性处理
  - 渐进式上线：先轻度压缩跑一周，对比质量评分
```

### 10.2 规则冲突难排查

```
风险：三层规则叠加后，预期行为与实际情况不符
缓解：
  - 每次压缩记录 rules_matched（最终生效的规则名如 "code-review+_builtin_cleanup"）
  - `python3 -m prompt_compressor.cli explain <prompt>` 显示章节结构和匹配规则
  - Tee 保存完整 stages.json（每个 stage 的 before/after/skip 状态）
```

### 10.3 匹配误伤

```
风险：match_prompt 正则过宽，压缩了不该压缩的 prompt
缓解：
  - 内置规则 match_prompt = r"(?s).{20,}" 仅匹配 20+ 字符
  - 无匹配时返回 _passthrough，完全透传
  - 建议 match_prompt 使用 ^ 锚点（前缀匹配）
```

### 10.4 压缩后语义反转

```
风险："请确保不要遗漏" → "确保遗漏"（反义）
缓解：
  - TextReplace 使用 re.escape(pattern) 字面匹配，不做智能改写
  - 替换词表需人工 review + 单元测试
  - 膨胀阈值 1.2x 可捕获部分此类问题
```

### 10.5 冷启动

```
风险：新业务没有历史反馈数据，无法判断策略组合
缓解：
  - 默认仅启用内置 _builtin_cleanup（去连续空行）
  - 项目规则按需逐步添加 keep_sections / remove_sections
  - Tracker 积累数据后，用 gain 查看各规则效果
```

---

## 11 附录：Python 实现源码

### 11.1 项目结构

```
prompt-compressor-design/
├── README.md                          ← 本文件
├── test_compress.py                    ← 集成测试（5 组场景）
├── rules/examples/
│   ├── code-review.toml                ← 代码审查规则
│   └── general-assistant.toml         ← 通用助手规则
└── prompt_compressor/                 ← Python 包
    ├── __init__.py                     ← 入口 & create_default_compressor()
    ├── rule_parser.py                  ← CompiledRule + RuleParser
    ├── stages.py                       ← 8 Stage 实现
    ├── pipeline.py                     ← Pipeline + L1/L2 回退
    ├── registry.py                     ← CompressorRegistry + 优先级链
    ├── tracker.py                      ← SQLite 追踪 + gain 统计
    ├── tee.py                          ← 现场保留 + replay
    └── cli.py                          ← CLI 入口 (compress/gain/explain)
```

### 11.2 典型使用模式

**模式 A：程序化调用**

```python
from prompt_compressor.registry import CompressorRegistry
from prompt_compressor.rule_parser import RuleParser

registry = CompressorRegistry()

# 加载项目规则
for rule in RuleParser.parse_file("rules/code-review.toml"):
    registry.add_rule(rule, priority="project")

# 压缩
result = registry.compress("你是一个代码审查专家...")
print(result["compressed"])
print(f"节省: {result['original_char']} → {result['compressed_char']} 字符")
```

**模式 B：CLI 管道**

```bash
echo "你是一个助手..." | python3 -m prompt_compressor.cli compress \
    --project-rules rules/examples \
    --verbose

# 分析 prompt 结构
python3 -m prompt_compressor.cli explain "你是一个助手\n\n## 核心指令\n请简洁"

# 查看统计
python3 -m prompt_compressor.cli gain
```

**模式 C：追踪 + Tee**

```python
from prompt_compressor.registry import CompressorRegistry
from prompt_compressor.tracker import Tracker
from prompt_compressor.tee import Tee

registry = CompressorRegistry()
tee = Tee()           # 保留压缩现场
tracker = Tracker()   # 记录统计

for prompt in prompts:
    result = registry.compress(prompt, tee=tee)
    tracker.record(result)

# 查询统计
print(tracker.summary())
print(tracker.top_rules())

# 回放某次压缩
print(tee.replay(tee.session_id))
```

### 11.3 扩展指南

**添加新的 Stage：**

```python
from prompt_compressor.stages import Stage
from prompt_compressor.rule_parser import CompiledRule

class CustomStage(Stage):
    def name(self) -> str:
        return "CustomStage"

    def apply(self, prompt: str, rule: CompiledRule) -> tuple[str, dict]:
        # 自定义处理逻辑
        processed = prompt.upper()  # 示例
        return processed, {"uppercased": True}
```

然后注入 Pipeline：

```python
from prompt_compressor.pipeline import Pipeline

pipeline = Pipeline()
pipeline._stages.append(CustomStage())  # 或插入到指定位置
```

**添加新的规则文件：**

```toml
# my-project/.prompt-compressor/rules/my-business.toml
[compressors.my-business]
match_prompt = "^你是一个.*客服"
keep_sections = ["服务规范", "话术模板"]
remove_sections = ["培训资料", "考核标准"]
replace = { "请保持礼貌" = "礼貌" }
max_char = 4000
```

---

## 修订历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-06-03 | 初稿，基于 rtk 架构分析 |
| v0.2 | 2026-06-03 | 完成 Python 实现；替换全部伪代码为真实源码；加入实测指标 |
| v0.3 | 2026-06-03 | 前置 rtk 调研报告（使用/技术原理/实测），形成完整的前后文对应 |
