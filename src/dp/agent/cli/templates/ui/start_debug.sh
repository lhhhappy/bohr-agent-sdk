#!/bin/bash
# 调试启动脚本

echo "🚀 启动 Agent 调试模式..."
echo "================================"

# 设置调试环境变量
export DEBUG=true
export LOG_LEVEL=DEBUG

# 显示当前配置
echo "📋 当前配置:"
echo "  工作目录: $(pwd)"
echo "  配置文件: ${AGENT_CONFIG_PATH:-config/agent-config.json}"
echo "  Project ID: ${BOHR_PROJECT_ID:-未设置}"
echo ""

# 启动服务器
echo "🌐 启动服务器..."
echo "  主页面: http://localhost:50002"
echo "  调试面板: http://localhost:50002/debug.html"
echo ""
echo "📝 日志输出:"
echo "--------------------------------"

# 使用 python 直接运行，确保看到所有日志
python -u run_server.py 2>&1 | tee debug.log