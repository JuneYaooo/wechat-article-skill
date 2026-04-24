# 上传文章到微信公众号草稿箱

> **何时用**：文章已经由 `wechat-write` 生成并保存在 `output/公众号/` 下，现在要推到公众号草稿箱。

## 执行流程

1. **定位文章**：从 `output/公众号/` 目录找到目标文章（用户给路径或按标题匹配）
2. **读取内容**：`.md` 原稿 + `meta.json`
3. **获取账号凭证**：从环境变量 / skill `.env` / 用户对话中读取 `WECHAT_APP_ID` 与 `WECHAT_APP_SECRET`
4. **获取 Access Token**：`GET /cgi-bin/token`
5. **渲染 HTML**：Markdown → HTML（用户自备渲染器，推荐 mdnice 主题）
6. **上传封面图**：`POST /cgi-bin/material/add_material`，返回 `thumb_media_id`
7. **上传正文图片**：`POST /cgi-bin/media/uploadimg`，把 `.md` 中的本地图片路径替换为返回的微信 CDN URL
8. **创建草稿**：`POST /cgi-bin/draft/add`，返回草稿 `media_id`
9. **输出结果**：`media_id`，用户在公众号后台→草稿箱查看与发布

## 凭证读取顺序

本 resource 不绑定数据库。按下面顺序查找凭证：

1. 环境变量 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`
2. skill 目录 `.env` 文件：
   ```
   WECHAT_APP_ID=wx...
   WECHAT_APP_SECRET=...
   ```
3. 用户在对话中直接提供

**⚠️ 安全**：`appSecret` 不要写入任何提交到 git 的文件，也不要打印到日志。

## 微信 API 速查

| 步骤 | Endpoint | 说明 |
|------|---------|------|
| 获取 Token | `GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}` | 有效期 7200 秒 |
| 上传封面图（永久素材） | `POST https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={TOKEN}&type=image` | multipart 上传，返回 `media_id` |
| 上传正文图片 | `POST https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={TOKEN}` | multipart 上传，返回微信 CDN URL |
| 创建草稿 | `POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token={TOKEN}` | JSON body，返回草稿 `media_id` |

### 草稿 JSON 结构

```json
{
  "articles": [
    {
      "title": "文章标题（≤64 字符）",
      "author": "作者",
      "digest": "摘要（≤120 字符）",
      "content": "<p>HTML 正文……</p>",
      "content_source_url": "原文链接（可空）",
      "thumb_media_id": "封面图上传返回的 media_id",
      "need_open_comment": 1,
      "only_fans_can_comment": 0
    }
  ]
}
```

## 参考实现（纯 Bash + curl）

最小实现，不依赖任何 Python 库：

```bash
# 1. 获取 token
TOKEN=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=$WECHAT_APP_ID&secret=$WECHAT_APP_SECRET" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 2. 上传封面图
THUMB_ID=$(curl -s -F "media=@cover.jpg" \
  "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=$TOKEN&type=image" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['media_id'])")

# 3. 上传正文图（对每张 images/*.jpg 做）
CDN_URL=$(curl -s -F "media=@images/img_001.jpg" \
  "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=$TOKEN" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['url'])")
# 然后在 HTML 中把 images/img_001.jpg 替换成 $CDN_URL

# 4. 创建草稿（body.json 按上面结构准备好）
curl -s -X POST -H "Content-Type: application/json" -d @body.json \
  "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=$TOKEN"
```

## 注意事项

- Access Token 有效期 7200 秒，不要缓存过期的
- 标题 ≤64 字符，摘要 ≤120 字符，超出会被截断
- HTML 中的图片**必须**替换为微信 CDN URL，否则在后台不显示
- 封面图 ≤1MB，支持 JPG / PNG
- 上传成功后文章在**草稿箱**，最终发布仍需用户手动到后台操作
