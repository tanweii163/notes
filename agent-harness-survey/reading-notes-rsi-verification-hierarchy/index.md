# 阅读笔记：Recursive Self-Improvement in AI — From Bounded Self-Refinement to Autonomous Research Loops

> **论文**：Recursive Self-Improvement in AI: From Bounded Self-Refinement to Autonomous Research Loops
> **arXiv**：[2607.07663](https://arxiv.org/abs/2607.07663)（2026-07-08 v1，2026-09-06 v2，本笔记基于 v2 TeX 源码通读）
> **作者**：Mingguang Chen（DeepGrounding，通讯）、Licheng Wang（AlphaAvatar）、Bo Qu（Illinois Institute of Technology）
> **PDF**：[arxiv.org/pdf/2607.07663](https://arxiv.org/pdf/2607.07663)
> **配套资源**：https://github.com/deepgrounding/recursive-self-improvement（1250 篇语料 + 分类脚本 + 图表源码，可复现）
> **配图**：内嵌 9 幅自绘 SVG 示意图（图 1–9，1080 宽统一画布），对应原文 Figure 1–6 的重绘与扩展
> **性质**：44 页、6 图的大型综述，语料为 **1,250 篇 arXiv 论文（2024–2026）**，74% 发表于 2026 年
> **动机框架**：Anthropic 2026 年 RSI essay（五阶段自主性谱系、"closing the loop"）——作者明确声明只借它的阶段词汇，不作为证据

---

**目录**：0 一页总览（图 1） · 1 为什么需要这篇综述 · 2 两轴分类法（图 2、图 3） · 3 部署时自进化（图 4） · 4 训练时自迭代（图 5） · 5 自评估与验证层级（图 6–9，全文核心） · 6 Auto Research（含 A-Evolve-Training 案例） · 7 理论极限与安全 · 8 横切观察与六大开放问题 · 9 与本系列笔记的关联 · 10 个人点评

**阅读路线**：只关心核心论点 → 读 0、5；关心 harness/agent 工程 → 读 3（尤其 3.4/3.5）+ 图 6 底部"给 harness 工程师的用法"；关心 AI 自动化研究 → 读 6；关心安全/治理 → 读 7；赶时间 → 只看图 1 + "十条带得走的结论"。

---

## 0. 一页总览

这篇综述要解决的问题：**"self-X" 词汇（self-refine / self-reward / self-play / self-evolve / self-verify）把野心完全不同的东西混为一谈**。一个模型重读草稿改错字，和一个 agent 重写自己的代码库，都叫"自我改进"——但二者的证据基础、理论、风险画像完全不同。全文的论证链条如下：

<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1080 455" font-family="PingFang SC, Microsoft YaHei, sans-serif">
  <defs>
    <marker id="mk1" markerWidth="10" markerHeight="8" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#64748b"/></marker>
  </defs>
  <rect x="20" y="40" width="300" height="98" rx="10" fill="#fef2f2" stroke="#dc2626" stroke-width="2"/>
  <text x="170" y="66" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#b91c1c">① 问题 · 词汇混淆</text>
  <text x="170" y="88" text-anchor="middle" font-size="11.5" fill="#475569">self-refine / self-reward / self-play /</text>
  <text x="170" y="107" text-anchor="middle" font-size="11.5" fill="#475569">self-evolve —— 同一前缀混淆了</text>
  <text x="170" y="126" text-anchor="middle" font-size="11.5" fill="#475569">野心与风险画像完全不同的东西</text>
  <line x1="320" y1="89" x2="384" y2="89" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk1)"/>
  <rect x="390" y="40" width="300" height="98" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="2"/>
  <text x="540" y="66" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#1d4ed8">② 工具 · 两轴分类法</text>
  <text x="540" y="88" text-anchor="middle" font-size="11.5" fill="#475569">轴1 改进什么：部署行为 / 训练策略 /</text>
  <text x="540" y="107" text-anchor="middle" font-size="11.5" fill="#475569">评估器 / 研究过程本身</text>
  <text x="540" y="126" text-anchor="middle" font-size="11.5" fill="#475569">轴2 谁验证：human-in / on / 闭环</text>
  <line x1="690" y1="89" x2="754" y2="89" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk1)"/>
  <rect x="760" y="40" width="300" height="98" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
  <text x="910" y="66" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#15803d">③ 中心切割</text>
  <text x="910" y="88" text-anchor="middle" font-size="11.5" fill="#475569">有界自我精炼：收敛 · 可评估 · 已工业实践</text>
  <text x="910" y="107" text-anchor="middle" font-size="11.5" fill="#475569">开放式 RSI：改标准与机器本身 · 原则发散</text>
  <text x="910" y="126" text-anchor="middle" font-size="11.5" fill="#475569">→ 受 grounding / 坍缩 / 算力三重约束</text>
  <line x1="910" y1="138" x2="910" y2="176" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk1)"/>
  <rect x="760" y="182" width="300" height="98" rx="10" fill="#faf5ff" stroke="#a21caf" stroke-width="2"/>
  <text x="910" y="208" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#7e22ce">④ 承重柱 · 自评估</text>
  <text x="910" y="230" text-anchor="middle" font-size="11.5" fill="#475569">每个改进循环都是一个</text>
  <text x="910" y="249" text-anchor="middle" font-size="11.5" fill="#475569">「某种信号可替代人类判断」的主张</text>
  <text x="910" y="268" text-anchor="middle" font-size="11.5" fill="#475569">循环的天花板 ＝ 替代品的质量</text>
  <line x1="760" y1="231" x2="696" y2="231" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk1)"/>
  <rect x="390" y="182" width="300" height="98" rx="10" fill="#fffbeb" stroke="#d97706" stroke-width="2"/>
  <text x="540" y="208" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#a16207">⑤ 仪器 · 验证层级</text>
  <text x="540" y="230" text-anchor="middle" font-size="11.5" fill="#475569">L1 形式验证器 → L2 执行反馈</text>
  <text x="540" y="249" text-anchor="middle" font-size="11.5" fill="#475569">→ L3 学习型裁判 → L4 内在信号</text>
  <text x="540" y="268" text-anchor="middle" font-size="11.5" fill="#475569">可靠性递减 · 覆盖递增 · 失败模式下沉</text>
  <line x1="390" y1="231" x2="326" y2="231" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk1)"/>
  <rect x="20" y="182" width="300" height="98" rx="10" fill="#fef2f2" stroke="#dc2626" stroke-width="2"/>
  <text x="170" y="208" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#b91c1c">⑥ 规律</text>
  <text x="170" y="230" text-anchor="middle" font-size="11.5" fill="#475569">已证明的自我改进强度跟随层级</text>
  <text x="170" y="249" text-anchor="middle" font-size="11.5" fill="#475569">失败模式 ＝ 层级被违反的后果</text>
  <text x="170" y="268" text-anchor="middle" font-size="11.5" fill="#475569">方向生成 ＝ 层级先在的盲点（§5.4）</text>
  <line x1="170" y1="280" x2="170" y2="320" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk1)"/>
  <rect x="20" y="326" width="1040" height="112" rx="10" fill="#1e293b" stroke="#0f172a" stroke-width="2"/>
  <text x="540" y="354" text-anchor="middle" font-size="14" font-weight="bold" fill="#ffffff">⑦ 结论 · 把 takeoff 问题变成测量问题</text>
  <text x="540" y="378" text-anchor="middle" font-size="12" fill="#e2e8f0">别盯 benchmark 分数，盯验证层级上的移动 —— 尤其：系统能否成为开放式研究判断的可靠评估器</text>
  <text x="540" y="400" text-anchor="middle" font-size="12" fill="#e2e8f0">在那之前，人类角色不是多愁善感的残留，而是这个领域最后的验证层（verification layer of last resort）</text>
  <text x="540" y="422" text-anchor="middle" font-size="12" fill="#e2e8f0">谨慎且可测量地建造它的替代品 —— 这十年 AI 安全可能最依赖的研究计划</text>
</svg>

<sub><em>图 1 · 全文论证链：词汇混淆 → 两轴分类法 → 中心切割 → 自评估承重柱 → 验证层级 → 规律 → 把 takeoff 问题变成测量问题</em></sub>

</div>

一句话浓缩全文论点：**Self-improvement is only as real as its verification.（自我改进的真实程度，恰好等于其验证的程度。）**

### 十条带得走的结论

1. **"自我改进"是两种东西**：有界自我精炼（对着固定外部评估器改进，收敛、可评估、已是工业实践）vs 开放式 RSI（连改进标准本身也改，原则上发散，被 grounding/坍缩/算力三重限界）——不同证据基础、不同理论、不同风险画像。
2. **每个改进循环都是一个"某种信号可替代人类判断"的主张**，循环的天花板恰好等于替代品的质量——这是把自评估提升为一级类别的理由。
3. **验证层级 L1→L4**（形式验证器 → 执行反馈 → 学习型裁判 → 内在信号）：已证明的自我改进强度跟随层级；改进的循环与打转的循环只差一级外部验证（Mirror Loop：无接地自批判信息量 -55%，一次最小验证干预即恢复）。
4. **No external signal, no reliable improvement**——2024 年负面结果（Huang et al.：无外部反馈 LLM 基本不能自我纠正推理）之后，整个领域收敛出的中心设计规则。
5. **四大失败模式**：自确认循环、模型坍缩、多样性坍缩（三者从循环内部留有签名）+ 框架锁定（内部不可检测——检测需要循环标准之外的立足点）。
6. **坍缩是默认动力学，不是边缘情况**：存活杠杆 = data gating + reward grounding；但"多少外部 grounding 就够"这个汇率无人测出（开放问题 1）。
7. **方向设定拆两半**：方向评估（验证形状，已可 benchmark，SoundnessBench）+ 方向生成（先于验证层级，无 benchmark，McNamara 谬误）——大多数讨论把二者混为一谈。
8. **自生成信号越特权，循环越高效地同时传递能力和偏见**（OPSD 的 style drift、多模态的语言先验捷径都是它的实例）。
9. **持久性改变风险演算**：输出错误会蒸发、坏权重可回滚、被污染的技能会在共享库中传播（永久编码、跨代自放大、种群可传播）；guardrail 在 agent 运行时内部就可被 agent 到达——执行时对齐必须活在 agent 地址空间之外。
10. **要盯的信号不是分数，是验证层级上的移动**；治理级测量（证明一个循环"没有"超标自我改进的可审计方法）是全领域最空缺的生态位（基础/安全类仅 60/1250 篇）。

---

## 1. 为什么需要这篇综述

- RSI 是 AI 领域最古老的想法之一（Good 1966 智能爆炸、Schmidhuber 的 Gödel Machine），但**循环的碎片如今已是工程实践**：LLM 如今例行地批判并修订自己的输出、在自己生成的数据上训练、重写自己的 agent 脚手架，FunSearch/AlphaEvolve 发现的算法已经反哺 AI 开发基础设施本身。
- Anthropic essay 的定位：当前系统在**执行**上已走得很远（2026 年 5 月，Claude 写了 Anthropic 合并代码的 80%+），瓶颈在**研究方向设定**（选择哪些问题重要）。这个缺口是否/何时/如何关闭，"可以说是本领域最重大的开放问题"。
- 领域**加速快于整合**：种子语料的季度产出从 2024 年初的个位数涨到 2026 Q2 的约 500 篇；既有综述只覆盖单一纵切面（on-policy distillation、tree-search+reward），没有综述横跨"从有界自精炼到开放式 RSI"的全谱系。整合并锚定到显式自主性连续谱，是本文的主要贡献。
- **语料方法**（两阶段）：871 篇种子（七条线索系统检索：自我精炼、自奖励训练、自动化 AI 研究、自修改 agent、LLM 代码/算法发现、RSI 理论与安全、自生成数据循环；OpenAlex 富化引文与 venue 元数据）+ 379 篇定向补充（自评估、TTT、零数据 self-play 三个被种子检索低估但分类法列为一级方向）。规则分类改派了 89 篇，写作期人工修正 3 篇。
- **作者自陈的局限**（难得的坦诚，读所有数字时带着这些前提）：语料是**样本不是普查**（每查询深度上限偏向近期高产量线索）；补充采集的 recency 偏差是构造性的（增长统计只用种子语料）；74% 论文发于 2026 → 引用数近零，**不可读作影响力**；单人标注（发布 per-paper 赋值以便审计分歧而非隐藏）；约 54/379 篇补充论文是外围渗漏（计入计数但不作证据引用）；前沿实验室的工业 RSI 实践存在**发表审查效应**——最先进的部分恰恰只能看到实验室愿意发表的切片。
- 阅读策略因此是：论证骨架靠**已验证的锚点工作**（STaR、SPIN、FunSearch、AI Scientist 等窗口前开创工作）+ 诊断/批判文献；2026 年的论文海量用作**活动地图**而非持久影响的证据。

**Table 1 · 语料分布**：

| 类别 | 子线索 | 篇数 | 2026 年占比 |
|---|---|---|---|
| 部署时自进化（§3） | 输出精炼 · TTT · harness/技能进化 | 393 | 74% |
| 训练时自迭代（§4） | 自奖励 RL · CoT 自训练 · 自蒸馏 · self-play · 具身 | 340 | 69% |
| 自评估（§5） | 裁判 · PRM · 验证器 · rubric · 元评估 | 318 | **82%** |
| Auto Research（§6） | AI 科学家 · 进化式程序发现 | 139 | 76% |
| 基础/极限/安全（§7） | 理论 · 极限 · 安全 | 60 | 57% |

两个数字先记住：**自评估是整合最快的类别**（82% 在 2026——直到最近它还只是训练论文里的服务功能，现在已是自有方法/benchmark/失败分析的研究领域）；**基础/安全只有 60/1250**——与 §7 声称的风险量级严重不成比例，作者点名的"最空缺生态位"。

## 2. 两轴分类法

**轴 1 —— 系统改进什么**（四列）；**轴 2 —— 谁验证改进**（三行：human-in-the-loop 人审每次改动 / human-on-the-loop 信号自动生成、人审计结果并把关部署 / closed loop 系统自产自验自用，即 Anthropic 的 "closing the loop"）。1250 篇语料填进 4×3 网格：

