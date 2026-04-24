#!/usr/bin/env python3
"""
Sogou-based WeChat article search (HTML scrape).

Modes
  article       -- search articles by keyword (type=2)
  gzh           -- search official accounts by name (type=1)
  gzh_history   -- best-effort: search account, then list its recent articles

Usage
  python scripts/sogou_search.py "AI 教育"
  python scripts/sogou_search.py "AI 教育" --start 20260101 --end 20260401
  python scripts/sogou_search.py "人民日报" --mode gzh
  python scripts/sogou_search.py "人民日报" --mode gzh_history --max 10
  python scripts/sogou_search.py "AI" --page 2 --max 20 -o results.json

Output
  JSON to stdout, or to -o <file>. Logs to stderr.

Etiquette
  - 1s sleep between requests (already baked in)
  - rotates among 3 UA strings
  - date filter is client-side (Sogou's API does not filter reliably)
  - do NOT loop pages aggressively; this tool is for research
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    sys.stderr.write(
        f"Missing dependency: {e}. Install with:\n"
        f"  pip install requests beautifulsoup4\n"
    )
    sys.exit(2)


BASE_URL = "https://weixin.sogou.com/weixin"
TIMEOUT = 15
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]


class _UA:
    def __init__(self):
        self.i = 0

    def headers(self):
        ua = USER_AGENTS[self.i % len(USER_AGENTS)]
        self.i += 1
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }


def _date_to_ts(s: str, end: bool = False) -> int | None:
    try:
        dt = datetime.strptime(s, "%Y%m%d")
        if end:
            dt = dt.replace(hour=23, minute=59, second=59)
        return int(dt.timestamp())
    except ValueError:
        sys.stderr.write(f"warn: invalid date {s!r} (expected YYYYMMDD)\n")
        return None


def search_article(query: str, page: int, max_results: int,
                   start_date: str | None, end_date: str | None,
                   ua: _UA) -> list[dict]:
    url = f"{BASE_URL}?type=2&query={quote(query)}&page={page}"
    sys.stderr.write(f"GET {url}\n")
    resp = requests.get(url, headers=ua.headers(), timeout=TIMEOUT)
    resp.encoding = "utf-8"
    time.sleep(1)
    if resp.status_code != 200:
        sys.stderr.write(f"warn: HTTP {resp.status_code}\n")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.find_all("div", class_="txt-box")

    out: list[dict] = []
    for item in items[:max_results]:
        try:
            h3 = item.find("h3")
            if not h3 or not h3.find("a"):
                continue
            a = h3.find("a")
            title = a.get_text(strip=True)
            link = a.get("href", "")

            p = item.find("p", class_="txt-info")
            abstract = p.get_text(strip=True) if p else ""

            gzh_name = ""
            ts = int(time.time())
            s_p = item.find("div", class_="s-p")
            if s_p:
                span = s_p.find("span", class_="all-time-y2")
                if span:
                    gzh_name = span.get_text(strip=True)
                script = s_p.find("script")
                if script:
                    m = re.search(r"timeConvert\('(\d+)'\)", script.get_text())
                    if m:
                        ts = int(m.group(1))

            out.append({
                "type": "article",
                "title": title,
                "url": link,
                "abstract": abstract,
                "gzh_name": gzh_name,
                "published_at": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                "timestamp": ts,
            })
        except Exception as e:
            sys.stderr.write(f"debug: parse item failed: {e}\n")

    # Client-side date filter
    start_ts = _date_to_ts(start_date) if start_date else None
    end_ts = _date_to_ts(end_date, end=True) if end_date else None
    if start_ts is not None or end_ts is not None:
        before = len(out)
        out = [
            r for r in out
            if (start_ts is None or r["timestamp"] >= start_ts)
            and (end_ts is None or r["timestamp"] <= end_ts)
        ]
        sys.stderr.write(f"date filter: {before} -> {len(out)}\n")

    out.sort(key=lambda r: r["timestamp"], reverse=True)
    return out


def search_gzh(query: str, page: int, max_results: int, ua: _UA) -> list[dict]:
    url = f"{BASE_URL}?type=1&query={quote(query)}&page={page}"
    sys.stderr.write(f"GET {url}\n")
    resp = requests.get(url, headers=ua.headers(), timeout=TIMEOUT)
    resp.encoding = "utf-8"
    time.sleep(1)
    if resp.status_code != 200:
        sys.stderr.write(f"warn: HTTP {resp.status_code}\n")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.find_all("div", class_="txt-box")

    out: list[dict] = []
    for item in items[:max_results]:
        try:
            h3 = item.find("h3")
            if not h3 or not h3.find("a"):
                continue
            a = h3.find("a")
            name = a.get_text(strip=True)
            profile_url = a.get("href", "")
            p = item.find("p", class_="txt-box")
            intro = p.get_text(strip=True) if p else ""
            out.append({
                "type": "gzh",
                "name": name,
                "profile_url": profile_url,
                "intro": intro,
            })
        except Exception as e:
            sys.stderr.write(f"debug: parse item failed: {e}\n")
    return out


def gzh_history(query: str, max_results: int, ua: _UA) -> dict:
    gzh_list = search_gzh(query, 1, 1, ua)
    if not gzh_list:
        return {"error": f"gzh not found: {query}"}
    articles = search_article(query, 1, max_results, None, None, ua)
    return {
        "type": "gzh_history",
        "gzh": gzh_list[0],
        "articles": articles,
    }


def main():
    parser = argparse.ArgumentParser(description="Sogou-based WeChat article search")
    parser.add_argument("query", help="Search keyword")
    parser.add_argument("--mode", choices=["article", "gzh", "gzh_history"], default="article")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--max", type=int, default=10, help="Max results")
    parser.add_argument("--start", help="Start date YYYYMMDD (article mode only)")
    parser.add_argument("--end", help="End date YYYYMMDD (article mode only)")
    parser.add_argument("-o", "--output", help="Write JSON to this file instead of stdout")
    args = parser.parse_args()

    ua = _UA()
    if args.mode == "article":
        result = search_article(args.query, args.page, args.max, args.start, args.end, ua)
    elif args.mode == "gzh":
        result = search_gzh(args.query, args.page, args.max, ua)
    else:
        result = gzh_history(args.query, args.max, ua)

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
        sys.stderr.write(f"wrote: {args.output}\n")
    else:
        print(payload)


if __name__ == "__main__":
    main()
