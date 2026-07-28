# 08 · 上下文压缩（Compaction）

> 长对话上下文要爆了怎么办？V2 有两套压缩策略（自动 + 溢出），把旧历史压成结构化摘要，保留近期 Tail，让对话能一直跑下去。
>
> [04-runner.md](./04-runner.html) 的 ⑦ 节讲了压缩的**调用入口**（`compactIfNeeded` 怎么被 runner 调、`TurnTransition` 怎么续跑），本篇讲压缩的**内部**：策略分工、摘要怎么生成、Tail 怎么保留、历史怎么重建。

---

## 一、心智模型：会议纪要

想象一场开了三个小时的会。每个人都记着从头到尾的每一句话——脑子迟早要炸。真实做法是：**每隔一段，把前面的讨论总结成一页摘要，最近的关键讨论保留原话，之后基于「摘要 + 近期原话」继续开。**

LLM 的上下文窗口就是那颗「迟早要炸的脑子」。模型能塞进去的 token 是有限的（**context window**，上下文窗口），长对话里历史消息不断累积，早晚超过窗口上限——这时模型要么拒绝处理，要么报 **context overflow**（上下文溢出，即「塞不下了」）错误。

> **术语：token 估算**。模型不按「字数」算账，按「token」算（大致 1 个英文词 ≈ 1 token，中文更碎）。精确分词要调模型的 tokenizer，很贵；V2 用一个粗略近似：**4 个字符 ≈ 1 token**（`Token.estimate`，`util/token.ts:3-5`）。这个估算不精确，但够用来判断「要不要提前压缩」。

压缩做的事就是「会议纪要」：

```
压缩前（一条长历史）：
[消息1] [消息2] [消息3] ... [消息97] [消息98] [消息99] [消息100]

压缩后（摘要 + 近期原文）：
┌─────────────────────────┐  ┌──────────────────────────────┐
│  摘要（Summary）         │  │  近期原文（Tail / Recent）     │
│  把 消息1..消息97 压成   │  │  消息98、消息99、消息100 原样保留 │
│  一页结构化纪要          │  │                              │
└─────────────────────────┘  └──────────────────────────────┘
         └──────── 这两者拼成一条新的「compaction 消息」落账本
```

之后每个 turn 开始前重新加载历史时，旧消息（消息1..97）被「折叠」进摘要，模型看到的就只有**一条摘要消息 + 几条近期消息**，token 大幅下降。

---

## 二、两套策略：自动 vs 溢出

![两套压缩策略：自动（发请求前预防）与溢出（报错后兜底），共享同一压缩实现](./assets/08-compaction-strategy.svg)

V2 把压缩设计成**两道防线**，一道主动、一道被动：

|  | 自动压缩 `compactIfNeeded` | 溢出压缩 `compactAfterOverflow` |
|---|---|---|
| 触发时机 | **发请求前**，预估 token 超阈值 | **请求发出后**，provider 明确报 context overflow |
| 性质 | 主动、预防性 | 被动、兜底 |
| 配置门控 | 受 `config.compaction.auto` 开关控制 | 不受开关控制，只在 overflow 时触发 |
| 调用入口 | runner 在构建好 request 后、发流前调（`llm.ts:215`） | 通过 `recoverOverflow` 参数传入 runner，仅流式失败收尾时调（`llm.ts:286`） |

文字版（终端友好）：

