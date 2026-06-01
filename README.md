<div align="center">

# 📡 InfoDigest · 信息聚合

### 你的个人情报官——一句话，把论坛 / 社区 / 频道的今日声音读成一份报告

把 **LinuxDo 论坛**、**小黑盒盒友杂谈**、**Telegram 频道** 过去 24 小时的海量信息，
自动读取 → 分类 → 按「建议阅读分」筛选 → 合成一篇有观点的深度日报。

[English](README_EN.md) · 中文

[![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)](#-环境要求)
[![Claude Code Skills](https://img.shields.io/badge/Claude%20Code-Skills-D97757)](#-它由什么组成)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows)](#-环境要求)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

> 📝 **关于项目名**：仓库此前未正式命名。基于它的定位，推荐使用 **InfoDigest（中文：信息聚合）**。
> 备选：`SignalHub`（信号枢纽）/ `DigestKit`（摘要箱）。下文以 InfoDigest 行文，最终以你的选择为准。

---

## 信息太多，时间太少

每天 LinuxDo 有几百条新帖，小黑盒杂谈区热度滚动，关注的 Telegram 频道还在不停推送。
全部刷完不现实，但只看标题又会错过真正有价值的内容。

**InfoDigest 替你读完，然后只把值得读的，连同「为什么值得读」，写成一份日报交给你。**

它不是简单的关键词抓取。每一条信息都会过一套二维思考框架，再给出 **0–10 的建议阅读分**：

- **信息维度** —— 它说了什么、又刻意没说什么？是实操教程、资源分享、情感生活，还是科普讨论？
- **效力维度** —— 它的流量钩子是什么？它在试图影响你的认知与决策吗？是如何构建起来的？

## 🧩 它由什么组成

InfoDigest 是一组协同工作的 **Claude Code Skills** + 一个数据层 CLI：

| 模块 | 来源平台 | 做什么 | 触发词 |
| --- | --- | --- | --- |
| **forum-research** | LinuxDo（及任意论坛） | 连接已登录浏览器，读新帖+评论，按回复数排序，分类后写结构化调研报告 | 「帮我看看 linuxdo 今天有什么」「社区调研」 |
| **xiaoheihe-daily-digest** | 小黑盒 · 盒友杂谈 | 抓取热门 Top 60，取正文，合成「今日杂谈」深度观察报告 | 「小黑盒日报」「盒友在聊什么」 |
| **channel-digest** | Telegram 频道 | 汇总订阅频道近 24h 文字消息，落盘报刊风 HTML 并由 Bot 推送给你自己 | 「频道日报」「跑 tg digest」 |
| **`xiaoheihe-cli/xhh.py`** | 小黑盒 | 数据层 CLI，负责小黑盒抓取与排序、凭证管理 | `python xhh.py <command>` |

## ✨ 亮点

- 🧠 **有观点，不止聚合** —— 内置「信息维度 × 效力维度」思考框架 + 0–10 建议阅读分，帮你筛掉噪音。
- 🌐 **三端覆盖** —— 论坛、游戏社区、即时频道，一套工具读三类信息源。
- 🔐 **借你自己的登录态** —— 通过你已登录的浏览器读取（论坛会反爬，纯 fetch 会被拦），数据不经第三方。
- 📰 **报刊风日报** —— Telegram 日报落盘为 HTML 报刊样式，并经 Bot 推送，随时回看。
- 🗣️ **对话式触发** —— 一句中文自然语言即可跑，无需记命令。

## 🚀 快速上手

> InfoDigest 以 Claude Code Skills 形式运行，需先具备运行环境。

1. **准备环境**（见下方[环境要求](#-环境要求)）：Claude Code、Python 3、登录态浏览器、`tg-cli`。
2. **配置中央 config**：复制 `.claude/config.yaml.example` 为 `.claude/config.yaml`，填好各模块的频道列表、输出目录、Bot 凭证路径等。
3. **在 Claude Code 里自然语言触发**：

   ```text
   帮我看看 linuxdo 今天有什么      # → forum-research
   来份小黑盒日报                    # → xiaoheihe-daily-digest
   跑 tg digest                      # → channel-digest
   ```

4. 小黑盒凭证过期时，运行 `python xiaoheihe-cli/xhh.py setup` 按提示从浏览器 DevTools 重新捕获即可。

## 🔧 环境要求

- **Claude Code**（Skills 运行宿主）
- **Python 3**（`xhh.py` 数据层，零第三方依赖）
- **已登录的浏览器**（论坛/小黑盒正文抓取依赖你的登录态，配合 Claude-in-Chrome 扩展）
- **`tg-cli`** 已在 PATH（Telegram 频道读取与推送）
- **Telegram Bot** 凭证（仅推送给你自己；凭证只存在本地 `.env`，绝不写入对话或报告）

> 🔒 安全：所有凭证仅在本地读取、以变量传递，不会被打印到对话、写进 HTML 或作为命令行参数暴露。

## ⚙️ 配置

中央配置位于 `.claude/config.yaml`，按模块分节（`channel_digest:` / `xiaoheihe:` 等）。
参考仓库根目录的 `.claude/config.yaml.example` 创建你自己的版本。

## 🗺️ Roadmap

- [ ] 更多信息源（RSS / 微博 / X）
- [ ] 跨平台（macOS / Linux）适配
- [ ] 日报合并视图（三端汇总为一份）

## 📄 License

[MIT](LICENSE)