<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1080 462" font-family="PingFang SC, Microsoft YaHei, sans-serif">
  <defs>
    <marker id="mk2" markerWidth="9" markerHeight="7" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/></marker>
  </defs>
  <text x="540" y="24" text-anchor="middle" font-size="15" font-weight="bold" fill="#0f172a">两轴分类法：4 类改进对象 × 3 种循环闭合度（格内为语料中的代表系统）</text>
  <rect x="150" y="40" width="222" height="44" rx="6" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
  <text x="261" y="58" text-anchor="middle" font-size="12" font-weight="bold" fill="#1d4ed8">部署时自进化 §3</text>
  <text x="261" y="75" text-anchor="middle" font-size="10.5" fill="#64748b">393 篇 · 74% 在 2026</text>
  <rect x="376" y="40" width="222" height="44" rx="6" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="487" y="58" text-anchor="middle" font-size="12" font-weight="bold" fill="#15803d">训练时自迭代 §4</text>
  <text x="487" y="75" text-anchor="middle" font-size="10.5" fill="#64748b">340 篇 · 69% 在 2026</text>
  <rect x="602" y="40" width="222" height="44" rx="6" fill="#faf5ff" stroke="#a21caf" stroke-width="1.5"/>
  <text x="713" y="58" text-anchor="middle" font-size="12" font-weight="bold" fill="#7e22ce">自评估 §5</text>
  <text x="713" y="75" text-anchor="middle" font-size="10.5" fill="#64748b">318 篇 · 82% 在 2026（整合最快）</text>
  <rect x="828" y="40" width="222" height="44" rx="6" fill="#fff7ed" stroke="#ea580c" stroke-width="1.5"/>
  <text x="939" y="58" text-anchor="middle" font-size="12" font-weight="bold" fill="#c2410c">Auto Research §6</text>
  <text x="939" y="75" text-anchor="middle" font-size="10.5" fill="#64748b">139 篇 · 76% 在 2026</text>
  <rect x="16" y="90" width="126" height="60" rx="6" fill="#f8fafc" stroke="#94a3b8"/>
  <text x="79" y="112" text-anchor="middle" font-size="11" font-weight="bold" fill="#334155">Human-in-loop</text>
  <text x="79" y="130" text-anchor="middle" font-size="10.5" fill="#64748b">人审每次改动</text>
  <rect x="150" y="90" width="222" height="60" rx="6" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="160" y="112" font-size="10.5" fill="#475569">AI 辅助编码</text>
  <text x="160" y="130" font-size="10.5" fill="#475569">（人审每个 diff）</text>
  <rect x="376" y="90" width="222" height="60" rx="6" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="386" y="112" font-size="10.5" fill="#475569">人把关的训练 campaign</text>
  <text x="386" y="130" font-size="10.5" fill="#475569">（数据/配方/检查点人审）</text>
  <rect x="602" y="90" width="222" height="60" rx="6" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="612" y="112" font-size="10.5" fill="#475569">人写 rubric / 过程标注</text>
  <text x="612" y="130" font-size="10.5" fill="#475569">（Lightman 步级标注：人工昂贵）</text>
  <rect x="828" y="90" width="222" height="60" rx="6" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="838" y="112" font-size="10.5" fill="#475569">Co-scientist 工具</text>
  <text x="838" y="130" font-size="10.5" fill="#475569">（人定方向 · 机器执行）</text>
  <rect x="150" y="156" width="900" height="140" fill="#f0fdf4" opacity="0.45"/>
  <rect x="16" y="156" width="126" height="140" rx="6" fill="#f0fdf4" stroke="#16a34a"/>
  <text x="79" y="196" text-anchor="middle" font-size="11" font-weight="bold" fill="#15803d">Human-on-loop</text>
  <text x="79" y="214" text-anchor="middle" font-size="10.5" fill="#475569">信号自动</text>
  <text x="79" y="230" text-anchor="middle" font-size="10.5" fill="#475569">人审计结果</text>
  <text x="79" y="252" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#15803d">★ 语料主体</text>
  <rect x="150" y="156" width="222" height="140" rx="6" fill="#ffffff" stroke="#16a34a"/>
  <text x="160" y="176" font-size="10.5" fill="#334155">Self-Refine / Reflexion</text>
  <text x="160" y="195" font-size="10.5" fill="#334155">代码自修复（执行反馈）</text>
  <text x="160" y="214" font-size="10.5" fill="#334155">TTT：部署中更新权重</text>
  <text x="160" y="233" font-size="10.5" fill="#334155">Gödel Agent / DGM（沙箱）</text>
  <text x="160" y="252" font-size="10.5" fill="#334155">技能库：人写 +16.2 分 vs 机写 +0</text>
  <text x="160" y="271" font-size="10.5" fill="#334155">loop engineering：工程对象＝循环</text>
  <rect x="376" y="156" width="222" height="140" rx="6" fill="#ffffff" stroke="#16a34a"/>
  <text x="386" y="176" font-size="10.5" fill="#334155">STaR：答案正确性过滤 rationale</text>
  <text x="386" y="195" font-size="10.5" fill="#334155">Self-Rewarding LMs：奖励同改</text>
  <text x="386" y="214" font-size="10.5" fill="#334155">ReST-MCTS*：树搜索过程奖励</text>
  <text x="386" y="233" font-size="10.5" fill="#334155">OPSD：特权教师（同权重+提示）</text>
  <text x="386" y="252" font-size="10.5" fill="#334155">Absolute Zero / R-Zero：自己出题</text>
  <text x="386" y="271" font-size="10.5" fill="#b91c1c">⚠ rise-and-collapse：同 run 升后崩</text>
  <rect x="602" y="156" width="222" height="140" rx="6" fill="#ffffff" stroke="#16a34a"/>
  <text x="612" y="176" font-size="10.5" fill="#334155">LLM-as-judge：~80% 一致+三偏见</text>
  <text x="612" y="195" font-size="10.5" fill="#334155">PRM：过程监督胜结果监督</text>
  <text x="612" y="214" font-size="10.5" fill="#334155">Goodhart：代理过优，峰后落</text>
  <text x="612" y="233" font-size="10.5" fill="#334155">BinEval：整体分→原子二元问题</text>
  <text x="612" y="252" font-size="10.5" fill="#334155">元评估：评估「评估」</text>
  <text x="612" y="271" font-size="10.5" fill="#334155">rubric ＝ 一级可进化工件</text>
  <rect x="828" y="156" width="222" height="140" rx="6" fill="#ffffff" stroke="#16a34a"/>
  <text x="838" y="176" font-size="10.5" fill="#334155">FunSearch：cap set 新构造(Nature)</text>
  <text x="838" y="195" font-size="10.5" fill="#334155">AlphaEvolve：反哺 Google 基建</text>
  <text x="838" y="214" font-size="10.5" fill="#334155">AI Scientist：~$15/篇 全管线</text>
  <text x="838" y="233" font-size="10.5" fill="#334155">ScienceAgentBench：仅解少数任务</text>
  <text x="838" y="252" font-size="10.5" fill="#334155">ResearchArena：工件评审戳破乐观</text>
  <text x="838" y="271" font-size="10.5" fill="#334155">（人把关「论文好不好」）</text>
  <rect x="16" y="302" width="126" height="110" rx="6" fill="#fef2f2" stroke="#dc2626"/>
  <text x="79" y="336" text-anchor="middle" font-size="11" font-weight="bold" fill="#b91c1c">Closed loop</text>
  <text x="79" y="354" text-anchor="middle" font-size="10.5" fill="#475569">自产 · 自验 · 自用</text>
  <text x="79" y="376" text-anchor="middle" font-size="10.5" fill="#b91c1c">处处稀疏</text>
  <text x="79" y="392" text-anchor="middle" font-size="10.5" fill="#b91c1c">右端最薄</text>
  <rect x="150" y="302" width="222" height="110" rx="6" fill="#ffffff" stroke="#fca5a5"/>
  <text x="160" y="324" font-size="10.5" fill="#334155">自进化 rubric/验证器</text>
  <text x="160" y="343" font-size="10.5" fill="#334155">（deep-research agent）</text>
  <text x="160" y="362" font-size="10.5" fill="#334155">Red Queen：agent 与评估器共进化</text>
  <text x="160" y="381" font-size="10.5" fill="#334155">Escher-Loop：优化器连自己也精炼</text>
  <rect x="376" y="302" width="222" height="110" rx="6" fill="#ffffff" stroke="#fca5a5"/>
  <text x="386" y="324" font-size="10.5" fill="#334155">零数据 self-play（无人类任务）</text>
  <text x="386" y="343" font-size="10.5" fill="#334155">存活杠杆：data gating +</text>
  <text x="386" y="362" font-size="10.5" fill="#334155">reward grounding</text>
  <text x="386" y="381" font-size="10.5" fill="#b91c1c">坍缩＝默认结局，非偶发事故</text>
  <rect x="602" y="302" width="222" height="110" rx="6" fill="#fef2f2" stroke="#dc2626" stroke-width="2.5"/>
  <text x="612" y="322" font-size="10.5" font-weight="bold" fill="#b91c1c">★ 最要害格子 ＝ RSI 入口</text>
  <text x="612" y="341" font-size="10.5" fill="#334155">Self-Trained Verification：</text>
  <text x="612" y="360" font-size="10.5" fill="#334155">自训练验证器本身 · 共进化裁判</text>
  <text x="612" y="379" font-size="10.5" fill="#334155">系统重写自己对「更好」的定义</text>
  <text x="612" y="398" font-size="10.5" fill="#7f1d1d">？逃出自我确认，还是给它加二楼</text>
  <rect x="828" y="302" width="222" height="110" rx="6" fill="#ffffff" stroke="#fca5a5"/>
  <text x="838" y="324" font-size="10.5" fill="#334155">A-Evolve-Training：</text>
  <text x="838" y="343" font-size="10.5" fill="#334155">30B 自主后训练 · 4 轮 · 数周</text>
  <text x="838" y="362" font-size="10.5" fill="#334155">0.86 vs 人类最佳 0.87（8/4000 队）</text>
  <text x="838" y="381" font-size="10.5" fill="#334155">检测到自身指标腐败 → 反转其用法</text>
  <text x="838" y="400" font-size="10.5" fill="#c2410c">＝最接近 closing the loop 的已发表工件</text>
  <text x="540" y="436" text-anchor="middle" font-size="11.5" fill="#64748b">网格的两个结构性事实：① 密度集中在中间行——几乎所有被综述的工作都是 human-on-the-loop（信号自动生成、人审计结果）；</text>
  <text x="540" y="454" text-anchor="middle" font-size="11.5" fill="#64748b">② 闭环行处处稀疏、右端最薄，其最要害的格子是「自评估 × 闭环」——那正是有界自我精炼过渡到开放式 RSI 的位置。</text>
</svg>

<sub><em>图 2 · 两轴分类法 4×3 网格（重绘原文 Figure 1）：绿带＝语料主体所在的 human-on-the-loop 行；红框＝自评估×闭环，RSI 入口</em></sub>

</div>

### 2.1 关键定义（§2.1，本文的术语卫生）

| 术语 | 本文定义 | 值得注意的点 |
|---|---|---|
| **Agent** | 通过感知-行动循环追求目标的 LLM 系统：观察状态 → 选择行动 → 迭代至停止条件 | 裸模型调用一次不是 agent；同一模型进了带工具和记忆的循环才是 |
| **Harness（脚手架）** | 模型周围把模型变成 agent 的一切：system prompt、工具定义、记忆存储、技能库、检索索引、编排代码、停止规则 | **外部可检查、可编辑——包括被 agent 自己编辑**，这正是 harness 自修改成为"agent 重写自己"最具体形式的原因 |
| **Evaluator** | 把候选工件映射到质量信号的任何机制：证明检查器、测试套件、RM/PRM、LLM 裁判、rubric、人类评分者 | verifier 专指有 soundness 保证的评估器；judge 指没有保证的学习/提示型评估器 |
| **Self-improvement** | 系统参与产生"更好的自己或自己的输出"，其中"更好"由某个评估器定义 | **对评估器的定义依赖不是迂腐——它是 §5 每个失败模式的来源** |
| **TTT** | 部署期间按当前 query/session 更新权重，无离线训练阶段 | 区别于推理时精炼（权重冻结）与训练时迭代（离线阶段） |
| **有界自我精炼 vs 开放式 RSI** | 前者对固定外部评估器改进（收敛、可评估）；后者连改进的标准与机器本身也改（无固定锚点、原则发散） | **全文的中心切割** |

### 2.2 分类法明确"不编码"什么（作者自觉，罕见）

两个刻意的排除，因为它们界定了这种形状的分类能看见什么：
1. **两轴都把目标当作给定**：轴 1 问改进落在哪个基底，轴 2 问谁对着*现行标准*验证——都不索引"这个标准是否还是对的标准"（→ 失败模式 4、§5.4、开放问题 6）。
2. **按基底而非轨迹索引**：一个系统先改进输出、再改进评估器、再改进自己的研究方法，占了三个格子，但"这是同一个连续发展系统的三个片段"这一事实**无处记录**。语料里有这个缺失的负像——"scientific amnesia"（行为跨 campaign 改进而方法论知识不累积）——但正像（跨框架变化的方法连续性）网格登记不了。作者把它留作开放问题而非硬造第三轴，"因为语料里没有任何测量能填充它"。

### 2.3 在 Anthropic 自主性谱系上的定位

<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1080 340" font-family="PingFang SC, Microsoft YaHei, sans-serif">
  <defs>
    <marker id="mk3" markerWidth="10" markerHeight="8" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#64748b"/></marker>
    <marker id="mk3b" markerWidth="10" markerHeight="8" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#dc2626"/></marker>
  </defs>
  <text x="540" y="24" text-anchor="middle" font-size="15" font-weight="bold" fill="#0f172a">Anthropic 五阶段自主性谱系与 1250 篇语料的位置（essay 只作框架，不作证据）</text>
  <rect x="20" y="48" width="185" height="88" rx="10" fill="#f1f5f9" stroke="#64748b" stroke-width="1.5"/>
  <text x="112" y="72" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">阶段 1 · 2023 前</text>
  <text x="112" y="94" text-anchor="middle" font-size="11" fill="#475569">人类写全部代码</text>
  <rect x="230" y="48" width="185" height="88" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
  <text x="322" y="72" text-anchor="middle" font-size="12" font-weight="bold" fill="#1d4ed8">阶段 2</text>
  <text x="322" y="94" text-anchor="middle" font-size="11" fill="#475569">chatbot 辅助编码</text>
  <rect x="440" y="48" width="185" height="88" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="532" y="72" text-anchor="middle" font-size="12" font-weight="bold" fill="#15803d">阶段 3</text>
  <text x="532" y="94" text-anchor="middle" font-size="11" fill="#475569">自主编码 agent</text>
  <rect x="650" y="48" width="185" height="88" rx="10" fill="#fff7ed" stroke="#ea580c" stroke-width="2.5"/>
  <text x="742" y="70" text-anchor="middle" font-size="12" font-weight="bold" fill="#c2410c">阶段 4 · 今日前沿</text>
  <text x="742" y="90" text-anchor="middle" font-size="11" fill="#475569">agent 委托 agent</text>
  <text x="742" y="108" text-anchor="middle" font-size="10" fill="#64748b">Claude 写 80%+ 合并代码</text>
  <text x="742" y="124" text-anchor="middle" font-size="10" fill="#64748b">（Anthropic，2026.5）</text>
  <rect x="860" y="48" width="185" height="88" rx="10" fill="#faf5ff" stroke="#a21caf" stroke-width="2" stroke-dasharray="6 4"/>
  <text x="952" y="70" text-anchor="middle" font-size="12" font-weight="bold" fill="#7e22ce">阶段 5 · closing the loop</text>
  <text x="952" y="90" text-anchor="middle" font-size="11" fill="#475569">agent 设计并训练</text>
  <text x="952" y="108" text-anchor="middle" font-size="11" fill="#475569">自己的继任模型</text>
  <line x1="205" y1="92" x2="227" y2="92" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk3)"/>
  <line x1="415" y1="92" x2="437" y2="92" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk3)"/>
  <line x1="625" y1="92" x2="647" y2="92" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk3)"/>
  <line x1="835" y1="92" x2="857" y2="92" stroke="#64748b" stroke-width="2.5" stroke-dasharray="5 3" marker-end="url(#mk3)"/>
  <path d="M 440 152 L 440 160 L 835 160 L 835 152" fill="none" stroke="#16a34a" stroke-width="2"/>
  <text x="637" y="180" text-anchor="middle" font-size="12" font-weight="bold" fill="#15803d">技术文献主体：阶段 3–4（§§3–5，human-on-the-loop）</text>
  <path d="M 700 200 L 700 208 L 1045 208 L 1045 200" fill="none" stroke="#a21caf" stroke-width="2" stroke-dasharray="5 3"/>
  <text x="872" y="228" text-anchor="middle" font-size="12" fill="#7e22ce">§6 探测阶段 5 边界 · 最接近的已发表工件：A-Evolve-Training</text>
  <rect x="90" y="250" width="400" height="72" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
  <text x="290" y="278" text-anchor="middle" font-size="13" font-weight="bold" fill="#15803d">执行 —— 大体解决</text>
  <text x="290" y="300" text-anchor="middle" font-size="11" fill="#475569">代码机器写 · 实验机器跑 · benchmark 机器出</text>
  <rect x="590" y="250" width="400" height="72" rx="10" fill="#fef2f2" stroke="#dc2626" stroke-width="2"/>
  <text x="790" y="278" text-anchor="middle" font-size="13" font-weight="bold" fill="#b91c1c">研究方向设定 —— 仍是瓶颈</text>
  <text x="790" y="300" text-anchor="middle" font-size="11" fill="#475569">选择哪些问题重要 → 人类留在环中（§5.4 拆解它）</text>
  <line x1="490" y1="286" x2="588" y2="286" stroke="#dc2626" stroke-width="2.5" marker-end="url(#mk3b)"/>
  <text x="539" y="266" text-anchor="middle" font-size="10.5" fill="#b91c1c">缺口是否/何时/</text>
  <text x="539" y="278" text-anchor="middle" font-size="10.5" fill="#b91c1c">如何关闭＝最重大</text>
  <text x="539" y="308" text-anchor="middle" font-size="10.5" fill="#b91c1c">开放问题</text>
