#!/usr/bin/env python3
"""
Unified text-to-image generator with provider fallback.

Order (first available provider wins, auto-fallback on error):
    1. gpt-image-2  via  JULING 中转 (JULING_BASE_URL / JULING_API_KEY)
    2. nano-banana-pro (gemini-3-pro-image-preview) via NANO_BANANA_BASE_URL / NANO_BANANA_API_KEY
    3. jimeng-4.0  via  JIMENG4_BASE_URL / JIMENG4_API_KEY

Usage:
    python scripts/generate_image.py "a cat in a sunlit room" -o images/img_001.jpg
    python scripts/generate_image.py "..." -o cover.jpg --aspect 3:4
    python scripts/generate_image.py "..." -o img.jpg --provider nano-banana

Env vars can be placed in the skill-local `.env` (auto-loaded if python-dotenv is available).
"""
from __future__ import annotations
import argparse
import base64
import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    sys.stderr.write("Missing dependency: requests. Install: pip install requests\n")
    sys.exit(2)

# Optional: load .env from skill root
try:
    from dotenv import load_dotenv  # type: ignore
    _env_file = Path(__file__).resolve().parent.parent / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
except Exception:
    pass


PROVIDERS = ("gpt-image-2", "nano-banana", "jimeng")


def _ensure_parent(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def _extract_image_ref(text: str) -> Optional[str]:
    """Extract image payload from a model's text response (base64 data URI or URL)."""
    m = re.search(r"data:image/[\w]+;base64,[A-Za-z0-9+/=]+", text)
    if m:
        return m.group(0)
    m = re.search(r"!\[.*?\]\((https?://[^\)\s]+)\)", text)
    if m:
        return m.group(1)
    m = re.search(r"(https?://[^\s\)]+\.(?:png|jpg|jpeg|webp|gif))", text, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"(https?://[^\s\)]+)", text)
    if m:
        return m.group(1)
    return None


def _save_payload(payload_str: str, output_path: str) -> None:
    if payload_str.startswith("data:image/"):
        b64 = payload_str.split(",", 1)[1]
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(b64))
    elif payload_str.startswith("http"):
        r = requests.get(payload_str, stream=True, timeout=300)
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    else:
        # raw base64
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(payload_str))


# ---------- gpt-image-2 (JULING) ----------

