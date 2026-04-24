<div align="center">

# wechat-article-skill

**一句话喂主题，产出一篇 2000-4000 字的微信公众号推文，还能直接上传到草稿箱。**

Claude Code / OpenClaw Skill。装进 agent 后，从参考搜集 → 大纲构思 → 长文写作 → 配图 → 去 AI 化 → 上传公众号草稿，全链路可用。

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-orange.svg)](https://www.anthropic.com/claude-code)
[![Platform](https://img.shields.io/badge/platform-公众号-07c160.svg)](https://mp.weixin.qq.com/)
[![Zh](https://img.shields.io/badge/lang-zh--CN-red.svg)](./README.md)

</div>

---

## ✨ 能做什么

- ✍️ **2000-4000 字长文写作** —— H2 起始、不写 H1、每 1-2 章配一张图（写作同步完成，不留占位符）
- 🎯 **7 种标题公式内置** —— 关键词吸引 / 冲突对比 / 提问 / 悬念 / 场景 / 情感 / 强调，按内容类型自动推荐
- 🧹 **内置去 AI 化 playbook** —— 5 层 50+ 条规则（禁用词、句式、节奏、活人感），重写后给质量评分（满分 50）
- 🔎 **双通道搜参考** —— 通用 WebSearch / WebFetch ＋ 搜狗微信文章搜索（支持日期范围过滤）
- 📤 **一键上传草稿箱** —— 直接调微信官方 API（token / 素材 / 草稿）完成封面图上传、正文图替换 CDN、草稿创建
- 🖼 **零水印配图纪律** —— 下载后多模态目视检查，Getty / 视觉中国 / IC 这类水印必须处理再用
- 🧰 **纯 skill，无重后端依赖** —— 只用 Claude 内置工具 + 微信官方 HTTP API

## 📦 产物长这样

```
output/公众号/2026-04-24/AI就业报告_202604241500/
├── AI冲击就业_Anthropic最新研究揭示劳动力市场的真相.md
├── meta.json                      # 标题、摘要、theme、tags、cover_image
├── images/
│   ├── img_001.jpg
│   └── img_002.jpg
└── reference/
    ├── thinking.md
    ├── search_results.json
    ├── summary.md
    └── articles/
        └── ref_001_Anthropic官方博客.md
```

完整 schema 见 [`docs/meta-schema.md`](./docs/meta-schema.md)，目录规范见 [`docs/output-spec.md`](./docs/output-spec.md)。

---

## 🚀 安装

### 方式一：让 AI 自己装（推荐）

把下面这段 prompt 丢给你的 AI 助手（Claude Code / OpenClaw / Codex / Cursor / Trae 都行）：

```
帮我安装 wechat-article-skill：
https://raw.githubusercontent.com/JuneYaooo/wechat-article-skill/main/docs/install.md
```

agent 会自己 clone 仓库、跑安装脚本、提示你重启、问你要（可选的）公众号 AppID / AppSecret。

### 方式二：手动安装

```bash
git clone git@github.com:JuneYaooo/wechat-article-skill.git
cd wechat-article-skill
bash install_as_skill.sh
```

脚本会把 skill 装到 `~/.claude/skills/wechat-article-skill/`，Claude Code 重启后自动识别。

**写作模式不需要任何 key 就能跑**。只有要**上传公众号草稿**时才需要在 `~/.claude/skills/wechat-article-skill/.env` 填：

```bash
WECHAT_APP_ID=wx...
WECHAT_APP_SECRET=...
```

> 🔒 **不会误吃密钥**：脚本只从 skill 自己目录的 `.env` 加载，**不会**向上递归读项目目录的 `.env`。
>
> 🛡️ 微信 `AppSecret` 一旦泄露可被冒用发文，请只写在 skill 目录的 `.env`（已 `.gitignore`），不要提交到任何仓库。

---

## 🛠 在 Claude Code 里怎么用

### 写一篇公众号文章

装完直接跟 Claude 说人话：

> 帮我用 **wechat-article** 写一篇分析 **Anthropic 最新经济报告** 的文章，角度是 AI 对就业的真实影响，大概 3000 字。

Claude 会：

1. 先问你目标读者 / 标题倾向 / 要不要同步上传草稿箱
2. 多轮搜参考（通用 + 微信生态），交叉验证核心数据
3. 给大纲让你确认（H2 起始，3-5 章）
4. 逐章写正文 + 同步配图（零水印检查）
5. 生成标题（7 公式）+ ≤20 字摘要
6. 按去 AI 化规则重写并给评分
7. 告诉你产物目录路径

### 上传到公众号草稿箱

```
/wechat-article 把刚才那篇文章上传到公众号草稿箱
```

前提：`.env` 里有 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`，或你直接在对话里粘给 Claude。

会走完：Token 获取 → 封面图上传 → 正文图片替换为微信 CDN URL → 创建草稿 → 返回 `media_id`。最终发布仍需手动在公众号后台点「发送」。

> 🧑‍💻 想自己写脚本而不走 agent？看 [`SKILL.md`](./SKILL.md) 和 [`resources/wechat-publish.md`](./resources/wechat-publish.md)，所有 endpoint、body 结构、参考 curl 实现都在那。

---

## 🎯 7 种标题公式

| # | 公式 | 适用 | 示例 |
|---|------|------|------|
| 1 | 关键词 + 具体数字 | 技术 / 产品发布 | "OpenAI 新模型，跑分超 GPT-4 15%" |
| 2 | 冲突对比 | 观点 / 评论 | "人类在放弃思考，AI 却在学会反思" |
| 3 | 提问式 | 观点 / 评论 | "为什么 ChatGPT 突然变笨了？" |
| 4 | 悬念式 | 故事 / 测评 | "我用了三个月 Cursor，最后换回了 VSCode" |
| 5 | 场景式 | 访谈 / 故事 | "凌晨三点，客服机器人收到了最难的那条消息" |
| 6 | 情感式 | 个人感受 | "写了十年代码，我被一个 agent 整破防了" |
| 7 | 强调式 | 行业 / 资源分享 | "所有做 AI 产品的人，都该看看这份报告" |

标题 15-30 字（公众号后台 ≤64 字符会截断）。

---

## 🎨 可选：HTML 渲染

本 skill 默认只产出 `.md` + `meta.json`。如果要渲染成带主题的 `.html`，推荐用 [mdnice](https://editor.mdnice.com/) 主题：

橙心（默认）/ 灵动蓝 / 简 / 兰青 / 红绯 / 萌粉 / 嫩青 / 重影 / 凝夜紫 / 山吹 / 蓝莹 / 科技蓝 / 雁栖湖 / 极简黑 / 极客黑 / 萌绿 / 绿意

自备 CLI 工具把 Markdown 转成自包含样式 HTML，文件名填 `{文章完整标题}_{主题名}.html`，`meta.json.theme` 填主题名。

---

## 📁 文件结构

```
wechat-article-skill/
├── SKILL.md                    # Claude Code skill 入口（权威文档）
├── AGENTS.md                   # codex / aider / cursor 的薄索引
├── README.md                   # 本文件
├── install_as_skill.sh         # 一键安装脚本
├── .env.example                # WECHAT_APP_ID / WECHAT_APP_SECRET 模板
├── docs/
│   ├── install.md              # 给 AI agent 自动安装读的指引
│   ├── output-spec.md          # 目录与命名规范
│   └── meta-schema.md          # meta.json 字段定义
├── resources/
│   ├── humanizer-zh.md         # 去 AI 化完整指南
│   ├── reference-search.md     # 通用参考资料采集
│   ├── image-sourcing.md       # 配图搜索 / 版权检查 / 水印处理
│   ├── wechat-publish.md       # 草稿箱上传完整流程
│   └── wechat-search.md        # 搜狗微信文章搜索
└── agents/
    └── openclaw.yaml
```

---

## 🔗 相关仓库

- [xhs-writer-skill](https://github.com/JuneYaooo/xhs-writer-skill) —— 小红书笔记生成 skill（姊妹仓库）

## 🙏 致谢

- 去 AI 化规则综合自维基百科「AI 写作特征」、学术降 AI 率实践、中文公众号写作研究（卡兹克写作法）
- 目录规范脱胎于内部写作系统 `记小兰` 的约定

## License

Apache License 2.0，详见 [LICENSE](./LICENSE)。
