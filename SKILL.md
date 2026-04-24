---
name: wechat-article
description: Generate WeChat Official Account (公众号) long-form articles -- 2000-4000 chars, 7 headline formulas, inline images, mdnice-ready Markdown, saved to output/公众号/. Also covers draft upload to WeChat Official Account backend (wechat-publish mode) and Sogou-based WeChat article search (wechat-search mode). Use when the user asks to 写公众号文章 / 写一篇公众号推文 / 公众号长文 / 上传公众号草稿 / 搜微信文章 / write a WeChat Official Account article.
---

# wechat-article -- 微信公众号文章生成 & 发布

覆盖三个子模式：

- **write 模式**（默认）：把一个主题 / 一份素材写成 2000-4000 字的公众号长文，产物保存到 `output/公众号/`
- **publish 模式**：把已生成的文章上传到微信公众号草稿箱（见 [`resources/wechat-publish.md`](resources/wechat-publish.md)）
- **search 模式**：基于搜狗 HTML 接口搜微信文章作为参考素材（见 [`resources/wechat-search.md`](resources/wechat-search.md)）

## 核心理念：长文 + HTML 渲染

公众号发布形式是**完整的 HTML 长文章**，通过公众号后台素材库发布。

- 字数：2000-4000
- 结构：H2 起始，3-5 个章节（**不写 H1**，标题放 `meta.json`）
- 每 1-2 个章节配一张图（写作同步完成，不留占位符）
- 参考来源不写入正文（只保存到 `reference/`）

## 调用规范（对 agent 的硬约束）

当用户说"写公众号文章 / 写一篇公众号推文"时：

1. **先问三件事**（不要直接动手）：
   - 主题 / 目标读者 / 想表达的核心观点？
   - 标题倾向？（按下面 7 种公式映射推荐 1-2 个）
   - 是否需要同步上传到草稿箱？（需要时走 publish 模式）
2. **先搜参考**：按 [`resources/reference-search.md`](resources/reference-search.md)，如果是微信生态话题再叠加 [`resources/wechat-search.md`](resources/wechat-search.md)
3. **先给大纲**（H2 起始，3-5 章）让用户确认
4. **逐章写正文 + 同步配图**（见 [`resources/image-sourcing.md`](resources/image-sourcing.md)）
5. **生成标题 + ≤20 字摘要**（7 种公式见下方）
6. **终稿去 AI 化**：读 [`resources/humanizer-zh.md`](resources/humanizer-zh.md) 做一遍完整扫描
7. **保存产物**：按 [`docs/output-spec.md`](docs/output-spec.md) 的目录规范
8. **（可选）上传草稿**：读 [`resources/wechat-publish.md`](resources/wechat-publish.md)，需要用户提供 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`

## write 模式：写作流程

### 1. 搜集参考

读 [`resources/reference-search.md`](resources/reference-search.md)。

- 多角度多轮搜（中英文、事实 / 观点 / 数据），至少 3 轮
- 微信生态话题 → 叠加 [`resources/wechat-search.md`](resources/wechat-search.md) 按日期范围搜微信文章
- 交叉验证关键数据
- 结果保存到该文章目录的 `reference/` 子目录

### 2. 构思大纲

- H2 起始，3-5 章
- 每章一个论点 + 至少一个具体例子 / 数据
- 给用户看大纲，确认后再动笔

### 3. 写正文（2000-4000 字）

- **不写 H1**，从 H2 开始
- 第一人称（我觉得 / 我看到 / 我发现）
- 口语化、具体例子、逻辑转折、混杂段落长度
- **每 1-2 章配一张图，写作同步完成**（见 image-sourcing 资源）
- 图片用相对路径引用：`![描述](images/img_001.jpg)`
- **不留 `【插入图片：...】` 占位符**

### 4. 标题与摘要

**7 种标题公式**：

| # | 公式 | 示例 |
|---|------|------|
| 1 | 关键词吸引（核心名词 + 具体数字） | "OpenAI 新模型，跑分超 GPT-4 15%" |
| 2 | 冲突对比（A vs B） | "人类在放弃思考，AI 却在学会反思" |
| 3 | 提问式 | "为什么 ChatGPT 突然变笨了？" |
| 4 | 悬念式 | "我用了三个月 Cursor，最后换回了 VSCode" |
| 5 | 场景式 | "凌晨三点，客服机器人收到了最难的那条消息" |
| 6 | 情感式 | "写了十年代码，我被一个 agent 整破防了" |
| 7 | 强调式 | "所有做 AI 产品的人，都该看看这份报告" |

**选型原则**：技术 / 产品类优先 1 / 4 / 7；观点 / 评论类优先 2 / 3；故事 / 访谈类优先 4 / 5 / 6。

**标题长度** 15-30 字（公众号后台 ≤64 字符会截断）。

**摘要**：1-2 句、≤20 字，是标题的延伸钩子，不是全文总结。

### 5. 去 AI 化

读 [`resources/humanizer-zh.md`](resources/humanizer-zh.md) 的五层原则，对终稿做完整扫描重写，输出**质量评分**（总分 50）。

### 6.（可选）HTML 渲染

公众号发布形式是 HTML，`wechat-publish` 也需要 HTML 输入。调 `scripts/md2html.py`（mistune + mdnice 主题，自包含）：

```bash
# 默认橙心主题
python scripts/md2html.py output/公众号/.../article.md

# 指定主题
python scripts/md2html.py article.md --theme 灵动蓝 -o article_灵动蓝.html

