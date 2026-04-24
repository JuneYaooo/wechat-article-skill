# AGENTS.md -- 给 codex / aider / cursor 等 agent 的入口说明

本仓库是一个微信公众号文章生成 + 草稿上传 skill，**权威文档在 [`SKILL.md`](./SKILL.md)**。任何涉及"写公众号文章 / 写推文 / 公众号长文 / 上传公众号草稿 / 搜微信文章"的请求，都先完整读 `SKILL.md` 再动手，不要凭本文件的摘要就开跑 —— 下面只是索引。

## 一分钟索引

- **三种模式**：`write`（写作，默认）/ `publish`（上传草稿）/ `search`（搜微信文章）
- **主入口**：读 [`SKILL.md`](./SKILL.md) 的「调用规范」和各模式流程章节
- **产物目录规范**：[`docs/output-spec.md`](./docs/output-spec.md)
- **meta.json 字段**：[`docs/meta-schema.md`](./docs/meta-schema.md)
- **去 AI 化规则**：[`resources/humanizer-zh.md`](./resources/humanizer-zh.md)（5 层原则 + 质量评分）
- **参考搜集 playbook**：[`resources/reference-search.md`](./resources/reference-search.md)
- **配图 + 版权**：[`resources/image-sourcing.md`](./resources/image-sourcing.md)
- **草稿上传完整流程**：[`resources/wechat-publish.md`](./resources/wechat-publish.md)
- **搜狗微信搜索**：[`resources/wechat-search.md`](./resources/wechat-search.md)

## 调用规范（对 agent 的硬约束）

### write 模式

1. **先问三件事**：主题 / 目标读者、标题倾向（按 7 种公式选）、是否同步上传草稿
2. **永远先给大纲让用户确认**（H2 起始，3-5 章），不要直接开写
3. **逐章写正文 + 同步配图**，不留 `【插入图片：...】` 占位符
4. **永远做去 AI 化并输出评分**（按 humanizer-zh 的 5 层 + 总分 50）
5. **文件命名严格按 `docs/output-spec.md`**

### publish 模式

1. **永远确认凭据来源**：env / `.env` / 用户现提供，三选一，不要编
2. **永远先上传封面图拿 `thumb_media_id`，再上传正文图替换 URL，最后创建草稿**
3. **永远明确告知用户**「文章在草稿箱，最终发送需手动点」
4. **绝对不要**尝试用任何接口直接发布（避开安全审查）

### search 模式

1. **仅用作参考资料采集**，结果保存到 `reference/`
2. **不做大规模爬取**，单次任务控制在几十条以内
3. **不绕过反爬**，公众号搜索受限就按 `wechat-search.md` 给的"公众号名 + 关键词"替代方案

## 凭据

- 写作模式：无需任何 key
- 发布模式：`WECHAT_APP_ID` / `WECHAT_APP_SECRET`，从 `~/.claude/skills/wechat-article-skill/.env` 读取，不向上递归读项目 `.env`
- `AppSecret` 一旦进了日志 / git / 对话历史就算泄露，必须在公众号后台重置

## 不要做的事

- 不要跳过大纲确认直接写全文
- 不要在 `.md` 里写 H1 标题（标题放 `meta.json.title`）
- 不要在正文末尾堆"参考来源 / References"（只保存到 `reference/`）
- 不要在 `.md` 里留 `【插入图片：...】` 占位符
- 不要把 `WECHAT_APP_SECRET` 打印到终端 / 写进 git / 放进 issue
- 不要大规模爬搜狗 / 不要试图绕过反爬

## 同步提醒

本文件是薄索引。如果 `SKILL.md` 有新增章节或流程变更，只在 `SKILL.md` 里维护，本文件的锚点列表按需补；**正文描述不要复制到这里**，避免两边漂移。
