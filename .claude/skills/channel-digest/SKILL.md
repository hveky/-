---
name: channel-digest
description: 把订阅的 Telegram 频道过去 24h（昨 8:00 → 今 8:00 Asia/Shanghai）的文字消息汇总成一篇文章式日报，HTML 报刊风落盘并通过 Bot 推送给用户自己。触发词：「频道日报」「跑 tg digest」「channel digest」「telegram digest」。
---

# channel-digest

## 何时触发
用户说「频道日报 / 跑 tg digest / channel digest / telegram digest」时跑。这是一个**流程式 workflow** 任务，必须按 Step 1 → Step 8 严格顺序执行，不要跳步。

## 凭证 & 路径
- Bot 凭证路径由 `config.yaml` 的 `auth.env_file` 指定（Step 1 读取；若字段缺失回退到 `E:\01-programs\tg-cli\.env`）。**绝不把 token 打印到对话、写进 HTML、或作为命令行参数。** Python 内 `os.environ` 或读文件后用变量传递。
- `tg-cli` 已在 PATH（`tg --help` 能跑）。
- 同目录配置：`./config.yaml`（与本 skill.md 同目录）。
- 默认报告落盘：`C:\Users\Hveky\Desktop\tg-digest\YYYY-MM-DD.html`（路径可被 config 覆盖）。

---

# Thinking frame（深度思考时严格使用）

**如何处理信息？** 一个二维度的框架：信息维度、效力维度。

- **信息维度**：事实层和虚假层。他说了什么，什么没说？现实里不仅真实之物在发挥作用，虚假的东西同样影响现实。所以不仅要考量真的事实，还要考量藏在背后的权力斗争关系。初步分类：实操教程类、资源分享类、情感与生活、科普讨论。
- **效力维度**：信息、内容、文章、视频都在市场中，几乎所有内容都有内在的流量要素、内容钩子。要看它是否在影响、改变认知与决策？如果是，它是如何构建起来的？

每一条消息（或一组同源消息）都过这两层，再给一个 **0–10 的「建议阅读分」**。

---

# Workflow

## Step 1 — 读 config + 刷新

1. 读 `C:\Users\Hveky\Desktop\信息聚合\channel-digest\config.yaml`。
   - 不存在 → 用本 skill 自带的模板（见文末「config.yaml 模板」段落）创建一份，**直接停下来**告诉用户：「已生成 config.yaml，请在 `channels:` 填好要 digest 的频道名再重新触发」。不要继续往下跑。
   - 同时取 `auth.env_file`（Bot 凭证 .env 文件路径）。
2. `tg refresh --yaml`（失败不致命，记 warning 继续）。
3. 取 `config.channels`：
   - 非空 → fuzzy match，每个频道命中失败给 warning；
   - 为空 `[]` → 跑 `tg chats --type channel --yaml` 拿全部 broadcast channel。

## Step 2 — 拉 24h 消息（固定 8am→8am 窗口）

1. 用 Python 算时间窗（`zoneinfo.ZoneInfo("Asia/Shanghai")`）：
   - `until = today 08:00 +08:00`
   - `since = until - 24h`
   - 如果 `config.window.mode == "rolling_24h"`：`until = now`, `since = now - 24h`。
2. 对每个频道：`tg export "<CHAT>" --hours 24 -f json -o <tmp>/<safe_name>.json`。
3. 读每个 JSON，按 `since <= message.date < until` 二次过滤（`--hours` 是滚动窗，需要本地对齐）。

## Step 3 — 过滤垃圾（只看文字）

对每条 message 依次过：