```
┌─ turn 开始 ──────────────────────────────────────────────────────┐
│                                                                  │
│  ① 构建 request（system + messages + tools）                      │
│                                                                  │
│  ② 自动压缩 compactIfNeeded（发请求前）                            │
│     估算 token ──超阈值──► 压缩 → 抛 ContinueAfterCompaction 重跑  │
│                  └─没超─► 继续                                     │
│                                                                  │
│  ③ llm.stream(request) ──► provider                              │
│                          │                                       │
│                 ┌────────┴────────┐                              │
│                 ▼                 ▼                              │
│            正常返回          context overflow 报错                │
│                                  │                               │
│  ④ 溢出压缩 compactAfterOverflow（收到错误后，兜底）               │
│     压缩成功 → 抛 ContinueAfterOverflowCompaction 重跑（仅一次）   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 为什么需要两套

自动压缩靠**估算**判断要不要压，但估算是粗略的（4 字符 ≈ 1 token），而且 provider 真实的窗口边界、系统提示占用、工具定义占用都可能和估算对不上。**估算说「没超」，provider 实际却 overflow 了**——这时候就需要溢出压缩兜底：既然 provider 明确说塞不下了，那就压一把再重试。

反过来，单靠溢出压缩也不行：每次都要「发请求→失败→再压→再发」，浪费一次 provider 调用（还要钱）。所以正常情况下靠自动压缩提前避开，估算失灵时溢出压缩兜底。

> **重要**：两套策略最终都调用**同一个内部实现** `compactAfterOverflow`（`compaction.ts:172-224`）——它才是真正「切历史、跑摘要、写账本」的核心。区别只在**触发条件**：
> - `compactIfNeeded`（`compaction.ts:225-236`）先检查 `config.auto` + token 阈值，过了才委托给 `compactAfterOverflow`。
> - runner 的溢出恢复直接调 `compactAfterOverflow`，不做阈值检查。
>
> 名字有点误导（`compactAfterOverflow` 听起来只服务溢出场景），实际它是**共享的压缩实现**。

---

## 三、压缩的本质：head / recent 切分 + 摘要生成

核心实现在 `compactAfterOverflow`（`compaction.ts:172-224`），分四步：

### 第 1 步：把历史切成 head（旧）+ recent（新）

`select` 函数（`compaction.ts:128-159`）把序列化后的对话从**末尾往前**累加 token，直到加满 `keepTokens`（默认 8000）预算。预算之内的算 **recent（Tail，近期保留原文）**，超出的算 **head（旧历史，要被压成摘要）**：

```
[消息1] [消息2] ... [消息97] | [消息98] [消息99] [消息100]
└────── head（摘要） ──────┘   └──── recent（Tail 原文） ────┘
                                  ▲
                          从这里往前累加，加满 8000 token 为止
```

两个细节：

- **先序列化再切**。每条消息先经 `serialize`（`compaction.ts:86-112`）拍平成带前缀的文本（如 `[User]: ...`、`[Assistant tool call]: write(...)→[Tool result]: ...`），工具输出超长的会被 `truncate` 截断（见下）。
- **会在一条消息内部切**。如果加到某条消息时刚好超预算，`select` 不会整条丢到 head，而是**按字符把这条消息劈成两半**：前缀进 head、后缀进 recent（`compaction.ts:144-148`），尽量用满预算。

> **术语：Tail（近期原文）**。压缩后保留的、未经摘要的最近若干条消息。它的体量由 `DEFAULT_KEEP_TOKENS` 控制。Tail 必须保留原文——因为模型做后续推理需要精确的、未失真的近期上下文（比如最近一次工具的返回值、用户最新一句话），摘要会丢细节。

### 第 2 步：截断超长工具输出

工具（尤其读文件、跑命令）经常返回几千上万字符。序列化时用 `truncate`（`compaction.ts:76-77`）把每段工具输出裁到 `TOOL_OUTPUT_MAX_CHARS`（2000 字符）以内，超出部分以 `[truncated]` 标记。这一步发生在 `serialize` 里（`compaction.ts:100`），既减小 head 的体积、也减小 recent 的体积。

### 第 3 步：调一次 llm.stream 生成结构化摘要

用 `buildPrompt`（`compaction.ts:161-168`）拼出摘要请求，再调一次 `llm.stream` 跑一个**不带工具**的纯文本生成（`compaction.ts:195-212`）。这一步是压缩的「成本」：每压缩一次，多花一次模型调用。

摘要请求里塞三样东西：

1. **上一轮的摘要**（如果存在）。压缩是**增量**的——历史里可能已经有一条旧的 compaction 消息，这轮会把「旧摘要 + 新增对话」合并，而不是从头重摘。prompt 里会从 `Update the anchored summary`（`compaction.ts:163-164`）切到 `Create a new anchored summary`（`compaction.ts:165`），视情况而定。
2. **SUMMARY_TEMPLATE**（结构化模板，见下一节）。
3. **head 文本**（要被摘掉的旧对话）。

### 第 4 步：写账本，生成 compaction 消息

摘要成功就发 `Compaction.Started` + `Compaction.Ended` 两个事件（`compaction.ts:186-191`、`215-222`）。`Ended` 带上 `text`（摘要全文）和 `recent`（保留的近期原文）。projector 把这条 `Ended` 投影成一条 `compaction` 类型的消息（`message-updater.ts:377-388`），从此它就是历史的一部分。

---

## 四、SUMMARY_TEMPLATE：结构化交接单

摘要是用 `SUMMARY_TEMPLATE`（`compaction.ts:16-46`）约束模型生成的，**不是自由摘要**。模板长这样：

```text
## Objective
- [一两句话：用户想达成什么]

