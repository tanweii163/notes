# 论文阅读笔记：Applying Anthropic Primitives at Large Enterprises — Harness Paradigm for Knowledge Work

> **论文：** Applying Anthropic Primitives at Large Enterprises: Harness Paradigm for Knowledge Work
> **作者：** George Salapa（G.S. s.r.o. / PwC Austria）
> **arXiv：** [2608.20622](http://arxiv.org/abs/2608.20622)（cs.AI，2026-08-20）
> **阅读日期：** 2026-08-25
> **参考实现：** [microcc](https://pypi.org/project/micro-cc/)（论文自称的"reference harness"，全篇机制都基于它）
> **发布地点：** 归档于 `agent-harness-survey/`（与 `Code as Agent Harness`、`What makes a harness` 同一系列）

---

## 0. 摘要

这篇论文的起点是一个很尖锐的观察：

> **Frontier models have collapsed the cost of writing custom code … The cost of reviewing, understanding, and maintaining that code afterwards hasn't collapsed at all.**

写代码变免费了，但**评审、理解、维护**这些"事后成本"一分没降——每个专家随手写的专属方案互相漂移，理解一个方案等于从零读一遍它的代码库。所以大企业内部，这种"个人 DIY"基本不被背书，管理层仍然想要"能看见到底在跑什么"。

论文站在三条近期研究共识上（都是本目录熟悉的面孔）：

| 共识 | 出处（本目录关系） |
|------|------------------|
| harness 在任务层面够用，且胜过更花哨的 agent 架构 | arXiv:2604.00073（Terminal Agents Suffice）、arXiv:2604.13107（Coding Agents as General Agents） |
| **harness 的选择对 benchmark 结果方差贡献 > 模型选择** | arXiv:2605.23950（Stop Comparing LLM Agents） |
| 通往企业落地的缺口是**治理（governance）** | arXiv:2605.10223（AgentRunner）、arXiv:2605.18747（Code as Agent Harness，见本目录笔记） |

然后给出一个**架构方案**来补上"治理"这个缺口。核心主张一句话：

> **一个 harness 不改一行代码作为骨干，底层代码在所有部署中保持完全一致。于是评审一个新方案，从"读一遍它的代码库"退化成了"读一个 instructions 文件"。**

今天企业把 harness 留在工程师的终端里，反而为每个新用例重新造轮子（画 LangChain graph、搭 Copilot Studio 编排、把模型焊进现有软件当自动补全）。论文主张**反过来：harness 本身就该坐在那个正中央的位置**。

支撑这一主张的是 **4 个机制**（§4）：

1. **Credential-scoped tooling（凭证作用域的工具）**：不给每个操作写一个方法；每个后端只给一个通用 request 工具 + 一个绑定身份、窄作用域的 token。网关决定你**能不能到某个后端**，进去之后模型自己组合要什么调用。治理由此能对接企业真实的身份与访问系统——控制在凭证层面，而不是逐个操作去查。
2. **授权逻辑永远不写进 harness 本身**：因此同一个 harness 产物可以在无人值守的 cron 骨干、业务向的 chat 执行引擎、交互式终端三种表面上无修改运行，共享同一身份与治理模型。
3. **注册是部署的副作用**：审计企业的 N 个 agent 方案，折叠成审 N 个版本控制的 instructions 文件。
4. **"法官"是新鲜实例**：模型自己标 risky 的调用，先交给一个**新 spawn 出来的同款 harness 实例**去评判（新上下文评判这个调用，而不是组合它的那个上下文给自己的作业打分），法官也扛不住才升级给人。

四个机制共享同一个基建动作：**fork 参考仓库 → 改 instructions 文件 + config 文件 → push**。CI/CD 构建容器、注册方案、部署，接上三个注册表：工具注册表（能调什么）、方案注册表（谁部署了什么、是什么）、技能库（过程知识，构建期默认 bake 进镜像，或配置里指名 live 的运行时从 GitHub 拉）。唯一另一个可动部件是 run-trigger 端点，让 Copilot Studio 这类聊天表面按需启动同一个容器。

---

## 1. 引言：企业现状的四种模式，以及它们的共同病根

论文把今天企业的 AI 落地画成四张互不相通的脸：

| 模式 | 典型形态 | 病根 |
|------|---------|------|
| ① RAG 管线 | LangChain / LlamaIndex 搭的检索增强管线 | 每团队各搭各的，不共享工具层或治理模型 |
| ② graph 编排 | Semantic Kernel / CrewAI / 大量自定义 Python | 每问题一张新图，端到端自成一派，不共享任何东西 |
| ③ 低代码平台当编排器 | Copilot Studio | 治理审计白送、采购已签、业务团队不靠工程师就能发——但编排能力弱（跨不了几步动作就漏）、内部决策路径是团队无法检查/修改的黑盒 |
| ④ 内部聊天机器人 | SoTA 模型 + Web 搜索 + 受限无文件访问的解释器 | 推理顶级但**开不了公司文档库里的文件**，够不着真正的工作 |

四条模式各自冒出来的通病（原文提炼，值得背）：

- **模型是"焊上去的自动补全"**——被召来回答一个孤岛式切片问题；
- **工具是工程师定义的**——一份手工枚举的方法目录，一个预期动作一个方法，**目录随每个新系统/新操作线性膨胀**；
- **架构随表面选**——聊天团队用低代码平台，自动化团队接 graph 框架，开发工具团队上终端 harness，各自独立、各自库/笔记；
- **治理是"许可式"的**——动手写代码前先问评审委员会/安全部门"允不允许建"，然后等。结果大量有价值的创新**跑到雷达外**去做。

论文的立场：把上述"工程师终端里的小工具"提升为**企业基础设施**。给模型"手、循环、记忆、文件系统访问"是新一代的基本软件单元——API-first 的十年让软件对其他软件可读，下一步是**软件对模型可读**，基本构件变成 "model in a box"：一个循环、内存、文件系统、bash；box 之间通过消息传递组合（§4.5），工程努力转移到它们之间的墙（治理、身份、风险闸门）上。

---

## 2. 相关工作：七篇论文的定位 + 本论文补的那个洞

论文老老实实把相关工作的"共识"和"缺的洞"都列了——这是本目录里读过的论文的交叉引用表：

| 论文 | 说了什么 | 本论文怎么接 |
|------|---------|-------------|
| **Terminal Agents Suffice for Enterprise Automation**（2604.00073） | 终端+文件系统 agent 匹配或胜过 MCP/GUI 类复杂架构 | §4 共享这个主张 |
| **Can Coding Agents be General Agents?**（2604.13107） | 对 ERP 系统测试：简单任务不需要 ERP 专用工具也能成——工具不是瓶颈，瓶颈在"领域逻辑↔代码执行"的桥接。点出 **4 个失败模式：lazy heuristics（懒启发式）、hallucination（幻觉）、dropped constraints（丢约束）、overconfidence（过度自信）** | 工具网关（§4.2）只回答"能不能安全触达某系统"这个更窄的问题，**不解决 4 个失败模式**；真正的缓解靠 §4.7 的部署路径（先交互跑通再蒸馏进 instructions） |
| **Code as Agent Harness**（2605.18747）——[本目录有专门笔记](../reading-notes-code-as-agent-harness/) | 代码作为 agent 系统的运行介质；开放问题含"多 agent 间一致共享状态""安全关键动作的人监督" | §4.5（跨盒状态）直接回应前者，§4.6（approval queue）直接回应后者 |
| **Dive into Claude Code: The Design Space**（2604.14228） | 同一组设计问题，不同系统给不同答案，占据设计空间不同区域 | §4 更进一步：**一个 harness 核心自己供给全部三种部署上下文**，单一身份与治理模型 |
| **Beyond Autonomy: Dynamic Tiered AgentRunner**（2605.10223） | 现有框架重自治、轻企业需要的可治理性，提出风险分级评审 | §4.6–4.8 的 entitlement / 注册门 / 阻塞审批队列就是它论证的一个**具体而更窄的实例**：没有独立治理协议、没有第二拨 agent 来跑它 |
| **Stop Comparing LLM Agents Without Disclosing the Harness**（2605.23950） | harness 选择解释了 benchmark 结果的大部分方差 | 本论文**不跑对比 benchmark**，在自己的精神下直接披露实现（microcc） |
| **SHarD: Distributing Security Controls Through Harness Engineering**（2607.25890） | 从安全角度落到同一论点：要分发/构建的单位不是按团队买的 agent 配置，而是**一个加固的 harness**，中央工程一次、无修改到处跑 | 强化 §4.2；本论文只深入了 SHarD 三个控制（OS 沙箱 / 技能扫描 / 工具限制）中的"工具限制"（见 §5 局限） |

最后点出缺口（也是本文从第一步就是冲着它去的）：

> **None of this work addresses the deployment topology argued for here: a single harness artifact that runs, without modification, as an unattended container-and-scheduler backbone, as the execution engine behind a business-facing chat surface, and interactively at a terminal, under one identity and governance model.**

没有人解决"一个未修改的 harness 同时在 cron 骨干、聊天执行引擎、交互终端三种表面下运行，共享一身份一治理"的部署拓扑——这就是本文要填的洞。

---

## 3. 从 Chat 到 Harness 的演进：四个阶段

论文给了 2022 以来的四段演进，每段治的是上一段的病：

| 阶段 | 形态 | 能干什么 | 致命短板 |
|------|------|---------|---------|
| **Chat** | SoTA 模型做内部聊天机器人，对话循环保上下文 | 上下文跨轮保留 | 没有"手"：只能在聊天窗内行动，工具固定且窄到产品经理当初预料的范围，没法中途扩展 |
| **DAG / chain 编排** | graph 框架把多次模型调用接进预设图 | 加了持久化与多步结构 | **图在设计期冻死**：模型每节点完成一个预设子任务，发现不了设计者没想过的路径，图外用例全挂 |
| **Autocomplete 层** | 单次模型调用嵌进现有产品当一次性兜底建议 | 窄范围内可靠（起草邮件、总结记录、补字段） | 只是装饰：给文本让人接受/编辑/丢弃，够不着跨系统工作 |
| **Harness** | 一个循环反复调同一模型、把结果喂回去 | **迭代**：自行推理、失败恢复、借文件系统创建和取回自己的工作产物；模型每步自己决定下一步、边跑边塑造工作环境 | ——（本论文押注的就是它） |

一个关键的落地观察：

> 企业里的真工作很少是"回答一个孤岛式问题"，而是**跨系统铺开、从每个系统拉数据点、对结果迭代推理**——跟人干这活的方式一样。前三阶段物理上够不到那么远。

而且**驱动 harness 不需要工程师**。熟练的领域专家（pharmacovigilance lead 这类人）能导航模型穿过一次性系统：看方向、微调、丢弃、重建。她一行代码不写，但每一轮都是她的。终端对她依然是门槛——所以 harness 开始给循环配上 GUI（microcc 自带一个浏览器内的 TSX 界面）。

论文刻意强调：**这不是一篇讲 coding agent 的论文**。编程只是 harness 先征服的领域（模型擅长生成代码）。论点是把同一个范式——"模型在 while loop 里、一次性建议换成迭代、带着记忆与自写方法塑料化地贴合问题"——搬向企业里大量**根本不是软件工程**的知识工作：文档评审、工单分诊、报告生成。

---

## 4. 系统架构（论文核心，逐节拆）

### 4.1 起点与两个设计目标

起点是 §1 的现状：团队各自自建 RAG、代码评审助手、需求分析工具、报告生成器，共享同一个病——**没有公共注册表、没有公共访问层、管理层看不见"有什么、谁拥有、花多少钱"**。

架构被证明能跑三种典型工作，都值得列出（类型学参考）：

1. **策略自动化**：对 LOB 系统（如 Dynamics 365 Business Central）里的结构化记录应用策略规则，按需调用外部服务并把决策写回——人工复核环节被端到端自动化；
2. **CRM 工单分诊**：从多个系统拉上下文、完成响应（起草函件、更新客户记录、发起下游交易）；
3. **制造业文档核验**：把"工程师手工比对供应商合规证书和材料规范"替换成 harness 对任意格式（PDF/Excel、SAP 导出、规范原文）做同一比对。

共同形状：**可重复但复杂、需要跨系统推理的任务**——正是 harness 意外擅长的地方。而这个架构随模型变强自动变强，**企业不需要重新设计**。

两个设计目标因此涌现：
1. 让团队能用"有手的模型"（能循环、能纠错、能跨步探索、能借文件系统产出并保存工件）；
2. 给每个团队**同一个可再部署架构**——不管解决什么问题，底层代码处处一致。这就是整个舰队可审计的前提：**评审新方案不再是代码评审，而是读一个 instructions 文件**。

### 4.2 四个核心设计决策

① **Frontier 模型是唯一编排者**。没有设计期固定的 graph/chain。一个 harness 实例反复调同一模型，每轮观察上一轮结果；它还能 spawn 更多自己（§4.5），**在运行时自己组合编排图**。于是"流程变更"变成对系统提示做文本编辑，而不是一个开发 sprint；模型升级对所有已部署方案零代码生效。

② **工具网关是共享能力层**。一个常驻服务收纳所有企业工具集成（数据平台、文档库、ERP），统一在一个协议后面。团队从注册表里选工具而不是自己写集成；加工具 = 对网关做一次配置变更，**瞬间对每个方案可用**。

③ **结构性治理（Governance by construction）**。三道防线全部建在路径上，不给事后加检查的机会：
- 基础设施策略在资源创建时拦不合规项；
- CI/CD 自动把每次部署登记进生命周期注册表；
- **风险按调用判，不按工具判**：模型必须在每个调用上显式声明 `risky`，由它刚构造的参数来评判，而不是从静态工具/分组定义里查；漏标直接拒绝。risky 调用在到达后端前先过"法官"（§4.5），只有法官自己也过不去才升级到人。

④ **简单 = 采用路径**：fork、configure、push。克隆参考仓库，把 instructions 文件和 config 文件做好，push。CI/CD 供应基础设施、部署、自动注册。

### 4.3 四层架构

```
┌─ 知识底座（§4.4）   git 镜像 + 身份过滤的企业文档库副本，harness 直接读
├─ Harness 引擎（§4.5） loop + 记忆 + bash_；一个可 fork 的参考仓库；由两个文本文件驱动；CI/CD 部署
├─ 工具网关（proxy 后） 智能层：执行前查 entitlement；持有"模型自标 risky"的审批队列
└─ 云治理骨架          management-group 级别策略 + RBAC + tagging；隐形但保证成本透明与控制
```

### 4.4 知识底座 = git 镜像，不是向量库（对 RAG 的正面批评）

这是全篇最"反主流"的一节，值得整段读。论文对 RAG 向量检索的批评有三条：

1. **检索应该是主动探索**。`bash_` 本来就给了 harness 人脑逛共享盘的那套工具；向量库让它改对相似度分数推理，**关掉了它本来的探索能力**。
2. **丢结构与出处**。片段被剥离了所在文档、上下文树和 provenance。
3. **不可审计**。没有任何记录说明某次运行"可能检索到什么"，事后没法重建"agent 决策时已知什么"。

替代机制（贴原文核心代码）：

```js
async function syncSource(source, cursor) {
  const changes = await source.delta(cursor);        // 原生变更键（cTag/页面版本/rowversion）
  for (const item of changes) {
    const text = isTextual(item) ? item.body : await renderToText(item); // 视觉文档转写为文本
    await writeMirrorFile(mirrorPath(source, item), text, item.aclGroup);
  }
  return commitMirror(`sync: ${source.id} @ ${changes.newCursor}`);
}
```

- **增量同步**：按源系统自己的变更键（SharePoint 的 cTag delta 查询、Confluence 的页面版本、关系源的 rowversion）走，不是每次全量爬；
- **镜像路径 = 无损索引**：文件在镜像里的位置对应它在源系统目录树里的位置；
- **可审计性靠 git**：每次同步一个 commit；模型每次读取解析到"此刻"那个 commit，网关把 commit 和读操作一起记下来。审计员拉出该次运行记录、checkout 对应 commits，就能**精确重建模型当时眼前的内容**——哪怕已经过了好几个同步周期；
- **ACL 随文件走**：镜像把源 ACL 写成目录组引用，读工具按调用者的组先过滤再返回。看都看不见，更别说读。与 §4.6 工具目录的 discovery-then-filter 是**同一套机制**驱动两处（知识底座 + 工具目录）。

> 论文用"同步滞后换可审计性"：上次同步后改过的文档对运行不可见，直到下次同步完成——这是刻意的代价，不是要调掉的疏漏（§5 也重申）。

### 4.5 Harness 引擎

一切建立在循环之上：一个进程反复调模型、喂回结果、跨轮保留记忆和文件系统。这节的分子机制：

**a. Harness 能写并派生 harness（multi-agent）**
同一个 loop/记忆/filesystem/bash 原语让 harness 写出"贴合手头问题的图"并 **spawn 更多自己**：再跑一个无头 harness、指到新文件夹、从它写出的文件读回结果。lead agent 派生 worker 各探一片问题再汇总（引述 Anthropic 的 multi-agent research system 工程文）。microcc 的实现细节：每个子进程用一个小的 status 文件跟踪（不轮询）；子盒之间经同一文件系统通信——目标活着就走 live socket，不在就走 durable inbox。**图不是固定的**：给一个问题，模型运行时自己决定层次、结构、顺序和给实例的 prompt。

**b. Loop**：一次运行构建一条系统消息且**从不改写**，只有外围上下文每轮重建。

**c. Skills（指令/技能）三 tier**
模型按需拉取的文档+附属脚本。企业规模下关键在**从哪加载**：

| tier | 位置 | 覆盖关系 |
|------|------|---------|
| built-in | 随 harness 发货 | 默认 |
| 共享平台库 | 一个真实 git 仓库（中央团队维护的版本化过程知识库） | 同名覆盖 built-in |
| 项目特定 | 方案仓库里的 `skills/` | **同名胜出** |

- 交互时：加载器用工程师自己的 PAT 认证共享库——"库的 entitlement 就是另一个仓库权限"，与 §4.5 工具调用同一凭证作用域原则；
- 部署时默认 **baked**：config 的 `skills:` 指名哪些，CI/CD 构建期拉进镜像，容器里**没有库凭证**，被攻破的运行身份也没法偷读更多；
- `live_skills:` 指名的：CI/CD 给该部署自己的 scoped token，容器每次运行开头直连 GitHub（on-behalf-of 交换，同工具凭证解析），**每次运行都拿到该技能当前 commit**——这是"构建期信任一次"与"运行时信任每次"的分界，也是 §5 指出的注入风险所在。

```js
if (mode === "baked") return readFromImage(name);          // 读一次，运行期零网络
return fetchFromGit(SKILL_LIBRARY_REPO, name, token);     // 每次运行直连 GitHub
```

**d. 工具发现**：一小撮常驻工具（文件、记忆、读技能）随每次运行发货；其余全部运行时向网关发现（身份过滤后服务器端给什么看什么，见 §4.6）——交互用工程师账号、cron 用部署身份、chat 触发用终端用户身份。

**e. `bash_` 是一切**：模型训练时看过海量 shell 用法，"读 man page / API 文档然后组合正确调用"是模型天生能力。**每个别的工具都在努力变得更像 bash_**：不预写严格方法，靠文档+常识组合调用。

**f. Credential-scoped tooling（本论文招牌机制）**
- 不搞"每预期操作一个方法"（如 list-files/get-item）；网关对 SharePoint 这类系统注册的是**凭证经纪**：对目标系统认证调用者身份，交给 harness 一个窄 scope 的 token。模型对它调**一个通用 request 工具**（跟 bash_ 一个形状），自己组合 Graph 查询 / OData 过滤器 / 搜索语法。
- **反 MCP 立场**（原文明确）：严格 per-action JSON Schema、带类型/枚举参数（包括广义上的 MCP）是**净负**——它把模型脑子里那个更宽的 API 模型换成一个更窄、手工维护的模型，还把访问冻结在 schema 作者当初预料到的操作上。SQL 仓库下同样工具长 `{sql, catalog, schema?}`，Graph 下是 `{method, path, body?}`——模型从它已知的后端常识里挑形状。
- 每个后端只贡献一个手写的 `usage_hint` 字符串（合并进工具描述当 docstring），只讲**这个部署的私有接线**（比如"这个后端现在活在 SQL 面还是 REST 面"），不重教公共 API——因为模型对 Graph/OData/SQL 惯例如数家珍。
- 调用信封：`{params, risky}`。`risky` **必填**、模型按自己刚构造的参数自评；漏标在到后端前就被 400 拒（错误信息逼它"再想想"）。风险是**调用级、自声明**的，从来不是自上而下贴在工具/工具组上的静态层级。

**g. 三类状态**
| 状态 | 特性 |
|------|------|
| 会话历史 | 持久，崩溃/断线后能续跑 |
| 工具发现缓存 | 短命、TTL 过期，跨方案所有副本共享 |
| 长时记忆 | **按调用者身份作用域**，跨运行甚至跨方案；instructions 文件指示模型边走边写下（可行的 workaround、要记住的约束），**keyed 条目**，每轮只把 keys 载入上下文，全量惰性加载——和 Skills 同一个懒加载模式 |

**h. Judge：spawned verdict，不是 self-report**
模型自标 risky 的调用，如果让"组合它的那个模型"自己判，等于让同一个已丢过约束的上下文给自己打分（呼应 2604.13107）。所以：**flagged 调用 spawn 一个全新 sub-harness**，让它看调用、方案 instructions、截至目前 trace——新鲜上下文来判。harnesses 之间没有 API，就靠共享文件系统 + 每个实例 poll 的 `inbox.json`。

**i. 高风险工具的审批闸**
risky 调用先过 judge；judge 也过不去的才到人。`approvalQueue.enqueueAndWait` 把调用、参数、judge 推理、调用者身份发到 Teams 频道（webhook，每条消息带一个 approve/deny 动作按钮），**挂起请求直到某负责人点了**。点击直达网关的决策端点，pending call 解开、enqueueAndWait 返回（§4.8 注册审批用同一个模式）。

**j. 自报告（self-reporting）**
每次运行结束时模型用一行结构化状态自述结果：`done / needs input / failed` + 摘要。外层 wrapper 自己解析这一行（不再依赖单独的分类器调用），发到生命周期注册表，和 owner、解决的问题、运行历史一起持久化。

### 4.6 身份与工具可见性

唯一裁决工具可见性的东西：config 声明的工具组 → CI/CD 据此申请部署身份进入对应目录组 → 运行期网关的 **entitlement 映射（就是一坨 git 版本化的 YAML，管理员编辑）** 决定谁能看见/调用什么。三种调用方一视同仁：无人值守部署自己的身份、交互工程师的账号、聊天触发的终端用户身份。

两个核心函数（值得背，别的都围绕它们）：

```js
async function discover(caller) {
  const groups = await resolveDirectoryGroups(caller);
  return catalog.filter(t => groups.some(g => t.directoryGroups.has(g)));
}

async function call(caller, toolId, request) {
  const tool = (await discover(caller)).get(toolId);
  if (!tool) return { status: 403 };                    // 目录里有，但不是给你这个调用者的
  if (typeof request.risky !== "boolean") return { status: 400 }; // 无默认、无推断
  if (request.risky) {
    const review = await judge.spawnAndWait(caller, toolId, request);
    if (review.status !== "resolved") {
      const verdict = await approvalQueue.enqueueAndWait(caller, toolId, request, review.reasoning);
      if (verdict !== "approved") return { status: 403 };
    }
  }
  return tool.execute(request.params);
}
```

- `discover` 每次运行调一次，构建模型看到的目录，也是 describe 路径（不在目录里的工具 404）；
- `call` **不信模型给的 tool id，现场重算同一份过滤集合**——目录外的 id 403。没有第二套权限检查要同步；
- `risky` 是必填字段：缺失时 400，发生在 entitlement 检查和 judge 之前；
- harness 本身不过滤工具、不藏工具、不分配风险等级 → **同一个 harness artifact 在 §4.10 说的三种上下文里无修改运行都安全**，没有 harness 侧的副本逻辑可绕过。

### 4.7 部署机制：fork, configure, push（五步）

1. **交互跑通**：工程师先在终端对真问题跑 harness，此时工具发现只会显示自己身份有权的——第一步前无需请求任何东西；
2. **蒸馏**：把跑通的写进自然语言 instructions 文件；可复用出单用例的部分**拆成独立 skill 文档**，不进 instructions；
3. **配置**：config 文件字段如：

```yaml
owner: crm-team@company.com
problem: "Triage inbound CRM requests and draft first-pass responses"
tool_groups: [crm-triage, sharepoint-readonly]
skills: [crm-triage-playbook, sharepoint-search-patterns]
live_skills: [crm-triage-playbook]   # 每次运行从 GitHub 拉，而非 baked
business_area: customer-service
model: claude-sonnet-5
schedule: "*/15 * * * *"
trigger: cron
registration_id:   # 留空，首次部署由 CI/CD 回填
```

4. **push** → CI/CD 干活：
   - 无 registration_id = 首次部署：先跑 §4.8 的注册门（重叠+风险检查），人注意的事浮在 build summary 里，然后 **bot commit 把注册 id 写回 config**；后续 push 变成更新已有注册；
   - 按 `skills:` 从技能库烘焙进镜像（用作用域服务凭证，不是工程师自己的 PAT）；
   - `live_skills:` 的反而是给部署自己的 token，让它每个 run 直连 GitHub；
   - 构建推送镜像 + 从共享 IaC module 生成基础设施（每个方案的部署模板 = 同一个 module 调用、不同参数；**治理-by-construction 的决策编码在 module 里，不是在 config 里**）；
   - 基础设施真的存在后（目录对象此时才存在），申请授予运行时工具可见性的目录组身份。

5. **无人值守跑**：方案按调度/触发跑同一引擎，走和交互路径完全相同的 entitlement（相同网关、相同审批、相同身份）。

工程细节（原文强调）：工程师全程**不碰**认证、模型客户端代码、基础设施脚本、审计日志、工具实现、工具过滤、注册调用——全是结构性的、为所有方案各固定一次的东西。

论文用 Figure 3 走了一遍：应付账款分析师 fork 仓库，对 Business Central 的三方匹配异常（采购单/收货/发票行对不平）交互跑通，把扛得住足够多案例的模式蒸馏成 skill 文档，用自己 PAT 提交进共享技能库，在 config 里指名这个 skill + cron 调度，push——**这就是她全部要做的**。此后同一个未修改的 harness 无人值守地按调度重读她的 skill，处理每一批新异常。

### 4.8 注册门控：三道门，全部 git 化

| 门 | 机制 | 触发 |
|----|------|------|
| **entitlement 门** | 解析触发部署者的目录组成员（用其**已有的 SSO 身份**，不用服务账号），查一个 git 小文件（同工具网关 entitlement 的习语） | 此人有没有资格在这个 business area 注册方案；未配置的领域**默认低天花板** |
| **overlap 门** | 对新方案 problem statement 做 embedding，取最近的已有注册，交给一个小模型分类"两者实际重叠多少" | **阈值放在分类结果上，不是裸 cosine**。低档只供评审参考、永不阻塞；只有近乎确定的重复才过 BLOCK_THRESHOLD |
| **risk 门** | 读方案实际是什么（instructions + 已解析的 skill 集 + 请求的工具组），给大模型一个任务：这个组合在这个业务域，该不该在人看之前就运行？（"同一工具组 + 只读查查"和"同一工具组 + 写着要写支付系统的 instructions"读起来是两回事） | risky → pending-review |

失败不拒绝、不静默放行：标记 **pending-review**，CI/CD 把原因打进自己的 build summary 并干净退出，不供应任何基础设施。评审请求投到团队聊天频道（approve/deny 链接），点击直达注册表决策端点，一步翻转评审记录和注册状态，随后邮件+频道通知请求者。

> 注册门是"**先注册、后建设**"的入口：团队不等委员会就能开建，只有三道门真踩雷才升级到人。

### 4.9 业务用户路径（chat 入口）

业务用户在 Copilot Studio / Teams / Slack 这类日常表面工作，两个入口打同一个网关、同一身份模型：

- **直接工具调用**：聊天助手同步调一个网关注册的工具——适合短、只读查询；
- **完整 harness 跑**：作为聊天动作触发——其余一切。多步 harness 跑会超聊天连接器超时，所以**入口与执行拆成两个服务**：

```js
async function onChatAction(req) {
  const caller = await verifyCallerIdentity(req);
  await queue.enqueue({ solutionId, caller, payload });
  return { accepted: true };
}
```

恒在端点只负责验身份、入队、立刻返回——整个 run-trigger 服务就这些，**入队后不持有任何状态**。执行由独立隔离实例接手，跑完整循环后把结果回调回去。拆分是操作原因：恒在端点要承受正常缩容/重部署，长循环跑同一个进程里会被杀在半路。整条链路携带的身份是**终端用户本人的**（不是调用方服务的），聊天触发的工具可见性按用户自己的权限走。

### 4.10 代码结构：五个仓库/服务

| 组件 | 形态 | 谁拥有 |
|------|------|--------|
| Harness | 参考仓库，拉取本地用；指令/工具经 config 变更并 push | 中央平台团队 |
| Skill library | git 仓库的共享过程知识（交互走工程师 PAT；部署 baked 或 live） | 中央/各团队共建 |
| Tool gateway | 常驻 API | 平台团队 |
| Solution registry | 常驻 API | 平台团队 |
| Run-trigger service | 常驻 API，手动拉起 cron 部署的后端、供业务用户经 Copilot Studio 等交互 | 平台团队 |

整节收尾重申 §4.6 的成果：授权全部在 harness 进程之外，所以同一个 harness 代码库在终端、cron 骨干、chat 执行三种上下文无修改运行、单一身份模型。

### 4.11 运营模型（组织设计，容易被忽略的一节）

- **中央平台团队**拥有：网关、生命周期注册表、参考 harness 仓库、策略基线。**不拥有用例、不为团队建方案**；
- **业务/工程单元**各自负责自己的用例识别与交付；
- 中间的 **enablement 职能**：onboarding 新工具进网关、审高风险请求、办公时间答疑。职责是"解卡（批准/拒绝）"。**如果某单元反复让 enablement 帮它建，那是信号说明该单元需要不同的支持——不是说 enablement 该扩成交付团队**。
- **注册替代审批成为入口**：团队先注册（owner、用途、工具、业务域），部署流程作为副产物已产生；只有资格/重叠门真踩雷才升级到人。中央团队与单元 leader 定期同步，让注册表保持活的。
- 全篇组织论点的收束（很有力的一段）：

> 自定义代码曾经给"事前门禁"提供了合理性，因为回头看它太贵：评审一个方案 = 读它的代码，而每团队的代码都不一样。前沿模型已经塌掉了另一半：工程师现在能便宜地建出他们看见需要的那个专属东西。嵌入自己领域的人能看到中央团队永远排不上优先级的利基问题——太小或太专项，但真实到每周烧几小时。**一个什么都得自己建的中央团队只能按规模排优先级，利基问题永远不被解决。让真正看见问题的人自己便宜地把修好它建出来，这才是"写代码变便宜"的全部意义。**

这个架构移除了为门禁提供合理性的成本：每个注册方案跑同一参考代码库，只经 instructions+config 变化，所以评审企业 agent 方案**永不读代码库**。治理变成 §4.7/4.8 部署路径的自然产物。**N 个方案共享一个相同代码库时，审计 N 个 = 读 N 个 instructions 文件——每个都比交付同一变更原本要走的 PR 更短、更易读。**

### 4.12 设计的耐久性

架构是**押注前沿模型能力持续复合增长**的：
- harness 架构把能力提升**直接换算成每个已部署方案的免费增值**，零代码改动；graph/chain 架构不享有这免费升级——行为冻结在设计者布线时；
- 押注的是"通用能力提升"，**不押任何一家实验室**；开源权重模型快速追赶，是同一耐久性论证上的真实 hedge。架构无任何绑定单提供商的部分。

---

## 5. 讨论与局限（原文自曝，照抄要点）

- **没有 benchmark**。所有"harness 够用/胜过复杂架构"的主张都挂靠在 §2 引用的工作 + 现场经验。本文自己没跑对照。
- **4 个失败模式**（2604.13107 的 lazy heuristics / hallucination / dropped constraints / overconfidence）**没有专属机制**；缓解只能是 §4.7 部署路径（先交互跑通、再蒸馏进 instructions），且没有受控 benchmark 证明它到底对哪些模式有效。
- **Governance by construction 只覆盖从参考仓库新建的路径**，管不了已安装基座（老 RAG 管线、旧 custom chains、早期手工集成），旧访问不追溯关闭。
- **Credential-scoped tooling 的好坏 = 模型组合调用的能力**。对微软 Graph 这种广泛、文档好的表面成立；对**内部未公开、形状怪异的 API 未经验证**——那里手工方法可能仍胜过模型从零组合。
- **SHarD 的三个控制只做了一个**（工具限制）。容器隔离是进程/命名空间级的粗粒度保证，没测过 SHarD 报告的那种跨边界行为；**skill scanning 完全没有**——baked skill 是构建期信任内容、无人检查注入指令；`live_skills` 把构建期信任一次的洞扩成**每次运行都信任**，且没有可 diff 的"上一个已知良好镜像"。
- **知识底座继承源系统 ACL 保真度**：特别是 Microsoft Graph 想枚举"有效权限"（而非显式权限）很难；镜像的治理边界 = 同步时捕获的 ACL 组。滞后窗口是刻意的。
- **证据基础**：欧洲企业、几个行业、仅 Azure 身份与策略原语验证过。换云/on-prem 是否成立仍是开放主张。

---

## 6. 结论

> Harness 是企业 AI 自动化的通用架构，本文给出"这样治理地、企业规模地跑它"的机制。四个机制干活：凭证作用域的工具把策展权交给模型，而不是僵化工具 schema；同一个 harness 产物在终端、业务聊天表面、无人值守 cron 部署间无修改运行——企业不再需要每表面一套系统；注册是发布的副作用，治理成为部署的自然产物；而因为 harness 能派生自己，被标记的调用在请人之前先由新实例评判。

落点是**耐久性论证**：不主张新奇，押注前沿模型能力继续复合；开源权重让这个赌更好下——不绑单一家。也押注**治理足够便宜**，让团队自愿持续选快路径。**本文没补上的洞是测量**——无 benchmark 陪伴这些主张（跟 §2 的披露精神一致：披露参考实现，把与替代方案的比较留给后续工作）。

---

## 7. 全文结构速览

```
§1 Introduction — 企业四模式与通病；论点：harness 应是企业基础设施骨干
§2 Background / Related Work — 7 篇相关论文的共识 + 缺口（单一 harness 无修改跑三种表面）
§3 Evolution: Chat → DAG → Autocomplete → Harness — 四阶段演进；知识工作才是主战场
§4 System Architecture（核心）
  §4.1 起点（现状病）与两目标（有手的模型 / 处处一致的架构）
  §4.2 四个设计决策（唯一编排者 / 工具网关 / 结构性治理 / fork-configure-push）
  §4.3 四层架构（知识底座 / 引擎 / 网关 / 治理骨架）
  §4.4 知识底座 = git 镜像（反 RAG；增量同步；commit 审计；ACL 随文）
  §4.5 harness 引擎（spawn、skills 三 tier、bash_、凭证作用域工具、三类状态、judge、审批闸、自报告）
  §4.6 身份与工具可见性（discover/call；risky 必填；无 harness 侧副本逻辑）
  §4.7 部署：fork → configure → push（五步；CI/CD 注册 + bake skills + IaC module）
  §4.8 注册门控（entitlement / overlap / risk 三门；pending-review）
  §4.9 业务用户路径（chat 入口；run-trigger 拆服务；终端用户身份一路到底）
  §4.10 代码结构（5 仓库/服务）
  §4.11 运营模型（平台团队 / 单元 / enablement；注册替代审批）
  §4.12 耐久性（押模型能力复合；开源 hedge；不绑厂商）
§5 Discussion / Limitations — 无 benchmark；无失败模式机制；老基座不管；冷门 API 未验证；skill 注入风险；Azure-only
§6 Conclusion — 4 机制收束 + 耐久性论 + 测量缺口
```

---

## 8. 主线速览（增量补充）

### 8.1 骨架句

> **写代码成本塌了，事后成本（评审/维护/理解）没塌 → 企业不能靠"每个人 DIY"，需要一个中央供给、可治理的公共底座 → 这个底座就是 harness（循环+记忆+文件系统+bash 的 model-in-a-box），一个产物无修改跑遍所有表面 → 治理不靠审批流程，靠架构本身：凭证作用域（身份控访问）、授权不进 harness（一个产物处处同理）、部署即注册（审计=读 instructions）、新鲜实例当法官（防自我评分）→ 押注模型能力持续免费传导。**

### 8.2 逻辑主线：六层递进

| 层 | 追问 | 答案 | 对应章节 |
|----|------|------|---------|
| 起点 | 为什么企业不能放任每个人 DIY？ | 写代码免费了，评审/理解/维护没免费——自治方案的"事后成本"没塌 | §1 / 摘要 |
| 缺口 | 那缺什么？ | 治理：近作共识说 harness 够用甚至更优，卡在治理（可审计、身份、审批） | §2 |
| 介质 | 治理的地基选什么？ | harness 作为企业基础设施——不是终端小工具，是骨干 | §1、§3 |
| 机制 | 具体哪 4 个机制让治理成立？ | 凭证作用域工具 / 授权不进 harness / 部署即注册 / 新鲜实例当法官 | §4.2、§4.5–4.8 |
| 落地 | 组织上怎么跑起来？ | fork-configure-push + 三门注册 + 三职责分离（平台/单元/enablement）；注册替代事前审批 | §4.7、§4.8、§4.11 |
| 展望 | 值不值得赌？ | 耐久性：能力复合 → 已部署方案免费升级；缺的是测量 | §4.12、§5、§6 |

### 8.3 收束图

```
写代码成本塌陷（起点）
  ↓ 事后成本没塌 → 企业要集中供给、要透明可见（问题定义）
  ↓ harness 是企业通用架构（介质选择）
  ↓ 4 机制让"无修改一处跑三面"可治理（机制）
         凭证作用域工具 —— 治理对接企业真实 IAM
         授权不进 harness —— 一个产物处处同理，无副本逻辑可绕过
         部署即注册 —— 审计 N 方案 = 读 N 个 instructions
         新鲜实例当法官 —— risky 调用先自证再请人
  ↓ CI/CD 化：fork → configure → push（落地路径）
  ↓ 运营：平台 / 单元 / enablement 三职责（组织形态）
落点：治理成为部署的自然产物；缺口是测量（无 benchmark）
```

### 8.4 与同目录论文的关系（交叉引用）

| 本目录论文 | 关系 |
|-----------|------|
| [Code as Agent Harness](../reading-notes-code-as-agent-harness/) | 被引为"代码作为运行介质"综述（§2）：两个开放问题（跨 agent 共享状态、人监督）正好分别对应本文的 §4.5 跨盒状态与 §4.6 审批队列——像"综述的补丁" |
| What makes a harness a harness | 本文直接复用其"harness = loop + 记忆 + filesystem + bash"的部件观，并且落到具体运营：harness 同时是 cron 骨干、chat 引擎、终端工具 |
| LoopsBench（loop engineering） | 本文的"夹具"视角（benchmark 方差主要来自 harness）与 LoopsBench 的"循环工程"是同一主张的两面：这边讲 runner，那边讲 loop 本身 |
| agent_harness_engineering_survey | 工业界 put-into-production 一脉：本文就是"harness 进企业"的完整部署拓扑补全 |

### 8.5 与本会话 Cloudflare 文章的对照（外部补充）

> 会话补充：两天前读了 Cloudflare 的 [How Cloudflare enforces engineering standards using AI](https://blog.cloudflare.com/engineering-standards-enforcement/)（Codex 系统）。两篇是同一场运动的两半：

| 维度 | Cloudflare Codex | 本文（Salapa） |
|------|------------------|----------------|
| 收口位置 | **评审侧**：把规范抽成 statements.json，让 agent 在评审时对照检查 | **部署/架构侧**：harness 一个产物处处跑，治理靠身份+注册，审计读 instructions |
| 治理对象 | 工程规范（RFC → approved → enforced 两段式） | agent 解决方案本身（注册门三门；entitlement 映射） |
| 机器可读知识 | 规范 → 结构化 statements.json → 懒加载 | 文档库 → git 镜像纯文本树 → commit 可审计 |
| 配套工具 | oxlint 毫秒级 lint + 本地 CLI | bash_ + credential-scoped 通用请求工具 |
| 共同底色 | **"让检查/审计不靠人"**：规范自动化；多 agent 方案的可见性自动化 | 同左 |

两篇合起来的启示：**LLM 让"造"免费之后，企业真正的战场是"看得见、管得住、审得动"**——一个在评审时刻自动化规范，一个在部署时刻自动化治理；老谭工作空间里的 skill 沉淀 + AGENTS.md 归档约定，其实已经是这个思路的迷你版（把约定写下来、让 agent 在执行时自动遵守）。

### 8.6 一句话总纲

> **把 harness 当企业基础设施而不是编码玩具：一次构建、处处无改运行、治理内建在凭证与部署路径里，于是"N 个方案"在审计账面上退化成"N 个 instructions 文件"——一切以写代码变免费、模型能力持续复合为赌注，唯一诚实未竟之事是测量。**