| 规则 | 丢弃条件 |
| --- | --- |
| 互推 / 纯转发 | `forwarded_from` 存在 **且** 文本 ≤ 20 字；或命中「推荐关注 / 频道互推 / channel exchange / 互推 / 大家好我是」 |
| 广告 | 命中 `"招商"、"代理"、"USDT"、"contact @"、"投放"、"商务合作"、"承接"、"出U"、"收U"、"日入"、"被动收入"、"加我私聊"` |
| 短水贴 | 纯文字 ≤ `filter.short_text_threshold`（默认 15）字 **且** 没有 URL / 代码块 / 命中白名单 |
| 媒体水贴 | 有 media（photo/video/audio）**且** caption ≤ `filter.media_caption_threshold`（默认 30）字 |
| 系统消息 | service messages、pin 通知、加群通知等 |

`config.filter.extra_spam_keywords` 追加进广告关键词；`config.filter.extra_whitelist_keywords` 命中则**强制保留**（覆盖所有过滤）。

如果过滤后总消息数 < 5：**不写报告**，跟用户说「过去 24h 全频道有效信息不足，今日跳过」。

## Step 4 — 深度思考（主对话直接做，不开 subagent）

主对话读完所有过滤后的消息，按 Thinking frame 给每条打草稿（在 thinking 里推演，**不要落 .md 中间文件**）：
- 信息维度：分类 + 「说了什么 / 没说什么」
- 效力维度：钩子识别 + 是否在改造认知/决策
- 综合给 0–10 的「建议阅读分」

## Step 5 — 排序 + 标签

按建议阅读分 desc 排：
- **Top 3** → 「建议阅读」
- 中段 → 「可看」
- 尾段 → 「可不看」

## Step 6 — 撰写报告（文章式，不分点，**长文**）

**严格格式**：

1. **大标题**：一个有深度的、反问式的句子。例：「当所有人都在喊 AI 替代时，谁在悄悄定义下一个范式？」不要平铺直叙。
2. **副标题**：一句话点出当天的张力 / 落点。
3. **正文（长度强制 ≥ 6000 中文字符，目标 6000–8000 字）**：散文式两大段，**不要分点、不要用 bullet、不要小标题**：
   - 第一段以「**从信息维度来看**……」开头，2500–4000 字。要做到：每一条值得说的消息都点名提到（频道名+核心命题），剖析"说了什么 / 没说什么"，分类到[实操教程 / 资源分享 / 情感与生活 / 科普讨论]，并把它们彼此勾连——找出当天频道之间隐藏的共振或对照。**不能停留在概括，要落到具体内容**。
   - 第二段以「**从效力维度来看**……」开头，2500–4000 字。要做到：把每条高分内容的钩子构造、流量机制、认知改造手法拆给读者看（开头钩子、中段悬念、尾部链接、号召动作）；把"优质"和"劣质"的钩子放在一起对照；指出哪些内容是在悄悄改写读者的世界观默认值。
   - 字数不够就回去再啃消息——宁可写慢，不要写水。**最后用 `len(正文中文字符)` 自检一次，低于 6000 必须续写**。
4. **推荐阅读**：3 条。每条 = 序号 + 频道名 · 30 字内推荐理由 · 原文链接：
   - public channel：`https://t.me/<username>/<message_id>`
   - private channel（id 形如 `-100xxxxxxxxxx`）：`https://t.me/c/<id_去掉 -100>/<message_id>`
5. **其余**：一段散文（不分点），形如「另外，xxx 频道的 XX 可看，xxx 频道的 XX 可不看……」，至少覆盖 6–10 条剩余消息，每条一句话点评。

## Step 7 — 生成 HTML（报刊风）

**单文件、内联 CSS、不外链 JS**。版式要像纸质日报：

