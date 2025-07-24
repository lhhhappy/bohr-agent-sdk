# Bohr Agent SDK UI 使用指南

## 简介

Bohr Agent SDK UI 是一个基于 React 和 TypeScript 开发的现代化 Web 界面，为科学计算 Agent 提供了美观、易用的交互界面。UI 已预构建并集成在 SDK 中，无需额外配置即可使用。

## 安装

### 方式一：从 PyPI 安装（推荐）

```bash
pip install bohr-agent-sdk --upgrade
```

### 方式二：从 GitHub 安装最新版本

```bash
pip install git+https://github.com/dptech-corp/bohr-agent-sdk.git #目前
```

### 方式三：从源码安装（开发者）

```bash
git clone https://github.com/dptech-corp/bohr-agent-sdk.git
cd bohr-agent-sdk
pip install -e .
```

## 快速开始
### 1. 基本使用

```bash
# 在包含 agent 模块的项目目录下运行
dp-agent run agent --config agent-config.json
```

浏览器会自动打开 UI 界面（默认地址：http://localhost:50002）

### 2. 命令说明

```bash
dp-agent run agent --config <配置文件路径>
```

- `--config`: 指定配置文件路径（必需）
- UI 会根据配置文件中的设置自动启动

## 配置文件详解

### 完整配置示例

创建 `agent-config.json`：

```json
{
  "agent": {
    "module": "agent.agent",
    "rootAgent": "root_agent",
    "name": "Paper Research Assistant",
    "welcomeMessage": "I am a paper research assistant" 
  },
  "ui": {
    "title": "Paper Research Assistant",
  },
  "server": {
    "port": 50002,
    "host": ["localhost", "127.0.0.1"]
  },
    "files": {
    "watchDirectories": ["./output"] #展示文件目录
    }
}
```

### 配置参数说明

#### agent 部分（必需）

- **module** (string, 必需): Agent 模块的导入路径
  - 例如: `"myproject.agent"` 表示从 myproject 包导入 agent 模块
  
- **rootAgent** (string, 必需): Agent 入口函数名
  - 默认值: `"root_agent"`
  
- **name** (string): Agent 显示名称
  - 在 UI 顶部显示
  
- **welcomeMessage** (string): UI页面展示
  

#### ui 部分（可选）

- **title** (string): 浏览器标签页标题
  - 默认值: "DP Agent Assistant"

#### server 部分（可选）

- **port** (number): HTTP 服务器端口
  - 默认值: 50002
  
- **host** (array/string): 允许访问的主机地址
  - 默认值: ["localhost", "127.0.0.1"]
  - 可以添加其他 IP 地址或域名以允许远程访问

#### files 部分

- **watchDirectories** 监控文件系统
  - 默认值: ["./output"]


## UI 功能特性

### 核心功能

1. **聊天界面**
   - 支持 Markdown 渲染
   - 代码高亮显示
   - 支持表格、列表、链接等富文本格式
   - 消息历史记录

2. **文件浏览器**
   - 实时显示监视目录的文件
   - 支持文件预览和下载
   - 支持图片查看
   - 支持分子结构文件（.xyz）3D 查看

3. **终端集成**
   - 显示 Agent 执行的命令
   - 实时输出命令结果
   - 支持 ANSI 颜色代码

4. **会话管理**
   - 多会话支持
   - 会话历史记录
   - 会话切换和删除

### 技术特点

- **零依赖部署**：用户无需安装 Node.js，UI 已预构建
- **实时通信**：基于 WebSocket 的双向实时通信
- **响应式设计**：适配不同屏幕尺寸
- **现代化技术栈**：React + TypeScript + Tailwind CSS

## 故障排除

### 1. 找不到 agent 模块

**错误信息**: `ModuleNotFoundError: No module named 'xxx.agent'`

**解决方案**:
- 确保在包含 agent 模块的正确目录下运行命令
- 检查配置文件中的 `module` 路径是否正确
- 确认 agent 模块文件存在且有 `root_agent` 函数

### 2. 端口被占用

**错误信息**: `[Errno 48] Address already in use`

**解决方案**:
```json
// 在配置文件中修改端口
{
  "server": {
    "port": 8080  // 改为其他端口
  },
}
```

### 3. UI 无法加载

**检查项**:
- 确认浏览器地址是否正确（默认 http://localhost:50002）
- 查看浏览器控制台（F12）是否有错误信息
- 检查防火墙或安全软件是否阻止了连接
- 确认 WebSocket 端口（默认 8000）没有被占用

### 4. WebSocket 连接失败

**错误信息**: `WebSocket connection failed`

**解决方案**:
- 检查 WebSocket 端口是否与配置文件一致
- 确认没有代理软件干扰 WebSocket 连接
- 尝试使用不同的端口


## 更新版本

```bash
# 更新到最新版本
pip install --upgrade bohr-agent-sdk

# 查看当前版本
pip show bohr-agent-sdk
```

## 相关文档

- [开发者指南](src/dp/agent/cli/templates/ui/DEVELOPER.md) - 如何开发和更新 UI
- [项目主页](https://github.com/dptech-corp/bohr-agent-sdk)