#!/bin/bash

##############################################################################
# wechat-article-skill -- Claude Code Skill 安装脚本
#
# 把当前仓库内容拷贝到 ~/.claude/skills/wechat-article-skill/
# 并引导配置（可选的）.env。
#
# 用法: bash install_as_skill.sh
##############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info()    { echo -e "${BLUE}(i)  $1${NC}"; }
print_success() { echo -e "${GREEN}[OK] $1${NC}"; }
print_warning() { echo -e "${YELLOW}(!)  $1${NC}"; }
print_error()   { echo -e "${RED}[X] $1${NC}"; }
print_header()  { echo ""; echo "========================================"; echo "$1"; echo "========================================"; echo ""; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

main() {
    print_header "wechat-article-skill -- 安装"

    SKILL_DIR="$HOME/.claude/skills/wechat-article-skill"
    print_info "目标目录: $SKILL_DIR"

    if [ -d "$SKILL_DIR" ]; then
        print_warning "Skill 目录已存在: $SKILL_DIR"
        read -p "是否覆盖？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "取消"
            exit 0
        fi
        # 备份用户的 .env（含公众号凭证）
        if [ -f "$SKILL_DIR/.env" ]; then
            cp "$SKILL_DIR/.env" "/tmp/wechat-article.env.bak"
            print_info "已备份现有 .env 到 /tmp/wechat-article.env.bak"
        fi
        rm -rf "$SKILL_DIR"
    fi

    print_info "创建 Skill 目录..."
    mkdir -p "$SKILL_DIR"
    print_success "目录已创建"

    print_info "复制项目文件..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    rsync -a \
        --exclude='.git' \
        --exclude='output' \
        --exclude='outputs' \
        --exclude='venv' \
        --exclude='.venv' \
        --exclude='__pycache__' \
        --exclude='.env' \
        "$SCRIPT_DIR/" "$SKILL_DIR/"

    print_success "文件复制完成"

    # 恢复备份的 .env
    if [ -f "/tmp/wechat-article.env.bak" ]; then
        mv "/tmp/wechat-article.env.bak" "$SKILL_DIR/.env"
        print_success "已恢复用户 .env"
    fi

    print_header "配置（写作模式不需要，发布到公众号草稿才需要）"

    if [ -f "$SKILL_DIR/.env" ]; then
        print_info "已存在 .env，跳过"
    else
        cp "$SKILL_DIR/.env.example" "$SKILL_DIR/.env"
        print_success "已生成 $SKILL_DIR/.env"
        print_info "本 skill 的写作模式开箱即用，无需配置。"
        print_warning "仅在需要上传到公众号草稿箱时，才编辑该文件填入："
        print_info "  WECHAT_APP_ID=wx..."
        print_info "  WECHAT_APP_SECRET=..."
        print_info "编辑命令: nano $SKILL_DIR/.env"
    fi

    print_header "安装完成"

    print_success "已装到 $SKILL_DIR"
    echo ""
    print_info "下一步："
    print_info "  1. 重启 Claude Code 让 skill 生效"
    print_info "  2. 直接对 Claude 说: '帮我用 wechat-article 写一篇关于 XXX 的公众号文章'"
    echo ""
}

trap 'print_error "安装过程出错"; exit 1' ERR

main
