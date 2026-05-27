---
name: xiaoheihe-daily-digest
description: Use when the user asks for a 小黑盒/heybox community digest, says 「今日杂谈」「盒友在聊什么」「小黑盒日报」「看看小黑盒」「来份杂谈摘要」, or wants a synthesized view of what Chinese gamers on heybox 盒友杂谈 are discussing today.
---

# 小黑盒杂谈日报

## Overview

Harvest the top 60 hot posts from 小黑盒 · 盒友杂谈 (topic_id 7214), fetch each post's full body via the user's logged-in Edge browser, then synthesize a deep observation report. The CLI handles ranking; the browser handles body fetching; **you** do the analysis.

**Project root:** `C:\Users\Hveky\Desktop\xiaoheihe-cli`  
**Config:** `C:\Users\Hveky\.xhh\config.yaml`  
**CLI:** `python xhh.py <command>` (run from project root)

---

## CLI Reference

The `xhh.py` script is the data layer. All commands run from the project root:

```bash
cd /c/Users/Hveky/Desktop/xiaoheihe-cli
```

### `xhh setup` — 刷新凭证

当 API 返回 `非法请求` 时运行。需要用户从浏览器 DevTools 捕获一条 API URL。

```bash
python xhh.py setup
```

交互步骤：
1. 在 Edge 打开 `https://www.xiaoheihe.cn/community/topic/7214`（盒友杂谈）并登录
2. 打开 DevTools → Network，刷新页面，过滤 `topic/feeds`
3. 右键请求 → Copy → Copy as URL
4. 粘贴到 setup 提示中，按两次 Enter 提交

凭证保存到 `C:\Users\Hveky\.xhh\creds.json`（即 `config.yaml` 中 `auth.creds_file` 的路径）。

### `xhh harvest` — 批量抓帖子元数据（Skill 主用）

输出 JSON 到 stdout，供 Skill 读取后进行浏览器正文抓取。

```bash
python xhh.py harvest --top 60 > _today.json
# --top N    抓取最多 N 篇（默认 60）
# --topic ID 指定板块 topic_id（默认 7214 杂谈）
```

输出结构：
```json
{
  "topic_id": 7214,
  "topic_name": "盒友杂谈",
  "harvested_at": 1716500000,
  "count": 60,
  "posts": [
    {
      "linkid": 181682374,
      "title": "...",
      "user": "username",
      "awards": 42,
      "comments": 363,
      "preview": "正文前200字...",
      "url": "https://www.xiaoheihe.cn/app/bbs/link/181682374"
    }
  ]
}
```

### `xhh feed` — 快速浏览 Feed（人工用）

```bash
python xhh.py feed              # 盒友杂谈第1页（默认）
python xhh.py feed -p 2         # 第2页
python xhh.py feed --all        # 全站推荐 feed
```

输出编号列表（标题 / 作者 / 点赞 / 评论数），结果缓存到 `~/.xhh/last_feed.json`。

### `xhh open` — 在浏览器打开帖子（人工用）

```bash
python xhh.py open 3            # 打开上次 feed 中第3条
python xhh.py open 181682374    # 直接用 linkid 打开
```

---

## When NOT to use

- User asks about a specific post they already have a link to → just open it with `xhh open <linkid>`
- User wants raw data export only → call `xhh harvest` directly, skip the report step

---

## Workflow

### 0. Read config

Read project config to get paths:

```
file_path: C:\Users\Hveky\.xhh\config.yaml
```

Extract:
- `output_dir` → report save directory (fallback: `C:\Users\Hveky\Desktop\reports\xiaoheihe`)
- `auth.creds_file` → path to xhh credentials JSON (fallback: `C:\Users\Hveky\.xhh\creds.json`)

### 1. Harvest top 60 post meta

```bash
cd /c/Users/Hveky/Desktop/xiaoheihe-cli && python xhh.py harvest --top 60 > _today.json
```

Read `_today.json`. Structure: see CLI Reference → `xhh harvest` above.

If harvest errors with `non-ok status` / `非法请求`, credentials are stale (credentials read from `auth.creds_file` in config.yaml) → tell the user to run `xhh setup` following the CLI Reference steps above.

### 2. Fetch each post body via browser

For all 60 posts in the JSON:

1. Use `mcp__Claude_in_Chrome__tabs_context_mcp` if you don't have a tab yet.
2. For each post:
   - `mcp__Claude_in_Chrome__navigate` to `post.url`
   - Wait 2s for SPA render (`setTimeout` promise in `javascript_tool`)
   - Extract with this JS:
     ```js
     JSON.stringify({
       body: document.querySelector('.image-text__content')?.innerText || '',
       comments: Array.from(document.querySelectorAll('.children-item__comment-content'))
                      .slice(0, 8).map(e => e.innerText)
     })
     ```
3. Batch 3-5 navigations per `browser_batch` call to amortize round-trip cost.
4. Posts with empty `.image-text__content` are image-only — fall back to the JSON `preview` field. Note this in the report.