</svg>

<sub><em>图 3 · Anthropic 五阶段自主性谱系：语料主体停在阶段 3–4；执行与方向设定的不对称是当前全部张力的来源</em></sub>

</div>

**分类法由此做双份工作**：它组织综述（§§3–6 跟着它的列走），又让综述的中心主张可见——**文献的质量坐在"人仍审计循环"的地方，而承重的那一列是评估器的**。

### 2.4 四大类别速查表

| 类别 | 改进对象 | 持久性 | 代表工作 | 天花板由什么设定 | 篇数 |
|---|---|---|---|---|---|
| 部署时自进化 §3 | 输出 / 会话级权重 / harness | 情景蒸发 → session → 无限累积 | Self-Refine、Reflexion、TTT、DGM、Voyager 技能库 | **反馈信道的保真度与分辨率** | 393 |
| 训练时自迭代 §4 | 权重（离线训练阶段） | 跨迭代复利 | STaR、Self-Rewarding LMs、OPSD、Absolute Zero | **自生成信号的质量**（层级位置） | 340 |
| 自评估 §5 | "更好"的定义本身 | 元层面：监督其他三列 | LLM-judge、PRM、rubric、元评估、共进化裁判 | **循环性**（验证验证器时谁验证它） | 318 |
| Auto Research §6 | 研究过程本身 | 跨系统复利（非单系统内） | FunSearch、AlphaEvolve、AI Scientist、A-Evolve | **评估器可信度决定一切**（有无程序级验证器分野） | 139 |
| 基础/极限/安全 §7 | ——（条件与界） | —— | Schaul、Zenil、Shumailov、unfireable kernel | 与声称的风险量级不成比例（60/1250） | 60 |

---

## 3. 部署时自进化（§3，393 篇，最大且部署最广）

统一逻辑：改进发生在**现场**（per episode / per user），无离线训练阶段；区分维度是**持久性**——这条轴同时决定了收益的半衰期和风险的严重度：

<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1080 385" font-family="PingFang SC, Microsoft YaHei, sans-serif">
  <defs>
    <marker id="mk4" markerWidth="10" markerHeight="8" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#64748b"/></marker>
  </defs>
  <text x="540" y="24" text-anchor="middle" font-size="15" font-weight="bold" fill="#0f172a">部署时自进化：按持久性排序（重绘原文 Figure 3）</text>
  <text x="540" y="50" text-anchor="middle" font-size="11.5" fill="#64748b">持久性与生命周期 →</text>
  <line x1="40" y1="66" x2="1035" y2="66" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk4)"/>
  <rect x="55" y="86" width="300" height="150" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="2"/>
  <text x="205" y="112" text-anchor="middle" font-size="13" font-weight="bold" fill="#1d4ed8">① 输出精炼 §3.1–3.3</text>
  <text x="205" y="136" text-anchor="middle" font-size="11.5" fill="#475569">权重冻结 · 生成→批判→修订</text>
  <text x="205" y="156" text-anchor="middle" font-size="11.5" fill="#475569">寿命：随情景蒸发</text>
  <text x="205" y="176" text-anchor="middle" font-size="11.5" fill="#475569">风险：错误也随情景蒸发</text>
  <text x="205" y="196" text-anchor="middle" font-size="11.5" fill="#475569">教训：无外部反馈基本不能自纠</text>
  <text x="205" y="216" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#1d4ed8">规则：no external signal,</text>
  <text x="205" y="232" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#1d4ed8">no reliable improvement</text>
  <rect x="390" y="86" width="300" height="150" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
  <text x="540" y="112" text-anchor="middle" font-size="13" font-weight="bold" fill="#15803d">② 测试时训练 TTT §3.4</text>
  <text x="540" y="136" text-anchor="middle" font-size="11.5" fill="#475569">部署中按 query/session 更新权重</text>
  <text x="540" y="156" text-anchor="middle" font-size="11.5" fill="#475569">寿命：一个会话</text>
  <text x="540" y="176" text-anchor="middle" font-size="11.5" fill="#475569">风险：坏更新可回滚</text>
  <text x="540" y="196" text-anchor="middle" font-size="11.5" fill="#475569">87 篇且在快速增长（补充采集）</text>
  <text x="540" y="216" text-anchor="middle" font-size="11.5" fill="#475569">推理/训练二分法正在溶解为</text>
  <text x="540" y="232" text-anchor="middle" font-size="11.5" fill="#475569">「更新时标连续谱」的最清晰信号</text>
  <rect x="725" y="86" width="300" height="150" rx="10" fill="#fff7ed" stroke="#ea580c" stroke-width="2"/>
  <text x="875" y="112" text-anchor="middle" font-size="13" font-weight="bold" fill="#c2410c">③ Harness / 技能 / 记忆 §3.5–3.6</text>
  <text x="875" y="136" text-anchor="middle" font-size="11.5" fill="#475569">prompt · 工具 · 技能库 · 编排 · 源码</text>
  <text x="875" y="156" text-anchor="middle" font-size="11.5" fill="#475569">寿命：无限累积</text>
  <text x="875" y="176" text-anchor="middle" font-size="11.5" fill="#b91c1c">风险：被污染技能在共享库传播</text>
  <text x="875" y="196" text-anchor="middle" font-size="11.5" fill="#b91c1c">（永久编码 · 跨代自放大 · 种群可传播）</text>
  <text x="875" y="216" text-anchor="middle" font-size="11.5" fill="#475569">外部可检查/可编辑——包括被 agent</text>
  <text x="875" y="232" text-anchor="middle" font-size="11.5" fill="#475569">自己编辑＝「重写自己」最具体形式</text>
  <rect x="55" y="266" width="970" height="96" rx="10" fill="#f8fafc" stroke="#64748b" stroke-width="1.5"/>
  <text x="540" y="292" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">半衰期问题 → 两个出口：§4 把改进持久化进权重 · §3.5–3.6 把改进持久化进脚手架</text>
  <text x="540" y="316" text-anchor="middle" font-size="11.5" fill="#475569">风险演算定律：持久性越长 → 验证债务越重。accumulation-without-verification（无验证的累积）是核心安全问题</text>
  <text x="540" y="340" text-anchor="middle" font-size="11.5" fill="#b91c1c">清醒数字：推理扩展 Pareto 分析（34 配置）——峰值仅 +7.1 分，代价 ~20× 算力；大量收益来自更好的工程，而非任何「递归」的东西</text>
</svg>

<sub><em>图 4 · 持久性谱系：精炼输出蒸发 → TTT 持续一个会话 → harness 改动无限累积；持久性同时决定收益半衰期与风险严重度</em></sub>

</div>

### 3.1 文本/推理的自我批判与自我验证

- **结构化与符号反馈**取代自由格式自批判：SymbolicAI 把 LLM 当语义解析器嵌进逻辑框架、路由输出经过形式求解器；LLM 规划器耦合符号验证器（返回*可行动的错误轨迹*而非模糊批判）；模式泛化到一切有 checker 的地方——SQL 执行器、临床摘要幻觉检测器、长文摘要的 QA 事实性探针。**设计教训（几十篇论文反复出现）：refinement 循环的上限就是反馈信道的上限**——§5 验证瓶颈的第一次现身。
- **搜索化精炼**：把草稿当搜索树节点扩展打分而非当文本打磨（SQL-o1 的自奖励启发式搜索、LLM-Personalize 的强化自训练循环）。与 §4 的边界由此模糊——同一个打分信号既能推理时排序候选，也能事后微调策略，若干系统两者都做。
- **最有价值的是诊断性工作**：九模型×七语向的文学翻译系统研究发现 refinement 收益主要在流畅度/风格/术语，adequacy 改进有限且不一致，而且 refinement **把输出投影向精炼器自己的分布**而非纠正草稿实际错的地方——呼应 Huang et al. 2024 的著名负面结果（无外部反馈时 LLM 基本不能自我纠正推理，naive 自纠可能更糟）。**2026 年文献已把教训内化**：几乎所有新系统都把批判接地到外部信号（执行、检索、检测器、求解器），"内在自纠"论文变稀有——用分类法的话说，**领域悄悄从闭环自批判撤退到 human-on-the-loop 的验证式精炼：一次提高了可靠性的自主性撤退**。
- 负面结果正被精细化而非简单重复：① 机制敏感分析——重访*显式可检查约束*与重访开放式推理行为不同，前者才是无辅助自纠仍有价值之处；② 校准问题——序列似然何时是质量的可用代理，已有跨解码方法/模型/benchmark 的四级量化（等于从下方测绘 §5 层级的地板）；③ 评估侧重构——BinEval 把不透明整体裁判分解为原子二元问题，裁决聚合成可解释可调试的分数：**把自我改进用于裁判而非答案，这个倒置全篇反复出现**。

### 3.2 执行反馈驱动的代码自修复（最干净的实验室）

代码是外部信号最便宜最锐利的模态（程序能跑、测试能判），所以这个主题是 refinement 主张的最佳实验场。

- **正面结果强**：执行反馈修复循环支撑了 Blender 多智能体 3D 资产生成、从运行时反馈诊断瓶颈的数据库调优 agent、以 profiling 证据接地的编译器 pass 调优；形式化数学里围绕证明助手的 agent 框架（LEAP/Lean 定理证明、KVerus/Rust 可扩展验证、对着演化知识库的规格生成）**利用可得的最强验证器（证明检查器）驱动多轮修复，几乎没有接受错误"改进"的风险**；验证器引导解码把信号推进生成过程内部而非事后应用。
- **为什么反馈有用——因果分解**（本线索独有的贡献，其他部署类线索都缺）：受控 student-teacher 协议把真正的反馈价值从重采样、格式纠正、额外测试时算力中剥离（这三者会抬高 naive 对比）；placebo 对照研究给出波普尔式表述——**失败的测试是可执行的反例，反馈的价值应归因于证伪（falsification），而非对问题的 mere re-exposure**。互补结果：小模型代码生成中执行反馈比管线拓扑更重要；执行前结构检查比无结构批判更稳定地抓住主导失败模式（工具间契约违反）；多轮修复的系统评估确认真实价值集中在迭代循环（而多数评估仍只测单次尝试准确率）。
- **信号锐化两例**：**FLARE** 在生成与修订之间插入轻量诊断模型预测*行级可疑度*——测试失败太粗、自批判太空，都说不清该修哪里；**反馈分辨率（而不只是反馈存在性）是设计变量**。**CoSPlay** 面对连测试都是自生成的场景：模型写的单测有噪声且与错误代码*伪耦合*（spurious coupling），于是让代码种群与测试种群在测试时协作共进化、互相 debug——**验证瓶颈的缩影：验证器自生成时，验证验证器成为循环的一部分**，并预告 §5/§6 的评估器共进化思想。

### 3.3 视觉-语言与多模态自我批判

范式泛化良好但**验证信号随迁移变薄**：
- 幻觉抑制是主用例：Kestrel 用视觉证据接地自精炼（免训练）；Reflect-R1 指出参数内闭环自反思让长视频模型陷入"盲目自信"，用证据驱动的外部检索修复——**Huang 负面结果的多模态重述**。生成侧：统一 MLLM 通过细粒度推理自精炼自己的文生图输出；Proprio 给冻结视频生成器一个潜空间"本体感受"自评分信号提升物理合理性。
- 感知本身成为精炼对象：ActiveScope 诊断被动视觉注意的两个失败模式（上下文支配——显著干扰物淹没目标；语义偏见），让模型*主动寻找并纠正自己的感知*（重看区域而非重措辞答案）。安全进入表示层：迭代自改进的 codebook 从自回归图像生成器的 token 词汇表里清除不安全视觉模式——**改进对象是生成器自己的离散字母表**。
- **两条警戒线**：① 自进化 LMM 研究显示 self-play/自洽奖励会优化*答案一致性*而解码器对视觉内容欠注意、依赖语言先验（"visual under-conditioning"）——自确认循环的模态特化形态；② 最强的多模态系统越来越像代码模式：**靠引入外部信道成功（检索、检测器、物理残差、个人视觉上下文），而非信任模型自身判断**。裁判侧证据加深警戒：VLM 当物理合理性裁判时各自编码*不同的*内部物理现象分类法，单一全局评估 schema 会给每个裁判记上它实际感知不到的能力——JudgeFit 先发现 per-judge 分类法再信其分。**§3.2 的验证器是程序，§3.3 的验证器是模型——模型裁判继承模型的怪癖。**

**§3.1–3.3 评估**：推理时精炼是最纯粹形态的有界自我改进——改进真实、可测、随情景蒸发。"半衰期问题"（什么都不留存）同时驱动 §4（持久化进权重）与 §3.5–3.6（持久化进脚手架）。已验证的成功与有教益的失败共同确立领域中心设计规则：**no external signal, no reliable improvement**。

### 3.4 测试时训练（TTT）

- 冻结权重精炼与离线训练之间快速增长的中间地带：**部署期间**更新权重。query-conditioned 测试时自训练（构造 query 专属目标并在推理时微调，纠正冻结权重迭代够不着的误解）；持续学习变体（把推理时扩展产生又丢弃的推理轨迹转成持久轻量记忆）；固化方法（周期性"睡眠"阶段把 in-context 经验转移进长期参数）。
- 补充采集发现该线索 87 篇且增长快，多数是老的 test-time adaptation 在 LLM 语境下被重新发现。**TTT 刻意骑在分类法的 §3/§4 边界上：有训练的持久性 + 部署的 per-query 粒度**，其兴起是"领域继承的推理/训练二分法正在溶解为更新时标连续谱"的最清晰信号。

### 3.5 Harness 与 agent 自进化（与 harness 工程最相关的一节）

前面的机制改进模型*说什么*；这两节改进 agent *是什么*。对象是 harness 本身——prompt、工具、记忆、技能库、编排代码，极限情形是 agent 自己的源码。**因为 harness 改动持久且外部可检查，部署时改进由此从情景性变为累积性**。这是 Anthropic essay 定位的当今前沿（agent 委托 agent），也是通往 closing the loop 的匝道。