## Important Details
- [约束/偏好、已做的决定及原因、关键事实/假设、继续下去必需的精确上下文，否则写 (none)]

## Work State
### Completed
- [已完成的工作、已验证的事实、已做的改动，否则 (none)]

### Active
- [当前在做的事、半成品改动、调查进度，否则 (none)]

### Blocked
- [卡点、失败的命令、未知项，否则 (none)]

## Next Move
1. [紧接着的具体动作，或 (none)]
2. [下一个动作（如果知道），或 (none)]

## Relevant Files
- [文件或目录路径：为什么重要，或 (none)]
```

模板末尾还附了硬规则（`compaction.ts:42-46`）：每节都要保留（哪怕填 `(none)`）、用简短 bullet 不用段落、**精确保留文件路径/符号/命令/错误串/URL/标识符**、不要提「这是压缩出来的」。

### 为什么用结构化模板

自由摘要容易丢三落四——模型可能把「为什么这么决定」的理由漏了，或把「下一步该干嘛」模糊带过。一旦这些丢了，后续推理就建立在残缺的上下文上。

这份模板本质是一张**交接单**（handoff）——像两个工程师交接工作时的 checklist：目标是什么、关键约束、干到哪了、卡在哪、下一步、相关文件。强制模型按这个框架组织，保证摘要里**该有的工程信息都在**，且结构稳定（每次都是同样的节），模型后续解析也容易。

具体到各节的用意：

| 节 | 解决「自由摘要会漏掉什么」 |
|---|---|
| **Objective** | 漏掉「用户最初到底想干嘛」——长对话里这个容易被埋没 |
| **Important Details** | 漏掉「为什么这么选」「用户明确说过的约束」这类**决策依据** |
| **Work State · Completed/Active/Blocked** | 漏掉「进度状态」——尤其 Blocked，防止模型重复踩同一个坑 |
| **Next Move** | 漏掉「紧接着该做什么」，避免压缩后模型原地打转 |
| **Relevant Files** | 漏掉「相关文件路径」——精确路径丢了就得重新找，浪费工具调用 |

---

## 五、配置常量

四个常量定义在 `compaction.ts:12-15`，都可通过 config 文档覆盖（`settings` 函数 `compaction.ts:114-126` 读 `config.compaction`）：

| 常量 | 默认值 | 含义 |
|---|---|---|
| `DEFAULT_BUFFER` | 20 000 | 自动压缩的**缓冲 token**。估算时留出 `max(output, buffer)` 的余量不压，避免压完还是紧巴巴 |
| `DEFAULT_KEEP_TOKENS` | 8 000 | **Tail 保留多少**。`select` 用这个预算从末尾往前保留近期原文 |
| `TOOL_OUTPUT_MAX_CHARS` | 2 000 | 工具输出**截断阈值**。序列化时每段工具结果超过这个字符数就裁断 |
| `SUMMARY_OUTPUT_TOKENS` | 4 096 | **摘要最大长度**（生成时的 `maxTokens`）。摘要本身不能太长，否则又占窗口 |

自动压缩的触发阈值（`compaction.ts:230-234`）是：

```
若 estimate(system + messages + tools) > context - max(output, buffer)
则触发压缩
```

- `context`：模型的上下文窗口上限，来自 `model.route.defaults.limits.context`。
- `output`：这一 turn 预期的输出 token，来自 `request.generation.maxTokens` 或模型默认 output 上限。
- `buffer`：上面的 `DEFAULT_BUFFER`。

意思是：**给输出和缓冲留够空间后，剩下的才允许塞历史；塞不下就先压**。

---

## 六、Compaction 事件三连

压缩过程发三种事件（`session-event.ts:398-432`）：

| 事件 | 落库？ | 内容 | 时机 |
|---|---|---|---|
| `Compaction.Started` | ✅ durable | `messageID`、`reason`（"auto"/"manual"） | 压缩开始，发摘要请求前 |
| `Compaction.Delta` | ❌ live-only | `messageID`、`text`（摘要碎片） | 摘要流式生成时，每个 text 碎片 |
| `Compaction.Ended` | ✅ durable | `messageID`、`reason`、`text`（完整摘要）、`recent`（近期原文） | 压缩完成，摘要全文到手 |

### 为什么 Delta 不落库，Ended 落库

这呼应 [01-event-log.md](./01-event-log.html) 的 durable / live-only 区分：

- **`Delta` 是流的中间碎片**——和 `Text.Delta`（文字流碎片）、`Tool.Input.Delta`（入参碎片）一样，是瞬态的。它的最终值会由 `Ended` 的 `text` 字段完整落库。如果把每个 Delta 都写进账本，一次压缩就要写几十上百条碎片，账本被高频碎片撑爆，重放时还要拼回原样，纯亏。
- **`Ended` 是语义边界**——它带的是「摘完了的完整结果」，是真正的、可重放的事实。projector 拿它生成 compaction 消息（`projector.ts:395`、`message-updater.ts:377-388`）。

技术上，`Compaction.Delta` 的定义（`session-event.ts:410-417`）**不带 `...options`**（即没有 `durable` 标记），所以它不在 `DurableDefinitions` 清单里（`session-event.ts:472-473` 只有 `Started` 和 `Ended`），只出现在全量 `Definitions`（`session-event.ts:506-508`）里。这就是「不落库、只在线上流一次」的代码体现。

> 当前实现里 `Compaction.Delta` 虽然在 schema 里定义了，但 `compaction.ts` 的摘要流式消费（`compaction.ts:205-209`）只把 `textDelta` 累积进 `chunks` 数组、并没发布 `Delta` 事件——也就是说**目前 Delta 事件实际没有被发出**，schema 先把位置占好了，留作未来给前端「实时显示摘要生成进度」用。

> 注：`reason` 字段当前两条路径都写 `"auto"`（`compaction.ts:190`、`219`）。schema 支持 `"manual"`（`session-message.ts:194`、`session-event.ts:405`），但暂无代码路径发它。

---

## 七、TurnTransition：压缩完怎么续跑

压缩会**改写历史**——一旦写了 compaction 消息，原来那个 request（基于旧历史构建的）就失效了，必须**用压缩后的新历史重建 request、重跑这个 turn**。

[04-runner.md](./04-runner.html) 第六节讲过 `TurnTransition` 机制：用 `Effect.die` 抛一个带 `_tag` 的 defect（非类型化异常，绕过错误通道），被外层 `catchDefect` 捕获后递归重跑。压缩贡献了两种 transition（`llm.ts:152-156`）：

| transition | 抛出点 | 含义 |
|---|---|---|
| `ContinueAfterCompaction` | `llm.ts:216`（自动压缩成功） | 主动压缩后重跑，**走回 `runTurn`**，还能再触发任意一种压缩 |
| `ContinueAfterOverflowCompaction` | `llm.ts:288`（溢出压缩成功） | 被动压缩后重试，**走专用的 `runAfterOverflowCompaction`**，不能再触发溢出压缩 |

两种 transition 的捕获与重跑（`llm.ts:369-381`）：

```ts
const runTurn = ... runTurnAttempt(..., compaction.compactAfterOverflow).pipe(
  Effect.catchDefect(function* (defect) {
    if (!(defect instanceof TurnTransitionError)) return yield* Effect.die(defect)  // 真 defect 原样重抛
    yield* Effect.yieldNow
    if (defect.transition._tag === "ContinueAfterOverflowCompaction")
      return yield* runAfterOverflowCompaction(...)   // 溢出路径：专用重跑
    return yield* runTurn(...)                          // 自动路径：递归重跑
  }),
)
```

### 为什么溢出压缩不能再 overflow

专用重跑入口 `runAfterOverflowCompaction`（`llm.ts:355-367`）调用 `runTurnAttempt` 时**不传 `recoverOverflow`**。于是在这个重跑里，如果 provider 又报 overflow，收尾逻辑（`llm.ts:283-288`）的 `recoverOverflow` 是 `undefined`，不会再尝试压缩，而是把 overflow 失败正常发布出去。

更直接地，`runAfterOverflowCompaction` 的 `catchDefect` 里对 `ContinueAfterOverflowCompaction` 显式 `die`（`llm.ts:360-361`）：

```ts
if (defect.transition._tag === "ContinueAfterOverflowCompaction")
  return yield* Effect.die("Post-compaction provider attempt cannot recover another overflow")
