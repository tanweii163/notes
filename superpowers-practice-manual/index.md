# Superpowers 实践手册

> 基于真实项目（codex-weekly-report）的实践记录，不是理论翻译。

---

## 1. 概述

**Superpowers** 是一套 AI 编程代理 (coding agent) 的技能 (skill) 集合。每个 skill 是一个 Markdown 文件，告诉 AI 在特定场景下该怎么思考、按什么步骤走、别犯什么错。

### 它解决了什么问题

裸的 AI 编程代理有两个致命毛病：

1. **太急**：一上来就写代码，没搞清楚需求 → 返工
2. **太散**：面对多步骤任务，想一步走一步 → 到后面忘了前面

Superpowers 用一套**强约束的流程**来解决：

```
想清楚（brainstorming）→ 写设计（writing-plans/specs）
→ 写测试（TDD）→ 执行（subagent/inline）
→ 验证（verification）→ 审查（code review）→ 收尾（finishing）
```

每个环节都是一个 skill，告诉 AI："现在你在这个环节，只做这个环节的事，别跳到下一步。"

### 核心理念

| 理念 | 含义 |
|------|------|
| **Progressive disclosure** | 每个 skill 文件很短（~100 行），只讲当下该知道的 |
| **Surgical precision** | 设计阶段不写代码，执行阶段不改设计 |
| **Verification before assertions** | 说"完成了"之前，先跑测试看到绿色 |
| **Human in the loop** | 关键决策点（合并、丢弃、大规模重构）由人说了算 |

---

## 2. 安装与启动

### 安装方式

有两种：

```bash
# 方式 1：全局安装（影响所有项目）
pi install superpowers

# 方式 2：项目本地安装（只影响当前项目）← 我们用的
cd mysuperpower
pi install -l superpowers
```

**为什么选本地安装？** 全局安装会让所有项目都走 superpowers 流程，不想要。本地安装只在这个目录生效。

安装后目录结构：

```
mysuperpower/
  .pi/git/github.com/obra/superpowers/
    skills/           ← 14 个 skill 文件
    hooks/            ← hook 配置（session-start 等）
    .pi/extensions/   ← pi 扩展代码
```

### 启动流程

项目启动时，`hooks/session-start` 自动执行：

1. 检查项目环境
2. 加载 `using-superpowers` skill
3. 告诉 AI："你有这些 skill 可用，遇到匹配场景就用"

**关键点**：启动后 AI 就知道有哪些 skill，会自动匹配场景调用。不需要人每次说 "用 XXX skill"。

---

## 3. 核心流程

![标准工作流程图](imgs/workflow-flow.svg)

一个完整 feature 的标准流程：

```
  User 提需求
    ↓
  brainstorming        ← 不写代码，只澄清需求（3-5 个问题）
    ↓
  写 spec 文档         ← 设计文档，不含实现代码
    ↓
  writing-plans        ← 把 spec 拆成可执行的步骤
    ↓
  executing-plans      ← 或 subagent-driven-development
    ↓                   ↕ 每步配合 TDD（RED → GREEN）
  verification         ← 跑测试、生成报告，验证结果
    ↓
  requesting-code-review  ← 派 subagent 审查
    ↓
  修问题               ← receiving-code-review 约束怎么处理反馈
    ↓
  finishing            ← 合并 / PR / 保持 / 丢弃
```

**本项目的实际路径**（略有变形，因为直接在主分支开发）：

```
  "帮我写 Codex CLI 周报工具"
    ↓
  brainstorming（3 个问题澄清需求）
    ↓
  写 spec（docs/superpowers/specs/）
    ↓
  writing-plans（拆成 3 个任务）
    ↓
  subagent-driven-development（3 个子任务并行执行）
    ↓
  requesting-code-review（发现问题修复）
    ↓
  加新功能（event-level token tracking）
    ↓ brainstorming → spec → plan → inline TDD 执行（3 步，21 测试）
    ↓
  requesting-code-review（再审查）
    ↓
  收尾（finishing 不适用——直接提交在 main）
```

**注意**：finishing-a-development-branch 在本项目中未真正执行，因为我们在 `main` 分支上直接开发，没有 feature 分支可合并。

---

## 4. 技能图鉴

> 以下逐个介绍 14 个 superpowers skill，均基于原始 SKILL.md 内容编写。

### 4.1 流程技能（按使用顺序排列）

#### using-superpowers