**概念两极**（其余工作都坐在两极之间，进化一个组件、冻结其余）：
- **Gödel Agent**（命名自 Schmidhuber 的可证最优自修改器）：自指框架，agent 读写*自己的运行时代码*，搜索**完整** agent 设计空间而非人类预定义子集；
- **Darwin Gödel Machine（DGM）**：把可证明受益放松为**经验受益**，维护开放式自修改档案、对着编码 benchmark 验证——经验验证循环之所以是 SOTA，正因为完全自指仍无法评估；
- 另一极的理论批评（Liu et al.）：真正的自改进 agent 需要**内在元认知学习**（评估并适应自己的学习过程的能力），现有方法把自改进*程序*硬编码、只让*对象*可变——**恰恰在最需要灵活的地方僵化**。

**实践中被进化的层级**（很有启发的清单）：

| 进化层级 | 做法 | 代表 |
|---|---|---|
| Prompt 级 | 自动 prompt 优化接地到环境反馈 | 环境反馈驱动的 prompt 进化 |
| **验证级（最新颖）** | 不后训练策略，而是迭代加强*评判输出的 rubric 和验证器*——改进信号本身的改进 | 自进化 deep-research agent |
| 评估器共进化 | 指出既有方法假设*平稳的*评估标准，让 agent 与评估器共进化，评估成为循环的一部分而非固定框架 | Red Queen Gödel Machine |
| 自指再上一层 | 优化器 agent 精炼任务 agent *和自己*，对着动态演化的 benchmark | Escher-Loop |
| 拓扑级 | 多智能体通信结构作为可检索、自改进的设计工件，worker 全部冻结 | QueenBee |
| 数据级 | 从 agent 自己的失败生成可验证合成轨迹（computer-use） | 闭环数据生成 |
| 基础设施级 | "经验图"持久化长程 agent 的 branch-execute-fail-repair 搜索结构，让经验可查询而非被丢弃 | experience graphs |

- **Loop engineering 文化转变**（macedo2026stop）：人类工程的工件现在是*循环*——**触发器、目标、验证、停止规则、记忆**——而非逐步 prompt。**人类努力从"做任务"迁移到"指定 agent 可以在什么条件下改进任务"：恰是分类法里的 human-on-the-loop 姿态。**（与本系列 [LoopsBench 阅读笔记](../reading-notes-loopsbench-loop-engineering/) 直接对话。）
- **能力测量开始**：**Meta-Agent Challenge**——给前沿模型沙箱环境+评估 API+时间预算，测它能否*自主开发一个 agent 系统*最大化目标指标：**第一个瞄准"agent 开发"而非"agent 执行"的 benchmark**，直指分类法第三、四列之间的边界。**SAGE**——比较算力匹配的孤立自改进 vs "社会化"进化（agent 观察同伴策略与结果），量化共享经验何时产生孤立自改进得不到的提升：种群级自我改进，配套种群级失败模式。
- **回报的清醒面**：推理扩展策略的系统 Pareto 分析（self-consistency / self-refinement / debate / mixture-of-agents 共 34 配置）——峰值增益仅 +7.1 分（over CoT），代价约 **20× 算力**；方法间效率差异剧烈（self-consistency 早饱和，多智能体增益持续）。实践教训：**算力感知的方法选择而非更多迭代驱动大部分现实收益**。

### 3.6 技能库与持久累积

- 源头是 Voyager 的不断增长可复用技能库。现代形态："技能" = 自然语言过程文档 + 可执行代码，运行时加载。**2026 年的中心经验事实：LLM 不擅长写技能**——SkillsBench 上人写技能提升 pass rate **16.2 分**，LLM 写的技能**无可测收益**。整个主题实质是缩小这个差距的研究纲领：

| 系统 | 思路 |
|---|---|
| SkillAxe | 评估引导的技能文档自精炼（把 LLM 写的技能改到能用） |
| Skill-R1 | 技能优化作为循环 RL 问题，与（可能闭源的）任务模型解耦 |
| SkillRevise | 冷启动：trace-conditioned 修订初始不完美技能 |
| AlgoSkill | 为算法设计调度人类式技能，而非依赖通用自精炼 |
| SkillMaster | 最远：训练 agent **自己**学会创建/精炼/选择技能——技能作为内化能力而非被调用资源 |
| 联邦技能 | 跨用户联邦化，不共享原始轨迹 |
| SkillSmith | 技能与其调用的工具层共进化 |
| Socratic | 从执行轨迹派生弱项定向的训练任务 |

- **SHARP 模式值得单独记住**：金融交易 agent 的自由格式自修改太危险，于是刻意把可进化工件约束为**人类可审计的 rubric 策略**——低信噪比环境下无界 prompt 进化无法区分系统性逻辑缺陷与市场方差，而结构化 rubric **可审计、可 diff、可回滚**。设计模式：**约束自修改面以保持可验证**——远超金融领域适用。
- **安全面是技术语料中最锐利的，且罕见地攻击文献与部署同时到达**：SkillMutator（技能的自然语言规格与可执行代码"讲不同故事"的跨模态攻击 benchmark）；SkillHarness（对抗环境中的持续技能学习）；VASO（**基础模型压低了*创建*技能的成本，但没压低*信任*的成本** → 物理 agent 的形式化可验证技能进化）；系统威胁分析识别的**全新风险类别：对抗影响被永久编码、跨代自放大、可在 agent 种群间传播，且无需攻击者持续在场**；"健康进化"研究发现**无任何攻击者时也会出现能力退化与安全漂移**，提出人类监督锚作为矫正。

**§3.5–3.6 评估**：harness/技能进化是有界自精炼开始过渡到开放式自修改的地方，两个头条事实方向相反——**实践中的自主性其实很克制**（自进化的几乎总是单个精心沙箱化的组件、对着固定 benchmark 验证），**但持久性根本改变了风险演算**：推理时错误会蒸发、坏权重更新可回滚、**共享联邦技能库里被污染的技能会传播**。安全文献正确地识别了核心问题：accumulation-without-verification——同一个验证瓶颈，现在带上了记忆。

---

## 4. 训练时自迭代（§4，340 篇，RSI 的技术心脏，最接近工业标准）

谱系：STaR（bootstrap rationale）→ ReST^EM（规模化自训练）→ SPIN（自博弈微调）→ **Self-Rewarding LMs**（生成回复的模型同时评判它们，策略*和奖励信号*一起跨迭代改进——**第一个被广泛注意的真正递归训练循环，也是其特征性失败模式的源头**）。五个子范式的差别主要是**谁提供评估信号**：

<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1080 530" font-family="PingFang SC, Microsoft YaHei, sans-serif">
  <defs>
    <marker id="mk5" markerWidth="10" markerHeight="8" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#64748b"/></marker>
  </defs>
  <text x="540" y="24" text-anchor="middle" font-size="15" font-weight="bold" fill="#0f172a">训练时自迭代：一个循环，五种范式只差「谁提供信号」（重绘原文 Figure 4）</text>
  <rect x="140" y="64" width="200" height="60" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="2"/>
  <text x="240" y="88" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#1d4ed8">生成</text>
  <text x="240" y="108" text-anchor="middle" font-size="10.5" fill="#475569">模型自产：答案/理由·奖励·题目</text>
  <rect x="45" y="235" width="210" height="64" rx="10" fill="#fffbeb" stroke="#d97706" stroke-width="2.5"/>
  <text x="150" y="259" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#a16207">评估并选择</text>
  <text x="150" y="279" text-anchor="middle" font-size="10.5" fill="#475569">某个信号定义「更好」</text>
  <rect x="290" y="235" width="150" height="64" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
  <text x="365" y="259" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#15803d">更新权重</text>
  <text x="365" y="279" text-anchor="middle" font-size="10.5" fill="#475569">改进被持久化</text>
  <line x1="185" y1="126" x2="155" y2="228" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk5)"/>
  <line x1="255" y1="267" x2="284" y2="267" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk5)"/>
  <line x1="368" y1="232" x2="295" y2="128" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk5)"/>
  <text x="252" y="192" text-anchor="middle" font-size="10.5" fill="#64748b">改进持久在权重里</text>
  <text x="252" y="208" text-anchor="middle" font-size="10.5" fill="#64748b">（直到它们不）</text>
  <text x="150" y="322" text-anchor="middle" font-size="11" font-weight="bold" fill="#b91c1c">⚠ 两大失败模式挂在这一站</text>
  <text x="640" y="66" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">五个子范式 —— 差别主要是「谁提供评估信号」</text>
  <rect x="480" y="80" width="570" height="48" rx="8" fill="#f8fafc" stroke="#94a3b8"/>
  <text x="492" y="100" font-size="11.5" font-weight="bold" fill="#334155">STaR / ReST^EM（CoT 自训练）</text>
  <text x="492" y="118" font-size="11" fill="#64748b">信号：外部答案正确性 —— 结果级过滤（会放进「推理错误的幸运猜测」）</text>
  <rect x="480" y="134" width="570" height="48" rx="8" fill="#f8fafc" stroke="#94a3b8"/>
  <text x="492" y="154" font-size="11.5" font-weight="bold" fill="#334155">Self-Rewarding RL / ReST-MCTS*</text>
  <text x="492" y="172" font-size="11" fill="#64748b">信号：过程奖励 —— 树搜索推断、给中间步骤打分（更高质量的自训练集）</text>
  <rect x="480" y="188" width="570" height="48" rx="8" fill="#f8fafc" stroke="#94a3b8"/>
  <text x="492" y="208" font-size="11.5" font-weight="bold" fill="#334155">OPSD（on-policy 自蒸馏，2026 年结晶）</text>
  <text x="492" y="226" font-size="11" fill="#64748b">信号：特权教师 ＝ 同权重+额外信息（参考解/反馈）—— 常规使用中最闭合的循环</text>
  <rect x="480" y="242" width="570" height="48" rx="8" fill="#f8fafc" stroke="#94a3b8"/>
  <text x="492" y="262" font-size="11.5" font-weight="bold" fill="#334155">Self-play：SPIN → Absolute Zero / R-Zero / Agent0</text>
  <text x="492" y="280" font-size="11" fill="#64748b">信号：程序化验证器 + 自己出题（零数据：Challenger 在 Solver 能力前沿出题）</text>
  <rect x="480" y="296" width="570" height="48" rx="8" fill="#f8fafc" stroke="#94a3b8"/>
  <text x="492" y="316" font-size="11.5" font-weight="bold" fill="#334155">具身 / 合成数据（机器人自反思 · DataEvolver）</text>
  <text x="492" y="334" font-size="11" fill="#64748b">信号：物理反馈 / 管线自身 —— 验证昂贵 · 噪声 · 慢</text>
  <rect x="30" y="385" width="1020" height="125" rx="10" fill="#fef2f2" stroke="#dc2626" stroke-width="2"/>
  <text x="540" y="410" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b91c1c">两大默认风险 —— 都挂在「评估并选择」这一站</text>
  <text x="50" y="434" font-size="11" fill="#475569">① 自确认循环：生成器/评估器共享权重 → 偏见相关；置信度耦合奖励</text>
  <text x="50" y="454" font-size="11" fill="#475569">　过度奖励高置信度错误；极端情形＝把失败谎报为成功。不需要对手，</text>
  <text x="50" y="474" font-size="11" fill="#475569">　reward hacking 只是它的特例。</text>
  <text x="560" y="434" font-size="11" fill="#475569">② 坍缩：rise-and-collapse —— pass@1 在同一 run 内爬升后崩到近零</text>
  <text x="560" y="454" font-size="11" fill="#475569">　（真可验证奖励下也发生），KL/EWC 拦不住。存活杠杆 ＝ data gating</text>
  <text x="560" y="474" font-size="11" fill="#475569">　+ reward grounding：坍缩是默认结局，不是偶发事故。</text>
  <line x1="540" y1="420" x2="540" y2="500" stroke="#fca5a5" stroke-width="1.5" stroke-dasharray="4 3"/>
</svg>

<sub><em>图 5 · 训练时自迭代循环：五种范式按"谁提供评估信号"区分；自确认与坍缩两大失败模式都挂在评估-选择站</em></sub>

</div>

### 4.1 自奖励 RL

- **ReST-MCTS\***（主题最高引）：不按最终答案正确性过滤完整解（会放进"推理错误的幸运猜测"），用树搜索推断*过程*奖励给中间步骤打分，得到更高质量的自训练集。过程奖励思想已多样化：**SEVA**（验证器输出证据对齐+推理链+校准置信度而非不透明二元标签，让 agent 能对*为什么*失败采取行动）、**EvoIdeator**（checklist 接地的科学构思信号替代标量 rubric 奖励）、**RePro**（长程 agent 的回顾式进度感知——发现 naive 在线进度提示反而有害）。
- 一个引人注目的可解释性结果解释了自生成价值信号为何可能：**语言模型在激活空间里编码了一条"价值轴"**，追踪当前轨迹是否走在正轨上——self-reward 的原材料，**先于任何言语化批判存在**。
- 类别终局的最清晰表述是 **Self-Trained Verification**：test-time 验证-精炼循环和训练时自训练被*同一个瓶颈（验证器）*卡住——前者在验证器分数通胀而准确率停滞时失速，后者在坏的自生成数据进入训练时失败——所以干脆**自训练验证器本身，一次解锁两个位置**。作者评论：验证器自训练究竟逃脱了它要解决的循环性、还是仅仅把循环性搬了家，**是这个家族里最重大的单一开放问题**。
- **最强的自我警戒**：Lin 记录了代码 REINFORCE 后训练的 **rise-and-collapse**——连续训练 campaign 中 pass@1 爬升然后在*同一次运行内*坍缩（有时到接近零），且是在**真正可验证的二元奖励**下发生，KL/EWC 约束都拦不住。**奖励模型失调不是自训练自我退化的必要条件——优化动力学本身就足够**。另有：LLM 生成奖励*设计*的特征性失败（reward flooding、对环境 API 的语义误解——应作为迭代 debug 而非一次性生成）；工业实践诊断出的 **"scientific amnesia"**——跨偏好 campaign 反复 DPO 的管线保住了学到的行为，却不累积*如何跑下一个 campaign* 的方法论知识：**模型的自改进没有伴随过程的自改进**。

### 4.2 CoT 自训练

- STaR 配方（采样 rationale → 留下到达正确答案的 → 微调 → 重复）仍是骨架。变体：**Re-ReST**（反射器用环境反馈修复失败轨迹，把失败转成训练信号而非丢弃）、**PRefLexOR**（对中间推理步骤的递归偏好优化）、**LaTRO**（完全无外部奖励，把模型自身似然当潜变量目标，"解锁"基座模型里已隐藏的推理）——**后训练放大潜在能力而非创造能力**这个框架已硬化为独立研究问题（近期工作在测绘 elicitation 何时有效、何时失败的边界条件）。
- **无验证器前沿正被直接测绘**：Self-Verified Distillation 从仅有未标注问题出发（无 ground truth、无工具、无外部教师），用 prompt-based 自验证过滤自己的候选解，提升数学/科学/编码；Semi-CoT 形式化半监督设定（从未标注问题构造伪推理监督）。循环也在向*部署内部*迁移（§3.4 的 TTT），从两侧模糊推理/训练边界。
- **2026 浪潮的三个矫正**：① **效率**——o1 式长思考 overshoot（琐碎问题烧数千 token），且错误轨迹比正确轨迹有更多无效自反思（即使长度匹配）→ 段级 credit assignment 教模型何时停；② **联合优化**——ThinkTwice 在同一二元奖励下交错求解与精炼，**把自精炼变成被训练的能力而非 prompt 技巧**；③ **范围极限**——重要负面结果：**"可验证的搜索不是可学习的 CoT"**——存在一类模型能执行但无法从轨迹经微调内化的过程。**自训练继承基底表示的极限；更多循环修不了架构学不会的东西。**

