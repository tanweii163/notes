# 单 Agent Token / 推理成本优化 — 技术调研报告

> **调研范围:** arXiv 最新论文 (2025-2026), 聚焦单 Agent (非多智能体) 场景下的 Token 和推理成本优化
> **筛选结果:** 125 篇候选 → 过滤 42 篇多智能体 → **83 篇单 Agent 论文** → 深度阅读 **7 篇核心论文**
> **撰写日期:** 2026-05-27

---

## 目录

1. [概述与问题背景](#1-概述与问题背景)
2. [技术路径全景图](#2-技术路径全景图)
3. [路径一: 推理开销诊断与分析](#3-路径一-推理开销诊断与分析)
4. [路径二: 动作空间压缩](#4-路径二-动作空间压缩)
5. [路径三: 自适应推理 Effort 选择](#5-路径三-自适应推理-effort-选择)
6. [路径四: 上下文/轨迹剪枝](#6-路径四-上下文轨迹剪枝)
7. [路径五: Agent 记忆压缩与蒸馏](#7-路径五-agent-记忆压缩与蒸馏)
8. [路径六: 预算感知模型路由](#8-路径六-预算感知模型路由)
9. [路径七: 确定性回放与录制重放](#9-路径七-确定性回放与录制重放)
10. [技术路线对比与选型建议](#10-技术路线对比与选型建议)
11. [对 Agent 成本绩效的落地建议](#11-对-agent-成本绩效的落地建议)

---

## 1. 概述与问题背景

### 1.1 为什么 Agent 成本是个特殊问题？

LLM Agent 的成本结构与单次推理有本质区别:

| 维度 | 单次 LLM 调用 | Agent 工作流 |
|------|--------------|-------------|
| Token 消耗模式 | 一次性输入+输出 | **轨迹不断累积**, 输入 token 随步骤增长 |
| 成本瓶颈 | 模型大小 × Token 数 | 轨迹膨胀 + 多轮推理 + Tool 输出 |
| 延迟敏感度 | TTFT/TPOT | 串行依赖, 每一步的延迟累加 |
| 优化空间 | 模型压缩/量化 | **动作表示 + 轨迹管理 + 路由策略** |

关键洞察: Agent 的输入 token 往往占 **99%** 以上的总 token 消耗 (OpenRouter 2025 年 9 月数据显示 Claude 4 Sonnet 每日 100B token 中 99% 是输入 token), 而输出 token 仅占约 1%。这意味着**优化输入 token 是 Agent 成本控制的核心战场**。

### 1.2 成本构成的三大层次

根据 TaxBreak 论文的分解方法, Agent 推理成本可分解为:

1. **框架层 (Framework Translation)** — Python 调度、ATen 分发等软件栈开销
2. **库层 (CUDA Library Translation)** — cuBLAS/cuDNN 前端开销
3. **内核启动层 (Kernel Launch)** — `cudaLaunchKernel` 到 GPU 执行之间的开销

关键发现: MoE 模型每输出 token 分发的内核数量是 dense 模型的 **8-11 倍**, 主机端开销更大。对于 Agent 场景, 多步推理放大了每一层的开销累积。

---

## 2. 技术路径全景图

从 83 篇论文中提炼出 **7 条核心技术路径**:

```
┌─────────────────────────────────────────────────────────────┐
│                  单 Agent 成本优化技术全景                      │
├───────────┬──────────────────┬────────────────┬──────────────┤
│  技术路径   │   核心思想        │   Token 节省    │  实现复杂度   │
├───────────┼──────────────────┼────────────────┼──────────────┤
│ ① 开销诊断  │ 分析瓶颈在哪层    │  间接(指导优化)  │  低(工具化)   │
│ ② 动作压缩  │ 压缩决策空间      │   30-60%       │  高(需训练)   │
│ ③ Effort自适应│ 动态分配推理级别  │   30-53%       │  中(轻量路由)  │
│ ④ 轨迹剪枝  │ 移除无用/冗余上下文│   40-60%       │  低(LLM驱动)  │
│ ⑤ 记忆蒸馏  │ 压缩历史到检索层   │   11x-50x      │  中(离线+检索) │
│ ⑥ 预算路由  │ 按步骤分配模型能力  │  20-50%        │  高(RL训练)   │
│ ⑦ 录制回放  │ 确定性重复执行     │   99%          │  中(任务特定)  │
└───────────┴──────────────────┴────────────────┴──────────────┘
```

---

## 3. 路径一: 推理开销诊断与分析

### 核心论文: TaxBreak (2603.12465)

**TaxBreak: Unmasking the Hidden Costs of LLM Inference Through Overhead Decomposition**

- **机构:** CMU NeuroAI Computer Architecture Lab
- **验证平台:** NVIDIA H100, H200

### 核心方法

TaxBreak 提出了一种 trace-driven 的方法, 将主机端编排开销分解为三个互斥且完备的组件:

```
T_Host = ΔFT (框架翻译) + ΔCT (CUDA库翻译) + ΔKT (内核启动)
```

并引入 **Host-Device Balance Index (HDBI)**:

```
HDBI = T_DeviceActive / (T_DeviceActive + T_Orchestration) ∈ (0,1)
```

- HDBI → 0: 主机端受限 (需要优化软件栈)
- HDBI → 1: 设备端受限 (需要优化 GPU 计算)

### 关键发现

| 发现 | 数据 |
|------|------|
| MoE 模型核数 | 每输出 token **8-11 倍**于 dense 模型 |
| CPU 单线程性能影响 | 更快的 CPU 减少编排开销 **10-29%** |
| 端到端延迟改善 | 提升 CPU 可改善 **11-14%** (即使 GPU 更慢) |
| 诊断指导 | 区分是优化软件栈还是设备负载 |

### 对你项目的启示

✅ **可以直接落地:** 使用 TaxBreak 的 profiling 方法论诊断你的 Agent 推理瓶颈, 判断成本卡在哪个层面。你可以:

1. 对 Agent 工作流做一次完整的 Host/Device 分解
2. 如果 HDBI 显示 host-bound → 考虑 torch.compile 或减少 Python 调度开销
3. 如果 kernel 启动次数是瓶颈 → 考虑 kernel fusion / CUDA Graphs
4. 注意 Agent 场景下的 CPU 单线程性能 (不是核心数)

---

## 4. 路径二: 动作空间压缩

### 核心论文: Latent Action Reparameterization (LAR) (2605.18597)

**Latent Action Reparameterization for Efficient Agent Inference**

- **机构:** Université de Montréal, Yale, DeepWisdom 等
- **代码:** https://github.com/EZ-hwh/LAR

### 核心洞察

当前 Agent 系统中, 动作用低层级的文本输出表示, 每个 token 构成一个显式决策。这导致**有效决策视野过大**——即使是语义简单的行为也需要多步低层级动作。

### 技术方案

LAR 学习一个**紧凑的潜在动作空间**, 其中每个潜在动作对应一个多步语义行为:

1. **压缩** low-entropy 的结构性重复模式 (system prompts, tool 调用语法, 重复配置)
2. **保留** high-entropy 的参数化输入 (搜索查询、数值实体)
3. 潜在动作直接从 Agent 轨迹中学习, 集成到模型中端到端优化

### 效果

| 指标 | 提升 |
|------|------|
| 有效决策视野 | 显著缩短 |
| 推理时间 | 显著降低 (固定计算预算下) |
| 任务成功率 | 维持或改善 |

### 对你项目的启示

⚠️ **需要训练, 短期成本高, 但长期收益大:**

1. 分析你的 Agent 轨迹中哪些是低信息密度的 "boilerplate" 动作
2. 考虑将常见的多步操作封装为更高层的 API/工具调用
3. 长期可训练一个轻量压缩器, 将低层级动作序列映射为潜在表示

---

## 5. 路径三: 自适应推理 Effort 选择

### 核心论文: Ares (2603.07915)

**Ares: Adaptive Reasoning Effort Selection for Efficient LLM Agents**

- **机构:** UC Santa Barbara, Accenture Center for Advanced AI

### 核心洞察

现代 thinking LLM (如 GPT-5, Gemini-3) 支持可配置的推理级别 (high/medium/low), 但**静态策略是次优的**: 全部用低 effort 会显著降性能, 全部用高 effort 则成本过高。Agent 应当在复杂步骤 (如导航网站结构) 用高推理, 简单步骤 (如打开 URL) 用低推理。

### 技术方案

Ares 训练一个**轻量级 Router (Qwen3-1.7B)** 来按步骤动态选择推理 effort:

```
训练流程:
1. 收集高质量轨迹 (使用高 effort 采样)
2. 对每一步标注"最低足够"的推理级别 (多轮采样验证)
3. 生成推理 rationale (3-5句话解释为什么选该级别)
4. SFT 微调 Router
5. GRPO 强化学习进一步优化
```

### 效果

| 基准 | Token 节省 | 性能影响 |
|------|-----------|---------|
| TAU-Bench (工具使用) | **52.7% 减少** | 轻微提升 |
| BrowseComp-Plus (深度研究) | 显著节省 | 保持 |
| WebArena (网页) | 显著节省 | 保持 |

### 对你项目的启示

✅ **高可行性的路径:** 如果你使用支持 thinking level 的模型

1. 先用 Ares 的数据标注方法分析你的 Agent 轨迹——哪些步骤需要高推理
2. 训练一个小路由器 (1.7B 级别成本很低)
3. 路由器按步骤调度 effort, KV cache 可复用 (同模型内切换)
4. 这是当前性价比最高的路径之一

---

## 6. 路径四: 上下文/轨迹剪枝

### 6.1 SWE-Pruner (2601.16746)

**SWE-Pruner: Self-Adaptive Context Pruning for Coding Agents**

- **机构:** 上海交通大学 LLMSE Lab, 抖音集团

### 核心洞察

人类开发者在阅读代码时会"选择性略读"——聚焦当前任务相关的部分。Agent 也应该做类似的事情: 根据当前目标 (如 "focus on error handling") 选择性保留上下文。

### 技术方案

- 训练一个轻量级 **Neural Skimmer (0.6B 参数)**
- 根据当前任务目标 (explicit goal hint) 动态选择上下文中的相关行
- 在 SWE-Bench Verified 上实现 **23-54% Token 缩减**, 成功率甚至略有提升
- 在 LongCodeQA 上达到 **14.84× 压缩**

### 6.2 Trajectory Reduction (2509.23586)

**Reducing Cost of LLM Agents with Trajectory Reduction**

- **机构:** 北京大学

### 核心洞察

Agent 轨迹中存在大量的 **无用、冗余、过期信息**:

| 类型 | 示例 |
|------|------|
| 无用信息 | 工具调用失败后的完整错误栈 (已被后续修复覆盖) |
| 冗余信息 | 反复查看同一文件的不同版本 |
| 过期信息 | 老的探索路径, 已被新的方向取代 |

### 技术方案

- 使用一个 cost-efficient 的 LLM 作为 reflection 模块
- 采用滑动窗口策略, 在每次长步骤后自动压缩
- 只有当压缩收益超过阈值时才应用 (避免频繁压缩的开销)

### 效果

| 指标 | 提升 |
|------|------|
| 输入 Token 减少 | **39.9% - 59.7%** |
| 总计算成本减少 | **21.1% - 35.9%** |
| Agent 性能 | 保持不变 |

### 对你项目的启示

✅ **最容易落地的路径:** 无需训练, 直接用 LLM 做轨迹压缩

1. 在你的 Agent 中定期调用轨迹压缩 (如每 5-10 步)
2. 识别三类可删除信息: 无用/冗余/过期
3. 使用滑动窗口控制压缩开销
4. SWE-Pruner 的思路也可以补充——训练一个超轻量的 Skimmer 按任务目标剪枝

---

## 7. 路径五: Agent 记忆压缩与蒸馏

### 核心论文: Structured Distillation for Personalized Agent Memory (2603.13017)

**Structured Distillation for Personalized Agent Memory: 11x Token Reduction with Retrieval Preservation**

- **作者:** Sydney Lewis

### 核心洞察

Agent 的对话历史携带完整信息太贵。但人真正记住的远少于原始对话——**"决定的结论、改的参数、解决的错误"**。

### 技术方案

将每个对话回合压缩为**结构化复合对象**:

```
蒸馏后的对象:
├── exchange_core:      1-2句总结 (类似 commit message)
├── specific_context:   一个关键技术细节 (类似 diff)
├── room_assignments:   1-3个主题分类
└── files_touched:      正则提取的文件路径
```

### 效果

| 指标 | 数据 |
|------|------|
| 压缩率 | **11x** (平均 814 tokens → 74 tokens/exchange) |
| 检索保留 (Vector) | 达到 verbatim 的 MRR |
| 检索保留 (BM25) | 显著退化 |
| 1,000 条对话 | ~39K tokens (原 ~407K) |

### 对你项目的启示

✅ **高价值路径:** 如果你有长历史对话或多轮 Agent 交互

1. 将 Agent 的历史交互离线蒸馏为结构化索引
2. 在线使用时只加载蒸馏后的检索结果
3. 原始数据保留用于 drill-down
4. 最佳组合: verbatim 的 keyword search + 蒸馏的 vector search

---

## 8. 路径六: 预算感知模型路由

### 核心论文: Budget-Aware Agentic Routing (2602.21227)

**Budget-Aware Agentic Routing via Boundary-Guided Training**

- **机构:** University of Cambridge, Microsoft M365 Research

### 核心洞察

不是每个 Agent 步骤都需要最强的模型。但简单的路由策略 (如随机选择) 在 Agent 场景下会失败——**早期错误会传播**, 反馈仅在轨迹结束时才有。

### 技术方案

形式化为两种范式的路由问题:

**1. Soft-Budget (效率前沿):** 在成功率和成本之间做 Pareto 优化

**2. Hard-Budget (严格限制):** 在固定预算 (如 $0.50/任务) 下最大化成功率

训练方法: **Boundary-Guided Training**

```
1. 用两个极端策略 (always-small / always-large) 构建难度分类
2. Easy/Intractable → 直接标注
3. Hard → 分层采样合成 cost-efficient 轨迹
4. BoPO (Boundary-Guided Policy Optimization) 防止"always-small"坍塌
5. Budget-Constrained Decoding 在推理时严格执行预算
```

### 效果

| 场景 | 效果 |
|------|------|
| 效率前沿 | 匹配 large-only 性能, 成本大幅降低 |
| 严格预算 | 无需专门训练即可适应不同预算上限 |
| 跨基准泛化 | 科学发现 / 指令跟随 / 工具使用均有效 |

### 对你项目的启示

⚠️ **需要强化学习训练, 实施周期长, 但效果显著**

1. 分析你的 Agent 工作流中哪些步骤是 "easy" (小模型就够) 哪些是 "hard" (需要大模型)
2. 使用边界策略 (全小/全大) 建立 baseline
3. 训练路由策略时注意防止退化到 always-small
4. 如果预算严格, 加入 Budget-Constrained Decoding

---

## 9. 路径七: 确定性回放与录制重放

### 核心论文: Good to Go: The LOOP Skill Engine (2605.14237)

**Good to Go: The LOOP Skill Engine That Hits 99% Success and Slashes Token Usage by 99% via One-Shot Recording and Deterministic Replay**

### 核心洞察

对于**周期性重复的 Agent 任务**, LLM 的随机性导致不可预测的失败, 而重复调用产生 prohibitive 的 token 成本。

### 技术方案

- **一次录制 (One-Shot Recording):** 首次执行时录制完整的确定性执行路径
- **确定性回放 (Deterministic Replay):** 后续执行时回放录制的路径, 不调用 LLM
- LLM 只用于异常处理和未知分支

### 效果

| 指标 | 数据 |
|------|------|
| Token 减少 | **99%** |
| 成功率 | **99%** |

### 对你项目的启示

✅ **对于固定模式的 Agent 任务极其高效**

1. 识别你的 Agent 工作流中哪些是可重复的固定流程
2. 首次执行时录制成功路径
3. 后续相同任务走确定性回放, 仅处理异常时调用 LLM
4. 适合: 定时任务、数据 ETL、CI/CD、监控报表等

---

## 10. 技术路线对比与选型建议

### 对比矩阵

| 技术 | Token 节省 | 实施成本 | 维护成本 | 适用场景 | 依赖 |
|------|:---------:|:--------:|:--------:|---------|------|
| **TaxBreak 诊断** | 间接 | ⭐ | ⭐ | 所有 Agent | 无 |
| **LAR 动作压缩** | 30-60% | ⭐⭐⭐ | ⭐⭐ | 长决策序列 Agent | 需训练数据 |
| **Ares Effort 自适应** | 30-53% | ⭐⭐ | ⭐ | 支持 thinking level 的模型 | 轻量 Router |
| **SWE-Pruner 剪枝** | 23-54% | ⭐⭐ | ⭐⭐ | Coding Agent | 0.6B Skimmer |
| **轨迹缩减** | 40-60% | ⭐ | ⭐ | 长轨迹 Agent | 一个 LLM 调用 |
| **记忆蒸馏** | 11x-50x | ⭐⭐ | ⭐ | 长历史记忆 | 离线处理 |
| **预算路由** | 20-50% | ⭐⭐⭐ | ⭐⭐ | 多模型可用 | RL 训练 |
| **录制回放** | 99% | ⭐⭐ | ⭐ | 固定模式任务 | 无 |

### 推荐实施阶段

```
Phase 1 (快速见效, 1-2周)
├── TaxBreak 诊断: 了解当前成本分布
├── 轨迹缩减: 直接调用 LLM 压缩无用/冗余/过期内容
└── 录制回放: 对固定任务做确定性执行

Phase 2 (系统优化, 2-4周)
├── Ares: 训练 effort Router 动态分配推理级别
├── 记忆蒸馏: 对长历史做结构化压缩
└── SWE-Pruner: 对 coding 场景做上下文剪枝

Phase 3 (深度改造, 4-8周)
├── LAR: 动作空间压缩
├── 预算路由: 多模型策略优化
└── 组合上述技术进行端到端优化
```

---

## 11. 对 Agent 成本绩效的落地建议

### 第一步: 建立成本可见性

借鉴 TaxBreak 的思路, 但你不需要做到 GPU kernel 级别的分解。对你的 Agent 工作流做如下诊断:

```python
# 简化的成本分解模板
每步成本 = 输入 tokens × 价格 + 输出 tokens × 价格

成本分解:
├── System prompt tokens      # 固定基数
├── 记忆/历史 tokens          # 随时间增长 ← 核心优化目标
├── 工具输出 tokens           # 每次调用产生 ← 第二大优化目标
├── 推理 tokens               # thinking token ← 第三大优化目标
└── 动作 tokens               # 输出动作 ← 受动作表示影响
```

### 第二步: 选择首轮切入点

根据你的 Agent 场景, 推荐的首轮方案:

| 场景 | 首轮方案 | 预期节约 |
|------|---------|:--------:|
| 长对话 Agent (多轮交互) | **轨迹缩减** + **记忆蒸馏** | 40-60% |
| Thinking Agent (推理模型) | **Ares Effort 自适应** | 30-53% |
| Coding Agent | **SWE-Pruner** + **轨迹缩减** | 40-60% |
| 定时/重复任务 | **录制回放 (LOOP)** | 99% |
| 已有多个模型可用 | **预算路由** | 20-50% |
| 通用场景, 快速见效 | **轨迹缩减** | 40-60% |

### 第三步: 组合优化

多种技术可以叠加使用, 产生乘数效应:

```
最佳组合示例:
┌─────────────────────────────────────────┐
│  ① 轨迹缩减 (40-60% 输入 token 减少)      │
│  +                                       │
│  ② Ares Effort 自适应 (30-53% 推理节省)   │
│  +                                       │
│  ③ 预算路由 (20-50% 模型成本节省)          │
│  =                                       │
│  综合节省: 60-85%                         │
└─────────────────────────────────────────┘
```

### 第四步: 持续监控

建立 Agent 成本仪表盘, 跟踪以下核心指标:

1. **Cost Per Task (CPT)** — 每任务总成本
2. **Cost Per Step (CPS)** — 每步平均成本
3. **Token Efficiency Ratio** — 有用 token / 总 token
4. **Waste Ratio** — 可压缩 token / 总 token
5. **HDBI (如可测量)** — 主机 vs 设备受限情况

---

## 参考文献

| ID | 论文 | arXiv |
|----|------|-------|
| 1 | TaxBreak: Unmasking the Hidden Costs of LLM Inference Through Overhead Decomposition | [2603.12465](https://arxiv.org/abs/2603.12465) |
| 2 | Latent Action Reparameterization for Efficient Agent Inference (LAR) | [2605.18597](https://arxiv.org/abs/2605.18597) |
| 3 | Ares: Adaptive Reasoning Effort Selection for Efficient LLM Agents | [2603.07915](https://arxiv.org/abs/2603.07915) |
| 4 | SWE-Pruner: Self-Adaptive Context Pruning for Coding Agents | [2601.16746](https://arxiv.org/abs/2601.16746) |
| 5 | Structured Distillation for Personalized Agent Memory (11x Token Reduction) | [2603.13017](https://arxiv.org/abs/2603.13017) |
| 6 | Budget-Aware Agentic Routing via Boundary-Guided Training | [2602.21227](https://arxiv.org/abs/2602.21227) |
| 7 | Good to Go: The LOOP Skill Engine (99% Token Reduction) | [2605.14237](https://arxiv.org/abs/2605.14237) |
| 8 | Reducing Cost of LLM Agents with Trajectory Reduction | [2509.23586](https://arxiv.org/abs/2509.23586) |

---

> **总结:** 单 Agent 成本优化不需要从零开始。最推荐的快速路径组合是 **轨迹缩减 (快速见效) + Ares 自适应 Effort (系统优化)**。如果你们有固定模式的重复任务, **录制回放 (LOOP)** 直接 99% 节省值得优先考虑。建议先做一次成本诊断 (TaxBreak 方法论), 找到最大浪费点再针对性优化。
