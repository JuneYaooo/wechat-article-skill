# scripts/ — 可执行脚本

这些脚本封装**脆弱操作**（精确 API 调用、格式严格的渲染），AI 直接 shell 调用，不读入上下文。

## generate_image.py

文生图，带多 provider 自动回退。

**回退顺序**：`gpt-image-2`（巨灵）→ `nano-banana`（Gemini 3 Pro Image）→ `jimeng`（即梦 4.0）

```bash
# 自动回退
python scripts/generate_image.py "a minimalist workspace, morning light" \
    -o output/公众号/.../images/cover.jpg --aspect 16:9

# 小红书竖图
python scripts/generate_image.py "..." -o card.jpg --aspect 3:4

# 强制单一 provider（不回退）
python scripts/generate_image.py "..." -o img.jpg --provider jimeng
```

**需要的环境变量**（任一组配齐即可启用对应 provider）：

```
JULING_BASE_URL / JULING_API_KEY          # gpt-image-2
NANO_BANANA_BASE_URL / NANO_BANANA_API_KEY  # nano-banana-pro
JIMENG4_BASE_URL / JIMENG4_API_KEY        # jimeng-4.0
```

放在仓库根 `.env` 里会被自动读取（需装 `python-dotenv`，非必需）。

---

## md2html.py

把 Markdown 渲染成带 mdnice 主题的自包含 HTML，可直接粘贴到公众号后台或传给 publish 流程。

```bash
# 默认橙心主题
python scripts/md2html.py output/公众号/.../article.md

# 指定主题，输出到指定路径
python scripts/md2html.py article.md --theme 灵动蓝 -o article_灵动蓝.html

# 列出可用主题
python scripts/md2html.py --list-themes
```

主题文件在 `../assets/mdnice_themes/`，共 28 个（橙心 / 灵动蓝 / 简 / 兰青 / 红绯 / 萌粉 / 嫩青 / 重影 / 凝夜紫 / 山吹 / 蓝莹 / 科技蓝 / 雁栖湖 / 极简黑 / 极客黑 / 萌绿 / 绿意 / 橙蓝风 / 蔷薇紫 / 前端之巅同款 / 全栈蓝 / 草原绿 / 姹紫 / 丘比特忙 / 锤子便签主题第2版 / Obsidian / Pornhub黄 / WeFormat）。

---

---

## wechat_publish.py

把 `output/公众号/` 下的一篇文章推到微信公众号草稿箱。

```bash
# 从 .env / 环境变量读 WECHAT_APP_ID / WECHAT_APP_SECRET
python scripts/wechat_publish.py output/公众号/2026-04-24/xxx/

# 干跑（只校验+渲染，不发请求）
python scripts/wechat_publish.py output/公众号/.../  --dry-run

# 没有 html 时指定主题，让脚本现渲染
python scripts/wechat_publish.py output/公众号/.../  --theme 灵动蓝

# 直接传凭证
python scripts/wechat_publish.py output/公众号/.../  --appid wx... --secret ...
```

读 `meta.json` → 定位/渲染 HTML → 拿 token → 传封面 → 正文图换成微信 CDN URL → 建草稿 → 打印 JSON。详细流程见 `../resources/wechat-publish.md`。

---

## sogou_search.py

基于搜狗 HTML 的微信文章检索。

```bash
# 文章搜索
python scripts/sogou_search.py "AI 教育"

# 带日期范围（YYYYMMDD，客户端过滤）
python scripts/sogou_search.py "AI 教育" --start 20260101 --end 20260401 --max 20

# 搜公众号（成功率低）
python scripts/sogou_search.py "人民日报" --mode gzh

# 存结果
python scripts/sogou_search.py "AI 教育" -o reference/search_results.json
```

自带 UA 轮换 + 每请求 1s 间隔。详见 `../resources/wechat-search.md`。

---

## 依赖安装

```bash
pip install -r scripts/requirements.txt
```

## 本地测试

```bash
# 渲染测试（不需要任何 API key）
echo "# H1\n## H2\n正文段落。" > /tmp/t.md
python scripts/md2html.py /tmp/t.md --theme 橙心 -o /tmp/t.html

# 生图测试（需要至少一组 API key）
python scripts/generate_image.py "a cat on a desk" -o /tmp/cat.jpg --provider gpt-image-2
```
