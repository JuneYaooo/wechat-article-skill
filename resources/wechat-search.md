# 微信公众号内容搜索与采集

> **使用边界**：仅用于内容研究与合规参考。不做大规模爬取、不绕过反爬机制、不模拟用户交互。

基于搜狗的公开搜索入口，检索微信公众号文章。适合为长文写作补充微信生态内的参考资料。

## 搜索能力矩阵

| 类型 | 说明 | 成功率 | 建议 |
|------|------|--------|------|
| 文章搜索 | 按关键词搜微信文章 | ✅ 较高 | **推荐首选** |
| 话题搜索 | 按话题名搜讨论 | ✅ 较高 | 用 "话题名 + 关键词" 组合更稳 |
| 公众号搜索 | 按公众号名搜账号 | ⚠️ 受限 | 改用 `"公众号名 + 关键词"` 的文章搜索替代 |
| 日期范围过滤 | 限定发布时间窗 | ✅ 支持 | 格式 `YYYYMMDD` |

## 核心搜索入口

搜狗微信搜索页（HTML）：

```
https://weixin.sogou.com/weixin?type=2&query=<关键词 URL 编码>&tsn=<日期类型>
```

参数：

- `type=2`：文章搜索
- `query`：关键词（URL 编码）
- `tsn`：时间筛选。`0` = 不限；`1` = 一天内；`2` = 一周内；`3` = 一个月内；`5` = 自定义
- 自定义日期：`&ft=YYYY-MM-DD&et=YYYY-MM-DD`（需 `tsn=5`）

## 执行流程

1. **构造 URL**：根据关键词 + 可选日期参数组装搜狗搜索 URL
2. **抓取列表**：用 `WebFetch` 或 `curl -A <UA>` 抓 HTML
3. **解析结果**：从 HTML 中提取 `<div class="txt-box">` 区块，抽出标题、链接、摘要、公众号名、发布时间
4. **采集正文**（可选）：对感兴趣的微信临时链接用 `WebFetch` 抓取正文 HTML，转 Markdown
5. **本地化**：结果写入 `reference/search_results.json` 和 `reference/articles/ref_xxx.md`

## 结果结构建议

```json
[
  {
    "title": "标题",
    "url": "https://mp.weixin.qq.com/s/...",
    "abstract": "摘要",
    "gzh_name": "公众号名称",
    "published_at": "2026-04-20",
    "fetched": true,
    "local_file": "articles/ref_001_....md"
  }
]
```

## 日期范围搜索示例

```bash
# 搜索 2026-03-01 ~ 2026-03-31 的 "AI 教育" 相关文章
URL="https://weixin.sogou.com/weixin?type=2&query=$(python3 -c 'import urllib.parse;print(urllib.parse.quote("AI 教育"))')&tsn=5&ft=2026-03-01&et=2026-03-31"
curl -s -A "Mozilla/5.0" "$URL" -o /tmp/sogou.html
```

然后用 Python + BeautifulSoup 或 Claude 直接 `Read` HTML 提取条目。

## 工作流场景

### 场景 1：为文章搜集参考资料

```
用户写作主题 → wechat-search 关键词搜索 → 挑选 3-8 篇相关文章
              → WebFetch 抓取正文 → 保存到 reference/articles/ → 写作引用
```

### 场景 2：采集特定公众号近期内容

由于直接搜公众号受限，推荐：

```
query = "公众号名称 + 关键词"
type  = "article"
tsn   = 3（最近一个月）
```

### 场景 3：历史回溯 / 趋势分析

用 `tsn=5` + 自定义 `ft` / `et` 按月或按季度切片采集。

## 限制与伦理

- 搜狗对公众号搜索（`type=1`）有反爬虫保护，成功率不稳定，**不要尝试绕过**
- 微信临时链接通常 7-30 天时效，要及时保存正文到本地
- 微信官方限制完整历史抓取，**不支持**采集某公众号全部历史文章
- 避免高频请求，单次任务内控制在几十条以内
- 不模拟用户交互（点赞、评论、关注）
