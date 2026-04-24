# wechat-article-skill 安装指南（给 AI agent 读）

> 本文档是**让 AI 助手自动完成安装**的可执行指引。Claude Code / OpenClaw / Codex / Cursor / Trae / Hermes Agent 等任一 agent 按以下步骤执行即可。
>
> 人类用户请**不要**手动照抄下面的步骤，直接把这份 URL 扔给你的 AI 助手，它自己会跑通。

## 项目一句话介绍

`wechat-article-skill` 是一个 Claude Code / OpenClaw Skill，把一个主题变成一篇 2000-4000 字的微信公众号推文，并可以选配上传到公众号草稿箱。

仓库：https://github.com/JuneYaooo/wechat-article-skill

## 前置依赖（agent 请先检查）

- **必需**：`git`、`bash`、`rsync`、`curl`
- **推荐**：`python3`（发布草稿时用来解析 JSON，几乎所有系统都自带）

## 安装步骤

### 1. 克隆仓库到临时目录

```bash
git clone https://github.com/JuneYaooo/wechat-article-skill.git /tmp/wechat-article-skill
cd /tmp/wechat-article-skill
```

### 2. 跑安装脚本

```bash
bash install_as_skill.sh
```

这一步会：

- 把项目文件拷贝到 `~/.claude/skills/wechat-article-skill/`
- 从 `.env.example` 生成 `~/.claude/skills/wechat-article-skill/.env` 骨架

安装脚本**交互式**，目标目录已存在时会问是否覆盖；agent 可以用 `yes | bash install_as_skill.sh` 自动选"是"。

### 3. 问用户是否要配置公众号凭证

**写作模式无需任何 key**，如果用户只想用 skill 写文章、不上传草稿，跳过本步。

如果用户想**直接把文章上传到公众号草稿箱**，agent 主动问用户：

> 你想开启「自动上传到公众号草稿箱」功能吗？如果要，请提供：
> 1. 公众号后台的 AppID（形如 `wx...`）
> 2. 公众号后台的 AppSecret
>
> 来源：公众号后台 → 设置与开发 → 基本配置 → 开发者 ID / 开发者密码。
>
> ⚠️ AppSecret 会被写到 `~/.claude/skills/wechat-article-skill/.env`（已 gitignore），一旦泄露可被冒用发文，请确认环境安全。

用户同意后写入 `~/.claude/skills/wechat-article-skill/.env`：

```bash
WECHAT_APP_ID=<用户提供>
WECHAT_APP_SECRET=<用户提供>
```

（可选）作者默认名和封面图生图服务也可以在此时一起配。

### 4. 提示用户重启 agent

装完之后告诉用户：

> 已装到 `~/.claude/skills/wechat-article-skill/`。请**重启 Claude Code**（或你正在用的 agent）让 skill 生效。

### 5.（可选）清理临时目录

```bash
rm -rf /tmp/wechat-article-skill
```

## 冒烟测试（用户重启 agent 后）

告诉用户直接跟 agent 说：

> 帮我用 **wechat-article** 写一篇 2000 字公众号文章，主题「猫为什么是液体」，标题走悬念式。

正常的话 agent 会：先问目标读者 → 搜参考 → 给大纲 → 写正文配图 → 去 AI 化 → 给产物路径。

想顺带上传草稿的话再接一句：

> 把这篇上传到公众号草稿箱。

## 常见问题（给 agent 参考）

- **Claude Code 识别不到 skill** → 确认目录是 `~/.claude/skills/wechat-article-skill/`，完全重启过 Claude Code
- **用户问"能不能用测试号"** → 可以，测试号和正式号接口一致，只是 AppID / AppSecret 不同
- **`errcode: 40013 invalid appid`** → 检查 AppID 是否填错，或该 AppID 是否有草稿 API 权限（订阅号默认无，需服务号或已认证订阅号）
- **`errcode: 45009 api freq out of limit`** → 公众号接口频率限制，让用户等几分钟
- **`ip not in whitelist`** → 公众号后台设置了 IP 白名单，需加入当前运行机器的公网 IP
- **用户问"能不能直接发布而不是草稿"** → 本 skill 只走草稿箱，最终「发送」动作需用户手动在后台确认，这是有意的安全设计，不要试图绕过

## 完成标志

以下两条都满足即视为写作模式安装成功：

1. `~/.claude/skills/wechat-article-skill/SKILL.md` 存在
2. agent 重启后，用户用自然语言要求写公众号文章时能触发本 skill

以下同时满足即视为发布模式也可用：

3. `~/.claude/skills/wechat-article-skill/.env` 里 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET` 为非占位符真实值

装完不用逐字读 `SKILL.md`，但需要告诉用户：

> 你可以直接用自然语言要公众号文章，skill 会先问你标题倾向和目标读者；写完如果你配了公众号 AppID/AppSecret，我还可以直接帮你上传到草稿箱，但最终「发送」需要你到公众号后台手动确认。