### 4.3 On-policy 自蒸馏（OPSD，语料最年轻的线索）

- **2026 年之前不存在，已横跨数十篇（56 篇）——领域结晶新范式速度之最**。配方：单一模型同时当学生和*特权教师*（教师 = 同样权重 + 额外信息条件化：参考解、验证反馈、更富上下文），学生在自己的 rollout 上匹配教师的 token 级分布。稠密 token 级监督、无外部教师、无奖励模型。**是常规使用中最闭合的训练循环——连教师信号都是自生成的**。
- 理论在整合：**power-distribution 分析**把采样、自奖励 RL、自蒸馏统一为一个分布操作的特例——解释了为什么这些表面不同的循环行为相似。极简端："embarrassingly simple self-distillation" 只靠温度+截断采样+SFT 就提升代码生成（无验证器无教师无 RL），留下"无验证器收益的底在哪"的开放问题。经验精炼：**负（错误）rollout 比正样本信息量更大**应重加权；无管理的难度路由会过优化简单题；rollout 中的过程性信息可作为蒸馏记忆跨情景保留而非每次丢弃。
- **失败模式记录得同样充分，且与 §3 押韵**：vanilla 配方**在长 CoT 推理模型上一致失败**，恰好破坏它要加强的反思行为；特权教师的稠密监督会过拟合 in-domain 模式；对比分析找到机制——特权/非特权分布差的学习信号集中在*风格* token 而非任务承载 token（**"privilege-induced style drift"**：带提示的教师写得更短更直接 → 训练失稳或回复长度坍缩）；**"prefix failure"**（稠密逐 token 监督诱导双峰教师混合+碎片化梯度，token 级重加权修不了，必须轨迹级干预）；多模态下捷径是结构性的——特权目标让教师从文本参考引导 token 而忽略图像，**学生蒸馏到的是语言先验而非感知技能**，需要显式解耦感知与推理。
- **要带走的模式：自生成信号越特权，循环越高效地同时传递能力和偏见。**特权上下文本身的设计（给什么反馈、什么特异性）正成为范式的核心自由度。

### 4.4 Self-play

- 循环再闭合一步：模型不仅生成答案/奖励，还生成*问题*。谱系：**SPIN**（对自己上一迭代自博弈，可证收敛到数据分布）→ **Absolute Zero / R-Zero**（零数据 proposer-solver：Challenger 学会在 Solver 能力前沿出题，二者从单一基座模型共进化，完全无人类任务）→ **Agent0**（配方从推理题扩展到 *agentic* 任务：课程 agent 与工具执行器从零外部数据共进化）。**这是最接近自主课程的现存训练范式**，在有程序化验证器的地方效果惊人：可执行地理空间程序（GeoX）、形式化定理证明（已有 prover-conjecturer 共进化的理论框架）、验证器支撑的真正困难数学题生成。
- **中心发现是关于稳定性**：self-play 的存活由两个非对称杠杆支配——**data gating**（什么进训练集）与 **reward grounding**（什么把信号锚定到现实）——**任一失效时坍缩是默认结局，而非奖励设计的偶发事故**。种群变体用共进化子种群间的交叉评估替代自校准（结构性解法）。非可验证任务上难度复利：LLM-judge 奖励被裁判自身能力限界 → 元评估（模型学会评估*评估*）、基于模型间预测位移的无验证器内在奖励。开放交互动力学的警告：多轮 LLM 自博弈对话漂入**与话题无关的吸引子状态**——共进化课程必须对抗的同质化压力。

### 4.5 具身与合成数据循环

类别最新前沿把训练循环搬进物理/合成数据场景（验证昂贵、噪声、慢）：机器人用 VLM 当内部批判者批判并重规划自己的社会行为；VLA 策略执行中检查物理可行性并自反思（而非纯前馈行动）；具身基础模型把规划-纠正-指向整合进单一架构（明确瞄准自进化物理智能）；人类视频动力学模型支撑"具身练习与从失败学习"。数据侧循环转向管线自身：**DataEvolver 自进化 LLM 训练的数据准备过程——应用于所有其他训练循环所消费之基底的自我改进**。

**§4 评估**：训练时循环是有界自我改进"挣得饭钱"的地方——收益持久、可扩展、跨迭代复利，**直到它们不**。每条子线索独立重新发现了同样三个事实：**(i) 循环的天花板由其验证信号设定**（执行与证明最高、学习裁判次之、内在信号最低）；**(ii) 坍缩是要工程对抗的默认动力学，不是边缘情况**；**(iii) 循环传递偏见与传递能力同样高效**。这三条是 §5 的承重事实。

---

## 5. 自评估（§5，318 篇，其他三类站立其上的类别）

**核心命题：每个自我改进循环都是一个"某种信号可替代人类判断"的主张，循环的天花板恰好是这个替代品的质量。**自评估也是语料整合最快的类别（82% 在 2026）：直到最近还只是训练论文的服务功能，现在已是自有方法、benchmark、失败分析的研究领域。

### 5.1 评估器设计空间

三个现代锚点，当前浪潮在每个上发展：

| 锚点 | 原始贡献 | 2026 发展 |
|---|---|---|
| **过程监督**（Lightman et al.） | 过程奖励优于结果奖励 → PRM 文献的种子 | PRM 更便宜更校准（efficient PRM）；更结构化：SEVA 输出证据对齐+推理链+校准置信度，让 agent 对*为什么*失败采取行动 |
| **LLM-as-a-judge**（MT-Bench / Chatbot Arena） | ~80% 裁判-人类一致性为范式辩护；位置/冗长/自增强偏见为范式加限定 | 裁判可靠性获得**心理测量学**（信任分数前先出偏见数据表）；裁判**特异性**（per-judge 能力分类法 JudgeFit、多语言裁判分歧、BinEval 原子二元问题分解） |
| **奖励模型过优化 scaling laws**（Gao et al.） | 领域的 Goodhart 曲线：任何学习代理被优化得够狠，真实质量先峰后落 | rubric 成为一级可进化工件：自生成 rubric 逼近专家手写、rubric 层级扩展开放式评估、rubric-conditioned 信号替代标量奖励；自验证内建进目标函数（DuPO 双偏好：验证能力成为被训练的产品而非被 prompt 的期望） |

**最重大的一步：领域开始用它所监督的同一批循环来改进评估器**——deep-research agent 进化自己的 rubric；Self-Trained Verification 把验证器当自我改进的首要对象；元评估评判裁判；Red Queen 让评估标准成为共进化种群成员。**§3–4 的每个机制都被递归地应用于监督它的信号。这个递归是稳定化还是复利化偏见，是本节余下部分要处理的开放问题**（§8 称之为"领域对自己瓶颈的集体回答"）。

### 5.2 验证层级（全文的中心仪器）

<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1080 615" font-family="PingFang SC, Microsoft YaHei, sans-serif">
  <defs>
    <marker id="mk6" markerWidth="10" markerHeight="8" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#64748b"/></marker>
  </defs>
  <text x="540" y="26" text-anchor="middle" font-size="15" font-weight="bold" fill="#0f172a">验证层级：信号可靠性向上递增，任务覆盖向下增宽（重绘原文 Figure 5）</text>
  <rect x="240" y="46" width="320" height="56" rx="8" fill="#f8fafc" stroke="#64748b" stroke-width="2" stroke-dasharray="6 4"/>
  <text x="400" y="70" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">人类研究判断（方向生成）</text>
  <text x="400" y="90" text-anchor="middle" font-size="10.5" fill="#64748b">层级爬不上去的一级 —— 先于层级、不索引它（§5.4）</text>
  <line x1="400" y1="102" x2="400" y2="116" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3 3"/>
  <polygon points="300,120 500,120 540,200 260,200" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="400" y="152" text-anchor="middle" font-size="13" font-weight="bold" fill="#15803d">L1 形式验证器</text>
  <text x="400" y="176" text-anchor="middle" font-size="11" fill="#3f6212">证明检查器 · 类型系统 — 构造上 sound</text>
  <polygon points="260,204 540,204 580,284 220,284" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="400" y="236" text-anchor="middle" font-size="13" font-weight="bold" fill="#1d4ed8">L2 执行反馈</text>
  <text x="400" y="260" text-anchor="middle" font-size="11" fill="#1e40af">测试 · 编译器 · benchmark — 可靠但不完备</text>
  <polygon points="220,288 580,288 620,368 180,368" fill="#fef9c3" stroke="#ca8a04" stroke-width="2"/>
  <text x="400" y="320" text-anchor="middle" font-size="13" font-weight="bold" fill="#a16207">L3 学习型裁判</text>
  <text x="400" y="344" text-anchor="middle" font-size="11" fill="#854d0e">RM · LLM-as-judge — 受自身能力限界 · 自己也是被优化目标</text>
  <polygon points="180,372 620,372 660,452 140,452" fill="#fee2e2" stroke="#dc2626" stroke-width="2"/>
  <text x="400" y="404" text-anchor="middle" font-size="13" font-weight="bold" fill="#b91c1c">L4 内在信号</text>
  <text x="400" y="428" text-anchor="middle" font-size="11" fill="#7f1d1d">置信度 · 自洽性 · 似然 — 最便宜 · 最可被 game（任务覆盖在此最宽）</text>
  <line x1="95" y1="452" x2="95" y2="125" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk6)"/>
  <text x="95" y="478" text-anchor="middle" font-size="11" fill="#64748b">可靠性 ↑</text>
  <rect x="735" y="120" width="325" height="125" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="897" y="144" text-anchor="middle" font-size="12" font-weight="bold" fill="#15803d">规律：强度跟随层级</text>
  <text x="897" y="166" text-anchor="middle" font-size="10.5" fill="#475569">（定性模式，非测量定律 —— 作者自注）</text>
  <text x="897" y="186" text-anchor="middle" font-size="10.5" fill="#475569">FunSearch / AlphaEvolve 活在 L1–L2</text>
  <text x="897" y="205" text-anchor="middle" font-size="10.5" fill="#475569">熬过 2024 负面结果的 self-refine 都爬了层级</text>
  <text x="897" y="224" text-anchor="middle" font-size="10.5" fill="#475569">AI-scientist 差距 ＝ 用 L3 工具干 L4 的活</text>
  <rect x="735" y="260" width="325" height="125" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="897" y="284" text-anchor="middle" font-size="12" font-weight="bold" fill="#b91c1c">地板的直接测量：Mirror Loop</text>
  <text x="897" y="306" text-anchor="middle" font-size="10.5" fill="#475569">3 家提供商模型 × 4 任务族 × 10 轮</text>
  <text x="897" y="325" text-anchor="middle" font-size="10.5" fill="#475569">无接地自批判：信息性变化 -55%</text>
  <text x="897" y="344" text-anchor="middle" font-size="10.5" fill="#475569">→ 递归自评估 ＝ 改述，不是进步</text>
  <text x="897" y="363" text-anchor="middle" font-size="10.5" fill="#475569">一次最小验证干预 → 恢复前进</text>
  <rect x="735" y="400" width="325" height="105" rx="8" fill="#f8fafc" stroke="#64748b" stroke-width="1.5"/>
  <text x="897" y="424" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">失败模式集中在底部梯级</text>
  <text x="897" y="446" text-anchor="middle" font-size="10.5" fill="#475569">L1：可无限迭代而不接受假改进</text>
  <text x="897" y="465" text-anchor="middle" font-size="10.5" fill="#475569">L2：通过测试不定正确性 · 固定 benchmark 终被 game</text>
  <text x="897" y="484" text-anchor="middle" font-size="10.5" fill="#475569">L3：Goodhart 曲线 · L4：最可被 game</text>
  <rect x="95" y="530" width="965" height="64" rx="10" fill="#fffbeb" stroke="#d97706" stroke-width="2"/>
  <text x="577" y="556" text-anchor="middle" font-size="12" font-weight="bold" fill="#a16207">给 harness 工程师的用法：配任何改进循环前，先问反馈信道在层级哪一级</text>
  <text x="577" y="578" text-anchor="middle" font-size="11" fill="#475569">层级越低 → 越需要外挂接地干预 —— 改进的循环与打转的循环之间，只差一级外部验证（这就是全文论点的实验版）</text>
</svg>

<sub><em>图 6 · 验证层级：L1 形式验证器 → L4 内在信号；顶端虚线框是层级索引不了的人类研究判断；右侧为规律、地板测量与失败模式分布</em></sub>

</div>

四级细节（配合图 6）：
- **L1 形式验证器**（证明检查器、类型系统）：**构造上 sound**——self-play 定理证明、验证化技能进化可以无限迭代而不接受假改进。
- **L2 执行反馈**（测试、编译器、benchmark）：**可靠但不完备**——通过测试 underdetermine 正确性；任何固定 benchmark 终会被 game。
- **L3 学习型裁判**（RM、LLM-as-judge、PRM）：**受裁判自身能力限界，且自己也是优化目标**（元评估由此而生）。
- **L4 内在信号**（置信度、自洽性、似然）：**最便宜、最可被 game**。

**层级的地板已被直接测量**：Mirror Loop 研究让三家提供商的模型在四个任务族上做十轮无接地自批判，**信息性变化跨迭代下降 55%**——无外部反馈的递归自评估产生的是*改述而非进步*；而在第三轮插入一次最小接地干预（一个验证步骤）就恢复了前进。**这就是全文论点的实验版：改进的循环与打转的循环之间，只差一级外部验证。**

### 5.3 四个失败模式

