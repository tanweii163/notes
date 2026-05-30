# Lightpanda Browser 使用说明

> **Lightpanda** 是一个从零开始、用 Zig 语言编写的无头浏览器，专为 AI Agent 和 Web 自动化场景设计。  
> 它不是 Chromium/Blink/WebKit 的分支，而是一个全新的浏览器内核。
>
> 官网：<https://lightpanda.io> ｜ GitHub：<https://github.com/lightpanda-io/browser>

---

## 目录

- [快速安装](#快速安装)
- [基本用法：抓取网页](#基本用法抓取网页)
- [输出格式](#输出格式)
- [等待策略](#等待策略)
- [CDP 服务器模式](#cdp-服务器模式)
- [与 Puppeteer/Playwright 集成](#与-puppeteerplaywright-集成)
- [注入脚本](#注入脚本)
- [Cookie 管理](#cookie-管理)
- [代理与网络配置](#代理与网络配置)
- [MCP 服务器](#mcp-服务器)
- [常见问题](#常见问题)

---

## 快速安装

### macOS（Homebrew）

```bash
brew install lightpanda-io/browser/lightpanda
```

### Linux（直接下载）

```bash
curl -L -o lightpanda https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux && \
chmod a+x ./lightpanda
```

> ARM64 Linux 也支持，Nightly 发布页有对应二进制。

### Docker

```bash
docker run -d --name lightpanda -p 127.0.0.1:9222:9222 lightpanda/browser:nightly
```

### 验证安装

```bash
lightpanda version
# 输出示例：1.0.0-nightly.6490+f07eb3e2
```

---

## 基本用法：抓取网页

### 最简单的抓取

```bash
lightpanda fetch --dump markdown https://example.com
```

### 抓取为 HTML

```bash
lightpanda fetch --dump html https://example.com
```

### 等待页面加载完成后再抓取

```bash
# 等待网络空闲（推荐）
lightpanda fetch --dump markdown --wait-until networkidle https://example.com

# 等待指定元素出现
lightpanda fetch --dump markdown --wait-selector ".content" https://example.com

# 等待固定时长（毫秒）
lightpanda fetch --dump markdown --wait-ms 8000 https://example.com

# 等待 JS 表达式返回真值
lightpanda fetch --dump markdown --wait-script "document.querySelectorAll('.item').length > 5" https://example.com
```

### 控制日志输出

```bash
# 级别：debug | info | warn | error | fatal
lightpanda fetch --dump markdown --log-level warn https://example.com

# 更可读的日志格式
lightpanda fetch --dump markdown --log-format pretty --log-level info https://example.com
```

---

## 输出格式

Lightpanda 支持四种输出模式：

| 模式 | 说明 | 用途 |
|:---|:---|:---|
| `html` | 序列化 DOM 的 HTML | 标准抓取、存储网页 |
| `markdown` | 内容转为 Markdown | LLM 消费、文档处理 |
| `semantic_tree` | JSON 格式的语义树 | 结构化数据提取 |
| `semantic_tree_text` | 精简纯文本语义树 | 快速分析、摘要 |

### JSON 模式（携带元数据）

```bash
lightpanda fetch --dump markdown --json https://example.com
```

输出示例：

```json
{
  "status": 200,
  "url": "https://example.com",
  "content": "# ... markdown content ..."
}
```

### 按标签组剥离内容

```bash
# 移除所有脚本
lightpanda fetch --dump markdown --strip-mode js https://example.com

# 移除图片、视频、CSS、SVG 等 UI 元素
lightpanda fetch --dump markdown --strip-mode ui https://example.com

# 全部剥离
lightpanda fetch --dump markdown --strip-mode full https://example.com
```

---

## CDP 服务器模式

启动 Lightpanda 的 Chrome DevTools Protocol (CDP) 服务器：

```bash
lightpanda serve --host 127.0.0.1 --port 9222
```

验证服务是否正常：

```bash
curl http://127.0.0.1:9222/json/version
# 返回：{"Browser": "Lightpanda/1.0", "Protocol-Version": "1.3", ...}
```

常用启动参数：

```bash
# 遵守 robots.txt
lightpanda serve --obey-robots --host 127.0.0.1 --port 9222

# 开启外部样式表（影响 visibility 等 CSS 计算）
lightpanda serve --enable-external-stylesheets --host 127.0.0.1 --port 9222

# 禁用子框架和 Web Worker
lightpanda serve --disable-subframes --disable-workers --host 127.0.0.1 --port 9222
```

---

## 与 Puppeteer/Playwright 集成

Lightpanda 兼容 Chrome DevTools Protocol，只需将 `browserWSEndpoint` 指向 Lightpanda 即可。

### Puppeteer 示例

```bash
npm install puppeteer-core
```

```javascript
import puppeteer from 'puppeteer-core';

// 连接 Lightpanda CDP 服务
const browser = await puppeteer.connect({
  browserWSEndpoint: "ws://127.0.0.1:9222",
});

const context = await browser.createBrowserContext();
const page = await context.newPage();

await page.goto('https://example.com', { waitUntil: "networkidle0" });

const links = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('a')).map(row => 
    row.getAttribute('href')
  );
});

console.log(links);

await page.close();
await context.close();
await browser.disconnect();
```

### Playwright 示例

```bash
npm install playwright-core
```

```javascript
import { chromium } from 'playwright-core';

const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
const page = await browser.newPage();
await page.goto('https://example.com');
console.log(await page.title());
await browser.close();
```

### 支持的核心 CDP 能力

| 功能 | 支持 |
|:---|:---:|
| 页面导航 (`goto`) | ✅ |
| DOM 查询 (`querySelector`) | ✅ |
| JS 执行 (`evaluate`) | ✅ |
| 点击 (`click`) | ✅ |
| 表单输入 (`type`) | ✅ |
| Cookie 管理 | ✅ |
| 网络拦截 | ✅ |
| 截图（有头模式） | ❌ （纯 headless，无渲染管线） |

> ⚠️ Lightpanda 没有图形渲染引擎，所以 `page.screenshot()` 等绘图 API 不可用。

---

## 注入脚本

在页面 `<head>` 解析之前注入 JavaScript，可用于修改全局行为或绕过简单检测：

```bash
# 注入单行脚本
lightpanda fetch --dump markdown \
  --inject-script 'navigator.__defineGetter__("webdriver",()=>false)' \
  https://example.com

# 注入多行脚本（可重复使用 --inject-script）
lightpanda fetch --dump markdown \
  --inject-script 'Object.defineProperty(navigator,"getBattery",{value:()=>Promise.resolve({level:1,charging:true})})' \
  https://example.com
```

从文件读取脚本：

```bash
lightpanda fetch --dump markdown \
  --inject-script-file ./bypass.js \
  https://example.com
```

---

## Cookie 管理

### 保存 Cookie（请求后导出）

```bash
lightpanda fetch --dump markdown \
  --cookie-jar ./cookies.json \
  https://example.com
```

### 加载 Cookie（复用之前保存的）

```bash
lightpanda fetch --dump markdown \
  --cookie ./cookies.json \
  https://example.com
```

### 结合使用（维持会话）

```bash
# 第一次：抓取并保存 cookie
lightpanda fetch --dump html \
  --cookie-jar ./session.json \
  --wait-ms 10000 \
  https://teacher.bupt.edu.cn/zhaochen/zh_CN/index.htm

# 第二次：携带 cookie 再次请求
lightpanda fetch --dump html \
  --cookie ./session.json \
  --cookie-jar ./session.json \
  https://teacher.bupt.edu.cn/zhaochen/zh_CN/index.htm
```

Cookie 文件格式（JSON）：

```json
[
  {
    "name": "session_id",
    "value": "abc123",
    "domain": "example.com",
    "path": "/",
    "expires": 2095464787,
    "secure": true,
    "httpOnly": true,
    "sameSite": "lax"
  }
]
```

---

## 代理与网络配置

### HTTP 代理

```bash
lightpanda fetch --dump markdown \
  --http-proxy http://127.0.0.1:8080 \
  https://example.com

# 带认证的代理
lightpanda fetch --dump markdown \
  --http-proxy http://user:pass@127.0.0.1:8080 \
  https://example.com

# Bearer token 认证
lightpanda fetch --dump markdown \
  --http-proxy http://127.0.0.1:8080 \
  --proxy-bearer-token "your-token" \
  https://example.com
```

### 自定义 Headers

```bash
# 自定义 User-Agent
lightpanda fetch --dump markdown \
  --user-agent-suffix "MyBot/1.0" \
  https://example.com
```

> ⚠️ `--user-agent` 不允许包含 `Mozilla`，防止冒充真实浏览器。

### 网络控制

```bash
# 遵守 robots.txt
lightpanda fetch --dump markdown --obey-robots https://example.com

# 屏蔽私有网络请求
lightpanda fetch --dump markdown --block-private-networks https://example.com

# 自定义屏蔽 CIDR
lightpanda fetch --dump markdown \
  --block-cidrs 10.0.0.0/8,-10.0.0.42/32 \
  https://example.com

# 限制并发请求数
lightpanda fetch --dump markdown \
  --http-max-concurrent 5 \
  --http-max-host-open 2 \
  https://example.com

# 限制超时
lightpanda fetch --dump markdown \
  --http-timeout 15000 \
  https://example.com
```

---

## 禁用遥测

Lightpanda 默认会收集使用统计。可通过环境变量关闭：

```bash
LIGHTPANDA_DISABLE_TELEMETRY=true lightpanda fetch --dump markdown https://example.com
```

---

## 性能与基准

官方基准（AWS EC2 m5.large，933 个真实网页）：

| 指标 | Lightpanda | Headless Chrome | 差距 |
|:---|:---|:---|:---:|
| 内存峰值（100 页） | **123 MB** | 2 GB | ≈ 1/16 |
| 执行时间（100 页） | **5 s** | 46 s | ≈ 9x 快 |

适用场景：
- ✅ 大规模爬虫和数据采集
- ✅ AI Agent 的网页内容提取
- ✅ 自动化测试（无截图需求）
- ✅ CI/CD 流水线中的轻量浏览器环境
- ❌ 需要页面截图/PDF 渲染
- ❌ 对付高强度反爬 JS Challenge

---

## 常见问题

### Q: Lightpanda 支持截图吗？

不支持。Lightpanda 是纯无头浏览器，没有图形渲染管线。如果需要截图，请使用 Chromium headless 或其他方案。

### Q: 为什么某些页面返回空内容？

可能的原因：
1. **反爬 JS Challenge** — 页面通过 Cloudflare、阿里云 WAF 等验证浏览器真实性，Lightpanda 可能因缺少某些 Web API 被识别为机器人
2. **页面需要特定 Cookie** — 尝试使用 `--cookie-jar` 和 `--cookie` 维持会话
3. **JS 渲染超时** — 尝试增加 `--wait-ms` 或使用 `--wait-until networkidle`

### Q: 如何调试页面加载过程？

```bash
lightpanda fetch --dump html --log-level debug https://example.com 2>&1 | grep -E "not_implemented|error|navigate"
```

### Q: 和 Chromium headless 比有什么优缺点？

| | Lightpanda | Chromium Headless |
|:---|:---|:---|
| **体积** | ~66 MB | ~300+ MB |
| **启动速度** | 毫秒级 | 秒级 |
| **内存占用** | 极低 | 高 |
| **渲染/截图** | ❌ | ✅ |
| **JS 覆盖率** | 持续增长中 | 完整 |
| **反爬对抗** | 较弱 | 强 |
| **CDP 兼容** | 核心 API 可用 | 完整 |

### Q: 需要安装什么依赖？

- macOS：无需额外依赖，Homebrew 即可
- Linux：需要 `glibc`（不支持 musl/Alpine），以及常规构建工具
- 构建依赖：Zig 0.15.2、V8、Libcurl、html5ever（Rust）

---

## 参考链接

- [GitHub 仓库](https://github.com/lightpanda-io/browser)
- [官网](https://lightpanda.io)
- [官方文档](https://lightpanda.io/docs)
- [Demo 与基准测试](https://github.com/lightpanda-io/demo)
- [性能基准详情](https://github.com/lightpanda-io/demo/blob/main/BENCHMARKS.md)