**功能：** 所有 superpowers 的入口和基础规则。设定一条铁律：**在任何回应或行动之前，先检查是否有适用的 skill。** 即使是想问一个澄清问题，先检查 skill。同时还定义了 skill 优先级（流程 skill > 实现 skill）和常见"借口识别表"（Red Flags）。

**适用场景：** 每次会话开始时自动加载。是所有 skill 的"元规则"。

**触发方式：** 自动激活——hook `session-start` 加载。

**与其他 skill 的关系：** 被所有其他 skill 引用。定义了 "skill 优先级"（brainstorming/systematic-debugging > 其他）和 red flags 机制。不直接调用其他 skill，但约束所有 skill 的使用规则。

**本次实践：** 全程自动激活。我们遵循了 skill 优先级——先 brainstorming 后写 spec，先 TDD 后实现。但也遇到了"red flag"悖论：有时 skill 检查太频繁会打断自然流程。

---

#### brainstorming

**功能：** 把模糊的想法变成完整的设计文档（spec）。强制要求：在写任何代码之前，必须先完成设计并获得用户批准。流程分 9 步：探索项目上下文 → 逐个提问澄清需求 → 提出 2-3 个方案对比 → 展示设计 → 写 spec 文档 → 自我审查 → 用户审查 → 转交 writing-plans。

**适用场景：** 任何创造性工作——新功能、新组件、行为修改。即使是"简单到不需要设计"的项目也必须走。

**触发方式：** 自动激活（关键词："let's build", "create", "add feature"等）。

**与其他 skill 的关系：** 终端状态是调用 `writing-plans`。明确禁止调用任何实现 skill（如 frontend-design）。

**本次实践：** 在初期（写 codex-weekly-report）和后来（加 event-level token tracking）各走了一次。第一次中途跳过了 spec 文档步骤（被用户纠正后补上），第二次完整走完。关键学习：逐个提问很重要，不要一次甩多个问题。

---

#### writing-plans

**功能：** 将 spec 转化为可执行的实现计划。每个计划包含精确的文件路径、完整的代码示例、测试命令和预期输出。**不允许占位符**——"TBD"、"TODO"、"implement later"都是计划失败。每个步骤是一个 2-5 分钟的操作："写测试" → "跑测试（看它失败）" → "写代码" → "跑测试（看它通过）" → "提交"。

**适用场景：** 有 spec 后，多步骤任务开始前。

**触发方式：** 自动激活（由 brainstorming 调用，或手动）。

**与其他 skill 的关系：** 终端分叉——推荐 `subagent-driven-development`（并行子任务），备选 `executing-plans`（本会话顺序执行）。

**本次实践：** 走了两次。第一次拆成 3 个任务，每个任务代码完整（包含函数签名和返回值类型）。但这也暴露出一个张力和矛盾——计划里的完整代码和 TDD 的"测试先行"有**直接冲突**（详见第五章第 5.1 节）。

---

#### test-driven-development

**功能：** 铁律——**没有失败的测试，不写生产代码**。三阶段循环：RED（写测试，看它失败）→ GREEN（写最小代码，看它通过）→ REFACTOR（清理）。核心论点：如果你没看到测试失败，你就不知道它是否测对了东西。

**适用场景：** 所有功能、bug 修复、重构、行为修改。例外（需人类许可）：一次性原型、生成代码、配置文件。

**触发方式：** 自动激活（任何涉及代码编写的场景）。

**与其他 skill 的关系：** 被 `writing-plans` 强制要求（TDD 粒度的步骤），被 `executing-plans`/`subagent-driven-development` 在每步执行时要求。`writing-skills` 将 TDD 的概念应用到文档编写。

**本次实践：** 早期用 subagent 执行时，subagent 实际跳过了 RED → GREEN 的循环（因为计划里已有完整代码）。后来改为 inline 执行后严格遵守了 TDD。关键矛盾：writing-plans 要求"完整代码在每步"，但 TDD 要求"不能先写生产代码"（详见第五章）。

---

#### executing-plans

**功能：** 顺序执行一个已写好的实现计划。读计划 → 辩证审查 → 逐任务执行 → 完成后调用 finishing。适合**不需要并行**的场景。

**适用场景：** 有 writing-plans 产出的计划，任务之间有依赖关系，不能用并行。

**触发方式：** 手动或由 writing-plans 调用。