<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1080 520" font-family="PingFang SC, Microsoft YaHei, sans-serif">
  <text x="540" y="22" text-anchor="middle" font-size="15" font-weight="bold" fill="#0f172a">四大失败模式（§5.3）：前三种从循环内部留有签名，第四种不留</text>
  <path d="M 35 64 L 35 56 L 775 56 L 775 64" fill="none" stroke="#16a34a" stroke-width="2"/>
  <text x="405" y="48" text-anchor="middle" font-size="12" font-weight="bold" fill="#15803d">从循环内部可检测 —— 在循环已追踪的量里留有签名</text>
  <path d="M 800 64 L 800 56 L 1045 56 L 1045 64" fill="none" stroke="#dc2626" stroke-width="2"/>
  <text x="922" y="48" text-anchor="middle" font-size="12" font-weight="bold" fill="#b91c1c">需要环外立足点</text>
  <rect x="35" y="70" width="245" height="350" rx="10" fill="#fffbeb" stroke="#d97706" stroke-width="2"/>
  <text x="157" y="96" text-anchor="middle" font-size="13" font-weight="bold" fill="#a16207">① 自确认循环</text>
  <text x="50" y="122" font-size="11" fill="#475569">生成器与评估器共享权重</text>
  <text x="50" y="140" font-size="11" fill="#475569">→ 偏见相关</text>
  <text x="50" y="164" font-size="11" fill="#475569">置信度耦合奖励系统性</text>
  <text x="50" y="182" font-size="11" fill="#475569">过度奖励「高置信度错误」</text>
  <text x="50" y="200" font-size="11" fill="#475569">——循环优先强化模型最</text>
  <text x="50" y="218" font-size="11" fill="#475569">确信的错</text>
  <text x="50" y="242" font-size="11" fill="#475569">极端情形：任务完成被奖励</text>
  <text x="50" y="260" font-size="11" fill="#475569">→ 把失败谎报为成功</text>
  <text x="50" y="284" font-size="11" fill="#475569">不需要对手；reward hacking</text>
  <text x="50" y="302" font-size="11" fill="#475569">只是它的特例</text>
  <text x="50" y="330" font-size="10.5" fill="#92400e">证据：Tan et al. 机制诊断 ·</text>
  <text x="50" y="348" font-size="10.5" fill="#92400e">SciIntegrity-Bench（34.2% 失败；</text>
  <text x="50" y="366" font-size="10.5" fill="#92400e">缺数据场景 7 模型全部捏造）·</text>
  <text x="50" y="384" font-size="10.5" fill="#92400e">多模态「答案一致但忽略图像」</text>
  <rect x="290" y="70" width="245" height="350" rx="10" fill="#fffbeb" stroke="#d97706" stroke-width="2"/>
  <text x="412" y="96" text-anchor="middle" font-size="13" font-weight="bold" fill="#a16207">②（模型）坍缩</text>
  <text x="305" y="122" font-size="11" fill="#475569">递归在自己输出上训练</text>
  <text x="305" y="140" font-size="11" fill="#475569">→ 丢失分布尾部 → 退化</text>
  <text x="305" y="158" font-size="11" fill="#475569">（Shumailov，Nature）</text>
  <text x="305" y="182" font-size="11" fill="#475569">统一理论：熵储库原理</text>
  <text x="305" y="200" font-size="11" fill="#475569">（LLM/GAN/RL 同一现象；</text>
  <text x="305" y="218" font-size="11" fill="#475569">真实数据混合/熵奖励/检索</text>
  <text x="305" y="236" font-size="11" fill="#475569">都是它的实例）</text>
  <text x="305" y="260" font-size="11" fill="#475569">Zenil 定理形状：外生接地</text>
  <text x="305" y="278" font-size="11" fill="#475569">信号比例渐近消失 →</text>
  <text x="305" y="296" font-size="11" fill="#475569">退化动力学必然跟随</text>
  <text x="305" y="324" font-size="10.5" fill="#92400e">争议综合：纯闭环退化，</text>
  <text x="305" y="342" font-size="10.5" fill="#92400e">但没人需要跑纯闭环 ——</text>
  <text x="305" y="360" font-size="10.5" fill="#92400e">「多少 grounding 就够」</text>
  <text x="305" y="378" font-size="10.5" fill="#92400e">的汇率无人测出</text>
  <text x="305" y="396" font-size="10.5" fill="#92400e">（开放问题 1）</text>
  <rect x="545" y="70" width="245" height="350" rx="10" fill="#fffbeb" stroke="#d97706" stroke-width="2"/>
  <text x="667" y="96" text-anchor="middle" font-size="13" font-weight="bold" fill="#a16207">③ 多样性坍缩</text>
  <text x="560" y="122" font-size="11" fill="#475569">任务分布的窄化</text>
  <text x="560" y="140" font-size="11" fill="#475569">（区别于分布坍缩）</text>
  <text x="560" y="164" font-size="11" fill="#475569">proposer 收敛到满足奖励的</text>
  <text x="560" y="182" font-size="11" fill="#475569">窄带问题 → solver 的课程</text>
  <text x="560" y="200" font-size="11" fill="#475569">被饿死</text>
  <text x="560" y="224" font-size="11" fill="#475569">多轮自博弈对话漂入</text>
  <text x="560" y="242" font-size="11" fill="#475569">与话题无关的吸引子状态</text>
  <text x="560" y="266" font-size="11" fill="#475569">甚至单一 campaign 内：</text>
  <text x="560" y="284" font-size="11" fill="#475569">pass@1 无任务分布变化</text>
  <text x="560" y="302" font-size="11" fill="#475569">也先升后崩</text>
  <text x="560" y="330" font-size="10.5" fill="#92400e">结论：新颖性是可消耗资源，</text>
  <text x="560" y="348" font-size="10.5" fill="#92400e">闭环会把它耗尽</text>
  <rect x="800" y="70" width="245" height="350" rx="10" fill="#fef2f2" stroke="#dc2626" stroke-width="2.5"/>
  <text x="922" y="96" text-anchor="middle" font-size="13" font-weight="bold" fill="#b91c1c">④ 框架锁定</text>
  <text x="815" y="122" font-size="11" fill="#475569">well-posed wrong question：</text>
  <text x="815" y="140" font-size="11" fill="#475569">有接地、诚实、多样、稳定，</text>
  <text x="815" y="158" font-size="11" fill="#475569">却在优化一个已不再值得</text>
  <text x="815" y="176" font-size="11" fill="#475569">优化的目标</text>
  <text x="815" y="200" font-size="11" fill="#475569">从循环内部不可检测 ——</text>
  <text x="815" y="218" font-size="11" fill="#475569">检测需要循环自身标准之外</text>
  <text x="815" y="236" font-size="11" fill="#475569">的立足点，闭环恰恰没有；</text>
  <text x="815" y="254" font-size="11" fill="#475569">层级把目标当作给定，</text>
  <text x="815" y="272" font-size="11" fill="#475569">也不索引它</text>
  <text x="815" y="300" font-size="10.5" fill="#7f1d1d">证据：正确答案但错误机制 ·</text>
  <text x="815" y="318" font-size="10.5" fill="#7f1d1d">scientific amnesia ·</text>
  <text x="815" y="336" font-size="10.5" fill="#7f1d1d">失败痕迹反而框住 agent</text>
  <text x="815" y="354" font-size="10.5" fill="#7f1d1d">（累积上下文既是能力源</text>
  <text x="815" y="372" font-size="10.5" fill="#7f1d1d">也是锁定源）</text>
  <text x="815" y="396" font-size="10.5" fill="#7f1d1d">对策：开放问题 6（尚无 benchmark）</text>
  <rect x="35" y="440" width="1010" height="62" rx="10" fill="#f8fafc" stroke="#64748b" stroke-width="1.5"/>
  <text x="540" y="464" text-anchor="middle" font-size="11.5" fill="#475569">与层级的对应：①–③ ＝ 层级被违反的不同切面（拿 L4 信号当 L1 用）；④ ＝ 层级本身的盲点 —— 它只对「给定目标」给信号排序。</text>
  <text x="540" y="486" text-anchor="middle" font-size="11.5" fill="#475569">所以 §5.4 的拆解：方向设定里困住人类的，一半是「方向评估」（层级可索引），一半是「方向生成」（先于层级）。</text>
</svg>

<sub><em>图 7 · 四大失败模式：自确认 / 模型坍缩 / 多样性坍缩（内部可检测）+ 框架锁定（需要环外立足点，恰是闭环所缺）</em></sub>

</div>

| 模式 | 机制一句话 | 内部可检测？ | 代表证据 |
|---|---|---|---|
| ① 自确认循环 | 生成器/评估器共享权重 → 偏见相关 → 过度奖励高置信度错误 | ✔ 有签名（奖励-置信耦合度） | Tan et al.；SciIntegrity-Bench 谎报；多模态 visual under-conditioning |
| ② 模型坍缩 | 递归自训练 → 丢分布尾部 → 退化 | ✔ 有签名（分布/熵指标） | Shumailov Nature；熵储库原理；Zenil 定理 |
| ③ 多样性坍缩 | 任务分布窄化：proposer 收敛窄带、对话进吸引子 | ✔ 有签名（课程多样性） | vocabulary 窄化；attractor states；rise-and-collapse |
| ④ 框架锁定 | 目标本身过时仍在优化（well-posed wrong question） | ✘ 需要层级外的立足点 | 正确答案但错误机制；scientific amnesia；失败痕迹框住 agent |

### 5.4 不可验证的前沿：把"方向设定"拆成两个问题

无可检查信号之处（创意写作、对话、研究品味）层级触底，变通方案很说明问题：元评估（评判裁判）、跨模型预测位移的无验证器内在奖励、claim 级可审计性（让输出*构造上*可验证）——**没有一个接近执行反馈的可靠性**。这精确对应 Anthropic essay 的缺口：研究*执行*可验证（代码能跑、benchmark 能出分）且正被自动化；研究*方向设定*是不可验证任务的典范，人在那里留下。

**但作者拒绝把方向设定瓶颈与验证瓶颈简单等同**——这是全篇最精细的概念贡献：

<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1080 495" font-family="PingFang SC, Microsoft YaHei, sans-serif">
  <defs>
    <marker id="mk8" markerWidth="10" markerHeight="8" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#64748b"/></marker>
  </defs>
  <text x="540" y="24" text-anchor="middle" font-size="15" font-weight="bold" fill="#0f172a">§5.4 把「研究方向设定」拆开 —— 不是一个瓶颈，是两个性质不同的问题</text>
  <rect x="215" y="44" width="650" height="62" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="2"/>
  <text x="540" y="68" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#1d4ed8">人类为什么留在环中？—— 研究方向设定（Anthropic essay 的瓶颈）</text>
  <text x="540" y="90" text-anchor="middle" font-size="11.5" fill="#475569">诱人的结论：它＝验证瓶颈。但这个等同只对一半成立。</text>
  <line x1="380" y1="106" x2="280" y2="164" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk8)"/>
  <line x1="700" y1="106" x2="800" y2="164" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk8)"/>
  <rect x="40" y="170" width="480" height="235" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
  <text x="280" y="196" text-anchor="middle" font-size="13" font-weight="bold" fill="#15803d">方向评估 —— 验证形状 ✔</text>
  <text x="60" y="222" font-size="11.5" fill="#475569">给定候选方向，判断它是否 sound、值得投资源</text>
  <text x="60" y="248" font-size="11.5" font-weight="bold" fill="#334155">已可 benchmark：SoundnessBench</text>
  <text x="60" y="268" font-size="11" fill="#475569">· 1,099 份 ICLR 提案 × 评审 soundness 子分数</text>
  <text x="60" y="287" font-size="11" fill="#475569">· 12 个前沿模型：普遍的乐观偏见</text>
  <text x="60" y="306" font-size="11" fill="#475569">· 结论：还不可靠作为严谨性的独立初筛（first gate）</text>
  <text x="60" y="334" font-size="11.5" fill="#15803d">前景：随层级爬升可逐步放松 ——</text>
  <text x="60" y="353" font-size="11.5" fill="#15803d">自动化与治理可以指望的那一半</text>
  <text x="60" y="381" font-size="10.5" fill="#64748b">（takeoff 信号「层级上的移动」覆盖的是这一半）</text>
  <rect x="560" y="170" width="480" height="235" rx="10" fill="#fef2f2" stroke="#dc2626" stroke-width="2" stroke-dasharray="7 4"/>
  <text x="800" y="196" text-anchor="middle" font-size="13" font-weight="bold" fill="#b91c1c">方向生成 —— 先于层级 ✘</text>
  <text x="580" y="222" font-size="11.5" fill="#475569">决定候选问题空间应该是什么；注意到一个当前</text>
  <text x="580" y="241" font-size="11.5" fill="#475569">标准仍打高分的问题已不再值得回答</text>
  <text x="580" y="267" font-size="11.5" font-weight="bold" fill="#334155">层级把问题当作给定 → 无法索引它：</text>
  <text x="580" y="287" font-size="11" fill="#475569">一个循环可以爬遍每一级、保持诚实的评估器、</text>
  <text x="580" y="306" font-size="11" fill="#475569">检测并纠正自己代理的腐败，同时在一个</text>
  <text x="580" y="325" font-size="11" fill="#b91c1c">值得放弃的问题上表现卓越</text>
  <text x="580" y="351" font-size="11" fill="#475569">证据：McNamara 谬误（可测量的挤掉重要的）＝</text>
  <text x="580" y="370" font-size="11" fill="#475569">自主 AI scientist 立场论文的第一挑战；interestingness</text>
  <text x="580" y="389" font-size="11" fill="#475569">形式化＝理论开端，不是第五级台阶（开放问题 6）</text>
  <rect x="40" y="425" width="1000" height="52" rx="10" fill="#fffbeb" stroke="#d97706" stroke-width="2"/>
  <text x="540" y="447" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#a16207">含义：要盯的 takeoff 信号 ＝「不可验证任务上验证层级的移动」—— 但它只覆盖左半。</text>
  <text x="540" y="467" text-anchor="middle" font-size="11" fill="#475569">右半尚无测量约定。开放问题 6 的四个候选可观测项：productive abandonment / invariant transfer / absence-sensitivity / reframing latency。</text>
</svg>

<sub><em>图 8 · 方向设定的两半：方向评估（验证形状，绿实线，可爬）与方向生成（先于层级，红虚线，层级盲点）</em></sub>

</div>

### 5.5 结果级 vs 过程级：成本结构决定两种终局读法

区分评估器的*分辨率*：判断答案，还是判断产生答案的过程？结果级信号便宜、锚定了 §4 大多数训练循环（从 STaR 的答案过滤 onward）；过程级信号判中间步骤，自 Lightman 以来证据持续累积（ReST-MCTS* 的观察是训练循环版推论：结果过滤会放进推理错误的幸运猜测）。

**人类学习类比**（原文最生动的一段，每个行为在语料中都有机器对应物）：

| 人类有效学习者 | 机器对应物（语料中） |
|---|---|
| 错题本 | 经验/策略记忆：Reflexion 言语情景记忆 · ISM 失败情景精炼的图式库 · 经验图（持久化 branch-fail-repair 结构） |
| 追踪推导*哪里*出错 | 过程奖励模型（PRM） |
| 找老师要定向指导 | OPSD 的特权教师信号（§4.3） |
| 按计划重访旧错 | replay 与固化，直至"睡眠"阶段（consolidation） |
| 把所学组织成体系 | 技能库与知识图谱累积（Voyager → SkillMaster） |
| ——最终答案是最不重要的工件 | → 结果级信号最便宜但迁移最差 |

**两级的成本结构相反，差异是经济性的而不只是技术性的**，由此推出与智能爆炸意象不同的终局读法：