```

这是**防无限循环**：如果「压缩→重跑→又 overflow→又压缩」能无限套娃，一个超长 session 就会把压缩反复跑、把账本塞满 compaction 消息。所以设计成「溢出压缩只给一次机会」——压完还 overflow，就认输，把错误抛上去。

> 自动压缩（`ContinueAfterCompaction`）没有这个限制：它走回 `runTurn`，理论上可以连续触发多次自动压缩（每次压一轮、重跑、发现还超、再压）。但因为每压一次历史就短一截，正常情况下压一两次就够了。

---

## 八、压缩后的历史重建

压缩成功后，runner 的续跑会重新执行 `runTurnAttempt` 的开头几步（`llm.ts:179-214`），其中关键的是**重新加载历史**：

```ts
const entries = yield* SessionHistory.entriesForRunner(db, session.id, system.baselineSeq)
```

`entriesForRunner`（`history.ts:90-99`）内部先调 `latestCompaction`（`history.ts:13-22`）找最近一条 compaction 消息的 `seq`，再用 `messageRows`（`history.ts:24-53`）只取 **`seq >= compaction.seq`** 的消息（`history.ts:38`）。于是：

```
账本里的消息序列：
[m1] [m2] ... [m97] [compaction★] [m98] [m99] [m100]
                          │
                  latestCompaction.seq
                          │