**与其他 skill 的关系：** 终端调用 `finishing-a-development-branch`。前置是 `writing-plans`。备选是 `subagent-driven-development`（推荐后者）。

**本次实践：** 未使用。我们选择了 subagent-driven-development（因为有独立任务），后来又改用 inline 执行。

---

#### verification-before-completion

**功能：** 铁律——**没有新鲜验证证据，不能声称完成**。它规定了"声称完成"之前的门控函数：识别 → 运行 → 阅读 → 验证 → 然后才能声称。把"should work"、"probably fixed"这种模糊词定义为"撒谎"。

**适用场景：** 任何声称完成/修复/通过之前——提交前、创建 PR 前、任务完成前。

**触发方式：** 自动激活（检测到即将声称完成时）。

**与其他 skill 的关系：** 被 `systematic-debugging` 引用（Phase 4 验证修复），被 `receiving-code-review` 隐含要求（改一个测一个）。

**本次实践：** 隐式使用。每次声称"测试通过"时都跑了 `python3 test_report.py` 看到了 21/21 pass。但没有显式创建 checklist，这点不够严格。

---

#### requesting-code-review

**功能：** 派一个 subagent 审查代码。流程：获取 BASE/HEAD SHA → 填充审查模板（改了什么、需求是什么）→ 派 reviewer → 收到报告（Strengths / Issues / Assessment）→ 修问题。

**适用场景：** 完成任务后、实现主要功能后、合并前。subagent-driven-development 要求每个任务后审查一次。

**触发方式：** 手动或由 `subagent-driven-development` 调用。

**与其他 skill 的关系：** 被 `subagent-driven-development` 用于最终审查。和 `receiving-code-review` 形成审查的"发起→接收"两端（详见 4.4）。

**本次实践：** 走了两次。第一次用 subagent dispatch 失败（subagent 不返回结果），改为直接 inline 审查。第二次用的也是 inline。发现的真实问题：模型名大小写不统一、null info 处理用 continue。

---

#### receiving-code-review

**功能：** 收到审查反馈后的**正确反应流程**。核心：不要表演性同意（"你说得对！"）、不要盲改、要验证、该反驳就反驳。六步：READ → UNDERSTAND → VERIFY → EVALUATE → RESPOND → IMPLEMENT。

**适用场景：** 收到任何代码审查反馈时——来自 reviewer subagent、GitHub PR 评论、人类随口说的建议。

**触发方式：** 自动激活（收到反馈时）。

**与其他 skill 的关系：** 和 `requesting-code-review` 独立但互补——一个发起审查，一个处理审查结果。也可以独立应对非 subagent 来源的反馈。

**本次实践：** 部分使用。处理审查反馈时没有做表演性同意（好），但也没有显式走六步流程（不够严格）。早期对话中发现"receiving-code-review ≠ requesting-code-review 的对偶"，这是一个重要的理解纠正。

---

#### finishing-a-development-branch

**功能：** 开发完成后的收尾。四步：验证测试 → 检测环境 → 展示选项 → 执行选择。四种选项：合并到主分支、创建 PR、保持现状、丢弃。关键安全措施：丢弃操作需要用户输入 "discard" 确认。

**适用场景：** 所有任务完成，测试通过，需要决定如何整合工作。

**触发方式：** 手动或由 `executing-plans`/`subagent-driven-development` 终端调用。

**与其他 skill 的关系：** 是 `executing-plans` 和 `subagent-driven-development` 的终端状态。

**本次实践：** 未真正执行。因为我们直接在 `main` 分支上开发，没有 feature 分支可合并，也没有 worktree 可清理。唯一能做的就是验证测试（已手动完成）。

---

### 4.2 并行与调试技能

#### subagent-driven-development

**功能：** 用 subagent 执行计划——每个任务派一个全新 subagent，做完后派 reviewer 审查，通过后继续下一个。是 writing-plans 推荐的执行方式。亮点：每个 subagent 拿自己的 task brief（不读整个计划）、review 有两轮（spec 合规 + 代码质量）、支持 ledger 断点恢复。

**适用场景：** 有 writing-plans 产出的计划，任务之间独立或低耦合。

**触发方式：** 手动或由 writing-plans 调用。

**与其他 skill 的关系：** 前置 `writing-plans`，终端调用 `requesting-code-review`（最终审查）→ `finishing-a-development-branch`。备选 `executing-plans`。要求 subagent 使用 `test-driven-development`。

