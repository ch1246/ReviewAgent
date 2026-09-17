#!/bin/bash
# 安装 Git pre-push hook 到目标项目

if [ -z "$1" ]; then
    echo "用法: bash install_hook.sh <目标项目路径>"
    echo "示例: bash install_hook.sh /path/to/your/project"
    exit 1
fi

TARGET_DIR="$1"
HOOK_SOURCE="$(cd "$(dirname "$0")/hooks" && pwd)/pre-push"
HOOK_TARGET="$TARGET_DIR/.git/hooks/pre-push"

if [ ! -d "$TARGET_DIR/.git" ]; then
    echo "错误：$TARGET_DIR 不是 Git 仓库"
    exit 1
fi

# 复制 hook
cp "$HOOK_SOURCE" "$HOOK_TARGET"
chmod +x "$HOOK_TARGET"

# 设置 AIAGENT_DIR 环境变量
AGENT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "✅ Hook 已安装到 $HOOK_TARGET"
echo "📝 请在目标项目的 .git/hooks/pre-push 中设置 AIAGENT_DIR=$AGENT_DIR"
echo ""
echo "或者设置全局环境变量："
echo "  export AIAGENT_DIR=$AGENT_DIR"
