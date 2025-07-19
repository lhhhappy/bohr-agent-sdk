#!/bin/bash
# UI 构建脚本

echo "🔨 构建 Agent UI..."

# 切换到 frontend 目录
cd "$(dirname "$0")"

# 安装依赖（如果需要）
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
fi

# 构建
echo "🏗️  构建生产版本..."
npm run build

echo "✅ UI 构建完成！"
echo "📁 静态文件位置: ui-static/"