entriesForRunner 只取 ────┘──────────────────────►  [compaction★] [m98] [m99] [m100]
（旧的 m1..m97 被折叠进 compaction 的摘要里，不再单独加载）
```

这条 compaction 消息在翻译给模型时（`to-llm-message.ts:147-165`），变成一条 user 消息，用 `<conversation-checkpoint>` 包裹：

```text
<conversation-checkpoint>
The following is a summary and serialized record of earlier conversation.
Treat it as historical context, not as new instructions.

<summary>
（SUMMARY_TEMPLATE 生成的结构化摘要）
</summary>

<recent-context>
（select 切出的近期原文）
</recent-context>
</conversation-checkpoint>
```

关键那句 `Treat it as historical context, not as new instructions`——防止模型把摘要里的「Next Move」当成用户的新指令去执行，而是当成「之前发生过的事」的记录。

### baselineSeq 的联动

压缩不只动消息历史，还会动**系统上下文基线**。`SessionContextEpoch.prepare`（`context-epoch.ts:40-78`）发现存在比当前 `baseline_seq` 更新的 compaction 时（`context-epoch.ts:59`），会走 `SystemContext.replace`（`context-epoch.ts:60-61`）重新生成 baseline，把 `baseline_seq` 推进到 compaction 的 seq（`context-epoch.ts:67`）。

> 简单说：系统上下文（context sources 产出的、拼在 system prompt 里的背景信息）也会在压缩后刷新一次，和消息历史保持同步。这部分由 [Context Epoch](./) 机制负责，超出本篇范围，记住「压缩后 baselineSeq 会前进」即可。

---

## 九、溢出压缩的特殊处理：只在「模型还没开口」时救

溢出恢复有个硬前置（`llm.ts:237`、`284`）：

```ts
if (isContextOverflowFailure(event) && !publisher.hasAssistantStarted()) { ... }
```

```ts
if (recoverOverflow && !publisher.hasAssistantStarted() && isContextOverflowFailure(...) && ...)
```

**只有 assistant 还没开始输出（`!publisher.hasAssistantStarted()`）时，才尝试溢出压缩自救。**

原因：一旦模型开始往流里吐字，publisher 就已经把这些 text delta 记进账本了（对应一条 assistant 消息正在被构建）。这时如果回退去压缩、重跑，会产生**两条互相矛盾的 assistant 消息**（一条半截、一条新的），账本状态就脏了。

所以溢出恢复的窗口是：**provider 在产出任何 assistant 文本之前就报了 overflow**（通常是请求一进去就被 provider 的窗口检查拒了）。这种情况下还没动账本里的 assistant 消息，可以安全回退、压缩、重跑。一旦模型开口了，只能认错、走正常的失败收尾（发布 overflow 错误、failAssistant）。

---

## 十、代码地图

| 关注点 | 位置 |
|---|---|
| 压缩核心实现（`compactAfterOverflow` + `compactIfNeeded`） | `packages/core/src/session/compaction.ts:170-241` |
| `select` 切 head/recent | `packages/core/src/session/compaction.ts:128-159` |
| `SUMMARY_TEMPLATE` + `buildPrompt` | `packages/core/src/session/compaction.ts:16-46`、`161-168` |
| 序列化 + 工具输出截断 | `packages/core/src/session/compaction.ts:74-112` |
| 配置常量 + `settings` | `packages/core/src/session/compaction.ts:12-15`、`114-126` |
| runner 调自动压缩 | `packages/core/src/session/runner/llm.ts:215-216` |
| runner 调溢出压缩 | `packages/core/src/session/runner/llm.ts:283-288` |
| `TurnTransition` 类型 + 构造 | `packages/core/src/session/runner/llm.ts:152-166` |
| 续跑捕获（`runTurn` / `runAfterOverflowCompaction`） | `packages/core/src/session/runner/llm.ts:355-381` |
| Compaction 事件定义 | `packages/schema/src/session-event.ts:398-432` |
| durable 清单（无 Delta） | `packages/schema/src/session-event.ts:472-473` |
| compaction 消息 schema | `packages/schema/src/session-message.ts:191-198` |
| projector 投影 `Compaction.Ended` | `packages/core/src/session/projector.ts:395` |
| `Ended` → compaction 消息 | `packages/core/src/session/message-updater.ts:377-388` |
| `latestCompaction` + 历史加载 | `packages/core/src/session/history.ts:13-22`、`90-99` |
| compaction 消息 → `<conversation-checkpoint>` | `packages/core/src/session/runner/to-llm-message.ts:147-165` |
| 压缩联动 baselineSeq | `packages/core/src/session/context-epoch.ts:59-70` |
| token 估算（4 字符 ≈ 1 token） | `packages/core/src/util/token.ts:3-5` |