# 列出全部 28 个主题
python scripts/md2html.py --list-themes
```

主题文件在 `assets/mdnice_themes/`：橙心（默认）/ 灵动蓝 / 简 / 兰青 / 红绯 / 萌粉 / 嫩青 / 重影 / 凝夜紫 / 山吹 / 蓝莹 / 科技蓝 / 雁栖湖 / 极简黑 / 极客黑 / 萌绿 / 绿意 等 28 个。把使用的主题名写入 `meta.json.theme`。

## 输出目录（见 `docs/output-spec.md`）

```
output/公众号/{YYYY-MM-DD}/{短标题}_{YYYYMMDDHHmm}/
├── {文章完整标题}.md               # Markdown 源文件
├── {文章完整标题}_{主题名}.html    # （可选）mdnice 主题渲染
├── {文章完整标题}_cover.jpg        # （可选）封面图
├── meta.json                       # 元数据
├── images/                         # 文章配图
│   └── img_001.jpg ...
└── reference/
    ├── thinking.md
    ├── search_results.json
    ├── summary.md
    └── articles/
        └── ref_001_{来源标题}.md
```

## meta.json 必含字段

```json
{
  "title": "AI 冲击就业？Anthropic 最新研究揭示劳动力市场的真相",
  "summary": "失业率在下降，新岗位在增加。数据比标题党更有说服力。",
  "author": "",
  "platform": "公众号",
  "created_at": "2026-04-24T15:00:00+08:00",
  "theme": "橙心",
  "tags": ["AI", "就业", "劳动力市场"],
  "word_count": 3040,
  "cover_image": "cover.jpg",
  "cover_image_prompt": "A professional workspace, clean desk, natural light",
  "images": ["images/img_001.jpg", "images/img_002.jpg"],
  "references": {
    "search_queries": ["AI 失业 2026", "Anthropic economic index"],
    "source_count": 6,
    "summary_file": "reference/summary.md"
  }
}
```

完整 schema 见 [`docs/meta-schema.md`](docs/meta-schema.md)。

## publish 模式：上传到公众号草稿箱

**完整流程见 [`resources/wechat-publish.md`](resources/wechat-publish.md)。**

**一条命令**（脚本自动从环境变量 / `.env` / CLI 读凭证）：

```bash
python scripts/wechat_publish.py output/公众号/2026-04-24/xxx/
```

脚本内部：读 `meta.json` → 找 HTML（没有就用 `md2html.py` 现渲染）→ 拿 token → 传封面 → 正文图换成微信 CDN → 建草稿 → 打印 JSON `{media_id, thumb_media_id, ...}`。

**凭证准备**（按优先级查找）：

1. CLI `--appid` / `--secret`
2. 环境变量 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`
3. skill 目录 `.env`：
   ```
   WECHAT_APP_ID=wx...
   WECHAT_APP_SECRET=...
   ```

**⚠️ 安全**：`WECHAT_APP_SECRET` 不要提交到 git，不要打印到日志。脚本返回的 `media_id` 只是草稿 id，正式发布仍需用户到公众号后台手动点"发布"。

## search 模式：微信文章搜索

**完整流程见 [`resources/wechat-search.md`](resources/wechat-search.md)。**

基于搜狗的 HTML 接口，按关键词 + 可选日期范围搜微信文章：

```bash
# 文章
python scripts/sogou_search.py "AI 教育" --start 20260101 --end 20260401 --max 20

# 公众号
python scripts/sogou_search.py "人民日报" --mode gzh

# 存结果
python scripts/sogou_search.py "AI 教育" -o reference/search_results.json
```

**使用边界**：仅用于内容研究。不做大规模爬取、不绕过反爬、不模拟用户交互。

## 不要做的事

- ❌ 不写 H1（标题放 `meta.json.title`）
- ❌ 不在正文末尾写"参考来源 / 参考文献"（只保存到 `reference/`）
- ❌ 不在 `.md` 里留 `【插入图片：...】` 占位符
- ❌ 不跳过去 AI 化就交稿
- ❌ 不把 `WECHAT_APP_SECRET` 写进 git / 打印到日志
- ❌ 不大规模爬搜狗 / 不绕过反爬

## 文件结构

```
wechat-article-skill/
├── SKILL.md                    # 本文件（Claude Code skill 入口）
├── AGENTS.md                   # codex / aider / cursor 的薄索引
├── README.md                   # 项目说明
├── install_as_skill.sh         # 一键安装到 ~/.claude/skills/
├── .env.example                # WECHAT_APP_ID / WECHAT_APP_SECRET 模板
├── docs/
│   ├── install.md              # 给 AI agent 自动安装读的指引
│   ├── output-spec.md          # 目录与命名规范
│   └── meta-schema.md          # meta.json 字段定义
├── resources/                  # AI 按需加载的参考文档
│   ├── humanizer-zh.md         # 去 AI 化完整指南
│   ├── reference-search.md     # 通用参考资料采集
│   ├── image-sourcing.md       # 配图搜索 / 版权检查 / AI 生图
│   ├── wechat-publish.md       # 草稿箱上传完整流程
│   └── wechat-search.md        # 搜狗微信文章搜索
├── scripts/                    # 可执行脚本（AI shell 调用，不读入上下文）
│   ├── README.md
│   ├── requirements.txt
│   ├── generate_image.py       # 文生图：gpt-image-2 → nano-banana → jimeng 回退
│   ├── md2html.py              # Markdown → mdnice 主题 HTML
│   ├── wechat_publish.py       # 上传文章到公众号草稿箱
│   └── sogou_search.py         # 搜狗微信文章搜索
├── assets/                     # 直接用进产物的资源
│   └── mdnice_themes/          # 28 个 mdnice 主题模板
└── agents/
    └── openclaw.yaml
```
