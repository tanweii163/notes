# SVG 架构图设计规范

> 所有架构图必须遵守本规范，保证整套文档配图风格统一、可读、可缩放。
> 生成 SVG 前先通读本文件。

## 一、总体原则

1. **语义正确优先于美观**：图的每个方框、每条箭头、每个标签必须与文档正文和代码一致，不得臆造。拿不准就少画，不要画错。
2. **一张图讲一件事**：不要把所有组件塞进一张图。聚焦该小节的核心关系（数据流向 / 状态流转 / 层次结构）。
3. **少字**：方框里只放「角色名 + 一句话职责」。细节留给正文，图里不堆段落。
4. **可缩放**：一律用 `viewBox`，不写死像素尺寸；宽度控制在 880~1120 之间。

## 二、三区配色（强约束）

V2 架构分「写入侧 / 账本区 / 读取侧」三大区，全套装图用**同一套语义色**，让读者一看颜色就知道属于哪个区：

| 区 | 角色 | 填充色（浅） | 边框色（深） | 文字色 |
|---|---|---|---|---|
| 写入侧（命令侧：记 + 干） | admit / 调度员 / drain / SessionRunner | `#EAF2FB` | `#2F6FB0` | `#1B3B5F` |
| 账本区（核心枢纽：唯一真理） | 事件账本 / EventV2 总线 / 收件箱 | `#FCF3E3` | `#C8881F` | `#6B4A0E` |
| 读取侧（查询侧：派生 + 推） | projector / 读模型表 / 推送链路 / 前端 | `#EAF6EE` | `#2E9E5B` | `#1B4A2C` |
| 中性（外部 / 模型 / 工具 / 用户） | LLM 模型 / 工具 / 用户 | `#F2F2F4` | `#8A8A93` | `#3A3A40` |
| 强调 / 警示（错误、中断、回滚） | interrupt / revert / 失败收尾 | `#FBEDED` | `#C0392B` | `#6E1F18` |

辅助：
- 箭头线：`#555B66`，线宽 1.6；箭头头部用 `<marker>`。
- 背景（可选的大区分块底色）：写入侧 `#F5F9FD`、账本区 `#FEFBF3`、读取侧 `#F4FBF6`，极浅，仅作分区。
- 字体：`font-family="-apple-system, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif"`。标题 15~17px 加粗，正文 12~13px。

## 三、方框与箭头约定

- 方框：圆角矩形 `rx="8"`，`stroke-width="1.5"`。
- 角色名一行加粗，职责一行（或两行）常规字号、稍浅色。
- 箭头标签放在箭头中段，字号 11~12，颜色 `#555B66`，必要时加白色描边底（`paint-order="stroke"` + `stroke="#FFFFFF" stroke-width="3"`）避免压线。
- 数据流方向必须明确：写事件 → 账本用实线箭头；订阅/派生用实线箭头并标「订阅」「写表」「转发」；控制流（wake/interrupt/派活）可用**虚线** `stroke-dasharray="5 4"` 区分。
- 同步 vs 异步：事务内同步可标「事务内」，事务后异步标「事务后」，与正文术语一致。

## 四、SVG 骨架模板

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 560" font-family="-apple-system, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#555B66"/>
    </marker>
    <marker id="arrow-dash" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#8A8A93"/>
    </marker>
  </defs>

  <!-- 分区底色（可选） -->
  <rect x="20" y="20" width="920" height="520" rx="14" fill="#F5F9FD"/>

  <!-- 一个方框示例（写入侧配色） -->
  <g>
    <rect x="60" y="80" width="200" height="64" rx="8" fill="#EAF2FB" stroke="#2F6FB0" stroke-width="1.5"/>
    <text x="160" y="106" text-anchor="middle" font-size="15" font-weight="700" fill="#1B3B5F">admit 准入器</text>
    <text x="160" y="126" text-anchor="middle" font-size="12" fill="#1B3B5F" opacity="0.8">用户输入 → 账本 + 收件箱</text>
  </g>

  <!-- 一条带标签的箭头 -->
  <line x1="260" y1="112" x2="420" y2="112" stroke="#555B66" stroke-width="1.6" marker-end="url(#arrow)"/>
  <text x="340" y="104" text-anchor="middle" font-size="11" fill="#555B66" paint-order="stroke" stroke="#FFFFFF" stroke-width="3">publish</text>
</svg>
```

## 五、嵌入文档的方式

- 文件命名：`assets/0X-<slug>.svg`，例如 `assets/00-overview.svg`、`assets/03-entry-state.svg`。
- 在 markdown 里用相对路径引用，放在对应小节标题正下方：
  ```markdown
  ![架构全景图](./00-overview.svg)
  ```
- 保留原有 ASCII 图作为「文字版」放在 SVG 之后（或之前），二者互补；不要删除 ASCII 图，除非该 ASCII 图与 SVG 完全重复且 SVG 更清晰——此时可删 ASCII。默认保留。

## 六、验收清单（生成后自检）

- [ ] 只用本规范的配色，未自创颜色
- [ ] 有 `viewBox`，无写死 width/height（或 width 用百分比/auto）
- [ ] 所有文字在方框内、不溢出、不压线
- [ ] 箭头方向与正文描述的数据流向一致
- [ ] 控制流用虚线、数据流用实线
- [ ] 文件名与嵌入路径正确，markdown 能渲染
- [ ] 与正文术语一致（如「事务内 / 事务后」「steer / queue」「durable / live-only」）