**本次实践：** 第一期走了完整的三任务流程——每个任务派 subagent 实现 + reviewer 审查。发现的问题：1) subagent 有时不返回结果（可能超时/超 context）；2) 审查后的修复增加了不少 token 消耗；3) review-package 脚本相对复杂。第二期改为 inline TDD 执行，更快但失去了 subagent 的独立上下文优势。

---

#### dispatching-parallel-agents

**功能：** 并行派遣多个 subagent 处理独立问题。适用于多个不相干的测试失败、多个子系统独立损坏。每次 dispatch 应该是一个独立的问题域，配精确的 scope 和 expected output。

**适用场景：** 3+ 个测试文件有不同根因的失败、多个子系统独立损坏、每个问题不需要其他问题上下文。**不适用：** 失败相互关联、需要全系统理解、subagent 会互相干扰。

**触发方式：** 手动。

**与其他 skill 的关系：** 和 `subagent-driven-development` 互补——SDD 是串行逐任务，这个是并行独立问题。都依赖 subagent 工具。

**本次实践：** 未使用。我们的 3 个任务是按依赖顺序串行的（Task 1 产出被 Task 2 消费），不适合并行。

---

#### systematic-debugging

**功能：** 四阶段调试法——Phase 1 找根因（不是表象）、Phase 2 模式分析（对比正常代码）、Phase 3 假设验证（一次一个变量）、Phase 4 实现修复（写测试→修→验证）。铁律：**没有完成 Phase 1，不能提修复方案。** 特有规则：如果 3+ 个修复失败了 → 问题不在代码，在架构设计。

**适用场景：** 任何技术问题——测试失败、生产 bug、意外行为、性能问题。

**触发方式：** 自动激活（检测到 bug 或失败时）。

**与其他 skill 的关系：** Phase 4 引用 `test-driven-development` 写失败测试。引用 `verification-before-completion` 验证修复。

**本次实践：** 隐式使用。在 real data 集成阶段遇到了 `info: null` 导致的 bug——我们没有跳过 Phase 1 直接改代码，而是先通过日志分析确定了根因（token_count 事件中 info 字段为 null），然后才修复。但如果有复杂的 bug，这个 skill 的价值会很大。

---

### 4.3 基础设施技能

#### using-git-worktrees

**功能：** 创建和管理隔离的 git worktree。流程：检测现有隔离 → 优先用平台原生工具 → fallback 到 `git worktree add`。做完后跑项目 setup（npm install/pip install）和 baseline 测试。

**适用场景：** 开始需要隔离的特征工作时（保护当前分支不受影响）。

**触发方式：** 手动。

**与其他 skill 的关系：** 被 `executing-plans` 和 `subagent-driven-development` 引用为前置条件（确保在隔离空间中工作）。

**本次实践：** 未使用。因为我们选择了直接在本地 `main` 上开发，没有开 worktree。如果未来项目变大、多人协作，这是一个值得用的技能。

---

#### writing-skills

**功能：** 教你如何创建 superpowers skill。核心思想：**写 skill 就是给文档做 TDD**。用 subagent 做基线测试（看没有 skill 时 AI 怎么犯错）→ 再写 skill → 再跑同样场景（看 AI 是否遵守）→ 不断堵漏洞。

**适用场景：** 创建新 skill、编辑已有 skill、部署前验证。

**触发方式：** 手动。

**与其他 skill 的关系：** 依赖 `test-driven-development` 作为前置知识（"写 skill 就是 TDD 应用于文档"）。产出被 `using-superpowers` 加载。

**本次实践：** 未使用。没创建新 skill，但理解了这个 skill 后，对"为什么 TDD 和其他 skill 有那么多防借口表"有了更深理解——它们是经过 subagent 基线测试后逐步堵出来的。

---

### 4.4 技能关系全景

![技能关系全景图](imgs/skill-relationship-map.svg)

**本次实践的实际路径（green path）：**

```
using-superpowers → brainstorming → writing-plans
                                     │
                          ┌──────────┴──────────┐
                          ▼                      ▼
                   subagent-driven-dev    inline TDD execution
                   (一期: 3 tasks)        (二期: 3 task cycles)
                          │                      │
                          └──────────┬───────────┘
                                     ▼
                              requesting-code-review
                                     │
                                     ▼
                              修复 → 完成
```

