#!/usr/bin/env python3
"""
Upload a generated article to WeChat Official Account draft box.

Inputs
  - <article_dir>: a directory under output/公众号/ containing:
      - meta.json        (title / summary / author / cover_image / theme / ...)
      - *.html           (rendered body; if absent, will render <title>.md via md2html.py)
      - *.md             (source; used only if html is missing)
      - cover image      (meta.cover_image, path relative to article_dir)
      - images/*         (inline images referenced by <img src="images/...">)

Env (priority: CLI flag > process env > skill-root .env)
  - WECHAT_APP_ID
  - WECHAT_APP_SECRET
  - WECHAT_DEFAULT_AUTHOR (optional; overridden by meta.author)

Output (stdout, JSON)
  {
    "status": "success" | "error",
    "media_id": "...",                # draft id on success
    "thumb_media_id": "...",
    "image_count": N,
    "title": "...",
    "errmsg": "..."                   # only on error
  }

Usage
  python scripts/wechat_publish.py <article_dir>
  python scripts/wechat_publish.py <article_dir> --theme 橙心
  python scripts/wechat_publish.py <article_dir> --appid wx... --secret ...
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib import parse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    sys.stderr.write(
        f"Missing dependency: {e}. Install with:\n"
        f"  pip install requests beautifulsoup4\n"
    )
    sys.exit(2)

try:
    from PIL import Image
    from io import BytesIO
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
API_BASE = "https://api.weixin.qq.com/cgi-bin"


def load_env():
    """Load skill-root .env (best-effort; no hard dep on python-dotenv)."""
    env_file = SKILL_ROOT / ".env"
    if not env_file.exists():
        return
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)
    except Exception as e:
        sys.stderr.write(f"warn: failed to read {env_file}: {e}\n")


def get_access_token(appid: str, secret: str) -> str:
    qs = parse.urlencode({
        "grant_type": "client_credential",
        "appid": appid,
        "secret": secret,
    })
    url = f"{API_BASE}/token?{qs}"
    resp = requests.get(url, timeout=15)
    obj = resp.json()
    if "access_token" not in obj:
        raise RuntimeError(f"get_access_token failed: {obj}")
    return obj["access_token"]


def upload_permanent_image(path: Path, access_token: str) -> str:
    """Upload cover image as permanent material, return media_id."""
    url = f"{API_BASE}/material/add_material?access_token={access_token}&type=image"
    ext = path.suffix.lower().lstrip(".") or "jpg"
    if ext == "jpeg":
        ext = "jpg"
    mime = f"image/{'jpeg' if ext == 'jpg' else ext}"
    with path.open("rb") as f:
        files = {"media": (f"cover.{ext}", f, mime)}
        resp = requests.post(url, files=files, timeout=30)
    obj = resp.json()
    if "media_id" not in obj:
        raise RuntimeError(f"upload cover failed: {obj}")
    return obj["media_id"]


def upload_inline_image(src: str, access_token: str, base_dir: Path):
    """Upload one body image, return WeChat CDN URL or None."""
    url = f"{API_BASE}/media/uploadimg?access_token={access_token}"

    if src.startswith(("http://", "https://")):
        try:
            r = requests.get(src, timeout=30)
            r.raise_for_status()
            content = r.content
            name_guess = Path(parse.urlparse(src).path).name or "img.jpg"
        except Exception as e:
            sys.stderr.write(f"warn: download {src} failed: {e}\n")
            return None
    else:
        local = (base_dir / src).resolve()
        if not local.exists():
            sys.stderr.write(f"warn: local image not found: {local}\n")
            return None
        content = local.read_bytes()
        name_guess = local.name

    ext = Path(name_guess).suffix.lower().lstrip(".") or "jpg"
    if ext == "jpeg":
        ext = "jpg"

    def _post(data, filename, mime):
        try:
            r = requests.post(url, files={"media": (filename, data, mime)}, timeout=30)
            return r.json().get("url")
        except Exception as e:
            sys.stderr.write(f"warn: uploadimg failed ({mime}): {e}\n")
            return None

    mime = "image/png" if ext == "png" else "image/jpeg"
    result = _post(content, name_guess, mime)
    if result:
        return result

    if not HAS_PIL:
        return None
    try:
        img = Image.open(BytesIO(content))
        buf = BytesIO()
        if ext == "png":
            img.convert("RGB").save(buf, "JPEG")
            return _post(buf.getvalue(), Path(name_guess).stem + ".jpg", "image/jpeg")
        else:
            img.save(buf, "PNG")
            return _post(buf.getvalue(), Path(name_guess).stem + ".png", "image/png")
    except Exception as e:
        sys.stderr.write(f"warn: PIL fallback failed: {e}\n")
        return None


def create_draft(access_token: str, article: dict) -> str:
    url = f"{API_BASE}/draft/add?access_token={access_token}"
    data = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    resp = requests.post(
        url, data=data,
        headers={"Content-Type": "application/json; charset=utf-8"}, timeout=30,
    )
    obj = resp.json()
    if "media_id" not in obj:
        raise RuntimeError(f"draft/add failed: {obj}")
    return obj["media_id"]


def sanitize_html(html: str) -> str:
    """Strip whitespace around <ol>/<li> tags (WeChat editor corrupts them)."""
    html = re.sub(r"\s*(<ol>)\s*", r"\1", html)
    html = re.sub(r"\s*(<li>)\s*", r"\1", html)
    html = re.sub(r"\s*(</li>)\s*", r"\1", html)
    html = re.sub(r"\s*(</ol>)\s*", r"\1", html)
    return html


def rewrite_body_images(html: str, access_token: str, base_dir: Path):
    soup = BeautifulSoup(html, "html.parser")
    imgs = soup.find_all("img")
    ok = 0
    for idx, img in enumerate(imgs, 1):
        src = (img.get("src") or "").strip()
        if not src:
            continue
        if src.startswith("https://mmbiz.qpic.cn"):
            ok += 1
            continue
        cdn = upload_inline_image(src, access_token, base_dir)
        if cdn:
            img["src"] = cdn
            ok += 1
            sys.stderr.write(f"  [{idx}/{len(imgs)}] {src} -> {cdn[:60]}...\n")
        else:
            img["src"] = ""
            sys.stderr.write(f"  [{idx}/{len(imgs)}] {src} -> FAILED (cleared)\n")
        time.sleep(0.3)
    return str(soup), ok


def find_html(article_dir: Path, meta: dict):
    title = meta.get("title", "")
    theme = meta.get("theme", "")
    candidates = []
    if title and theme:
        candidates.append(article_dir / f"{title}_{theme}.html")
    if title:
        candidates.append(article_dir / f"{title}.html")
    for c in candidates:
        if c.exists():
            return c
    htmls = sorted(article_dir.glob("*.html"))
    return htmls[0] if htmls else None


def render_md_if_needed(article_dir: Path, meta: dict, theme: str) -> Path:
    title = meta.get("title", "")
    md_path = article_dir / f"{title}.md"
    if not md_path.exists():
        mds = sorted(article_dir.glob("*.md"))
        if not mds:
            raise FileNotFoundError(f"no .md or .html in {article_dir}")
        md_path = mds[0]
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        import md2html  # type: ignore
    finally:
        sys.path.pop(0)
    html = md2html.md_to_html(md_path.read_text(encoding="utf-8"), theme=theme)
    out = article_dir / f"{md_path.stem}_{theme}.html"
    out.write_text(html, encoding="utf-8")
    sys.stderr.write(f"rendered: {out}\n")
    return out


def resolve_cover(article_dir: Path, meta: dict) -> Path:
    cover_rel = meta.get("cover_image")
    if cover_rel:
        p = (article_dir / cover_rel).resolve()
        if p.exists():
            return p
    for name in ("cover.jpg", "cover.png", f"{meta.get('title','')}_cover.jpg"):
        p = article_dir / name
        if p.exists():
            return p
    raise FileNotFoundError(
        f"cover image not found in {article_dir}. Set meta.cover_image or place cover.jpg."
    )


def main():
    parser = argparse.ArgumentParser(description="Upload article to WeChat Official Account draft box")
    parser.add_argument("article_dir", help="Article directory under output/公众号/")
    parser.add_argument("--appid", help="WeChat AppID (overrides env)")
    parser.add_argument("--secret", help="WeChat AppSecret (overrides env)")
    parser.add_argument("--author", help="Author (overrides meta and env)")
    parser.add_argument("--theme", help="mdnice theme name if html must be rendered from md")
    parser.add_argument("--dry-run", action="store_true", help="Validate + render without uploading")
    args = parser.parse_args()

    load_env()

    art_dir = Path(args.article_dir).resolve()
    if not art_dir.is_dir():
        sys.exit(f"not a directory: {art_dir}")

    meta_file = art_dir / "meta.json"
    if not meta_file.exists():
        sys.exit(f"missing meta.json in {art_dir}")
    meta = json.loads(meta_file.read_text(encoding="utf-8"))

    title = (meta.get("title") or "").strip()
    summary = (meta.get("summary") or "").strip()
    if not title:
        sys.exit("meta.title is empty")
    if len(title) > 64:
        sys.stderr.write("warn: title >64 chars, truncating\n")
        title = title[:63]
    if len(summary) > 120:
        sys.stderr.write("warn: summary >120 chars, truncating\n")
        summary = summary[:119]

    author = args.author or meta.get("author") or os.environ.get("WECHAT_DEFAULT_AUTHOR", "")
    theme = args.theme or meta.get("theme") or "橙心"

    html_path = find_html(art_dir, meta)
    if not html_path:
        html_path = render_md_if_needed(art_dir, meta, theme)
    html_src = html_path.read_text(encoding="utf-8")

    cover_path = resolve_cover(art_dir, meta)

    sys.stderr.write(f"== article_dir: {art_dir}\n")
    sys.stderr.write(f"   title:       {title}\n")
    sys.stderr.write(f"   html:        {html_path.name}\n")
    sys.stderr.write(f"   cover:       {cover_path.name}\n")
    sys.stderr.write(f"   author:      {author or '(empty)'}\n")

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run", "title": title,
            "html": str(html_path), "cover": str(cover_path),
        }, ensure_ascii=False))
        return

    appid = args.appid or os.environ.get("WECHAT_APP_ID")
    secret = args.secret or os.environ.get("WECHAT_APP_SECRET")
    if not appid or not secret:
        sys.exit("missing WECHAT_APP_ID / WECHAT_APP_SECRET (CLI flag, env, or .env)")

    try:
        sys.stderr.write("-> fetching access_token ...\n")
        token = get_access_token(appid, secret)

        sys.stderr.write("-> uploading cover ...\n")
        thumb_id = upload_permanent_image(cover_path, token)
        sys.stderr.write(f"   thumb_media_id = {thumb_id}\n")

        sys.stderr.write("-> rewriting body images ...\n")
        html_cdn, ok = rewrite_body_images(html_src, token, art_dir)
        html_cdn = sanitize_html(html_cdn)

        sys.stderr.write("-> creating draft ...\n")
        media_id = create_draft(token, {
            "title": title,
            "author": author,
            "digest": summary,
            "content": html_cdn,
            "thumb_media_id": thumb_id,
            "show_cover_pic": 1,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        })

        print(json.dumps({
            "status": "success",
            "media_id": media_id,
            "thumb_media_id": thumb_id,
            "image_count": ok,
            "title": title,
        }, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "errmsg": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