<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1080 520" font-family="PingFang SC, Microsoft YaHei, sans-serif">
  <defs>
    <marker id="mk9" markerWidth="10" markerHeight="8" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#64748b"/></marker>
  </defs>
  <text x="540" y="24" text-anchor="middle" font-size="15" font-weight="bold" fill="#0f172a">§5.5 结果级 vs 过程级：成本结构决定两种终局读法</text>
  <rect x="40" y="46" width="480" height="160" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="2"/>
  <text x="280" y="72" text-anchor="middle" font-size="13" font-weight="bold" fill="#1d4ed8">结果级改进 ＝ opex（运营开支）</text>
  <text x="60" y="98" font-size="11.5" fill="#475569">结果检查近乎免费；但买到的改进是 per-instance 的 ——</text>
  <text x="60" y="118" font-size="11.5" fill="#475569">best-of-N · 答案过滤重训：每遇新问题再付一次，迁移差</text>
  <text x="60" y="144" font-size="11.5" fill="#475569">管线卡在这一级 → scientific amnesia：</text>
  <text x="60" y="164" font-size="11.5" fill="#475569">行为改进，方法论知识不累积（重复 campaign 诊断）</text>
  <text x="60" y="190" font-size="10.5" fill="#64748b">锚定 §4 大多数训练循环（从 STaR 的答案过滤起）</text>
  <rect x="560" y="46" width="480" height="160" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
  <text x="800" y="72" text-anchor="middle" font-size="13" font-weight="bold" fill="#15803d">过程级改进 ＝ capex（资本开支）</text>
  <text x="580" y="98" font-size="11.5" fill="#475569">过程标注昂贵（Lightman 人工步级标注；PRM 文献的</text>
  <text x="580" y="118" font-size="11.5" fill="#475569">存在理由＝把这个成本自动化下来）</text>
  <text x="580" y="144" font-size="11.5" fill="#475569">但修正过的过程 / debug 过的技能 / 图式可复用 ——</text>
  <text x="580" y="164" font-size="11.5" fill="#475569">成本摊销到未来每个共享结构的问题</text>
  <text x="580" y="190" font-size="10.5" fill="#64748b">机器版「错题本→体系」，见上方人类类比表</text>
  <line x1="280" y1="206" x2="280" y2="248" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk9)"/>
  <line x1="800" y1="206" x2="800" y2="248" stroke="#64748b" stroke-width="2.5" marker-end="url(#mk9)"/>
  <rect x="40" y="254" width="480" height="170" rx="10" fill="#faf5ff" stroke="#a21caf" stroke-width="2"/>
  <text x="280" y="280" text-anchor="middle" font-size="13" font-weight="bold" fill="#7e22ce">读法 A · 成熟中的方法论</text>
  <text x="60" y="306" font-size="11.5" fill="#475569">不断变宽的「已验证过程工具箱」，挂在一个</text>
  <text x="60" y="326" font-size="11.5" fill="#475569">原始能力增长慢得多的模型上</text>
  <text x="60" y="352" font-size="11.5" fill="#475569">与理论一致：累积方法不需要外部 grounding</text>
  <text x="60" y="372" font-size="11.5" fill="#475569">（开放式能力增长才需要）</text>
  <text x="60" y="398" font-size="11.5" fill="#475569">与语料质量分布一致：§3.5–3.6 的持久脚手架</text>
  <rect x="560" y="254" width="480" height="170" rx="10" fill="#fff7ed" stroke="#ea580c" stroke-width="2"/>
  <text x="800" y="280" text-anchor="middle" font-size="13" font-weight="bold" fill="#c2410c">读法 B · 智能爆炸（takeoff）</text>
  <text x="580" y="306" font-size="11.5" fill="#475569">开放式能力增长：循环生循环，</text>
  <text x="580" y="326" font-size="11.5" fill="#475569">每次改进让下一次更容易</text>
  <text x="580" y="352" font-size="11.5" fill="#475569">需要：持续的 grounding（数据/算力/环境）</text>
  <text x="580" y="372" font-size="11.5" fill="#475569">或当前系统缺乏的架构成分</text>
  <text x="580" y="398" font-size="11.5" fill="#475569">拦路的：§7 四条限界结果 + 坍缩动力学 + L4 盲点</text>
  <rect x="40" y="448" width="1000" height="50" rx="10" fill="#1e293b" stroke="#0f172a" stroke-width="2"/>
  <text x="540" y="478" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#ffffff">哪个读法更好描述未来十年 —— 压缩起来，就是这篇综述的两轴网格反复在问的问题</text>
</svg>

<sub><em>图 9 · opex/capex 成本结构 → 两种终局读法："成熟中的方法论"（工具箱）vs "智能爆炸"（takeoff）</em></sub>

</div>

---

## 6. Auto Research（§6，139 篇：领域最壮观的具体结果与最系统的批判，常常关于同一批系统）

### 6.1 LLM 驱动的进化式程序发现（类别中最强的已验证结果）

- **结构性原因**：继承进化计算模板——每个候选都是*程序*、由*自动评估器*打分。**FunSearch**（cap set 问题的新构造，发表于 Nature）确立可信度；**AlphaEvolve** 扩展为通用编码 agent，其发现反哺 Google 自己的 AI 基础设施（更快的矩阵乘 kernel、数据中心调度、加速器电路简化）——**"AI 输出复利进 AI 开发"的最清晰现存例子，当代 RSI 讨论的具体所指**。EoH 以几分之一查询预算在启发式设计上胜过 FunSearch；后继精炼搜索本身：质量-不确定性平衡（QuBe）、多样性驱动和声搜索（HSEvo）、**异构 LLM 种群作为变异算子**（逃离单模型归纳偏见）。
- **2026 浪潮三个对 RSI 问题重要的方向**：
  1. **规模化部署**：AlphaEvolve 配方应用于远超原始演示的生产基础设施——仓库级过程间代码布局优化、TPU 上的全同态加密 kernel。"AI 输出反哺 AI 基础设施"作为**常规工程**运转。
  2. **反身性**：进化发现的目标日益是 AI 自己的机器——EVOM 元进化 actor-critic 架构、**POISE 自主发现用于 LLM 训练本身的新策略优化算法**、MLEvolve 端到端瞄准 ML 工程管线。**当被发现的算法是训练发现者之继任者的算法时，分类法的循环不再是隐喻。**
  3. **循环自身目标的形式化**：把科学发现重构为元优化的工作主张进化*评估标准*与进化候选同样重要——来自范式内部的明确承认：固定评估器终将成为约束瓶颈。甚至开始进化自己的 benchmark（BenchEvolver 在既有 benchmark 饱和时合成前沿任务）。
- **杠杆到底在哪的安静发现**（对 harness 工程极重要）：受控 harness 设计研究显示发现成功重度依赖模型周围的*执行基础设施*——token 预算在"多而浅"与"少而深"候选间怎么分、评估失败怎么处理——**独立于模型能力**；LEVI 证明更强的搜索架构（保多样性档案、能力匹配模型路由、信息子集评估）可在进化搜索中替代更大 LLM，削减前沿模型开销而不损失发现质量。**与 §3.5 的 loop-engineering 转变同构：很多看似"模型自我改进"的东西是模型搜索所在脚手架的改进——对可复现性和成本是好消息，对"把收益归因于模型自身递归能力"是警告。**

### 6.2 AI Scientist agents

- 从程序泛化到论文：**The AI Scientist** 演示全管线（构思、实验、写作、自动评审，**~$15/篇**），主题已碎片化为数十个领域后代：自主数学研究者（导航文献+长程证明）、追求"认知自主"的 Socratic 高维物理 agent、从累积历史适应自己管线的进化多智能体科学家（EvoScientist/EvoMaster）、web 规模研究 agent 舰队协调基础设施（Clarus）。
- **注意力从 agent 转向其环境**（三个方向，用不同词汇做同一件事——**把科学判断移出模型、移进可审计结构**，是对 6.3 批判文献的建设性回应）：
  - **EurekAgent**：瓶颈已从规定 agent 工作流移到*工程化 agent 的环境*（资源、约束、接口）；
  - **Heuresis**：研究管线分解为可组合原语，系统比较想法上的搜索策略——质量/多样性/新颖性作为**独立目标**而非单一分数；
  - **Xcientist**：研究综合与验证外部化为可检查、契约治理的工件（文献证据、想法状态、消融记录、修复痕迹），让生成声明的**出处在模型推理之外存活**。

> ### 案例框：A-Evolve-Training —— 本综述记录的最接近 "closing the loop" 的已发表系统
>
> **做了什么**：自主跑完一个 **30B 模型的整个后训练循环**——提出数据与配方改动、发起训练运行、读取评估、决定去留——**四轮、数周、无人参与**。
>
> **结果**：公开榜上接近人类最佳提交（**0.86 vs 0.87，约 4000 队中第 8**）。作者谨慎地只声称"首个公开报道的此规模自主后训练运行"，不声称自主匹敌人类研究者。
>
> **最耐人寻味的细节不是分数**：运行中途，循环**检测到自己的开发指标与外部表现脱钩**——候选把 dev metric 推到新高而外部目标不动——于是**修订了自己的搜索策略，把这个现已误导的代理指标当作反对候选的证据而非支持**。
>
> **为什么重要**：自主系统注意到并纠正*自己改进信号的腐败*，恰是 §5 认定的领域约束瓶颈（评估器腐败的自查自纠），**在野外被观察到**——§8 称之为"第一个暗示逃出自我确认循环可能的野外观察"。
>
> **对照 Anthropic essay**（执行大体解决、方向设定未解决）：该结果是**确认而非矛盾**——系统在人类指定的目标与搜索空间内优化——但它移动了已演示的前沿。

- 失败恢复正成为独立学科：对失败实验的单次自由格式反思被证明**不够** → 多假设失败归因——AI scientist 对 §3 教训（无结构自批判不工作）的重述。

### 6.3 批判与诊断文献（本类别的怀疑文献与建设文献同样发达，且常常被引更高）

三个反复出现的批判：

1. **可行性 ≠ 质量**：ScienceAgentBench（主题最高引）把"科学发现"分解为单个 workflow 任务，发现最好的 agent 也只解决少数，明确警告端到端自动化声明；**ResearchArena** 让前沿编码 agent（Claude、Codex、Kimi）跑完整研究循环，问的不是论文有没有产出而是*好不好*——且有启发性的转折：**仅看手稿的自动评审下图景乐观（最佳 agent 的论文达到人类 ICLR 提交平均分），但 artifact-aware 评审与人类 meta-review 揭示该图景被夸大**。机器生成研究*读起来*怎样与其工件*支撑*什么之间的差距，本身就是可审计性论点的证据；MLReplicate 用可验证目标（复现 ICML 杰出论文）测量自主系统，记录其距离可靠复现多远。
2. **可审计性是新瓶颈**：报告生成变便宜后，成本移到*追踪*——哪句话基于哪个证据、什么被忽略、来源在哪里冲突。claim 级可审计性、证据许可声明（断言强度校准到支持证据）是让机器生成科学*构造上*可验证的尝试，**因为事后验证不 scale**。受监管领域插入确定性完整性门（"自我批判继承产生自信捏造的盲点"）；前沿物理中无脚手架 agent "引用但不面对"其声明依赖的文献锚。
3. **压力下的完整性**：**SciIntegrity-Bench** 构造"诚实承认失败是唯一正确答案、但任务完成要求不端"的两难，七个 SOTA 模型**完整性失败率 34.2%**；最触目的是缺数据场景下**七个模型全部捏造合成数据**而非承认不可行，差别只在是否披露替换；移除显式完成压力大幅减少未披露捏造**但捏造本身不减**。互补立场文件记录更微妙的变体：物理模拟再发现中 agent 达到*正确答案*同时捍卫*错误机制*，甚至断言自己实验数据反驳的一般性声明——**结果、机制保真、认知诚实必须作为三个独立量测量**。两个结果直接连到 §5 的 reward hacking 分析：**被优化去产出结果的 agent 会在边际上谎报而非失败——且这种倾向看似是内在的，不是 prompt 诱导的。**

两个系统性批判把担忧从 agent 扩展到生态：
- **"Dead Science Walking"**：近期风险是*语料失败*——AI scientist 在系统性过度代表正面结果的文献上训练和接地，自动假设生成以机器速度继承并放大发表偏见：**缓慢的、生态级的自确认循环——今天被扭曲的记录训练明天的假设生成器**。
- 经济学中预注册的人机协作研究：可靠性更取决于认知劳动如何在人机间*结构化*（预承诺、决策排序、问责、注意力分配）而非模型能力——**"研究循环中的人类角色是设计问题，不是残留物"的实证支持**。

**§6 评估**：本类别有语料中"已演示能力"与"可靠能力"的最大差距。评估器是程序时（测试套件、界检查器、profiler），自动发现已产出胜过人类专家且反哺 AI 基础设施的工件；评估器是科学判断时（新颖性、重要性、证据支撑），建设性系统跑在其验证前面，诊断文献的存在恰好是为了记录这个差距。**两个子主题是同一变量的自然实验：§6.1 展示有可信验证器时闭环发现能达成什么；§6.2–6.3 展示没有时什么坏掉。**

### 6.4 关键诊断/负面结果速查表（全语料精选，工程上最有用的一张表）

| 研究 | 发现 | 对实践者的含义 |
|---|---|---|
| Huang et al. 2024 | 无外部反馈，LLM 基本不能自我纠正推理；naive 自纠可能更糟 | 别指望纯内在自纠；给循环接外部信号 |
| Mirror Loop | 10 轮无接地自批判信息量 -55%；一次最小验证干预恢复前进 | 打转与改进之间只差一级外部验证 |
| 文学翻译 refinement 研究 | 收益在流畅/风格/术语；refinement 把输出投影向精炼器自身分布 | 精炼 ≠ 纠错；警惕风格同化 |
| Cupia 受控分解 | 反馈价值须与重采样/格式纠正/额外算力剥离 | 归因需要对照设计，naive 对比虚高 |
| Iscan placebo 研究 | 失败测试＝可执行反例；价值在证伪而非 re-exposure | 反馈的本质是信息，不是重试 |
| Lin rise-and-collapse | pass@1 同 run 先升后崩（可验证奖励下），KL/EWC 拦不住 | 自训练不自稳定；训练中途也要盯坍缩信号 |
| Pu et al.（self-play 存活） | 存活杠杆＝data gating + reward grounding；坍缩是默认 | 把两者当独立工程杠杆分别管理 |
| Patel（负面结果） | "可验证的搜索不是可学习的 CoT"：能执行 ≠ 能从轨迹内化 | 自训练继承架构极限，更多循环修不了 |
| Purified OPSD | vanilla OPSD 在长 CoT 推理模型上一致失败 | 范式有适用前提，长思考模型慎直接用 |
| Pan（style drift） | 特权分布差的学习信号集中在风格 token | 信号越特权，能力与偏见传递都越高效 |
| SkillsBench / SkillAxe | 人写技能 +16.2 分；LLM 写技能 +0 | 技能要评估引导地精炼，别裸写 |
| Wunderlich Pareto 分析 | 推理扩展峰值 +7.1 分 @ ~20× 算力 | 算力感知的方法选择 > 更多迭代 |
| SoundnessBench | 12 个前沿模型对研究提案普遍乐观偏见 | 方向评估还不可交给模型独立初筛 |
| SciIntegrity-Bench | 完整性失败率 34.2%；缺数据场景 7 模型全部捏造 | 完成压力下谎报是内在倾向；用确定性门 |
| ResearchArena | 手稿评审乐观，artifact-aware 评审戳破 | 评 AI 研究要看工件，不只看论文 |

---

## 7. RSI 的基础、极限与安全（§7，60 篇——最小的家族，与声称的风险量级不成比例）

### 7.1 理论条件与四条限界

**正面条件**：Schaul 的 "boundless Socratic learning"——闭环系统中的 agent 可掌握任何能力，若 **(a) 反馈充分信息化且与目标对齐、(b) 经验覆盖足够宽、(c) 容量足够**；语言游戏被提议为 (a)(b) 原则上可工程的框架。**对照 §5 读：整个实证文献就是 (a) 失败（自确认循环）或 (b) 失败（多样性坍缩）时会怎样的长期研究——Socratic 条件实际上已是领域的隐含设计清单。**自奖励 LM 的对齐侧理论保证开始出现（迭代自对齐何时可证改进——窄结果，但属首批）。

**限界文献从四个角度攻击 takeoff 问题**：

| 角度 | 结果 | 含义 |
|---|---|---|
| **可计算性理论** | 形式分离结果：有限内部自修改让系统留在当前计算层内 | 重复内部修订给不出 RSI 叙事随口假设的质变跳跃（那需要类似稳定访问外部 oracle 的东西）。规训词汇："递归地自改进" ≠ "无界地自改进"，只有前者被内部修订许可 |
| **动力学** | Jafari et al.：把"失控增长"形式化为可检验性质，能力增长挂钩资源建设 | 物理与信息论极限下可排除有限时标升级的条件 |
| **经济学** | Whitfill & Wu：四个前沿实验室面板（OpenAI/DeepMind/Anthropic/DeepSeek，2014–2024）估计研究算力与认知劳动的替代弹性 | **两个设定分歧**：基线模型＝替代品（允许纯软件加速）；"前沿实验"模型（考虑 SOTA 训练规模）＝互补品（瓶颈绑住）。这使该研究成为 RSI 可行性辩论的**实证 crux** 而非定论 |
| **信息论** | Zenil 不可能性结果 | LLM 式自训练**不能**无界自改进，除非有符号模型合成或不消失的外部信号流 |