**本次未使用但属于标准流程的技能（gray path）：**
- `systematic-debugging` — 没有遇到复杂 bug
- `dispatching-parallel-agents` — 任务是串行依赖的
- `using-git-worktrees` — 选择在 main 开发
- `writing-skills` — 没有创建新 skill
- `finishing-a-development-branch` — 在 main 上开发，无可合并的分支
- `verification-before-completion` — 隐式使用但未显式走流程
- `executing-plans` — 用 subagent-driven-development 替代了

---

## 5. 踩过的坑

本章记录本次实践中遇到的**真实矛盾和失误**，不是理论预习。

### 5.1 Plan 写代码 vs TDD 测试先行

**这是本次实践最大的发现。**

![Plan vs TDD 矛盾](imgs/plan-vs-tdd.svg)

`writing-plans` 要求：
> "Complete code in every step — if a step changes code, show the code"

`test-driven-development` 要求：
> "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"

这两个要求**直接矛盾**。如果计划里写了完整代码，执行者（subagent 或 inline）就不可能"先看测试失败再写代码"——代码已经在计划里了。

**解决方案（妥协）：**
- Plan 定位为**接口和边界地图**——定义函数签名、返回值类型、文件位置
- TDD 定位为**执行纪律**——在执行过程中发现具体实现
- Plan 不再写"完整代码"，改为写"test case + interface contract"

实际效果：第一期 subagent 拿到了完整代码的计划，直接跳过了 RED→GREEN。第二期改成 inline 执行，手动删掉 plan 中的实现代码，才真正走完了 TDD。

### 5.2 Subagent 不返回结果

dispatch subagent 后有时收到 "No result provided"。可能原因：超时、上下文爆炸、内部错误被吞掉。

**教训：** 不要塞整段计划给 subagent；用 `task-brief` 脚本提取单任务；如果连续失败，切到 inline 执行。

### 5.3 Finishing 在我们的场景里不适用

`finishing-a-development-branch` 假设你在 feature 分支开发，需要一个合并回 main 的收尾。但我们直接在 main 上开发，所有提交已经合入。这个 skill 只有 Step 1（验证测试）有意义。

**教训：** 不是所有 skill 都适合所有项目。在 main 上做小改动，finishing 可以跳。

### 5.4 技能过度使用

有些场景不需要走完整 skill 流程："文件叫什么名"不需要 brainstorming，"改个变量名"不需要 writing-plans，"看一眼代码"不需要 systematic-debugging。

`using-superpowers` 的规则是"有 1% 可能就用"，但过度触发会打断流畅对话。**平衡点：** 用户说"不执行，只解释"时跳过；实际代码变更时严格遵守。

### 5.5 AI 审 AI 的盲区

请求审查时 reviewer (AI) 和作者 (AI) 本质是同一个模型，只是给了不同 prompt。Reviewer 可能漏掉作者也漏掉的问题，或做出和作者一样的隐含假设。实际发现了一些问题（大小写、continue），但也漏掉了（cross-date token 精度问题直到集成才知道）。

**建议：** 如果有条件，让人类做最终审查。

---

## 6. 你的角色（人类 vs AI 分工）

### 你应该主动做的

| 环节 | 动作 | 原因 |
|------|------|------|
| brainstorming | 回答问题，**不要说"随便"** | AI 需要上下文才能正确取舍 |
| spec 文档 | **读一遍**再批准 | AI 可能写了你自己都不想要的东西 |
| 审查 | **手动看 diff** | AI 审 AI 有盲区 |
| 关键决策 | **拍板**：选方案、合并还是 PR | AI 可以有建议，但不能替你决策 |
| 争议 | 和 AI 想法不一样时**说出来** | AI 不会主动质疑你的决定 |

### AI 应该自动做的

| 环节 | 动作 | 触发条件 |
|------|------|---------|
| using-superpowers | 启动时加载 | 自动 |
| brainstorming | 提问澄清需求 | 你说 "build/make/create" |
| writing-plans | 拆任务写计划 | brainstorming 完成后 |
| TDD | 先写测试 | 任何代码变更 |
| subagent-driven-dev | 派 subagent 干活 | 计划有独立任务 |
| verification | 跑测试报结果 | 声称完成前 |
| requesting-code-review | 审查一轮 | 任务完成或合并前 |

### 什么时候该干预

