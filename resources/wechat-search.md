# 微信公众号内容搜索与采集

> **使用边界**：仅用于内容研究与合规参考。不做大规模爬取、不绕过反爬、不模拟用户交互。

基于搜狗的公开搜索入口，检索微信公众号文章。适合为长文写作补充微信生态内的参考资料。

## TL;DR

```bash
# 按关键词搜文章
python scripts/sogou_search.py "AI 教育"

# 带日期范围
python scripts/sogou_search.py "AI 教育" --start 20260101 --end 20260401 --max 20

# 搜公众号（成功率较低）
python scripts/sogou_search.py "人民日报" --mode gzh

# 把结果落盘（给 reference/ 用）
python scripts/sogou_search.py "AI 教育" --start 20260101 --end 20260401 \
    -o output/公众号/.../reference/search_results.json
```

## 脚本 `scripts/sogou_search.py`

### 模式

| `--mode` | 说明 | 成功率 |
|---------|------|--------|
| `article`（默认） | 按关键词搜文章（搜狗 `type=2`） | ✅ 较高 |
| `gzh` | 按名字搜公众号（搜狗 `type=1`） | ⚠️ 受限 |
| `gzh_history` | 先搜公众号，再按该名字搜文章 | ⚠️ 不稳 |

### 参数

```
query             关键词（位置参数，必填）
--mode            article | gzh | gzh_history（默认 article）
--page N          第几页（默认 1）
--max N           结果条数（默认 10）
--start YYYYMMDD  起始日期（只对 article 模式生效，客户端过滤）
--end   YYYYMMDD  结束日期
-o / --output     JSON 写入文件；不给就打印到 stdout
```

### 输出（article 模式）

```json
[
  {
    "type": "article",
    "title": "标题",
    "url": "https://weixin.sogou.com/link?url=...",
    "abstract": "摘要",
    "gzh_name": "公众号名",
    "published_at": "2026-04-20",
    "timestamp": 1713571200
  }
]
```

`url` 是搜狗跳转链接（有时效）。拿到后用 `WebFetch` 取最终 `mp.weixin.qq.com/s/...` 链接和正文。

### 输出（gzh 模式）

```json
[
  {
    "type": "gzh",
    "name": "公众号名",
    "profile_url": "https://weixin.sogou.com/...",
    "intro": "简介"
  }
]
```

### 输出（gzh_history 模式）

```json
{
  "type": "gzh_history",
  "gzh": { ... },
  "articles": [ ... ]
}
```

## 脚本内部细节

- 请求头：3 个桌面浏览器 UA 轮换，每次请求换一个
- 每次 `requests.get` 后 `sleep(1)`，别自己加循环再加频
- 日期过滤：搜狗服务端参数不可靠，脚本从结果页的 `<script>timeConvert('…')` 提时间戳，客户端按 `YYYYMMDD` 过滤
- 排序：article 模式按时间倒序

## 工作流场景

### 场景 1：为公众号长文搜参考

```bash
# 建目录
mkdir -p output/公众号/.../reference

# 多关键词跑几轮，每轮不同切入点
python scripts/sogou_search.py "AI 就业 2026" --max 15 \
    -o output/公众号/.../reference/search_ai_jobs.json
python scripts/sogou_search.py "Anthropic 劳动力" --max 10 \
    -o output/公众号/.../reference/search_anthropic.json

# 挑感兴趣的几条，用 WebFetch 抓正文存到 reference/articles/ref_xxx.md
```

### 场景 2：限定时间窗

```bash
# 搜 2026 年 Q1 的相关内容
python scripts/sogou_search.py "AI 教育" \
    --start 20260101 --end 20260331 --max 30
```

### 场景 3：采特定公众号近期文章

`gzh` 模式常不稳；推荐退而求其次，把公众号名写进关键词走 `article` 模式：

```bash
python scripts/sogou_search.py "人民日报 AI" --max 20
```

## 限制与伦理

- 搜狗对公众号搜索（`type=1`）有反爬保护，成功率不稳，**不要尝试绕过**
- 搜狗跳转链通常 7-30 天时效；要存的话及时 `WebFetch` 抓正文存本地
- 微信官方限制完整历史抓取，**不做**某公众号全部历史文章采集
- 避免高频请求；单任务控制在几十条以内
- 不模拟用户交互（点赞 / 评论 / 关注）
- 采集结果仅用于内容研究；引用正文需遵守来源版权

## 手搓 curl（不推荐，仅当脚本不可用时）

```bash
URL="https://weixin.sogou.com/weixin?type=2&query=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' 'AI 教育')&page=1"
curl -s -A "Mozilla/5.0" "$URL" -o /tmp/sogou.html
# 再自己写 BeautifulSoup 解析，或直接 Read /tmp/sogou.html 让 Claude 提条目
```

日期过滤是客户端行为，`tsn/ft/et` 这些参数搜狗服务端会忽略，别指望它们。
