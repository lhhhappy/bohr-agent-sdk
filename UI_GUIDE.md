# Bohr Agent SDK UI 使用指南

## 新用户安装

### 方式一：从 PyPI 安装（推荐）

```bash
pip install bohr-agent-sdk --upgrade
```

### 方式二：从 GitHub 安装最新版本

```bash
pip install git+https://github.com/lhhhappy/bohr-agent-sdk.git@main
```

### 方式三：从源码安装（开发者）

```bash
git clone https://github.com/lhhhappy/bohr-agent-sdk.git
cd bohr-agent-sdk
pip install -e .
```

## 使用 UI

### 基本使用

```bash
# 在包含 agent 模块的项目目录下运行
dp-agent run agent --config agent-config.json
```

浏览器会自动打开 UI 界面（默认地址：http://localhost:50002）

### 配置文件示例

创建 `agent-config.json`：

```json
{
  "agent": {
    "module": "your_agent.agent",
    "rootAgent": "root_agent",
    "name": "My Agent",
    "description": "我的智能助手",
    "welcomeMessage": "欢迎使用！"
  },
  "server": {
    "port": 50002
  },
  "websocket": {
    "port": 8000
  }
}
```

### 命令行参数

```bash
# 指定端口
dp-agent run agent --port 8080 --ws-port 8001

# 指定模块
dp-agent run agent --module myagent.agent

# 开发模式（需要 Node.js 环境）
dp-agent run agent --dev

# 无 UI 模式（即将支持）
dp-agent run agent --no-ui
```

## 特性说明

- **零依赖**：不需要安装 Node.js，内置静态文件服务
- **实时交互**：通过 WebSocket 与 Agent 实时通信
- **文件管理**：支持查看和下载 Agent 生成的文件
- **美观界面**：现代化的 UI 设计，响应式布局

## 故障排除

### 1. 找不到 agent 模块

确保：
- 在正确的目录运行命令
- 配置文件中的 `module` 路径正确
- Agent 模块已正确实现

### 2. 端口被占用

修改端口：
```bash
dp-agent run agent --port 8080 --ws-port 8001
```

### 3. UI 无法加载

检查：
- 防火墙设置
- 浏览器控制台错误信息
- WebSocket 连接是否正常

## 更新到最新版本

```bash
# 更新整个 SDK（包括 UI）
pip install --upgrade bohr-agent-sdk

# 或从 GitHub 更新
pip install --upgrade git+https://github.com/lhhhappy/bohr-agent-sdk.git@main
```

## 相关文档

- [开发者指南](src/dp/agent/cli/templates/ui/DEVELOPER.md) - 如何开发和更新 UI
- [项目主页](https://github.com/lhhhappy/bohr-agent-sdk)