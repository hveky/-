#!/usr/bin/env python3
"""xhh — minimal xiaoheihe (小黑盒) community reader CLI.

Commands:
  xhh setup       Paste a captured feeds URL once to seed auth params.
  xhh feed        Show the homepage feed.
  xhh feed -p 2   Show page 2 (10 items per page).
  xhh open N      Open the Nth post from the last `feed` listing in browser.
  xhh open <id>   Open a post by its linkid.

Auth strategy: replay a captured `/bbs/app/feeds` URL — the server doesn't
re-check the signature strictly on this endpoint, so one capture lasts.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

CFG_DIR = Path.home() / ".xhh"
CFG_FILE = CFG_DIR / "creds.json"
CACHE_FILE = CFG_DIR / "last_feed.json"
API_HOST = "https://api.xiaoheihe.cn"
WEB_LINK = "https://www.xiaoheihe.cn/app/bbs/link/{linkid}"

FEED_ALL = "/bbs/app/feeds"          # homepage recommended feed
FEED_TOPIC = "/bbs/app/topic/feeds"  # per-section feed (needs topic_id)
TOPIC_ZATAN = 7214                   # 盒友杂谈

# Params we strip when storing the template — they're either request-specific
# or page-state we want to override per call.
PER_CALL_PARAMS = {"offset", "pull", "dw", "topic_id", "limit", "lastval"}


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


# ---------- config ----------

def load_creds() -> dict:
    if not CFG_FILE.exists():
        die("not configured. run: xhh setup")
    data = json.loads(CFG_FILE.read_text("utf-8"))
    # Back-compat: old flat format stored params at top level (assume /bbs/app/feeds).
    if "endpoints" not in data:
        data = {"endpoints": {FEED_ALL: data}}
    return data


def save_creds(creds: dict) -> None:
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    CFG_FILE.write_text(json.dumps(creds, indent=2, ensure_ascii=False), "utf-8")


def template_for(creds: dict, path: str) -> dict:
    tpl = creds.get("endpoints", {}).get(path)
    if not tpl:
        die(f"no captured URL for {path}. run: xhh setup")
    return tpl


def cmd_setup(args: argparse.Namespace) -> None:
    print("Paste a captured API URL from DevTools → Network → Copy as URL.")
    print("Accepted endpoints:")
    print(f"  {FEED_ALL}        — homepage feed (for `xhh feed --all`)")
    print(f"  {FEED_TOPIC}  — section feed (for default `xhh feed`)")
    print("Press Enter twice to submit.")
    lines: list[str] = []
    try:
        while True:
            line = input().strip()
            if not line:
                break
            lines.append(line)
    except EOFError:
        pass
    url = "".join(lines).strip()
    if not url:
        die("no url provided")

    parsed = urllib.parse.urlparse(url)
    if parsed.path not in (FEED_ALL, FEED_TOPIC):
        die(f"url path {parsed.path!r} is not a supported endpoint")
    qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    template = {k: v[0] for k, v in qs.items() if k not in PER_CALL_PARAMS}

    creds = json.loads(CFG_FILE.read_text("utf-8")) if CFG_FILE.exists() else {}
    if "endpoints" not in creds:
        creds = {"endpoints": {FEED_ALL: creds} if creds else {}}
    creds["endpoints"][parsed.path] = template
    save_creds(creds)

    print(f"saved {parsed.path} → {len(template)} params to {CFG_FILE}")
    print(f"   heybox_id={template.get('heybox_id', '?')}")


# ---------- http ----------

def http_get_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (xhh-cli)",
            "Referer": "https://www.xiaoheihe.cn/",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        die(f"http {e.code}: {e.read().decode('utf-8', 'replace')[:200]}")
    except Exception as e:
        die(f"network: {type(e).__name__}: {e}")


def build_feed_url(path: str, template: dict, offset: int, topic_id: int | None) -> str:
    params = dict(template)
    params["offset"] = str(offset)
    params["dw"] = params.get("dw", "602")
    if path == FEED_ALL:
        params["pull"] = "0"
    if path == FEED_TOPIC:
        if topic_id is None:
            die("topic feed requires --topic")
        params["topic_id"] = str(topic_id)
        params["limit"] = "10"
        params["lastval"] = ""
    return f"{API_HOST}{path}?" + urllib.parse.urlencode(params)


# ---------- commands ----------

def cmd_feed(args: argparse.Namespace) -> None:
    creds = load_creds()
    if args.all:
        path, topic_id = FEED_ALL, None
    else:
        path, topic_id = FEED_TOPIC, args.topic
    tpl = template_for(creds, path)
    offset = max(0, (args.page - 1) * 10)
    url = build_feed_url(path, tpl, offset, topic_id)
    data = http_get_json(url)
    if data.get("status") != "ok":
        die(f"api: status={data.get('status')} msg={data.get('msg')}")
    links = data.get("result", {}).get("links", [])
    if not links:
        die("no posts returned")

    rows: list[dict] = []
    for i, l in enumerate(links, 1):
        title = (l.get("title") or "").strip()
        if not title:
            title = (l.get("description") or "").strip().replace("\n", " ")
        title = title[:60] + ("…" if len(title) > 60 else "")
        user = (l.get("user") or {}).get("username") or "?"
        topics = l.get("topics") or []
        tag = topics[0]["name"] if topics else ""
        rows.append({
            "i": i,
            "linkid": l.get("linkid"),
            "title": title,
            "user": user,
            "tag": tag,
            "up": l.get("link_award_num", 0),
            "cmt": l.get("comment_num", 0),
        })

    CFG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(rows, ensure_ascii=False), "utf-8")

    section = "全站推荐" if args.all else f"盒友杂谈" if topic_id == TOPIC_ZATAN else f"topic#{topic_id}"
    print(f"小黑盒 · {section}  page {args.page}  (offset {offset})")
    print("─" * 72)
    for r in rows:
        head = f"[{r['i']:>2}] {r['title']}"
        meta = f"     @{r['user']}  ▲{r['up']}  💬{r['cmt']}"
        if r["tag"]:
            meta += f"  #{r['tag']}"
        print(head)
        print(meta)
    print("─" * 72)
    print("open with:  xhh open <N>   (or: xhh open <linkid>)")


def cmd_harvest(args: argparse.Namespace) -> None:
    """Print JSON of top-N hot posts. Designed for skill/agent consumption."""
    creds = load_creds()
    tpl = template_for(creds, FEED_TOPIC)
    want = args.top
    seen: set[int] = set()
    posts: list[dict] = []
    offset = 0
    safety = 30
    while len(posts) < want and safety > 0:
        safety -= 1
        url = build_feed_url(FEED_TOPIC, tpl, offset, args.topic)
        data = http_get_json(url)
        if data.get("status") != "ok":
            die(f"api: {data.get('status')} {data.get('msg')}")
        links = data.get("result", {}).get("links", [])
        if not links:
            break
        for l in links:
            lid = l.get("linkid")
            if not lid or lid in seen:
                continue
            topics = l.get("topics") or []
            if not any(t.get("topic_id") == args.topic for t in topics):
                continue  # skip ads/cross-promo
            seen.add(lid)
            posts.append({
                "linkid": lid,
                "title": (l.get("title") or "").strip()
                         or (l.get("description") or "").strip().replace("\n", " ")[:80],
                "user": (l.get("user") or {}).get("username", "?"),
                "userid": l.get("userid"),
                "topic": (topics[0].get("name") if topics else ""),
                "awards": l.get("link_award_num", 0),
                "comments": l.get("comment_num", 0),
                "down": l.get("down", 0),
                "create_at": l.get("create_at"),
                "preview": (l.get("description") or "").strip().replace("\n", " ")[:200],
                "url": WEB_LINK.format(linkid=lid),
            })
            if len(posts) >= want:
                break
        offset += 10
    print(json.dumps({
        "topic_id": args.topic,
        "topic_name": "盒友杂谈" if args.topic == TOPIC_ZATAN else f"topic#{args.topic}",
        "harvested_at": int(time.time()),
        "count": len(posts),
        "posts": posts,
    }, ensure_ascii=False, indent=2))


def cmd_open(args: argparse.Namespace) -> None:
    target = args.target
    linkid: int | None = None
    # numeric short → index into cache; long → linkid
    if re.fullmatch(r"\d+", target):
        n = int(target)
        if n < 1000 and CACHE_FILE.exists():
            rows = json.loads(CACHE_FILE.read_text("utf-8"))
            for r in rows:
                if r["i"] == n:
                    linkid = r["linkid"]
                    break
            if linkid is None:
                die(f"no item #{n} in last feed (have 1..{len(rows)})")
        else:
            linkid = n
    if linkid is None:
        die("target must be index or linkid")
    url = WEB_LINK.format(linkid=linkid)
    print(f"opening {url}")
    webbrowser.open(url)


# ---------- main ----------

def main() -> None:
    p = argparse.ArgumentParser(prog="xhh", description="小黑盒社区 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("setup", help="paste a captured feeds URL")
    sp.set_defaults(func=cmd_setup)

    sp = sub.add_parser("feed", help="show feed (defaults to 盒友杂谈)")
    sp.add_argument("-p", "--page", type=int, default=1, help="page number (10/page)")
    sp.add_argument("--all", action="store_true", help="homepage all-section feed")
    sp.add_argument("--topic", type=int, default=TOPIC_ZATAN, help="topic_id (default: 7214 杂谈)")
    sp.set_defaults(func=cmd_feed)

    sp = sub.add_parser("harvest", help="emit JSON of top-N hot posts (for skill use)")
    sp.add_argument("--top", type=int, default=60, help="how many posts to collect")
    sp.add_argument("--topic", type=int, default=TOPIC_ZATAN, help="topic_id")
    sp.set_defaults(func=cmd_harvest)

    sp = sub.add_parser("open", help="open a post in your browser")
    sp.add_argument("target", help="index from last feed (e.g. 3) or linkid")
    sp.set_defaults(func=cmd_open)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