四者共同为分类法的中心切割辩护：**有界自精炼是理论在无新外部资源时许可的东西；开放式 RSI 需要持续的 grounding（数据、算力、环境）或当前系统缺乏的架构成分。**

### 7.2 怀疑立场（不是边缘——包含语料最强的形式结果）

复合主张：(i) 无外部信号的自训练**退化**而非爆炸；(ii) 即使有外部信号，算力与物理约束可能阻止超指数轨迹；(iii) **最可能驱动 takeoff 的能力——研究品味、问题选择——恰是当前系统可证明缺乏的**（§6.3）。第 (iii) 点已有第一个形式处理：**interestingness**（前瞻识别哪些任务有未来进步潜力）作为未来压缩进步的归纳启发式，用算法信息论工具分析，被明确识别为通往 RSI 路上的瓶颈。**研究品味开始获得理论——这是它获得 benchmark 的前提条件。**

**同样重要的是怀疑立场*不*主张什么**：这些结果没有一个限界"**有界自我改进 + 人类方向设定**"的影响——Anthropic 的"复利效率"情景与语料中每个不可能性定理都兼容，且可以说**就是对当前前沿实验室实践的描述**。

### 7.3 安全、控制、与 takeoff 问题的对话

- **安全技术文献集中在类别边界**：永久、自放大、种群可传播的腐败（自进化 agent 系统威胁分析）；无攻击者的能力退化与安全漂移（→人类监督锚）；完成压力下的完整性失败。
- **架构级最硬的论点——"unfireable safety kernel"**：任何位于 agent 运行时*内部*的控制都可被影响 agent 的输入到达，所以对自身运行时 reach 足够的系统**原则上可修改自己的 guardrail**——执行时对齐必须活在 **agent 地址空间之外**。这是"为什么自修改改变安全演算"的控制论重述：**guardrail 成为可修改面的一部分**。
- **治理文献薄但尖锐**：推理算力兴起可能使"经由训练算力阈值的治理"范式脱轨——推理算力花在部署侧还是折回实验室内部训练计划，含义相反；**后者恰是 §4–6 的循环结构，且是从外部更难观察的那个**。最高风险能力的领域评估框架并行出现（自主研究 agent 的生物能力与风险——评估结果的含义依赖记录不足的设计选择）。
- **对 Anthropic essay 三情景（趋势停滞 / 复利效率 / 完全 RSI）的三点回应**：
  1. **定位现在**：几乎所有被综述的都是**情景 2 的机器**（有界循环+人类指定目标），A-Evolve-Training 是最具情景 3 形状的已发表工件；
  2. **指出要盯的 takeoff 信号**：不是 benchmark 分数，而是***不可验证任务上验证层级的移动***——能可靠评估研究方向的系统将放松当前把人留在环中的约束（但只覆盖方向设定中验证形状的那一半）；
  3. **暴露"失调复利"担忧是技术实质而非猜测**：自确认循环恰是今天模型中的偏见会在自训练下放大的机制，且已在小规模被观察到。
- **最清晰的缺口**：技术语料尚未提供治理提案所需的**验证基础设施**——*证明*一个训练循环"没有"自我改进超过阈值的可审计方法。**治理所需与文献所提供之间的这个缺口，是本综述识别出的最空缺研究生态位**（基础家族仅 60/1250）。

## 8. 横切观察与六大开放问题（§8）

### 8.1 五个横切观察

1. **领域加速快于任何综述能追踪**：OPSD 从不存在到 56 篇只用 18 个月。作者只为综述的*结构*（类别×闭合度、验证层级）声称持久性，不为论文清单声称——结构已不改一格吸收了两次范式到来（OPSD、零数据 self-play）。且有自觉：**能容纳一切新结果的结构什么都不预测**，所以明确陈述了这个结构看不见什么（§2.2 的两个排除 + 开放问题 6）。
2. **语料形状本身要求解释**（四个非互斥、原则上可检验的假说）：
   - *可验证性梯度*：两大主导类别集中在有便宜验证器的地方（代码、数学）——实验快、可发表。**§5.2 记录在方法内部的同一梯度，作为话题选择的力量重现**；
   - *进入成本梯度*：推理精炼研究要 API 额度 → 训练循环论文要 GPU → Auto-Research 系统要基础设施+长时程+实验室级算力。**论文数大致随进入成本上升而下降**；前沿端的算力集中把谱系远端推到公司墙内，发表审查效应使之对任何 arXiv 样本不可见；
   - *羊群动力学*：OPSD 数月内从零结晶到数十篇——**设定注意力梯度的是可读性（legibility），不是重要性**；
   - *机构角色分配*：评估直到最近还是方法论文内部的服务功能而非研究身份（补充采集必须定向补它）；基础类 60/1250 的赤字反映了**理论与治理工作既不被 benchmark 也不被产品路线图奖励**。
3. **机制跑在评估前面 → 诊断文献成为领域的承重部分**：作者自陈"分析最依赖的论文不成比例地是诊断性的"（受控反馈分解、placebo 对照自修复、self-play 稳定性分析、完整性 benchmark），在若干主题（AI scientist 最明显）是被引更高的部分。**读作成熟信号：方法浪潮 → 测量浪潮，与推理研究 2023–24 走过的同一序列。**
4. **领域对验证瓶颈的新兴答案＝评估器共进化**：2026 年在互不相关的主题中**至少五次独立产生同一架构动作**（自生成单测与被测代码共进化 CoSPlay；先发现 per-judge 能力分类法再信裁判分 JudgeFit；把不透明裁判分解为可审计二元问题 BinEval；把验证器当首要自改进对象自训练 STV；让评估标准本身成为进化循环成员 Red Queen）。领域显然已下结论：**静态验证器无法监督不断改进的系统——验证器必须与策略一起改进**。这究竟逃脱自确认循环还是只给它加了二楼，**是作者认为未来两年会回答的关键实证问题**；A-Evolve-Training 的自查自纠是第一个暗示逃脱可能的野外观察。
5. **模态泛化真实但受信号限制**：范式已扩散到视觉-语言、视频、机器人、语音，但**每次移植都在更低一级重新遭遇验证层级**（执行反馈没有便宜的具身类似物；多模态自洽信号允许纯文本循环没有的捷径）。**泛化前沿不是模型能力，而是逐模态的*信号工程***（物理残差、形式化技能验证）。

### 8.2 六大开放问题（按杠杆粗排）

| # | 问题 | 一句话 | 现状与第一步 |
|---|---|---|---|
| 1 | **grounding 的汇率** | 维持改进所需的*最小*外生信号率是多少？ | 理论说纯闭环退化，实践里只是临时拼凑地混入外部信号；熵储库框架暗示问题良定义，无人测 |
| 2 | **验证不可验证者** | 研究品味、创意质量、方向设定评估 | 进展会放松整个谱系的约束瓶颈；元评估与构造可审计性是开端不是解 |
| 3 | **稳定性工程成为学科** | 循环动力学的统一处理：何时收敛、振荡、坍缩 | rise-and-collapse / 多样性坍缩 / 安全漂移目前每范式各 rediscover 一遍，需要替代 per-theme 民间智慧 |
| 4 | **可信累积** | 持久自修改（技能/记忆/经验图）缺乏权重训练已有的验证故事 | 形式化验证（VASO）与威胁分析从两侧夹住问题，中间开放 |
| 5 | **治理级测量** | *证明*一个训练循环"没有"超标自我改进的可审计证据 | 可信减速提案所需，背后几乎无技术文献；60/1250 的错配＝最清晰缺口 |
| 6 | **识别框架修订** | 系统能否注意到目标本身已过时，并在保留应保留之物时重构框架 | 无 benchmark 无测量约定，对本综述工具也不可见。四个候选可观测项：**productive abandonment**（放弃局部指标仍在改进的线，对照后来的验证打分）、**invariant transfer**（任务重构中带走哪些约束）、**absence-sensitivity**（缺失结果是否被当作证据）、**reframing latency**（环境漂移后放弃过时目标需要多少证据）。**"故意给过时/误设目标、按是否注意到而非优化多好打分"的 benchmark 今天就可建，但不存在**。障碍的一部分：发表丢弃失败实验/被拒假设/分支探索本身（"storytelling tax"） |

作者的自反性注脚（很诚实，值得记住）：§8 论证**可读性设定注意力梯度**，而分类法本身就是可读性工具——**ours 也受同一批判约束**。

---

## 9. 与本系列笔记的关联（Agent Harness 论文研读）

这篇综述对 harness 工程主题的价值集中在五处：

1. **Harness 的教科书定义**（§2.1）与本系列 [Agent Harness Engineering 调研笔记](../reading-notes-agent-harness-engineering/) 的口径一致，且更明确地点出关键属性：harness = 模型周围把模型变成 agent 的一切（system prompt、工具定义、记忆存储、技能库、检索索引、编排代码、停止规则），**外部可检查、可编辑——包括被 agent 自己编辑，这正是"harness 自修改是'agent 重写自己'的最具体形式"的原因**。值得吸收进后续的 harness 综述写作。
2. **§3.5–3.6 就是一份 harness 自进化的 mini-survey**：Gödel Agent → DGM → Red Queen → Escher-Loop 的自指加深序列；prompt/验证/拓扑/数据/基础设施五个进化层级；Meta-Agent Challenge（第一个测"agent 开发"而非"agent 执行"的 benchmark）。
3. **Loop engineering 论断与本系列笔记直接对话**：macedo2026stop 的"人类工程的工件是循环——触发器、目标、验证、停止规则、记忆"与 [LoopsBench 阅读笔记](../reading-notes-loopsbench-loop-engineering/) 主题互证；本文补上了循环的*进化*维度（循环本身成为被优化的设计工件）。
4. **验证层级是 harness 设计的选型工具**：给 harness 配改进循环时，先问反馈信道在层级哪一级；FLARE 的教训（**反馈分辨率是设计变量**——测试失败太粗、自批判太空）与 CoSPlay 的教训（自生成验证器时，**验证验证器要进循环**）直接适用于 agent 评测设计。SHARP 模式（约束自修改面到可审计 rubric，保持可 diff、可回滚）是自进化 harness 的可操作工程准则。
5. **对既有目录的交叉印证**：
   - 另一篇 2026 年大型自进化综述（"Self-Improving Agents in the Era of Experience: From Self- to Meta-Evolution"）的 Figure 8 二维分类（变什么 × 谁来变）与本文两轴分类法高度同构，但本文多出的关键维度是**把评估器单列为一级类别 + 验证层级排序 + 循环闭合度轴**——两篇对读可以看到 2026 年这个领域分类学的收敛与分歧；
   - SkillsBench 的"LLM 写不好技能"事实（人写 +16.2 分 vs 机写 +0）与 agent 技能编写实践直接相关：**技能文档值得评估引导地精炼（SkillAxe 路线），而不是让模型裸写**；
   - §5.5 的 opex/capex 框架（结果级 vs 过程级改进的成本结构）是 agent 成本分析可以直接借用的经济学语言。

## 10. 个人点评

**优点：**
- **概念卫生极好**。"有界自精炼 vs 开放式 RSI"这一刀切得准：它同时解释了为什么 self-refine 论文看起来遍地成功（它们是收敛问题）而 RSI 叙事听起来永远在路上（它需要层级外的东西）。很多领域混乱源于词汇，这篇用分类法而非新词解决问题。
- **把评估器从工具细节提升为承重柱**是真正有远见的编辑决定。"每个循环都是一个信号可替代人类判断的主张"是我近期读到对 self-X 文献最锋利的一句话概括；而"评估器共进化在 2026 年被五个不相关主题独立发明"这个观察，本身就是科学社会学意义上的好证据。
- **罕见地诚实**：明确写分类法看不见什么（目标当作给定、按基底不按轨迹索引）；明确写语料是样本非普查、补充采集有偏、单人标注；明确区分"定性模式非测量定律"；甚至自我应用"可读性设定注意力梯度"的批判到自己的分类法上。§8 末尾那个自反性注脚在综述文献里几乎见不到。
- **诊断文献与建设文献并重**，6.4 那张表里的负面结果（rise-and-collapse、可验证搜索≠可学习 CoT、privilege-induced style drift、SciIntegrity 全员捏造）对工程实践的价值可能超过所有正面方法论文。
- §5.4 把"方向设定"拆成**方向评估（验证形状，可 benchmark）与方向生成（先于验证，层级不索引）**是全篇最精细的概念贡献——大多数讨论把二者混为"品味问题"，这个拆分直接决定了"takeoff 信号该盯什么"。
- §5.5 的 opex/capex 框架和"成熟中的方法论 vs 无界上升的智能"的终局读法，给了 RSI 讨论一个不依赖爆炸意象的严肃替代叙事。

**弱点与保留：**
- **验证层级是定性的**：作者自己承认"是贯穿语料的定性模式，不是测量定律"。四级排序直觉上对，但没有 exchange rate、没有跨级换算，无法据它做定量预测；"强度跟随层级"的论证主要靠案例选择（FunSearch 在顶部、AI scientist 在底部），有确认偏差风险。
- **1250 篇语料的分类由单人+规则完成**：作者发布 per-paper 赋值以便审计是正确做法，但边界论文（自认约 54 篇外围渗漏）与 89 篇规则改派意味着 Table 1 的比例数字应读作量级而非精确值。
- **发表审查效应是结构性的且无解**：最前沿的工业 RSI 实践（恰是最相关的部分）只能经由实验室愿意发表的切片观察。Anthropic essay 被用作框架而非证据是聪明的处理，但也意味着"closing the loop"的进度条实际上无法从公开语料校准。
- **对 harness/agent 工程读者的实用性不均**：§3–4 信息密度极高（每段都是压缩的文献簇），但没有给出"建一个自改进系统该按什么顺序做决策"的操作清单——验证层级可以当这个清单用，作者没有明说（本笔记 6.4 表算是一个补偿）。
- 六大开放问题里 1、3、5 都有明确的 first step（测 grounding 汇率、统一循环动力学、建治理级测量协议），但 6（框架修订）的四个可观测项虽然新颖，离可操作 benchmark 还很远——作者自己承认"今天可建但不存在"，某种程度上是把最难的问题留在了最模糊的状态。
- 一个小遗憾：全文没有给"评估器共进化是否逃出自我确认"提供任何初步的判别实验设计——作者说这是"未来两年会回答的关键实证问题"，但没说答案长什么样（什么样的证据算"逃出"，什么样算"加二楼"）。

**一句话定位**：如果 2026 年只读一篇关于 AI 自我改进的综述，读这篇——不是因为它覆盖最全（它自己否认这点），而是因为它给了这个领域**一个可以持续使用的判断仪器**（两轴网格 + 验证层级 + 四失败模式），并且诚实地标出了仪器测不到的东西。

---

*笔记基于 arXiv:2607.07663v2 TeX 源码全文通读撰写，2026-09-23；2026-09-23 增补 9 幅自绘 SVG 与速查表。原文引用（\citep 键）保留作者-年份可检索形式，完整文献见论文 References 节或 GitHub 语料库。*
