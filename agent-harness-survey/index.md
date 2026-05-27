# Agent Harness Engineering: A Survey — 详细调研报告

> **论文标题**: Agent Harness Engineering: A Survey  
> **作者**: Junjie Li (CMU), Xi Xiao (UAB), Yunbei Zhang (Tulane), Chen Liu (Yale) 等  
> **机构**: CMU, Yale, JHU, NEU, Tulane, UAB, OSU, Virginia Tech, Amazon  
> **项目主页**: Awesome-Agent-Harness  
> **评审状态**: Under review as submission to TMLR  
> **PDF**: `./agent_harness_engineering_survey.pdf`

---

## 目录

1. [概述与核心论点](#1-概述与核心论点)
2. [The Binding Constraint: Harness over Model](#2-the-binding-constraint-harness-over-model)
3. [三阶段工程演进 (2022-2026)](#3-三阶段工程演进-2022-2026)
4. [ETCLOVG 七层分类法详解](#4-etclovg-七层分类法详解)
   - 4.1 [E — 执行环境与沙箱 (Execution Environment & Sandbox)](#41-e--执行环境与沙箱)
   - 4.2 [T — 工具接口与协议 (Tool Interface & Protocol)](#42-t--工具接口与协议)
   - 4.3 [C — 上下文与记忆管理 (Context & Memory Management)](#43-c--上下文与记忆管理)
   - 4.4 [L — 生命周期与编排 (Lifecycle & Orchestration)](#44-l--生命周期与编排)
   - 4.5 [O — 可观测性与运维 (Observability & Operations)](#45-o--可观测性与运维)
   - 4.6 [V — 验证与评估 (Verification & Evaluation)](#46-v--验证与评估)
   - 4.7 [G — 治理与安全 (Governance & Security)](#47-g--治理与安全)
5. [跨层综合 (Cross-Layer Synthesis)](#5-跨层综合)
6. [开放问题与未来方向](#6-开放问题与未来方向)
7. [生态系统映射的发现](#7-生态系统映射的发现)
8. [参考资料与项目](#8-参考资料与项目)

---

## 1. 概述与核心论点

> "The rapid deployment of large language model (LLM) agents in production has revealed a recurring pattern: task execution reliability depends less on the underlying model than on the infrastructure layer that wraps it, the agent execution harness."
> **译文**: LLM Agent 在生产环境中的快速部署揭示了一个反复出现的模式：任务执行的可靠性更多地取决于包裹模型的基础设施层——即 Agent 执行框架（harness）——而非底层模型本身。

**Agent Harness（Agent 执行框架/基础设施）** 指的是包裹语言模型、管理长周期多步骤任务执行的基础设施层。它包括执行环境、工具接口、上下文控制、编排逻辑、可观测性、验证评估和治理约束。

### 论文三个核心贡献

1. **概念主张**: Agent Harness 是一个独立的系统层，其工程质量决定了生产环境中的实际可靠性。提出 **binding-constraint thesis**（绑定约束论）。
2. **分类学主张**: 提出 **ETCLOVG** 七层分类法，首次将可观测性（Observability）和治理（Governance）提升为独立的架构层面。
3. **实证主张**: 对 **170+ 开源项目** 进行系统映射分析，揭示生态系统的密度分布、覆盖缺口和新兴设计原则。

### Practitioner–Research Gap（实践者-研究差距）

> "Practitioners know that harness infrastructure matters but lack the formal vocabulary to describe why, in terms that enable systematic improvement."
> **译文**: 实践者知道 harness 基础设施很重要，但缺乏正式的语言来描述其原因，从而无法实现系统性的改进。

- OpenAI 将 "harness engineering" 明确定义为：围绕 Codex agents 设计环境、约束、文档和反馈循环的学科
- Anthropic 的工程实践表明：有效 Agent 应使用简单可检查的架构，工具接口应为 Agent 使用而设计
- Martin Fowler 网站上的文章将其描述为 LLM 的 "cybernetic governors"（控制论调节器）

---

## 2. The Binding Constraint: Harness over Model

### 关键实证

| 研究 | 改动 | 效果 |
|------|------|------|
| Bölük (2026a) | 仅修改 edit-tool 格式和 tool harness | **10×** 编码基准提升（跨15个模型） |
| Trivedy (2026) | 仅系统提示重构 + 中间件上下文注入 + 自验证钩子 | **52.8% → 66.5%**（+13.7百分点） |
| Meta-Harness (Lee et al., 2026) | 自动化 harness 优化，无模型权重修改 | **76.4%** Terminal-Bench-2 |

> "Each of these harness-only gains exceeds the typical 2 to 4 percentage point improvements reported as meaningful model advances on the same benchmarks."
> **译文**: 这些仅通过改进 harness 获得的增益，每一项都超过了同一基准测试上被报告为有意义模型进步的典型 2 到 4 个百分点提升。

> "We refer to this pattern as the binding-constraint thesis: for long-horizon tasks evaluated across comparable frontier models, benchmark variance may be driven as much by the execution harness as by the model itself."
> **译文**: 我们将这种模式称为绑定约束论：对于在可比较的前沿模型上评估的长周期任务，基准测试结果的方差可能同样由执行框架（execution harness）和模型本身共同驱动。

### 对学界隐含假设的挑战

传统研究默认了 "agent capability is primarily a function of model capability"——一个足够强大的模型加上足够好的提示词就能产生足够可靠的行为。这篇论文从根本上挑战了这一假设。

---

## 3. 三阶段工程演进 (2022-2026)

论文将发展阶段概括为三个阶段，每个阶段是对前一个阶段的包含而非替代：

### Phase 1: Prompt Engineering（2022-2024）

> "The primary lever was the input prompt text. Practitioners optimized by crafting better instructions, few-shot examples, and reasoning templates. The engineering scope was narrow: optimize a single text input to a single model call."
> **译文**: 主要的杠杆是输入提示文本。实践者通过编写更好的指令、少样本示例和推理模板来优化。工程范围很窄：优化单个模型调用的单个文本输入。

- **焦点**: 优化单次模型调用的输入提示文本
- **典型技术**: 指令优化、少样本示例、推理模板（CoT）

### Phase 2: Context Engineering（2025）

> "As agents became longer-running, the binding constraint shifted from 'what is the input?' to 'what information should the model see at each step?'"
> **译文**: 随着 Agent 运行时间变长，绑定约束从"输入是什么？"转变为"模型在每一步应该看到哪些信息？"

- **焦点**: 管理多轮推理中模型能看到哪些信息
- **典型技术**: 上下文窗口管理、记忆检索与压缩、工具结果排序
- **范围**: 从单个输入扩展到管理多个流入上下文窗口的信息流

### Phase 3: Harness Engineering（2026）

> "Harness engineering therefore asks what governance, constraints, feedback loops, and execution controls must be designed around the model to make agent systems reliable. In our taxonomy, this phase treats all seven ETCLOVG layers as an integrated whole."
> **译文**: 因此，Harness 工程询问的是：要使 Agent 系统可靠，必须在模型周围设计什么样的治理、约束、反馈回路和执行控制。在我们的分类法中，这一阶段将所有七个 ETCLOVG 层视为一个整体。

- **焦点**: 设计治理、约束、反馈回路和执行控制
- **范围**: 全部七个 ETCLOVG 层作为一个整体

> "Each phase subsumes the previous: harness engineering includes context engineering, which includes prompt engineering."
> **译文**: 每个阶段都包含前一个阶段：harness 工程包含上下文工程，而上下文工程包含提示工程。

### 行业验证

> "OpenAI explicitly framed 'harness engineering' as the discipline of designing environments, constraints, documentation, and feedback loops around Codex agents, reporting in February 2026 that a small team produced an internal product of roughly **one million lines over five months without manually writing production code**."
> **译文**: OpenAI 明确将"harness 工程"定义为围绕 Codex Agent 设计环境、约束、文档和反馈循环的学科，并于 2026 年 2 月报告称，一个小团队在五个月内生产了大约 **一百万行内部产品代码，而无需手动编写生产代码**。

---

## 4. ETCLOVG 七层分类法详解

### 4.1 E — 执行环境与沙箱

#### 为什么沙箱在 Agent 时代至关重要

沙箱在 Agent 时代不仅仅是传统多租户代码执行的继承安全措施，它同时服务于三个不同的目的：

> "Anthropic reports that introducing sandboxing to Claude Code reduced permission prompts by **84%** while preserving safety."
> **译文**: Anthropic 报告称，在 Claude Code 中引入沙箱将权限提示减少了 **84%**，同时保持了安全性。

1. **安全性（Security）**: LLM 生成的代码不可审计且不可预测；提示注入攻击可将无害 Agent 转变为攻击向量。SandboxEscapeBench 报告 15%-35% 的逃逸成功率。
2. **可复现性（Reproducibility）**: 容器或 microVM 可按需销毁和重建，这是 SWE-bench、OSWorld 等工作流实现的基础。
3. **活性（Liveness）**: 沙箱定义了 Agent 可自由行动的"有界区域"，将权限从"逐动作审批"转变为"会话级配置"。**沙箱同时是笼子和许可证**（"a cage and a license"）。

#### 七大沙箱类别详解

| 类别 | 代表系统 | 核心特征 |
|------|---------|---------|
| **通用托管沙箱** | Daytona, E2B, Modal, Northflank, OpenSandbox, Docker Sandboxes | 商业/开源沙箱即服务；暴露 OCI 容器镜像 API |
| **计算机使用 Agent 基础设施** | Anthropic Computer Use, CUA, OSWorld | 模拟鼠标、键盘操作 GUI；VM 级隔离 |
| **代码专用沙箱** | Judge0, OpenAI Code Interpreter, sandboxed.sh, langchain-sandbox | 轻量级，预装编译器/解释器；从容器转向 WebAssembly |
| **框架集成运行时** | OpenHands, GoEX, smolagents executors | 捆绑在更大的 Agent 框架内，不可独立消费 |
| **浏览器评估环境** | WebArena, VisualWebArena, BrowserGym | 既是沙箱又是评估框架；天然用于研究间接提示注入 |
| **OS 级权限沙箱** | Anthropic sandbox-runtime, Claude Code sandboxing, IsolateGPT | 使用 OS 原语（bubblewrap, Seatbelt, seccomp-bpf）；原则是 **permission, not partition**（授权而非分区） |
| **沙箱抽象层** | SWE-ReX, smolagents executors, K8s Agent Sandbox | 统一多种沙箱后端到单一 API，使执行基础设施可替换 |

#### 关键设计趋势

**隔离强度的分化**:
> "Managed sandboxes are migrating from shared-kernel containers toward dedicated-kernel microVMs, while OS-level permission sandboxes dispense with separate environments entirely and instead narrow the host's view."
> **译文**: 托管沙箱正从共享内核容器向专用内核 microVM 迁移，而 OS 级权限沙箱则完全摒弃了独立环境，转而缩小主机的可见范围。

**安全威胁**:
> "SandboxEscapeBench evaluates frontier LLMs in a nested sandbox capture-the-flag setting and reports **15% to 35% escape success rates** against Docker-based containers."
> **译文**: SandboxEscapeBench 在嵌套沙箱的夺旗（CTF）场景中评估了前沿 LLM，报告称对基于 Docker 的容器的**逃逸成功率为 15% 至 35%**。

**部署模式**: 自托管（本地 Docker）→ 云托管（E2B/Modal）→ 混合（BYOC），三者沿延迟-安全性-可扩展性三个轴进行权衡。

---

### 4.2 T — 工具接口与协议

#### 核心矛盾

> "Increasing capability coverage by exposing more tools, versus preserving decision quality by keeping the action space and prompt footprint small."
> **译文**: 通过暴露更多工具来增加能力覆盖面，与通过保持较小的动作空间和提示占用来维持决策质量之间的矛盾。

> "Oversized tool menus can degrade reliability, increase token overhead, and amplify planning errors."
> **译文**: 过大的工具菜单会降低可靠性、增加 token 开销并放大规划错误。

#### 四大集成边界

论文按集成边界对工具/接口标准进行了分类，这比按厂商划分更合理：

| 边界 | 标准 | 描述 |
|------|------|------|
| Model↔Function | Function Calling (OpenAI) | 结构化函数调用，JSON schema |
| Agent↔Capability | MCP, OpenAPI | 运行时到工具的接口解耦；JSON-RPC |
| Agent↔Agent | A2A, ACP/ANP | 跨进程委托；Agent Cards 发现 |
| Agent↔Repo/Env | AGENTS.md / AGENT.md | 版本控制中的轻量级策略文件 |

#### MCP（Model Context Protocol）生态

> "MCP has become the most visible tool-integration substrate for coding and enterprise agents, with an explicit host-client-server architecture and JSON-RPC-based typed exchange of tools, resources, and prompts."
> **译文**: MCP 已成为编码和企业 Agent 中最引人注目的工具集成基础设施，具有显式的主机-客户端-服务器架构和基于 JSON-RPC 的工具、资源和提示的类型化交换。

MCP 的实际价值不仅是模式级的互操作性，更是 **生态流动性（ecosystem liquidity）**：Agent 构建者可以复用不断扩展的服务器目录，而无需为每次部署实现自定义连接器。

#### 工具选择设计原则

> "Fewer but better tools often outperforms brute-force tool exposure because it shrinks both prompt entropy and planner branching."
> **译文**: "更少但更好的工具"通常优于暴力暴露所有工具，因为它同时缩小了提示熵和规划器的分支。

> "If a human engineer cannot say which tool applies in a given situation, the model cannot be expected to do better."
> **译文**: 如果人类工程师都无法判断在某种情况下应该使用哪个工具，就不能指望模型做得更好。

**工具发现必须自适应**: 静态的全局工具列表无法扩展到快速演变的仓库或多租户企业部署。

---

### 4.3 C — 上下文与记忆管理

该层是 Prompt/Context Engineering 与 Harness Engineering 交汇的地方。

#### 为什么上下文必须被工程化（而非被动累积）

**1. 二次注意力代价**:
> "For n tokens, this produces n² pairwise weights; compute and memory scale quadratically with context length."
> **译文**: 对于 n 个 token，这会产生 n² 对权重；计算和内存随上下文长度呈二次方扩展。

**2. U 形注意力曲线** (Liu et al., 2024):
> "accuracy drops by more than 30% when the relevant document sits in the middle of the context."
> **译文**: 当相关文档位于上下文中间时，准确率下降超过 30%。

**3. 上下文腐烂（Context Rot）** (Hong et al., 2025):
> "A model rated for 200K tokens may show significant performance loss at 50K."
> **译文**: 一个被评价为支持 200K token 的模型，可能在 50K token 时就表现出显著的性能损失。

#### 三层记忆架构

##### 短期（Short-Term）：管理活动上下文窗口

**系统提示校准**:
> "Start with a minimal prompt on the best available model, identify failure modes empirically, then add targeted instructions to address specific gaps."
> **译文**: 从最佳可用模型上的最小提示开始，通过实验识别故障模式，然后添加针对性的指令来解决具体差距。

**Token 高效工具设计**: 工具定义是主要的上下文消耗者。工具描述应使用描述性参数名，自包含且健壮。

**渐进式披露（Progressive Disclosure）**:
> "Rather than loading all potentially relevant information upfront, effective agents maintain lightweight identifiers such as file paths, stored queries, and web links, and use them to load data on demand."
> **译文**: 有效 Agent 不会预先加载所有潜在相关信息，而是维护轻量级标识符（如文件路径、存储的查询和网络链接），并根据需要按需加载数据。

**KV-cache 感知设计**:
> "The Manus team identified KV-cache hit rate as 'the single most important metric for a production-stage AI agent,' noting that cached tokens on Claude Sonnet cost $0.30/MTok compared to $3.00/MTok for uncached tokens."
> **译文**: Manus 团队将 KV-cache 命中率视为"生产级 AI Agent 最重要的单一指标"，并指出 Claude Sonnet 上缓存的 token 成本为 $0.30/MTok，而未缓存的 token 成本为 $3.00/MTok。

三条设计规则:
1. **保持提示前缀稳定**: 系统提示开头的单个 token 差异会使后面的所有内容缓存失效
2. **上下文视为仅追加**: 修改过去的动作或观察会破坏缓存重用
3. **使用确定性序列化**: JSON 序列化中的非稳定键排序会在相同请求间静默地使缓存失效

##### 中期（Mid-Term）：会话状态与跨运行持久化

**结构化笔记**:
> "The key insight is that note-taking externalizes working memory. Rather than relying on conversation history to carry task state, the agent writes what matters to an external store and reads it back on demand."
> **译文**: 关键洞察在于，记笔记将工作记忆外部化。Agent 不是依靠对话历史来携带任务状态，而是将重要信息写入外部存储，并根据需要读回。

- 典型模式: NOTES.md / todo.md 文件，每次运行开始时读取，上下文清除前更新
- 工具: `planning-with-files`, `Trellis`, `claude-mem`, `everything-claude-code`（15万+ GitHub 星）

##### 长期（Long-Term）：持久化记忆系统

**代表性系统对比**:

| 系统 | 核心机制 | 特点 |
|------|---------|------|
| **MemGPT**(Packer et al., 2023) | OS 风格的分层记忆（RAM 类比上下文窗口，Disk 类比外部存储） | 显式分页函数，使幻觉拥有更大的上下文 |
| **Generative Agents**(Park et al., 2023) | Memory Stream：观察→反思→检索三联 | 重要性评分+时间衰减+相关性检索 |
| **MemoryBank**(Zhong et al., 2024) | Ebbinghaus 遗忘曲线+用户个性建模 | 动态遗忘机制，被 Mem0 继承 |
| **Mem0**(Chhikara et al., 2025) | 向量DB+图DB+键值存储+LLM 提取 | 1400万+下载量，41K星，AWS Agent SDK 独家记忆提供商 |
| **A-MEM**(Xu et al., 2025) | Zettelkasten 知识管理系统 | 动态链接网络，写入时更新已有笔记 |
| **Hindsight**(Vectorize.io, 2025) | retain → recall → reflect | 关注"学习"而非"记住"；LongMemEval SOTA |
| **Honcho**(Plastic Labs, 2025) | "Dreaming" 异步推理管线 | 用户建模而非事实存储；支持多 Agent 共享用户模型 |
| **cq**(Mozilla AI, 2025) | MCP 原生，三层架构 | 跨 Agent 实例的集体记忆，post-error hook 模式 |

#### 长周期技术（100+ 轮保持一致性）

**上下文压缩（Context Compaction）**:
> "The summary must preserve architectural decisions, unresolved bugs, and implementation details while discarding redundant tool outputs and intermediate reasoning already incorporated into later steps."
> **译文**: 摘要必须保留架构决策、未解决的错误和实现细节，同时丢弃冗余的工具输出和已被后续步骤吸收的中间推理。

推荐的调优工作流: 从最大化召回率开始，然后迭代以提高精确度。

**子 Agent 上下文隔离**:
> "Sub-agent context isolation is expensive: it produces larger prefills and eliminates KV-cache reuse across different system prompts."
> **译文**: 子 Agent 上下文隔离成本很高：它会产生更大的预填充，并消除跨不同系统提示的 KV-cache 重用。

**混合决策框架**:
> "Pre-load content that is always needed, retrieve just-in-time content that is conditionally needed, compact history when the window approaches saturation, and spawn sub-agents when a subtask requires exploration that would pollute the orchestrator's context."
> **译文**: 预加载总是需要的内容，按需检索有条件需要的内容，在窗口接近饱和时压缩历史，在子任务需要探索且会污染编排器上下文时生成子 Agent。

> "Context management should be the infrastructure's job, not the agent's."
> **译文**: 上下文管理应该是基础设施的职责，而不是 Agent 的职责。

#### Context Drift（上下文漂移）

> "Context drift is a property of an extended trajectory. As the agent accumulates turns, its behavior drifts from the original intent in ways that compaction and retrieval steps can slow but not prevent."
> **译文**: 上下文漂移是扩展轨迹的一个属性。随着 Agent 累积回合数，其行为会偏离原始意图，压缩和检索步骤只能减缓但无法阻止这种偏离。

根因: 每次压缩步骤中存活下来的摘要携带的细微不准确性会随着时间累积。

---

### 4.4 L — 生命周期与编排

该层关注 Agent 系统如何在多次模型调用、工具调用、失败、修订和交接中携带任务前进。

#### 单 Agent 内部循环

> "The single-agent inner loop follows the ReAct paradigm, interleaving reasoning, action, and observation."
> **译文**: 单 Agent 内部循环遵循 ReAct 范式，交错了推理、动作和观察。

| 系统 | GitHub Stars | 执行模型 |
|------|-------------|---------|
| OpenCode | 159K | Hybrid |
| Claude Code | 123K | Hybrid |
| Gemini CLI | 104K | Hybrid |
| Codex CLI | 82K | Stateless replay |
| Aider | 45K | Hybrid |
| SWE-agent | 19K | Hybrid |

#### 多 Agent 编排模式

| 模式 | 描述 | 代表系统 |
|------|------|---------|
| **层次化编排** (Hierarchical) | 高层控制器向子 Agent 分配工作 | DeerFlow, AutoGen, OpenAI Agents SDK, DeepAgents |
| **团队编排** (Team) | 一组有不同职责的 Agent 组成协调团队 | oh-my-claudecode |
| **工作流编排** (Workflow) | Agent 和工具组织成显式阶段/控制逻辑 | Semantic Kernel |
| **扇形展开** (Fan-out) | 多个并行 Agent 探索不同方案 | Emdash |
| **图组合** (Graph) | Agent/工具/状态作为交互图的节点 | LangGraph, Hive |

#### 完整生命周期流水线（Issue → Pull Request）

> "The central abstraction is the task runner: a harness that manages scheduling, state persistence, retries, validation, and iterative refinement over a complete task lifecycle."
> **译文**: 核心抽象是任务运行器（task runner）：一个管理调度、状态持久化、重试、验证和整个任务生命周期的迭代优化的 harness。

- Vibe Kanban: 看板式任务管理
- Symphony (OpenAI): 将 issue tracker 和 task runner 作为持久化控制平面
- GitHub Agentic Workflows: 将 Agent 工作流集成到 GitHub Actions

#### 状态管理的关键权衡

- **无状态重放（Stateless replay）**: Codex CLI 方式，提高可复现性和可审计性，但轨迹增长时成本高
- **有状态执行（Stateful execution）**: 在文件/数据库/仓库中持久化状态，改善连续性和恢复能力，但带来一致性和调试挑战
- **混合设计（Hybrid）**: 多数实际系统采用，结合可重放交互历史与持久化制品

---

### 4.5 O — 可观测性与运维

论文将可观测性提升为独立层（而非生命周期钩子的副产品），因为在生产系统中可观测性有专用工具生态和独特的工程实践。

#### 4.5.1 追踪与监控平台

| 工具 | 用途 |
|------|------|
| Langfuse | LLMOps 追踪和指标 |
| MLflow | 平台监控与评估 |
| Opik (Comet ML) | 监控、评估、追踪 |
| Arize Phoenix | 可观测性、追踪、评估 |
| OpenTelemetry | 通用追踪 |
| OpenLLMetry | OpenTelemetry 的 LLM 专用包装 |
| AgentSight / AgentTrace | Agent 专用追踪 |

#### 4.5.2 Agent 专用运维平台

- **AgentOps**: 成本追踪与监控
- **RagaAI Catalyst**: Agent 分析
- **Laminar**: 可观测性、追踪、评估
- **Claude-Code-Reverse**: 逆向工程 Claude Code 行为

#### 4.5.3 成本追踪与优化

> "Cached tokens on Claude Sonnet cost $0.30/MTok compared to $3.00/MTok for uncached tokens."
> **译文**: Claude Sonnet 上缓存的 token 成本为 $0.30/MTok，而未缓存的 token 成本为 $3.00/MTok。

优化策略:
- **FrugalGPT**: 模型路由
- **GPTCache**: 响应缓存
- **Dual-Pool Token-Budget Routing**: 将同构 vLLM 集群分为短上下文和长上下文池，减少 GPU 小时数 31-42%

#### 4.5.4 可靠性工程

**四种常见的故障模式**（来自 Anthropic）:
1. Agent 试图一次性完成整个任务（"one-shot"）
2. Agent 过早宣布项目完成
3. Agent 在会话间将环境留在损坏状态
4. Agent 标记功能完成但不做适当测试

**Anthropic 的两部分解决方案**:
1. **初始化 Agent**: 将任务分解为结构化功能列表，设置进度追踪制品（git repo, progress file, init script）
2. **编码 Agent**: 一次专注一个功能增量工作，留下干净的交接状态

**三 Agent 架构（GAN 启发）**:
> "Anthropic's GAN-inspired three-agent architecture (planner, generator, evaluator) introduces sprint contracts and separated self-evaluation."
> **译文**: Anthropic 受 GAN 启发的三 Agent 架构（规划器、生成器、评估器）引入了冲刺合约和分离的自我评估机制。

**关键原则 - 每次模型升级时简化 Harness**:
> "When upgrading from Opus 4.5 to Opus 4.6, they removed the sprint construct and context resets entirely, reducing cost from **$200 to $125** while maintaining output quality."
> **译文**: 当从 Opus 4.5 升级到 Opus 4.6 时，他们完全移除了冲刺结构和上下文重置，将成本从 **$200 降低到 $125**，同时保持了输出质量。

**Managed Agents 架构**: 将组件解耦为 "brain"（harness + LLM），"hands"（沙箱和工具），"session"（持久化事件日志），每个独立可恢复。组件从 "pets"（不可替换、手动维护的实例）变为 "cattle"（可互换、自动重新配置）——大规模可靠运行 Agent 的先决条件。

#### 4.5.5 可观测性-评估鸿沟

> "LangChain's 2026 survey reports that **89% of teams use observability** while only **52.4% run offline evaluations**."
> **译文**: LangChain 的 2026 年调查报告称，**89% 的团队使用可观测性**，而只有 **52.4% 的团队运行离线评估**。

> "Anthropic's study on infrastructure noise in agentic coding evaluations provides a cautionary complement: **infrastructure configuration alone can shift benchmark scores by 6 percentage points** (p < 0.01)."
> **译文**: Anthropic 关于 Agent 编码评估中基础设施噪音的研究提供了一个警示性的补充：**仅基础设施配置就能使基准分数偏移 6 个百分点**（p < 0.01）。

**Harness-as-Assumption 原则**:
> "Every harness component encodes an assumption about what the model cannot do on its own. The ideal observability system would include a meta-monitoring layer that tracks which interventions are still load-bearing, enabling continuous harness simplification alongside model upgrades."
> **译文**: 每个 harness 组件都编码了一个关于模型自身不能做什么的假设。理想的可观测性系统应该包含一个元监控层，用于跟踪哪些干预措施仍在承担负载，从而在模型升级的同时持续简化 harness。

---

### 4.6 V — 验证与评估

论文将评估组织为一个 **五阶段 task-to-feedback lifecycle**：

```
Task Grounding → Readiness Validation → Controlled Execution → Multi-level Judgement → Continuous Regression
```

#### Stage 1: 任务与基准锚定

LLM Agent 的任务不仅是自然语言提示，而是一个由环境状态、可用工具、允许动作、约束、终止条件和成功标准定义的"嵌入式问题"。

**代表性基准**:
- **SWE-bench**: 软件工程 Issue 修复
- **Terminal-Bench**: 终端自动化
- **WebArena / VisualWebArena**: 浏览器任务
- **OSWorld**: 操作系统级任务
- **AgentBench**: 跨领域评估
- **GAIA**: 通用 AI 助手
- **TheAgentCompany**: 企业多步骤任务

#### Stage 2: 执行前就绪验证

> "Failed runs may reflect not only model limitations, but also broken tools, stale context, non-reset sandboxes, flaky tests, benchmark ambiguity, or unstable judges."
> **译文**: 失败的运行可能不仅反映模型的局限性，还可能反映工具损坏、上下文过时、沙箱未重置、不稳定的测试、基准歧义或评估器不稳定。

**关键基础设施**:
- **Repo2Run**: 自动构建可复现的评估环境
- **HAL**: 标准化 Agent 评估框架
- **SWE-ReX**: 统一运行时接口

#### Stage 3: 受控执行与追踪捕获

**Trace-Native 评估**: Harness 应记录模型输出、工具调用、工具结果、环境状态变化、上下文快照、错误、重试、恢复动作、token 使用、延迟和成本。

> "Traces are not auxiliary debugging artifacts; they are primary evaluation data."
> **译文**: 轨迹不是辅助调试的副产品，它们是最主要的评估数据。

**成本-延迟-成功率三位一体**:
> "Rather than ranking agents only by success rate, evaluations should expose a success-cost-latency frontier."
> **译文**: 评估不应仅按成功率对 Agent 排名，而应揭示一个成功率-成本-延迟的前沿界面。

#### Stage 4: 多层次评判与故障归因

三个评估层次：

1. **结果级（Outcome-level）**: 最终任务目标是否达成（如单元测试是否通过）
2. **轨迹级（Trajectory-level）**: Agent 是否选择了合适工具、动作顺序是否合理、是否避免冗余调用、是否尊重权限边界、是否从错误中恢复
3. **评估器级（Evaluator-level）**: 评估器本身是否可信（确定性验证器 vs. LLM-as-Judge vs. 人工审计）

> "A final answer can be correct while the trajectory is still unacceptable."
> **译文**: 最终答案可能是正确的，但轨迹仍然可能是不可接受的。

**评估器级评估不是可选项**:
> "If a grader is flaky, a test is nondeterministic, or an LLM judge is biased, then evaluation noise can be misattributed to the agent or model."
> **译文**: 如果评分器不稳定、测试不确定或 LLM 评估器有偏见，那么评估噪音就可能被错误地归因到 Agent 或模型身上。

**推荐的分层评估器策略**: 确定性检查（客观状态变化）+ LLM Judge（语义/轨迹评估）+ 人工审计（高风险/模糊案例）

#### Stage 5: 持续回归与部署反馈

> "Because harness components interact, local improvements can create global regressions."
> **译文**: 因为 harness 组件是相互作用的，局部改进可能造成全局退化。

**分层评估套件**:
- 工具模式的单元级测试
- 局部决策的单步测试
- 端到端完成的全面部署测试
- 长周期连贯性的多轮模拟

**评估即持续改进信号**:
> "Meta-Harness extends this direction by treating harness design itself as an object of automated search."
> **译文**: Meta-Harness 通过将 harness 设计本身作为自动搜索的对象来扩展这一方向。

---

### 4.7 G — 治理与安全

治理是一个独立的工程层，贯穿三个子层：模型级（护栏、内容过滤）、系统级（网关、代理、权限模型）、组织级（审计、合规、人工监督）。

#### 权限模型与身份管理

**静态权限边界**: 预定义工具访问范围（如 Codex 的沙箱文件系统限制、Gemini CLI 的命令白名单/黑名单）。

**上下文相关权限控制**: Progent 引入 DSL，谓词可作用于工具名、参数和环境状态。Conseca 从可信上下文生成任务特定策略。

**身份管理与跨 Agent 访问控制**:
> "South et al. (2025) argue that agents need authenticated delegation: extending OAuth 2.0 and OpenID Connect with User ID Tokens, Agent ID Tokens, and scoped Delegation Tokens."
> **译文**: South 等人（2025）认为 Agent 需要认证委托机制：扩展 OAuth 2.0 和 OpenID Connect，加入用户 ID Token、Agent ID Token 和作用域委托 Token。

**凭据管理**: 将密钥存储在 vault 中，仅向 LLM 暴露占位符，在自动化层替换实际值。

**Web 级权限协调**: `agent-permissions.json`（类似 robots.txt）——声明网站 UI 元素的使用限制、速率限制、并发约束和需要人工确认的动作。

#### 生命周期钩子

四个钩子点构成一个工具调用周期：

```
Input → [H1: Input Guardrail] → LLM → [H2: Action Guardrail] → Tool → [H3: Post-exec IFC] → [H4: Human-in-the-loop] → Response
```

- **H1 预执行钩子（输入护栏）**: PromptShield, DataSentinel 检测提示注入
- **H2 调用前钩子（输出护栏/动作验证）**: ShieldAgent 验证动作安全约束，ControlValve 约束 Agent 间的控制流
- **H3 执行后钩子（信息流控制/污点追踪）**: CaMeL 实现基于能力的信息流控制，区分可信用户输入与不可信网络检索
- **H4 人工入环钩子**: 破坏性或范围外动作需要用户审批

> "Frequent requests lead users to approve dangerous actions reflexively, while infrequent requests leave coverage gaps."
> **译文**: 频繁的请求导致用户反射性地批准危险动作，而过少的请求则会留下覆盖缺口。

#### 组件强化

**模型强化（Model Hardening）**:
- **Instruction Hierarchy** (Wallace et al., 2024): 训练模型区分系统指令（高优先级）和不可信数据（低优先级）
- **SecAlign** (Chen et al., 2025a): 针对提示注入输入的偏好优化

**分类器运行时强化**: Llama Guard 部署小型辅助分类器，无需重新训练即可编辑安全分类体系。

**工具强化与 MCP 安全**:
> "Trail of Bits show that MCP servers can attack clients before a user ever invokes a tool, through poisoned tool descriptions."
> **译文**: Trail of Bits 展示，MCP 服务器可以在用户调用工具之前，通过投毒的工具描述来攻击客户端。

- **ETDI** (Bhatt et al., 2025): 扩展 MCP，加入加密签名和版本化工具定义
- **SAFEFLOW** (Li et al., 2025): 基于静态分析的工具强化

#### 声明式章程（Declarative Constitutions）

- **Claude's Constitution**: 宪法式 AI 对齐
- **AutoHarness**: 自动化生成和验证章程
- **AgentSpec** (Wang et al., 2026): 规则驱动的触发-谓词-执行模式
- **VeriSafeAgent** (Lee et al., 2025): 形式化验证安全属性

#### 审计基础设施

- **不可变事件日志**: 记录每个动作的身份、时间、内容
- **会话重放**: 从完整轨迹回放 Agent 行为
- **异常告警**: SentinelAgent 在三个层级分类异常；AgentFixer 部署 15 个验证工具达到 64-88% 的检测率

#### 八大开放研究方向

1. **标准化策略和审计语言**（类似 MCP 的社区驱动规范）
2. **形式化治理保证**（验证治理流水线的正确性）
3. **自适应治理**（LLM 生成的策略，以及策略生成器本身的治理）
4. **长周期 Agent 的治理**（跨会话的有效性续期、撤销和审计）
5. **可用的治理界面**（权限 UI、审计仪表盘 HCI 研究）
6. **跨层治理一致性**（训练时对齐、部署时配置、运行时执行的组合）
7. **端到端供应链治理**（从包仓库到 Agent 执行的全链路）
8. **统一对抗基准**（在共同对手模型下评估完整治理栈）

---

## 5. 跨层综合

### 成本-质量-速度三难困境

> "Harness reliability is constrained by a three-way tradeoff between cost, quality, and speed."
> **译文**: Harness 的可靠性受到成本、质量和速度三者之间权衡的约束。

| 追求 | 收益 | 代价 |
|------|------|------|
| 更强的沙箱/更真实的环境 | 提升安全性和可复现性 | 增加启动延迟和基础设施成本 |
| 更丰富的上下文和记忆策略 | 改善任务连续性 | 消耗 token 并引入检索开销 |
| 更深入的评估和可观测性 | 改进诊断 | 降低迭代速度、增加存储成本 |

### 能力-控制权衡

> "More capable harnesses expose more authority to the agent, but every increase in authority expands the control problem."
> **译文**: 更强大的 harness 向 Agent 暴露了更多的权限，但每次权限的增加都会扩大控制问题的范围。

具体表现:
- 更大的工具菜单 → 更广覆盖 + 更大选择错误和提示注入风险
- 持久化记忆 → 帮助长周期 + 引入来源追溯、数据过时和隐私风险
- 宽松的沙箱 → 使自主执行可用 + 扩大误对齐或受损动作的爆炸半径

### Harness 耦合问题

> "Harness layers are coupled in ways that make local optimization fragile."
> **译文**: Harness 层之间的耦合方式使得局部优化变得脆弱。

**关键耦合关系**:
- 执行环境通过包可用性、重置语义、延迟等方式改变评估结果
- 工具描述消耗上下文预算并影响模型行为
- 可观测性追踪只有同时以相同粒度捕获身份和权限状态时才成为治理证据
- 评估设计通过奖励某些恢复循环、惩罚其他循环来反馈编排

> "A prompt, tool, memory, sandbox, verifier, or monitor may look beneficial in isolation while degrading the whole rollout when combined with the rest of the control loop."
> **译文**: 提示词、工具、记忆、沙箱、验证器或监视器在孤立来看可能是有益的，但当与控制循环的其余部分结合时，可能会降低整体部署效果。

### 从 Agent 框架到 Agent 平台

| 维度 | 框架（Frameworks） | 平台（Platforms） |
|------|-------------------|-------------------|
| 范围 | 局部抽象（Agent、工具、记忆） | 持久化工作区、托管沙箱、身份、计费、可观测性... |
| 核心问题 | "如何构建一个 Agent？" | "如何运维一个 Agent 集群，使其行为在时间上保持可审查和可逆？" |
| 生命周期 | 开发/调试 | 部署/运维/合规 |

---

## 6. 开放问题与未来方向

### 6.1 强化和扩展执行环境

> "The open problem is to make the runtime substrate both measurable and composable."
> **译文**: 开放问题是如何使运行时基础设施既可测量又可组合。

需要解决的问题:
- 针对提示注入、目标误对齐和复合放大的**共同安全评估**
- 决定何时使用容器、microVM、OS 级权限边界、桌面 VM、浏览器环境或学习型替代环境的**成本模型**
- 跨本地、云端和混合部署保持语义的**可移植性层**

### 6.2 维护长周期 Agent 的可靠状态

> "The deepest context problem is... how to keep an agent's working state aligned with the true task state over long horizons."
> **译文**: 最深层上下文问题是如何在长时间跨度内使 Agent 的工作状态与真实任务状态保持一致。

研究议程应将上下文管理重构为 **状态估计（state estimation）** 问题：
- 能否量化每次压缩、检索或遗忘中丢失了多少任务相关信息？
- 能否界定 Agent 内部状态与真实任务状态的偏差？
- 需要不确定性感知摘要、来源追溯、矛盾处理、显式过期标记和恢复程序

### 6.3 从 Agent 轨迹诊断故障

> "Agent evaluation is still too often final-score-centric."
> **译文**: Agent 评估仍然过于以最终分数为中心。

**Trace-Native 评估**: 轨迹应成为计算结果分数、轨迹质量、故障归因和回归测试的主要对象。

> "Reflexion showed that agents can learn from their own traces in short-horizon settings; extending this idea to long-running, multi-session harnesses remains open."
> **译文**: Reflexion 展示了 Agent 可以在短周期设置中从自身轨迹中学习；将这一思想扩展到长期运行的、多会话的 harness 仍然是一个开放问题。

### 6.4 标准化的交接协议

> "What is missing is a cross-layer handoff contract."
> **译文**: 缺少的是一个跨层的交接契约。

交接应传递: 意图、约束、权限、制品、来源、预算状态、风险等级、追踪历史和未解决决策。

### 6.5 保持 Harness 在模型改进时仍然有用

> "Every wrapper, reset, verifier, planner, memory rule, and permission gate encodes an assumption about what the model cannot do reliably on its own."
> **译文**: 每个包装器、重置、验证器、规划器、记忆规则和权限门都编码了一个关于模型自身不能可靠完成什么任务的假设。

> "A concrete version: context resets that were useful for one model became dispensable for a stronger model, and removing them reduced cost without degrading quality."
> **译文**: 一个具体的例子：对某个模型有用的上下文重置，在更强的模型上变得可有可无，移除它们后成本降低了但质量没有下降。

**Meta-Engineering 议程**:
- **自适应简化**: 在任务、工具和模型能力变化时，harness 持续问哪些控制仍然必要
- **Meta-Harness**: 提示、工具和控制循环可作为优化目标搜索
- **Harness A/B 测试**: 影子模式或 A/B 测试跨 harness 变体
- **Benchmark Overfitting 风险**: 仅对狭窄套件进行自我优化的 harness 可能变得脆弱

---

## 7. 生态系统映射的发现

### 170+ 项目分布规律

| ETCLOVG 层 | 覆盖密度 | 说明 |
|------------|---------|------|
| E (Execution) | 高 | 编码、Web、终端、计算机使用 Agent 都需要可运行环境 |
| T (Tooling) | 高 | 工具契约和控制循环是 Agent 运行的基本要求 |
| C (Context) | 中等 | 通常嵌入在更大的框架中，而非独立发布 |
| L (Lifecycle) | 高 | 控制循环、编排器、任务运行器 |
| O (Observability) | 较薄 | 更多存在于商业平台而非开源 |
| V (Verification) | 高 | 基准测试、评估框架、验证器 |
| G (Governance) | 最薄 | 大部分在商业平台，开源工具较少 |

### 代表性系统的 ETCLOVG 覆盖

| 系统 | 源码来源 | 覆盖层 | 核心设计信号 |
|------|---------|--------|-------------|
| **Claude Code** | Anthropic | E, T, C, L, G | 高自由度本地编码工作流的生产参考：代码库感知提示、shell/tool 执行、权限/沙箱边界 |
| **OpenCode** | Anomaly | E, T, L | 角色分离、子 Agent 委托、编辑器/工具集成的可检查实现 |
| **Codex CLI** | OpenAI | E, T, L, V | 状态无关重放单 Agent 循环；结构化提示、工具调用重放、测试/验证反馈 |
| **OpenHands** | Wang et al. | E, T, C, L, V | 沙箱执行+shell/浏览器/工具交互+任务状态+面向评估的基准 |
| **SWE-agent** | Yang et al. | E, T, L, V | Agent-计算机接口：命令、观察、编辑动作、测试和远程执行后端 |
| **Symphony** | OpenAI | C, L, V, G | Issue 追踪和任务运行器作为持久化控制平面 |

---

## 8. 结论

> "This survey treats the agent harness as an independent engineering surface and argues that infrastructure quality, not model capability alone, sets the ceiling on real-world agent reliability."
> **译文**: 本综述将 Agent harness 视为一个独立的工程层面，并主张基础设施质量——而非单纯的模型能力——设定了现实世界中 Agent 可靠性的上限。

### 核心启示

1. **不要盲目追求更强的模型** — 对于长周期任务，Harness 的质量在边际上更重要
2. **Harness 有七层需要关注** — 从执行环境到治理安全，缺一不可
3. **Observability 和 Governance 是一等公民** — 不是 Lifecycle Hooks 的副产品
4. **成本-质量-速度必须一起权衡** — 不能单独优化
5. **Harness 层是耦合的** — 局部优化可能导致全局退化
6. **模型变强后 Harness 需要简化** — 每层控制都编码了一个关于模型不能做什么的假设
7. **评估不应只看最终分数** — 需要轨迹级诊断和故障归因

### 局限

- 语料偏向英语、GitHub 可见、开源项目
- 偏向编码 Agent 生态系统
- 闭源生产系统代表性不足（除非暴露了相关机制）

### 未来方向

> "The taxonomy itself is descriptive: turning ETCLOVG into a normative framework that can guide harness design decisions, rather than only classify them, is the natural next step."
> **译文**: 这个分类法本身是描述性的：将 ETCLOVG 转变为一个能够指导 harness 设计决策的规范性框架，而不仅仅是分类，是自然而然的下一步。

---

## 附录：核心参考文献速查

| 引用 | 内容 |
|------|------|
| Bölük (2026a) | 仅改工具格式获 10× 提升 |
| Bölük (2026b) | Binding-constraint thesis |
| Trivedy (2026) | 仅提示+上下文+验证钩子获 +13.7pp |
| Lee et al. (2026) | Meta-Harness 自动化优化达 76.4% |
| Yao et al. (2023) | ReAct 范式 |
| Liu et al. (2024) | U 形注意力曲线（Lost in the Middle） |
| Hong et al. (2025) | Context Rot |
| Marchand et al. (2026) | SandboxEscapeBench |
| Packer et al. (2023) | MemGPT（OS 风格记忆） |
| Park et al. (2023) | Generative Agents（Memory Stream） |
| OpenAI (2026a) | Harness Engineering 作为学科 |
| Anthropic (2025a,b,c,d,e,f,g) | 系列工程实践 |
| Anthropic (2026b) | Managed Agents 架构 |
| Anthropic (2026c) | 三 Agent 架构、简化 Harness |
| LangChain (2026a) | 89%追踪/52.4%评估的统计 |
| South et al. (2025) | 认证委托（OAuth for Agents） |
| Trail of Bits (2025) | MCP 安全攻击 |
| Debenedetti et al. (2024) | AgentDojo（提示注入基准） |
| Shim et al. (2023) | Reflexion（自我反省学习） |
