# 上传文章到微信公众号草稿箱

> **何时用**：文章已经由 `wechat-write` 生成并保存在 `output/公众号/` 下，现在要推到公众号草稿箱。

## TL;DR

```bash
# 1. 确保 .env 或环境里有 WECHAT_APP_ID / WECHAT_APP_SECRET
# 2. 一条命令搞定
python scripts/wechat_publish.py output/公众号/2026-04-24/xxx_20260424...
```

脚本会：读 `meta.json` → 找 html（没有就用 `md2html.py` 现渲染）→ 传封面 → 传正文图并把本地路径换成微信 CDN → 创建草稿 → 打印 JSON。

## 脚本 `scripts/wechat_publish.py`

### 输入

一个文章目录（位于 `output/公众号/YYYY-MM-DD/短标题_时间戳/`），里面至少得有：

- `meta.json`：必须字段 `title`、`summary`、`cover_image`（相对路径）；可选 `author`、`theme`
- 正文 HTML（`{title}_{theme}.html` / `{title}.html` / 任意 `*.html`）。没有时脚本会从 `{title}.md` 现渲染
- 封面图（路径由 `meta.cover_image` 决定）
- `images/*`：HTML 里 `<img src="images/...">` 引用的本地图

### 用法

```bash
# 标准用法（从 .env / 环境变量读凭证）
python scripts/wechat_publish.py output/公众号/2026-04-24/xxx/

# 指定主题（如果只有 .md、没有 .html，触发现渲染）
python scripts/wechat_publish.py output/公众号/.../ --theme 灵动蓝

# CLI 直接传凭证（覆盖环境变量）
python scripts/wechat_publish.py output/公众号/.../ --appid wx... --secret ...

# 干跑一遍（只校验+渲染，不发请求）
python scripts/wechat_publish.py output/公众号/.../ --dry-run

# 覆盖作者名
python scripts/wechat_publish.py output/公众号/.../ --author "某某"
```

### 输出（stdout 是 JSON，日志走 stderr）

```json
{
  "status": "success",
  "media_id": "xxx",          // 草稿 id
  "thumb_media_id": "yyy",    // 封面 media_id
  "image_count": 3,
  "title": "..."
}
```

失败时：

```json
{"status": "error", "errmsg": "..."}
```

## 凭证读取顺序

1. CLI `--appid` / `--secret`
2. 进程环境变量 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`
3. skill 根目录 `.env`（脚本自动加载，无需 python-dotenv）

`.env` 模板见 `.env.example`。**不要提交到 git**。

## 脚本内部流程

1. 读 `meta.json`，标题截到 64 字符、摘要截到 120 字符
2. 找 HTML；找不到就调 `md2html.py:md_to_html()` 用指定主题现渲染
3. `GET /cgi-bin/token` 拿 `access_token`
4. `POST /cgi-bin/material/add_material?type=image` 传封面 → `thumb_media_id`
5. BeautifulSoup 解析 HTML，对每个 `<img>`：
   - `src` 已经是 `https://mmbiz.qpic.cn/...`：跳过
   - 本地路径：读文件；远程 URL：先下载
   - `POST /cgi-bin/media/uploadimg` 上传，把 `src` 替换成返回的 CDN URL
   - 失败时（且装了 Pillow）PNG↔JPEG 转一次再试
6. 正则清理 `<ol>/<li>` 标签周围的空白
7. `POST /cgi-bin/draft/add` 建草稿（JSON body，`ensure_ascii=False` 的 UTF-8）

## 后续手动步骤

脚本返回的 `media_id` 是**草稿 id**，不是已发布文章。正式发布还得：

1. 登录公众号后台 → 草稿箱
2. 找到刚上传的那篇
3. 检查封面 / 排版 / 作者 / 摘要
4. 点"发布"

## 微信 API 速查（脚本已封装，手工 curl 用）

| 步骤 | Endpoint |
|------|---------|
| Token | `GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}` |
| 封面（永久素材） | `POST https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={T}&type=image` |
| 正文图 | `POST https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={T}` |
| 建草稿 | `POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token={T}` |

草稿 JSON body：

```json
{
  "articles": [{
    "title": "≤64 字符",
    "author": "作者",
    "digest": "≤120 字符",
    "content": "<p>HTML 正文……</p>",
    "thumb_media_id": "封面 media_id",
    "show_cover_pic": 1,
    "need_open_comment": 0,
    "only_fans_can_comment": 0
  }]
}
```

## 注意事项

- Access Token 有效期 7200 秒；脚本每次新取，不缓存
- 标题超 64 / 摘要超 120 脚本会截，但最好自己写够短
- 正文图必须换成微信 CDN URL，否则后台不显示——脚本已自动处理
- 封面图 ≤1MB，JPG / PNG
- `WECHAT_APP_SECRET` 只放 `.env`，别提交、别打印
- 脚本返回 `media_id` 只是草稿；正式发布要人手到后台操作