- **Masthead**：顶部全大写衬线刊名 `CHANNEL DIGEST`，下方一条 3px 粗黑实线 + 1px 细线；左下「YYYY 年 MM 月 DD 日 · 星期X · Asia/Shanghai」，右下「第 N 期 · 共 X 频道 · Y 条有效」（期号 = 距离 2026-01-01 的天数 +1）。
- **字体栈**：`'Source Han Serif SC', 'Noto Serif SC', 'Songti SC', 'STSong', Georgia, serif`。
- **大标题**：居中、48–56px、`letter-spacing: -0.02em`。
- **副标题**：居中、italic、`#555`，比大标题小 ~40%。
- **正文**：`column-count: 2; column-gap: 36px; text-align: justify; line-height: 1.85;`；首段首字 Drop-cap（`p.lede::first-letter { float: left; font-size: 3.2em; line-height: .9; padding-right: .08em; }`）。
- **引文 / 原话块**：左 3px 实线 + 米黄底 `#f5f1e8`，padding 12px 18px。
- **推荐阅读**：上下两条 1px 细线包夹的板块；每条用大号圆圈数字 ①②③，频道名粗体衬线 + 推荐理由 + 「→ 阅读原文」链接（链接色 `#8b1d1d`，hover 下划线）。
- **可看 / 可不看 尾段**：小字号 14px、`#666`。
- **页脚**：细线 + 生成时间戳 + `channel-digest v1`。
- 整体：`max-width: 880px; margin: 56px auto; background: #fafaf5; color: #1a1a1a; padding: 0 32px;`。
- 所有来自消息的原文一律 `html.escape`。

**文件名**：`<config.output_dir>\YYYY-MM-DD.html`；目录不存在就 `os.makedirs(exist_ok=True)`。

## Step 8 — Bot 推送

读 `auth.env_file`（从 Step 1 config 取到的路径；用 Python `dotenv` 或手撸 parser，只取 `BOT_TOKEN`/`BOT_CHAT_ID`），然后：

```python
import requests, pathlib
files = {"document": open(html_path, "rb")}
data = {"chat_id": chat_id,
        "caption": caption[:1024]}  # caption 用大标题，长度限制 1024
r = requests.post(f"https://api.telegram.org/bot{token}/sendDocument",
                  data=data, files=files, timeout=60)
r.raise_for_status()
```

- `config.push.enabled = false` 时只落盘不推。
- `config.push.caption_with_title = false` → caption 用 `f"频道日报 {YYYY-MM-DD}"`。
- 推送失败：保留 HTML，告知用户错误码，但不要把 token 打印出来。

---

# 安全 / 边界

- **绝不**把 `BOT_TOKEN` 打印到对话、写进 HTML、写进 git。
- HTML 渲染消息原文一律 `html.escape`。
- 私链不要泄露原始 `-100` 前缀以外的额外元信息。
- 全频道 24h 有效消息 < 5 条 → 不写报告，告诉用户跳过。
- 不抓媒体（图/视频/音频）。配了几句话的纯媒体当低信息丢掉。
- 不开 subagent，主对话直接思考。
- 不自动 cron / loop，等用户手动触发。
- 不动 `E:\01-programs\tg-cli` 仓库的任何文件。

---

# 验证（让用户跑一次完整流程）

1. `tg whoami --yaml` — 确认 MTProto session 活着
2. `tg chats --type channel --yaml | head` — 至少列出频道
3. 跑一次完整 skill，确认：
   - `<output_dir>\<today>.html` 存在、浏览器打开是报刊版式
   - Telegram 收到一份 `.html` 文档 + caption = 大标题
   - 推荐阅读链接点开能跳到对应消息

---

# config.yaml 模板（首跑时若不存在则写入同目录）

```yaml
# channel-digest 配置
# channels: 要 digest 的频道名（tg chats 里看到的 name 或 username，可模糊匹配）
#           留空 [] 表示跑全部 broadcast channel
channels: []

# 本地 HTML 落盘目录（不含文件名；文件名永远是 YYYY-MM-DD.html）
output_dir: "C:\\Users\\Hveky\\Desktop\\reports\\telegram"

# 时间窗
window:
  mode: fixed_8am   # fixed_8am | rolling_24h
  tz: "Asia/Shanghai"

# Bot 推送（凭证读 E:\01-programs\tg-cli\.env，这里只开关）
push:
  enabled: true
  caption_with_title: true

# 过滤器（在内置规则之上追加）
filter:
  extra_spam_keywords: []
  extra_whitelist_keywords: []
  short_text_threshold: 15
  media_caption_threshold: 30
```
