# Agent Harness 论文研读笔记

> 一个持续整理的 Agent Harness 领域论文阅读笔记集合。
> 核心问题：**什么是 Agent Harness？它和 Framework / SDK / Eval Harness 有什么区别？一个好的 Harness 应该具备什么条件？**

---

## 📚 已收录论文

| # | 论文 | 类型 | 状态 |
|:-:|------|------|:----:|
| 1 | **What makes a harness a harness** — Macedo (2026) | 概念定义 ✅ | [完整阅读笔记 →](./what-makes-a-harness/) |
| 2 | **Code as Agent Harness** — Ning 等 (2026) | 系统性综述 | ⏳ 整理中 |
| 3 | **Agent Harness Engineering: A Survey** — Li 等 (2026) | 工程实践综述 | ⏳ 整理中 |

---

## 论文 ①：What makes a harness a harness

> **必要且充分条件：Agent Loop + Tool Interface + Context Management + Control Mechanisms**

[查看完整阅读笔记 →](./what-makes-a-harness/)

### 一句话

这篇论文给了 **"什么是 Agent Harness"** 一个可操作的答案——用 **T1–T4 四个条件**的准入测试，任何系统拿来一问便知。

### 核心框架

**T1–T4 准入测试：**

| 条件 | 问题 | 及格线 |
|:----:|------|--------|
| **T1** Agent Loop | 有没有推理→行动→观察的循环？ | 自适应（下一步取决于上一步的观察） |
| **T2** Tool Interface | 能不能感知并**改变**外部环境？ | 可写（编辑/执行），不只是只读 |
| **T3** Context Management | 有没有主动管理上下文？ | **内容驱动**（task-aware），不是机械截断 |
| **T4** Control Mechanisms | 有没有不依赖模型配合的控制？ | 有效性独立于模型的合作意愿 |

四个 ✅ → Agent Harness；任何一个 ❌ → 落入相邻类别。

### 边界区分

| 概念 | 与 Harness 的关键区别 |
|------|---------------------|
| Agent Framework | 组合角色（❌ T2），不直接作用于环境 |
| Agent SDK | 提供积木块（❌ T1），不组装闭环 |
| IDE Plugin | 光标补全（❌ T1 ❌ T4），不关循环不验证 |
| Eval Harness | **事后**打分（❌ T1 内层循环），不参与执行 |
| Orchestrator | 固定图（❌ T1），非自适应循环 |

### 金句

> *"It is that layer, not the prompt, that separates a demo that impresses from a product that holds up."*
>
> *"The test decides **whether** a system is a harness. The anatomy qualifiers measure **how** robust it is. Treating those two questions as one is the source of much of the terminological mess."*

---

## 论文 ②：Code as Agent Harness（预告）

> **视角：** 代码不再只是 LLM 的输出产物，而是 Agent 推理、行动、环境建模的**操作介质**。
>
> **分类：** 三层体系——Harness Interface（接口）→ Harness Mechanisms（机制）→ Scaling the Harness（扩展）
>
> **覆盖：** 5 个应用领域（编程助手 / GUI 代理 / 科学发现 / 个性化 / 具身智能）+ 7 个开放挑战

⏳ 阅读笔记整理中……

---

## 论文 ③：Agent Harness Engineering: A Survey（预告）

> **视角：** Harness 才是 Agent 可靠性的**约束条件**（Binding-Constraint Thesis），而非模型本身。
>
> **分类：** ETCLOVG 七层——Execution / Tooling / Context / Lifecycle / Observability / Verification / Governance
>
> **实证：** 映射 170+ 开源项目，Harness 改动能带来 **10× 提升**。

⏳ 阅读笔记整理中……

---

## 更新日志

- **2026-07-03**：创建站点，收录论文①阅读笔记（完整逐章解读 + 7 张示意图）
