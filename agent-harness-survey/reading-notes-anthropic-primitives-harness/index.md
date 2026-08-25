# 论文阅读笔记 v2：Applying Anthropic Primitives at Large Enterprises（可理解性优先版）

> **论文：** Applying Anthropic Primitives at Large Enterprises: Harness Paradigm for Knowledge Work
> **作者：** George Salapa（G.S. s.r.o. / PwC Austria）
> **arXiv：** [2608.20622](http://arxiv.org/abs/2608.20622)
> **v2 重写日期：** 2026-08-25
> **重写原因：** v1 版术语堆砌、顺序混乱、机制讲得太抽象、没诚实承认局限。v2 重写以**可理解性**为第一优先级。

---

## 0. 一句话总览

> **写代码变便宜了，但"评审 + 理解 + 维护"这些事后成本没降。论文给企业 agent 落地设计了一套架构：让"造方案"和"治方案"都变得便宜。代价是赌模型能力持续提升 + 在关键决策点留给人。**

---

## 1. 起点：写代码便宜了，治理塌了

### 1.1 论文看到的现实

今天企业搞 AI agent，掉进四个坑里：

| 模式 | 典型形态 | 病根 |
|------|---------|------|
| RAG 管线 | LangChain / LlamaIndex 搭的检索增强 | 每团队各搭各的 |
| graph 编排 | Semantic Kernel / CrewAI | 每问题一张新图 |
| 低代码当编排 | Copilot Studio | 黑盒、业务团队改不了 |
| 内部聊天机器人 | SoTA 模型 + 受限解释器 | 开不了公司文档 |

**通病**：
- 模型被当自动补全——只能回答孤岛问题
- 工具是工程师定义的——一个操作一个方法，目录线性膨胀
- 架构按表面选——聊天团队、自动化团队、终端团队各搞一套
- 治理是"许可式"——写代码前要审批委员会批

### 1.2 核心矛盾

> **前沿模型把"造"这一半成本塌了——工程师能便宜地造专属方案。但"评"这一半成本没塌——因为每个团队的代码都不一样，评审一个方案等于读它的代码库。**

所以"个人 DIY"在企业内部基本不被背书。

### 1.3 论文的解法（一句话）

**让所有方案跑同一份代码库**——评审 N 个方案 = 读 N 个 instructions 文件，不再读代码。

---

## 2. 核心赌注：不是新东西，是组合拳

论文**没有发明任何新东西**。它做的是：

> 把"依赖注入 / 配置外部化 / 注册即部署 / 独立上下文当法官"这些**基本工程原则**，在企业 agent 场景下**串成一套可落地的架构**。

为什么强调这一点：

- 你看到机制② "身份外部注入"会想"这不是依赖注入嘛"——**对，就是依赖注入**
- 你看到机制④ "法官新实例"会想"不能自查嘛"——**对，就是不能自查**
- **单独看任何一个机制都不新鲜**

**论文的真正价值**：把这四条原则**贯穿到企业 agent 的每个层次**（工具层 / 身份层 / 部署层 / 运行时），并**给出具体的工程形态**。

读完论文后你会发现：**四个机制单独看都是常识，组合起来才显出价值**。

---

## 3. 架构总览图

先看全貌，再拆解：

```
┌─────────────────────────────────────────────────────────────┐
│  组织层 (§4.11)：中央平台 / 业务单元 / enablement 三职责分离   │
├─────────────────────────────────────────────────────────────┤
│  知识底座 (§4.4)：git 镜像企业文档库 + bash_ 主动探索         │
├─────────────────────────────────────────────────────────────┤
│  工具网关 (机制①)：通用 request 工具 + token scope 控制      │
├─────────────────────────────────────────────────────────────┤
│  身份层 (机制②)：身份从外部注入，harness 不存                 │
├─────────────────────────────────────────────────────────────┤
│  部署层 (机制③)：push 即注册，三道门 + 三角色                │
├─────────────────────────────────────────────────────────────┤
│  运行时闸门 (机制④)：法官新实例 + 必要时人审                 │
└─────────────────────────────────────────────────────────────┘
```

**每一层都是同一哲学：机器自动化 + 关键决策点留给人 + 可审计**。

---

## 4. 场景设定：acme-orders 客服退款（贯穿全文）

为避免抽象，我用一个**贯穿全文的故事**：

> **场景**：acme-orders 是公司订单系统。客服小李每天处理退款工单。她想用 agent 自动化"重复扣费退款"——读工单、查政策、判断金额、起草邮件。

涉及系统：
- **acme-orders**（订单系统，REST API）
- **SharePoint**（公司文档库）
- **邮件系统**（发邮件）

涉及身份：
- 小李的 Azure AD 账号（客服组）
- cron 服务账号 `crm-bot`（无人值守跑）
- 客户的 AD 账号（Teams 触发场景）

**这个场景后面会被反复用到**。

---

## 5. 机制①：凭证作用域工具（不鸡肋）

### 5.1 在解决啥问题

传统企业 agent 工具库的设计：

```
sharepoint_list_files(folder_id)
sharepoint_get_item(item_id)
sharepoint_upload(folder, file)
sharepoint_search(query)
acme_orders_create_order(...)
acme_orders_query(soql)
acme_orders_cancel(...)
... （30+ 个方法，每个新系统新操作都要扩）
```

**问题**：
- 方法目录**随系统线性膨胀**——每加一个系统加一堆方法
- 描述维护成本**持续**——产品改字段就要改 description
- 模型只能在**枚举里选**——schema 没列的操作它用不了
- 评审负担**重**——每个方法每个字段都要审

### 5.2 论文的解法（一句话）

> 每个后端只贡献一个**通用 request 工具** + 一段**私有 quirk 说明**，模型自己用 SOQL/Graph/REST 语法组合调用。

### 5.3 关键洞察：模型天生会 80% 的 API

论文的核心赌注（**机制① 唯一的"赌"**）：

> 前沿模型训练时见过几百万行 Graph/OData/SQL/REST 的代码和文档。你让 Claude 拼一个 `$filter=contains(...)` 的 OData 表达式、组装一个 Graph 的 `GET /me/drive/root/children` 请求——**它本来就会**。

MCP 干的事：**用一个更窄的、手工维护的 API 模型，替换掉模型脑子里那个更宽的、已经训练好的模型**。

### 5.4 用 acme-orders 走一遍

**传统做法（MCP）**：30 个方法，每个都要写 schema。

**论文做法**：

```yaml
# tools.yaml（每个后端一段 usage_hint）
tool: acme-orders
description: |
  acme-orders REST v2 通用请求工具。
  鉴权用 30 分钟窄 token。
  金额用 cents（整数），不接小数。
  客户 ID 前缀 CUS-，订单前缀 ORD-。
  列表分页 cursor-based，next_cursor 在响应里。
  取消和退款是两个独立 endpoint：
    取消: POST /orders/{id}/cancel
    退款: POST /refunds  ← 不在 orders 下
  OpenAPI 规范: https://acme-internal.company.com/openapi.json
  bash_ 可以直接 curl 拉。
```

模型自己组合请求：

```js
request("acme-orders", "POST", "/api/v2/orders",
        {customer_id: "CUS-4421", amount_cents: 380000, ...})
```

它**会**拼这个，因为：
1. REST POST 语法——**模型天生会**
2. 金额用 cents——**usage_hint 告诉它**（私有 quirk）
3. 字段名 customer_id——**模型见过类似命名**

### 5.5 真正的"机制"是双闸门

光通用工具还不够，论文配合了**双层控制**：

**第一闸：工具可见性（discover）**——决定你能看到哪些工具
```js
// 网关根据小李的 AD 组过滤
const catalog = filterByGroups(requesterGroups, toolsYAML);
// 小李看到：acme-orders, sharepoint-reader, email-sender
// 看不到：finance-system（不在她组里）
```

**第二闸：操作权限（token scope）**——决定你能用工具干啥
```js
// 网关用小李身份去换 token
const token = await exchangeOnBehalfOf(lisiIdentity, ACME_SCOPE);
// 换到 scope=orders.read（write 需要其他组）
```

两层**不可绕过**：模型看不到的工具碰不到，拿到 token 也只能干 scope 允许的事。

### 5.6 论文承认的局限

> ❌ **对内部、非标、文档不全的 API，未经验证**——这些场景手工方法可能仍胜过模型自己组合。

判断标准：
- 有 OpenAPI/Swagger 规范 → 适合通用 request
- 走 Graph/OData/SQL 标准化接口 → 适合
- 协议非标、字段嵌套极深、文档不全 → 手写专用方法兜底

---

## 6. 机制②：身份外部注入（鸡肋）

### 6.1 坦诚地说

**单独看机制② 就是依赖注入——Java Spring `@Autowired` 入门课内容**。

如果你读过任何依赖注入框架，机制② 就是常识。

### 6.2 但在 agent 领域被频繁违反

论文面对的现实：

| 框架 | 怎么违反 |
|------|---------|
| LangChain | 工具权限写在 chain 定义里 |
| CrewAI | 每个 agent 角色配自己的工具集 |
| Copilot Studio | 权限藏在低代码编排里 |
| 自研 LangGraph | 每个 use case 写一份权限判断 |

**所以论文把它叫"机制"不是因为它新颖，是因为 agent 领域需要被重新强调**。

### 6.3 用 acme-orders 走三个场景

| 场景 | 触发方式 | 身份来源 |
|------|---------|---------|
| 小李终端交互 | `microcc run --problem "..."` | 她的 `az login` 凭据 |
| cron 每 15 分钟跑 | K8s CronJob | 镜像里配的 `crm-bot` 服务账号 |
| Teams 客户触发 | 客户在 Teams 发消息 | Teams OAuth token 里提取的客户身份 |

**三种身份，三种来源，但同一份 harness 代码零修改**。

### 6.4 机制② 的全部内容（一句话）

> config.yaml 不是身份本身，是"身份的取用说明书"。身份本身永远在 harness 外面。harness 只负责按说明书去取 + 拿来用。

### 6.5 为什么论文坚持要叫它"机制"

不是它新颖，是：
1. **agent 领域需要被重新强调**——太多框架违反
2. **配合机制① 才显出价值**——身份外部注入 + 工具无 schema 约束 = "同一份代码无修改跑三种表面"
3. **治理友好**——评审员只看 entitlement 配置，不读代码

---

## 7. 机制③：注册即部署（不鸡肋，论文真正的工程贡献之一）

### 7.1 在解决啥问题

传统流程：

```
写代码 → 提 PR → 等 3 周审批委员会审批 → 部署 → 注册到台账
                     ↑
                  杀手
```

**问题**：
- 审批永远慢
- 大部分创新没机会走到审批
- 大家都跑去"雷达外"自己搞
- 治理完全失控

### 7.2 论文的解法（一句话）

> **改两个文件 → git push → CI/CD 自动部署 + 自动注册。注册是 push 的副产品。三道门自动检查，只有真踩雷才升级给人。**

### 7.3 用 acme-orders 退款走五步流程

**第 1 步**：小李在终端交互跑通

```bash
microcc run --problem "客户 CUS-4421 重复扣费 3800 美元，要退款"
```

**第 2 步**：把跑通的写进 instructions（自然语言）

```markdown
# instructions.md
## 任务
处理重复扣费退款。

## 步骤
1. 拉工单，提取 customer_id / order_id / amount
2. 查 acme-orders 拉客户近 6 个月订单
3. 查 SharePoint 的"退款政策 2026.pdf"
4. 按金额分类：< 1000 自动批 / 1000-5000 起草邮件 / > 5000 升级
```

**第 3 步**：写 config.yaml

```yaml
owner: lisi@company.com
problem: "处理退款工单分诊"
tool_groups: [crm-triage, sharepoint-readonly, email-sender]
skills: [refund-triage-playbook]
business_area: customer-service
model: claude-sonnet-5
schedule: "*/15 * * * *"
registration_id:    # ← 留空！
```

**第 4 步**：git push

**第 5 步**：CI/CD 自动干活

```
1. 发现 registration_id 空 → 走首次部署
2. 跑三道门（下面详述）
3. 通过 → 注册、拿到 uuid
4. bot commit 把 uuid 写回 config
5. 烘焙镜像 + 拉起 cron job
```

**5 分钟上线**（假设三道门都过）。

### 7.4 三道注册门（这是核心）

```js
async function register(deploy) {
  const requester = await resolveDirectoryGroups(deploy.triggeredBy);

  // 闸 1：entitlement（资格门）
  if (!entitlementGate.allows(requester, deploy.businessArea))
    return pendingReview(deploy, "entitlement");

  // 闸 2：overlap（重叠门）
  if ((await findSimilar(deploy)).score > BLOCK_THRESHOLD)
    return pendingReview(deploy, "overlap");

  // 闸 3：risk（风险门）
  if ((await assessRisk(deploy)).risky)
    return pendingReview(deploy, "risk");

  return registry.upsert(deploy);
}
```

**闸 1 entitlement**：小李在 crm-team 组吗？不在 customer-service 注册白名单？→ pending

**闸 2 overlap**：已有"退款分诊"方案，新 push "自动退款"重复吗？→ 用小模型分类（不靠裸 cosine）→ 真的重复才 pending

**闸 3 risk**：读 instructions + skills + tool_groups，判断组合在该业务域该不该在无人看时跑
- "tool_groups=finance-read" + "instructions=定期对账" → safe
- "tool_groups=finance-read" + "instructions=自动付款给供应商" → risky

### 7.5 关键设计：pending-review 不是拒绝

```
不是 exit 1（粗暴拒绝）
不是静默放行

而是：
  1. 把原因打进 build summary
  2. 不供应基础设施（cron job 不会跑起来）
  3. 推一条消息到 Teams 频道：
     [批准] [拒绝]  ← 主管点一下
  4. 一步翻转评审记录 + 注册状态
```

**精妙处**：机器审 + 人审 + 反馈即时，三者结合。

### 7.6 为什么这不鸡肋

**机制② 你说鸡肋**——因为依赖注入是入门课。

**机制③ 不鸡肋**——因为它解决真实的企业治理难题：

> **"前置审批"为什么不被讨厌**——传统认为审批必要是因为"评审代码太贵"，所以要事前筛。前沿模型改变了成本结构——评审代码库塌缩成读一个 instructions 文件。
> **所以前置审批的合理性消失了**——应该改成"先 push，机器自动筛，只有人类该看的才给人看"。

**这是治理范式转移**，不是工程小技巧。

---

## 8. 机制④：法官机制（重要但有核心缺陷）

### 8.1 在解决啥问题

模型自己检查自己写的作业，它会放水：

```
自己问自己："这次退款合理吗？"
自己答自己："合理。我前面查过订单、政策、客户历史，都对得上。OK 通过。"
```

**为什么不行**：
- 同一个上下文**已经决定了**要退款——它有立场
- 跑长链路时**约束会丢**（论文引用 2604.13107 的 4 个失败模式之一：dropped constraints）
- **没有外部制衡**——像让作者给自己写书评

### 8.2 论文的解法（一句话）

> Spawn 一个**全新的** harness 实例——新上下文、新记忆、干净判断力——让**它**看这次调用 + instructions + trace。

### 8.3 用 acme-orders 退款走一遍

**发起方客服 harness 跑了 3 轮后**：

```
轮 1: 拉订单 → 重复扣费 3 × 1267 = 3801 美元
轮 2: 查政策 → "1000-5000 美元需人工复核"
轮 3: 拉客户 → VIP，90 天无异常
得出结论：构造退款调用，risky=true
```

**构造调用**：
```js
request("acme-orders", "POST", "/api/v2/refunds",
        {customer_id: "CUS-4421", amount_cents: 380000})
risky: true
```

**spawn 法官**（全新 harness）：

```
法官任务：审下面这次调用是否合理
方案 instructions（摘要）：
  "1000-5000 美元需人工复核后发起"
trace（前 3 轮）：
  轮 1: 重复扣费 3801 美元
  轮 2: 政策"需人工复核"
  轮 3: VIP 客户
待审调用：
  POST /api/v2/refunds 3800 美元
```

**法官判断**：

> "金额符合损失。客户 VIP 良好。但 instructions 写明需人工复核，trace 里**没看到人工复核环节**。HOLD。"

**status: unresolved** → 弹 Teams 给客服经理审批 → 经理点批准 → 才真正调 acme-orders。

### 8.4 ⚠️ 诚实承认：法官本身也是 LLM

**论文没解决这个问题**。

法官也是 LLM，它也会：
- 幻觉（看到不存在的"已人工复核"字段）
- 丢约束（instructions 写了规则，法官看了但忘了）
- 过度自信（"我看了没问题"——其实没仔细看）
- 懒启发式（"金额在范围内放行吧"）

**论文 §5 局限性原文**（白纸黑字）：

> *"The four failure modes... have no dedicated mechanism addressing them in this paper. We don't have a controlled benchmark showing how well this holds up."*

### 8.5 论文的真实立场（不是技术承诺，是经济赌注）

**论文没承诺 100% 可靠**。它的真实承诺是：

1. **大部分常规操作模型能干**（节省人力）
2. **关键操作通过分层防御让人兜底**（不是 100% 但够用）
3. **错误能被发现**（trace 留底、对账、审计）
4. **治理成本够低**（不需要每笔都人审）

**整篇论文的核心赌注**藏在 §4.12：

> *"The architecture bets on continued frontier-model capability improvement."*

**大白话**：我们赌模型会越来越准。这是**信仰**，不是工程方案。

### 8.6 实际工程怎么补（论文没说）

如果你真的要把机制④ 用在 acme-orders 退款，要加这些：

**1. 关键路径强制人审**（不靠 LLM 自评）
```yaml
human_approval_required:
  always_for:
    - amount_cents > 100000   # > 1000 美元强制
    - involves: ["refund", "void", "transfer"]
```

**2. 法官可以是规则引擎**
```js
function judge(call) {
  if (call.amount > 50000 && !call.context.has_human_review) {
    return { status: "unresolved" };  // 硬规则，0% 幻觉
  }
  // 模糊地带才用 LLM
  return await llmJudge(call);
}
```

**3. 多重法官投票**
```js
const verdicts = await Promise.all([judge1(), judge2(), judge3()]);
if (verdicts.filter(v => v === "resolved").length >= 2) proceed();
```

**4. 事后审计对账**（兜底）
```bash
# 每天早上跑
diff acme-orders/actual_refunds.json harness-registry/agent_runs.json | alert
```

### 8.7 你的判断标准

| 你的场景 | 机制④ 是否合适 |
|---------|---------------|
| 必须 100% 可靠（救命药、核电） | ❌ 别用 LLM |
| 99.9% 可接受 + 审计兜底（客服退款） | ⚠️ 可用但要加硬约束 |
| 99% 可接受 + 试错空间（内容生成） | ✅ 论文够用 |
| 80% 可接受 + 快速迭代（内部工具） | ✅ 论文很好 |

**acme-orders 退款的真实答案**：法官不是最后闸门——**配置硬约束 + 后端权限 + 审计对账**这三层**不依赖 LLM**，才是 100% 可靠的兜底。

---

## 9. §4.4 知识底座 = git 镜像（反主流，但有道理）

### 9.1 在解决啥问题

**RAG 的三个根本问题**：

| 问题 | 后果 |
|------|------|
| 让模型不探索 | 把模型关在"相似度分数"里，只看分数高的几条 |
| 丢结构 | 片段被切碎，丢了所在文档、上下文树、provenance |
| 不可审计 | "那次检索到了啥"完全黑盒，无法重建 |

### 9.2 论文的解法（一句话）

> 把企业文档库**增量同步到一个 git 仓库**，模型用 bash_ 主动探索，不靠向量相似度。

### 9.3 用 acme-orders 退款查"政策"走一遍

**同步过程**（每天凌晨 2 点跑，不在 harness 主流程里）：

```js
async function syncSharePoint(cursor) {
  const changes = await sharepoint.delta(cursor);  // cTag 增量
  for (const item of changes) {
    const path = mirrorPath(item);  // 路径 = 源系统目录树位置
    const text = isTextful(item) ? item.body : await renderToText(item);
    await writeMirrorFile(path, text, item.aclGroup);  // ACL 跟文件走
  }
  return commitMirror(`sync: sharepoint @ ${changes.newCursor}`);  // 一个 commit
}
```

**镜像长这样**：

```
sharepoint-mirror/
├── .git/                      ← 完整 git 历史
├── 客服/
│   ├── 政策/
│   │   ├── 退款政策2026.pdf   ← ACL: [crm-triage]
│   │   ├── 退款政策2025.pdf   ← ACL: [crm-triage]
│   │   └── 退款政策2024.pdf
│   └── SOP/
│       └── 工单分诊SOP.md
└── 法务/
    └── 合规要求2026.pdf       ← ACL: [legal-team]
```

**客服 harness 查政策时**（用 bash_ 主动探索）：

```bash
# 列出客服政策目录
bash_: ls sharepoint-mirror/客服/政策/
# → 退款政策2026.pdf  退款政策2025.pdf  退款政策2024.pdf

# 看哪个最新
bash_: git -C sharepoint-mirror log --oneline -- 客服/政策/

# 读最新那份
bash_: cat sharepoint-mirror/客服/政策/退款政策2026.pdf
```

### 9.4 三个关键设计（论文真正的工程贡献）

**设计 1：路径 = 位置 = 无损索引**
- 文件在镜像里的路径 = 源系统目录树里的路径
- 模型看到路径**就知道**这是哪份政策、在哪个目录

**设计 2：增量同步（按源系统版本号）**
- SharePoint 用 cTag、Confluence 用页面版本、SQL 用 rowversion
- 只拉"上次同步后变了的东西"，不重复拉

**设计 3：git = 审计追踪器**
```
同步：每次同步 → 一个 git commit
读取：每次 bash_ cat → 网关记下"在 commit xxx 时读了 yyy"
审计：checkout 到 commit xxx → 看到模型当时眼前的内容
```

**为什么重要**：向量库"那次检索到了啥"永远无法重现，git 镜像能 checkout 回那一刻。

### 9.5 论文承认的局限

- **滞后窗口**：上次同步后改的文档对运行不可见（论文认为是"刻意的代价"）
- **ACL 边界**：镜像的 ACL 是同步时捕获的快照，源系统的"effective permissions"很难
- **运维复杂**：要维护一个 git 镜像系统
- **模型 bash_ 能力要求高**：大文档库 grep 不动

### 9.6 实际工程折中

- **结构化文档**（政策、SOP）→ git 镜像
- **大规模非结构化**（邮件附件、扫描件）→ RAG
- **两者并存**，按需用

---

## 10. §4.11 组织设计（核心政治宣言）

### 10.1 在解决啥问题

传统企业 AI 团队的两种失败模式：

**模式 A：中央 AI 团队啥都建**
```
业务部门提需求 → AI 中心排优先级 → 客服等了 6 个月没排上
                                          ↓
                              客服自己偷偷搞 LangChain
                                          ↓
                              合规部发现 → 关停
```

**模式 B：每个业务线自建**
```
客服搞 LangChain、销售搞 CrewAI、财务搞 Copilot Studio
N 个代码库、N 个治理模型、N 个孤儿
```

### 10.2 论文的解法：三职责分离

| 角色 | 拥有 | **不**拥有 |
|------|------|----------|
| 中央平台团队 | 网关、注册表、参考仓库、策略基线 | ❌ 不建用例、❌ 不为业务团队交付 |
| 业务/工程单元 | 自己的用例识别 + 自己的方案交付 | ❌ 不造轮子 |
| enablement | onboarding 新工具、审高风险、答疑 | ❌ 不当交付团队 |

### 10.3 用 acme-orders 场景走一遍

**小李（业务单元）**：
- fork 参考仓库
- 自己跑通退款处理
- 自己写 instructions.md 和 config.yaml
- 自己 push

**中央平台团队**：
- 维护 `microcc-harness-template` 参考仓库
- 维护 entitlement.yaml
- 维护工具网关
- **没**替小李写 instructions

**enablement**：
- 小李发现 acme-orders 工具权限配错
- 办公时间问 → enablement 帮她查 entitlement 配置 → 修正
- **没**替她写 instructions

**如果小李反复让 enablement 帮她写 instructions**：

> *"That's a signal the unit needs different support. It doesn't mean the enablement function should grow into a delivery team."*

**那是信号**——说明客服组**需要更多工程师**或**更好的工具**，不是说 enablement 应该扩成交付团队。

### 10.4 最有力量的一段（论文原文翻译）

> *"Custom code used to justify an upfront gate because looking back at it was expensive. Frontier models have already collapsed the other half of that: an engineer can now build the exact custom thing they saw a need for, cheaply."*

> **以前前置审批存在的理由是"评审代码太贵"。前沿模型把"造"这一半的成本塌了——工程师能便宜地造出他们看见需要的那个专属东西。**

> *"People embedded in their own domain see the niche problems nobody else does. These problems are too small or too specific for a central team to ever prioritize, but real enough to cost someone hours every week."*

> **嵌在自己领域里的人才看得见那些利基问题——太小、太具体，中央团队永远不会优先排，但真实到每周烧某个人的几小时。**

> *"A central team that has to build everything itself is stuck prioritizing by scale, and the niche problem never gets solved."*

> **一个啥都得自己建的中央团队只能按规模排优先级——利基问题永远不被解决。**

> *"This architecture removes the cost that justified the gate."*

> **这个架构移除了为门禁提供合理性的成本。**

### 10.5 前提条件

这套组织设计能跑起来需要：

1. 业务线有会写 instructions 的人
2. 中央平台团队足够强
3. enablement 真的"只解卡不交付"
4. 业务单元愿意承担 ownership

**如果这些前提不满足**，整个机制崩。

---

## 11. 业务逻辑全在 markdown 里（一个关键洞察）

### 11.1 这意味着啥

**这架构里几乎没有"业务代码"**——业务专家接触的所有东西都是文本文件：

| 谁 | 产出 | 形式 |
|----|------|------|
| 中央平台团队 | harness 代码 + IaC + 网关 | 真实代码（少数） |
| 业务专家 | instructions + skills + config | **自然语言 + 配置** |
| 模型 | bash_ 脚本 | **临时 shell**（不持久） |

**业务逻辑 99% 在 markdown 里**。

### 11.2 三种解读

**革命性解读**：
> 代码不再稀缺，业务逻辑应该用人类最自然的方式表达——自然语言。代码只是最后一步的执行细节。

**赌博性解读**：
> 我们赌模型能稳定理解自然语言 instructions。这个赌如果输了，所有方案都要重写。

**实用性解读**：
> 对 80% 的企业知识工作，自然语言 instructions 够用。比写代码便宜得多。

### 11.3 好处

| 维度 | 传统代码 | instructions |
|------|---------|--------------|
| 谁能写 | 必须会 Python/JS | 会写 markdown 就行 |
| 评审 | 读代码 | 读 markdown |
| 改一次 | 发版、PR、CI/CD | 改文本、push |
| 编译错误 | 经常有 | 不会有 |
| 测试覆盖 | 单元测试 | **没有**（靠"先跑通"代替） |

### 11.4 代价

| 维度 | 传统代码 | instructions |
|------|---------|--------------|
| 编译期验证 | 有 | **没有** |
| 调试 | stack trace | 看 trace 推测 |
| 可重现 | 同样输入同样输出 | **不同模型不同行为** |
| 类型检查 | 有 | **没有** |
| 文档同步 | 经常过时 | instructions 本身就是文档 |

**特别是**：instructions 写"看起来对但跑起来错"——只能跑一遍才知道。

### 11.5 缓解方法

§4.7 部署路径："**先跑通再蒸馏**"

```
1. 工程师在终端对真问题跑 harness（live 模式）
   → 跑 5 次、10 次，看到模型理解对了
2. 把跑通的模式写进 instructions
3. 把可复用部分抽出来成 skill
4. push
```

**这代替了单元测试**——靠"工程师先跑通"代替"代码测试"。

**论文 §5 承认**：

> *"We don't have a controlled benchmark showing how well this holds up, or against which of the four modes specifically."*

---

## 12. 论文整体图（一图流总结）

```
写代码成本塌了，事后成本没塌
         ↓
企业不能放任每个人 DIY
         ↓
harness 作为企业基础设施骨干
（一个产物无修改跑遍所有表面）
         ↓
四个机制让"无修改一处跑三面"可治理
         ├─ 机制① 凭证作用域工具（治理对接企业真实 IAM）
         ├─ 机制② 授权不进 harness（一个产物处处同理）
         ├─ 机制③ 部署即注册（审计 N 方案 = 读 N 个 instructions）
         └─ 机制④ 新鲜实例当法官（risky 调用先自证再请人）
         ↓
配合两个支撑设计
         ├─ §4.4 知识底座 = git 镜像（可审计）
         └─ §4.11 三职责分离（组织形态）
         ↓
落点：治理成为部署的自然产物
赌注：模型能力持续复合 + 模型 bash_ 能力足够
缺口：业务逻辑在 markdown 里的可靠性 + 100% 可靠的硬场景
```

---

## 13. 诚实未竟之事

论文**没解决**的核心问题：

### 13.1 机制④ 法官本身也是 LLM

论文 §5 承认 4 个失败模式（懒启发式、幻觉、丢约束、过度自信）**没专属机制**。法官能缓解"上下文污染"问题，但**法官自己也有这些失败模式**。

### 13.2 业务逻辑在 markdown 里的可靠性

没有编译期验证、没有类型检查、不可重现、调试难。**论文承认没有 benchmark 证明**"先跑通再蒸馏"能多大程度缓解。

### 13.3 只在 Azure + 欧洲企业验证过

论文的证据基础：欧洲几个企业、Azure 身份与策略原语。换云、换 on-prem 是否成立**仍是开放主张**。

### 13.4 核心赌注是"模型会越来越准"

整篇论文架构押注前沿模型能力**持续复合增长**。这是**信仰**，不是工程方案。

### 13.5 SHarD 的三个控制只做了一个

论文引用 SHarD 的三个安全控制（OS 沙箱 / 技能扫描 / 工具限制）——**只深入了第三个**。容器隔离是粗粒度的，**技能扫描完全没有**——`live_skills` 把构建期信任一次的洞扩成**每次运行都信任**。

### 13.6 老基座不管

"Governance by construction"只覆盖新方案，**管不了已安装基座**（老 RAG 管线、旧 custom chains、早期手工集成）。旧访问不追溯关闭。

---

## 14. 如果你是 X 角色

### 14.1 如果你是架构师

**可以直接用的机制**：
- 机制③ 注册即部署（fork-configure-push）→ 可直接落地
- §4.11 三职责分离 → 组织设计参考
- 知识底座 git 镜像（如果有结构化文档）

**要本地化的机制**：
- 机制① 凭证作用域工具 → 你企业的 API 标准化程度决定能不能直接用
- 机制② 身份外部注入 → 配合现有 IAM 系统调整

**谨慎用的机制**：
- 机制④ 法官机制 → 关键资金场景要加硬约束 + 多重法官 + 审计兜底

### 14.2 如果你是业务方

**怎么跟中央 AI 团队谈合作**：

1. **不要**让中央团队替你建方案——用 fork-configure-push
2. **要**让中央团队给你好用的参考仓库 + 工具网关 + 技能库
3. **要**enable 帮你接入新工具
4. **自己**承担方案 ownership：写 instructions、看 trace、处理异常
5. **如果反复需要 enable 帮你写 instructions**——那是信号，说明你需要更多工程师或更好的工具

### 14.3 如果你是中央 AI 团队 leader

**怎么转型**：

| 旧的 | 新的 |
|------|------|
| 交付团队 | 平台团队 |
| 替业务建方案 | 维护参考仓库让 fork 成本为 0 |
| 排优先级 | 让业务自己交付 |
| 越来越大 | 保持小而精 |
| 评审 PR 代码 | 评审 instructions 文档 |
| 业务线来提需求 | 业务线自己 fork + push |

**核心转变**：你的价值不在"交付了多少方案"，在"让交付变得便宜"。

### 14.4 如果你是怀疑者

**什么场景别用**：

| 场景 | 别用 | 因为 |
|------|------|------|
| 100% 不能出错（救命药、核电） | ❌ | 法官也是 LLM，论文没承诺 100% |
| 错误代价极高（核按钮） | ❌ | 形式化验证 > LLM 推理 |
| 内部完全非标 API | ❌ | 机制① 在标准 API 上成立 |
| 模型 bash_ 能力差（小模型） | ⚠️ | §4.4 git 镜像依赖 bash 探索 |
| 业务线没人会写 instructions | ❌ | §4.11 三职责分离前提不满足 |
| 文化上不愿意让业务单元当 owner | ❌ | enablement 会膨胀成交付团队 |

**什么场景适合用**：

- 客服退款分诊、文书审阅、报告生成等"可重复但需跨系统推理"的工作
- 业务专家能写 instructions
- 中央平台团队足够强
- 有 Azure AD / 类似的 IAM 系统
- 治理是真实痛点（碎片化严重）

---

## 附：v2 改进说明（相对于 v1）

| 维度 | v1 | v2 |
|------|----|----|
| 结构 | 论文原文顺序 | 按"可理解性"重新组织 |
| 语言 | 术语堆砌 | 大白话优先，术语在括号里 |
| 故事 | 多个场景混杂 | 单一 acme-orders 退款贯穿 |
| 鸡肋标注 | 辩护太多 | 直接标"鸡肋"vs"不鸡肋" |
| 机制④ | 当成"机制"讲 | 诚实承认有核心缺陷 |
| 业务逻辑在 markdown | 散落各处 | 单独成节 |
| 诚实未竟之事 | 局限散落 | 单独成节 |
| 给决策者 | 没单独节 | 按角色给 |
| 篇幅 | 41 KB | 目标 15 KB（更聚焦） |

v2 优先保证**读完能行动**，而不是**读完能复述论文**。