- AI 说 "太简单了不需要设计" → 打断，要求 brainstorming
- AI 说 "测试应该能过" 但没跑 → 要求他跑
- AI 跳过了 spec 开始写代码 → 要求先写 spec
- AI 在不适用场景强行走 skill → 告诉他跳过
- Subagent 反复失败 → 要求 inline 执行

### 什么时候不用管

- AI 大段读文件、写测试 → 正常工作过程
- AI 自言自语分析逻辑 → systematic-debugging 的 Phase 1
- AI 问你问题 → 需要你的上下文
- 测试是红色的 → TDD 要求先红后绿

---

## 7. 实战案例：Codex CLI 周报

### 完整时间线

```
Day 1
├─ 安装 superpowers（project-local）
├─ 探索 Codex CLI 数据格式
├─ brainstorming（3 个问题 → spec）
├─ writing-plans（拆 3 个任务）
└─ subagent-driven-development：
    ├─ Task 1: 日期范围 + 文件扫描 → fbf3284
    ├─ Task 2: 会话解析 + 数据提取 → 46b6e40
    └─ Task 3: 聚合 + 报告生成 → 3e7c596

Day 2
├─ requesting-code-review → 修复 3 个问题 (5a1a5e7)
├─ 讨论 plan vs TDD 矛盾
├─ 新需求：event-level token tracking
│   ├─ brainstorming → spec → plan
│   ├─ inline TDD（RED→GREEN, 21 个测试）
│   │   ├─ parse_session delta → 12df63b
│   │   ├─ 聚合重写 + model → 2ebeb86
│   │   └─ 报告 + 模型表 → 590a624
│   └─ 集成发现 info:null bug → 修
├─ requesting-code-review（二期）
│   └─ 发现大小写、continue → 764ba51
└─ 收尾（finishing 不适用）
```

### 最终产出

| 文件 | 行数 | 说明 |
|------|------|------|
| `codex-weekly-report.py` | 344 | 单文件，零外部依赖 |
| `test_report.py` | 430 | 21 个测试 |
| spec 文档 × 2 | — | 设计文档 |
| plan 文档 × 2 | — | 实现计划 |
| 周报 | 生成 | 4 节（总体、项目、模型、趋势）|

### 关键数字

- 14 个 skill 中用了 **7 个**，未用 7 个
- **最易跳过的：** brainstorming
- **最严格的：** TDD（数不清的防借口表）
- **最有价值的发现：** plan vs TDD 的矛盾

### 核心收获

1. **Superpowers 不是银弹**：需要选择性使用
2. **Plan vs TDD 是真实矛盾**：不是理解问题，是设计冲突
3. **AI 审 AI 有盲区**：人类需要介入
4. **项目本地安装正确**：不污染全局

---

## 附录 A：Skill 速查表

| 你要做什么 | 用哪个 skill | 触发方式 |
|-----------|-------------|---------|
| 开始新功能 | brainstorming | 自动 |
| 想法变计划 | writing-plans | brainstorming 后 |
| 写代码 | test-driven-development | 自动 |
| 执行独立任务 | subagent-driven-development | 手动 |
| 执行依赖任务 | executing-plans | 手动 |
| 多个独立问题 | dispatching-parallel-agents | 手动 |
| 遇到 bug | systematic-debugging | 自动 |
| 声称完成 | verification-before-completion | 自动 |
| 代码审查 | requesting-code-review | 手动 |
| 收到反馈 | receiving-code-review | 自动 |
| 收尾合并 | finishing-a-development-branch | 手动 |
| 隔离工作空间 | using-git-worktrees | 手动 |
| 写新 skill | writing-skills | 手动 |

---

## 附录 B：Plan vs TDD 矛盾详解

```
writing-plans 要求                    TDD 要求
┌──────────────────┐              ┌──────────────────┐
│ Complete code    │              │ NO production    │
│ in every step    │    ⚡直接冲突  │ code without     │
│                  │◄────────────►│ a failing test   │
│ "show the code"  │              │ DELETE existing  │
│                  │              │ code, start over │
└──────────────────┘              └──────────────────┘
         │                                  │
         │         我们的妥协方案              │
         └────────────┬─────────────────────┘
                      ▼
         ┌──────────────────────┐
         │ Plan = 接口地图       │
         │ 定义签名、类型、文件    │
         │                      │
         │ TDD = 执行纪律        │
         │ RED → GREEN 循环      │
         │ 发现具体实现           │
         └──────────────────────┘
```