Expected runtime: ~2-3 minutes for 60 posts.

### 3. Write the report

#### 3a. Headline (报刊选题逻辑)

Pick the **single most newsworthy post** from the 60 — the one with the strongest hook, clearest contrast, or highest emotional resonance. Do not write a "summary headline" that tries to cover all topics. Think newspaper front page: one story leads.

Format:
```
# 主标题（反问句）
## 副标题（一句凝练的话）
```

**主标题** — A rhetorical question that captures a genuine tension or surprise from that lead post. It should feel insightful, not clickbait.
- ❌ Bad: "今日小黑盒热门话题汇总"
- ❌ Bad: "游戏宅被歧视了？"
- ✅ Good: "练出腹肌又能怎样？游戏宅就该被一票否决吗？"
- ✅ Good: "五战考研全败，然后呢？努力真的是一张保险单吗？"

**副标题** — One sentence that names the specific situation and what it reveals.
- ✅ Good: "一个 30 岁男人的失败实验，照出了这个社区最诚实的婚恋共识"

#### 3b. Three-lens body (目标 10,000+ 汉字)

Synthesize, don't summarize-each-post. **Minimum 10,000 Chinese characters total.** Each section should read like a magazine feature — concrete scenes, named actors, quoted reactions, analysis of what the pattern means.

**① 大家在讨论什么内容？** — Cluster the 60 posts into 3-6 buckets. Each bucket needs:
- A real-world phenomenon name (not a generic tag)
- 500–800 characters of analysis citing specific linkids
- What makes this cluster feel different from other days (density, angle, emotion)

- ❌ Bad: "AI 讨论（3篇）"
- ✅ Good: "DeepSeek 新模型发布后，开发者在比较 Claude Code 与 DS 的 agent 能力 (#X, #Y, #Z)——与三个月前几乎只聊 GPT 相比，这是明显的认知迁移"

**② 出现了什么能够改变认知、决策的东西？** — The report's highest-value section. Each signal needs 400–600 characters. Cover:
- **New facts**: product release, policy change, industry shift
- **Reframes**: someone articulates an old issue in a new way
- **Decision signals**: trends that should change how the user thinks/acts
- **Anti-consensus posts**: well-argued dissent

Quote the actual insight. If nothing crosses the bar today, say so — "今日 60 篇中未见明显能改变认知的内容" — don't manufacture insight.

**③ 大家反应如何？** — 2,500+ characters. Analyze:
- **Consensus posts**: what drove the monolithic reaction? What does it reveal?
- **Split posts**: where did the community divide, and along what fault line?
- **Engagement asymmetry**: high-comments/low-awards = controversy; high-awards/low-comments = silent resonance
- **3 verbatim quotes** that capture group texture better than paraphrase
- **Overall emotional temperature**: what is the dominant mood today, and why?

#### 3c. One-sentence summary (~100 characters)

End with a single sentence that captures today's underlying theme — not a list of topics, but the human reality beneath them.

Save to `<output_dir from config>\YYYY-MM-DD.md` (use today's date). Print the report inline AND tell the user the file path.

---

## Selector reference

| Element | CSS selector |
|---------|--------------|
| Post body text | `.image-text__content` |
| Top-level comments | `.children-item__comment-content` |
| Post title | `document.title` (strip ` - 小黑盒` suffix) |

---

## Common issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `harvest` returns `非法请求` | feed creds expired | run `xhh setup` (see CLI Reference above) |
| Body is empty for many posts | mostly image-only posts (expected for 杂谈) | use `preview` field as fallback |
| Browser MCP not connected | extension not running | ask user to open Edge + ensure extension active |
| Comment text contains `[cube_xxx]` | heybox emoji codes | leave as-is, or strip via regex if it hurts readability |

---

## Report quality bar

**Length**: 10,000+ Chinese characters minimum. A 2,500-character report is a skeleton, not a report.

**Headline**:
- ❌ Bad: "2026-05-20 小黑盒日报"
- ✅ Good: "练出腹肌又能怎样？游戏宅就该被一票否决吗？" + 一句副标题

**Cluster analysis**:
- ❌ Bad: "今天大家在聊找工作、玩游戏、买东西。"
- ✅ Good: "今天 60 篇里 8 篇与求职/offer 直接相关，比往常密集——尤其 #181682374 一个应届生晒了 4 个 offer 求建议，363 条评论里普遍倾向劝去稳定大厂，说明社区里的玩家心态偏保守稳健，与 B 站/小红书同期相同话题的『冲创业』调性形成对照。"

**Cognition-shifting signals**:
- ❌ Bad: "有人讨论了 AI 工具。"
- ✅ Good: 引用具体数字、具体 linkid、具体决策含义，400–600 字/条

The report's value is in **patterns and contrasts the user couldn't see by skimming alone**. The user is reading this *to update their model of the world*, not to know what's trending.