def gen_gpt_image_2(prompt: str, output_path: str, aspect_ratio: str = "16:9") -> str:
    base_url = os.getenv("JULING_BASE_URL")
    api_key = os.getenv("JULING_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("gpt-image-2 未配置 (需 JULING_BASE_URL / JULING_API_KEY)")
    _ensure_parent(output_path)
    base_url = base_url.rstrip("/")

    if aspect_ratio in ("9:16", "3:4", "2:3"):
        size = "1024x1536"
        aspect_hint = "\n\n【画面比例|强制】严格按竖版生成 (portrait, vertical, height > width)，不要方图。"
    elif aspect_ratio == "1:1":
        size = "1024x1024"
        aspect_hint = "\n\n【画面比例|强制】1:1 方图。"
    else:
        size = "1536x1024"
        aspect_hint = (
            "\n\n【画面比例|强制要求】生成必须是横版宽屏 (landscape widescreen, 16:9)。"
            "宽度明显大于高度。不要方图或竖图。"
        )
    full_prompt = f"{prompt}{aspect_hint}"
    auth = {"Authorization": f"Bearer {api_key}"}

    # Path 1: chat completions (streaming multimodal)
    try:
        url = f"{base_url}/v1/chat/completions"
        payload = {
            "model": "gpt-image-2",
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": True,
            "temperature": 0.7,
        }
        headers = {**auth, "Content-Type": "application/json", "Accept": "text/event-stream"}
        resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=600)
        if resp.status_code != 200:
            raise RuntimeError(f"chat status {resp.status_code}: {resp.text[:300]}")
        parts = []
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except Exception:
                continue
            delta = (chunk.get("choices") or [{}])[0].get("delta") or {}
            if delta.get("content"):
                parts.append(delta["content"])
        merged = "".join(parts)
        ref = _extract_image_ref(merged)
        if not ref:
            raise RuntimeError(f"chat 未返回图片: {merged[:300]}")
        _save_payload(ref, output_path)
        return output_path
    except Exception as e_chat:
        sys.stderr.write(f"[gpt-image-2] chat 失败 ({e_chat})，回退 images 端点\n")

    # Path 2: /v1/images/generations
    url = f"{base_url}/v1/images/generations"
    resp = requests.post(
        url,
        json={"model": "gpt-image-2", "prompt": prompt, "n": 1, "size": size},
        headers={**auth, "Content-Type": "application/json", "Accept": "application/json"},
        timeout=600,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"images status {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    item = (data.get("data") or [{}])[0]
    if item.get("b64_json"):
        _save_payload(f"data:image/png;base64,{item['b64_json']}", output_path)
        return output_path
    if item.get("url"):
        _save_payload(item["url"], output_path)
        return output_path
    raise RuntimeError(f"gpt-image-2 响应解析失败: {str(data)[:300]}")


# ---------- nano-banana-pro ----------

def gen_nano_banana(prompt: str, output_path: str, aspect_ratio: str = "16:9") -> str:
    base_url = os.getenv("NANO_BANANA_BASE_URL")
    api_key = os.getenv("NANO_BANANA_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("nano-banana 未配置 (需 NANO_BANANA_BASE_URL / NANO_BANANA_API_KEY)")
    _ensure_parent(output_path)
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    full_prompt = f"{prompt}，图片比例为{aspect_ratio}。"
    payload = {
        "model": "gemini-3-pro-image-preview",
        "messages": [{"role": "user", "content": full_prompt}],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=payload, timeout=300)
    resp.raise_for_status()
    result = resp.json()
    if "choices" not in result:
        raise RuntimeError(f"nano-banana 响应异常: {str(result)[:300]}")
    content = result["choices"][0]["message"].get("content", "")

    # base64 in markdown
    marker = "base64,"
    pos = content.find(marker)
    if pos != -1:
        raw = content[pos + len(marker):]
        close = raw.find(")")
        if close != -1:
            raw = raw[:close]
        cleaned = re.sub(r"[^A-Za-z0-9+/=]", "", raw).rstrip("=")
        rem = len(cleaned) % 4
        if rem:
            cleaned += "=" * (4 - rem)
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(cleaned))
        return output_path

    ref = _extract_image_ref(content)
    if not ref:
        raise RuntimeError(f"nano-banana 未返回图片: {content[:300]}")
    _save_payload(ref, output_path)
    return output_path


# ---------- jimeng-4.0 ----------

def gen_jimeng(prompt: str, output_path: str, aspect_ratio: str = "16:9") -> str:
    base_url = os.getenv("JIMENG4_BASE_URL")
    api_key = os.getenv("JIMENG4_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("jimeng 未配置 (需 JIMENG4_BASE_URL / JIMENG4_API_KEY)")
    _ensure_parent(output_path)

    if aspect_ratio in ("9:16", "3:4", "2:3"):
        size = "1080x1920"
    elif aspect_ratio == "1:1":
        size = "1024x1024"
    else:
        size = "1920x1080"

    api_url = f"{base_url.rstrip('/')}/v1/images/generations".replace("/v1/v1/", "/v1/")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "jimeng-4.0",
        "prompt": f"{prompt}，高质量。",
        "n": 1,
        "size": size,
        "quality": "hd",
        "response_format": "b64_json",
    }
    resp = requests.post(api_url, headers=headers, json=payload, timeout=600)
    resp.raise_for_status()
    result = resp.json()
    data = (result.get("data") or [{}])[0]
    if data.get("b64_json"):
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(data["b64_json"]))
        return output_path
    if data.get("url"):
        _save_payload(data["url"], output_path)
        return output_path
    raise RuntimeError(f"jimeng 响应解析失败: {str(result)[:300]}")


# ---------- dispatcher ----------

_PROVIDER_FN = {
    "gpt-image-2": gen_gpt_image_2,
    "nano-banana": gen_nano_banana,
    "jimeng": gen_jimeng,
}


def generate(prompt: str, output_path: str, aspect_ratio: str = "16:9",
             provider: Optional[str] = None) -> str:
    """
    Generate with automatic fallback.
    If `provider` is set, use only that provider (no fallback).
    Otherwise try PROVIDERS in order.
    """
    if provider:
        if provider not in _PROVIDER_FN:
            raise ValueError(f"未知 provider: {provider}. 可选: {list(_PROVIDER_FN)}")
        return _PROVIDER_FN[provider](prompt, output_path, aspect_ratio)

    errors = []
    for name in PROVIDERS:
        try:
            path = _PROVIDER_FN[name](prompt, output_path, aspect_ratio)
            sys.stderr.write(f"[ok] provider={name} -> {path}\n")
            return path
        except Exception as e:
            sys.stderr.write(f"[skip] {name}: {e}\n")
            errors.append(f"{name}: {e}")
    raise RuntimeError("所有 provider 均失败:\n  " + "\n  ".join(errors))


def main():
    ap = argparse.ArgumentParser(description="Text-to-image with provider fallback")
    ap.add_argument("prompt", help="Image prompt (English recommended)")
    ap.add_argument("-o", "--output", required=True, help="Output image path")
    ap.add_argument("--aspect", default="16:9",
                    choices=["16:9", "9:16", "1:1", "3:4", "2:3", "4:3", "3:2"],
                    help="Aspect ratio (default 16:9; use 3:4 for RedNote vertical cards)")
    ap.add_argument("--provider", choices=list(_PROVIDER_FN),
                    help="Force a single provider (skip fallback)")
    args = ap.parse_args()

    generate(args.prompt, args.output, aspect_ratio=args.aspect, provider=args.provider)
    print(args.output)


if __name__ == "__main__":
    main()
