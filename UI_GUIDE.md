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
# 设置环境变量（本地测试时）
export BOHR_ACCESS_KEY=xxx  # 填写你的 Bohrium Access Key
export BOHR_APP_KEY=0 # Mock App_Key
# 在包含 agent 模块的项目目录下运行
dp-agent run agent --config config.json
```

启动后会显示：
```
🚀 WebSocket 服务器已启动（端口 50001）
📝 查看日志: websocket.log
✨ Agent UI 已启动: http://localhost:50001

按 Ctrl+C 停止服务...
```

### 2. 命令说明

```bash
dp-agent run agent --config <配置文件路径>
```

- `--config`: 指定配置文件路径（必需）
- UI 会根据配置文件中的设置自动启动

**注意**：
- 本地测试时需要设置 `BOHR_ACCESS_KEY` ,`BOHR_APP_KEY`环境变量
- 部署到 Bohrium App 时，用户在浏览器中会自动捕获 Access Key

## 配置文件详解

### 完整配置示例

创建 `config.json`：

```json
{
  "agent": {
    "module": "agent.py",
    "name": "Paper Research Assistant",
    "welcomeMessage": "I am a paper research assistant"
  },
  "ui": {
    "title": "Paper Research Assistant"
  },
  "server": {
    "port": 50001,
    "host": ["localhost", "127.0.0.1", "*"]
  }
}
```

### 配置参数说明

#### agent 部分（必需）

- **module** (string, 必需): Agent 模块路径
  - 例如: `"agent.py"` 表示 ADK agent 存放位置
  
- **name** (string): Agent 显示名称
  - 在 UI 界面上显示的助手名称
  
- **welcomeMessage** (string): 欢迎消息
  - Agent 启动时在 UI 中显示的欢迎语
  

#### ui 部分（可选）

- **title** (string): 浏览器标签页标题
  - 网页浏览器标签页上显示的标题

#### server 部分（可选）

- **port** (number): 后端启动端口
  - 默认值: 50001
  
- **host** (array/string): 允许访问的主机地址
  - `["localhost", "127.0.0.1"]`: 仅允许本地访问
  - `"*"`: 允许外部所有地址访问，适合部署在 App 或服务器时使用



## Agent 开发指南

### Agent.py 编写示例

为了支持不同 Bohrium 用户访问并获取其 Access Key、App Key 以及 project_id，需要使用以下标准接口：

#### 基础示例

```python
import os
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

# 加载环境变量（API Key 等）
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def create_agent(ak=None, app_key=None, project_id=None):
    """SDK 标准接口
    
    Args:
        ak: Bohrium Access Key
        app_key: Bohrium App Key  
        project_id: Bohrium 项目 ID
    """
    
    # 定义工具函数
    def my_tool(param: str):
        """工具描述"""
        return "result"
    
    # 创建并返回 Agent（相当于之前的 root_agent）
    return LlmAgent(
        name="my_agent",
        model=LiteLlm(model="deepseek/deepseek-chat"), 
        instruction="Agent 指令",
        tools=[my_tool]  # 注册工具
    )
```

## UI 功能特性

### 核心功能

1. **聊天界面**
   - 支持 Markdown 渲染（包括表格、列表、链接等）
   - 代码高亮显示（支持多种编程语言）
   - 消息历史记录本地存储
   - 打字机动画效果
   - 消息动画过渡

2. **文件管理**
   - 实时文件树展示（支持文件夹结构）
   - 多格式文件预览：
     - 图片查看器（PNG、JPG、SVG 等）
     - 文本文件查看器（带语法高亮）
     - CSV 表格视图
     - JSON 树形视图和格式化显示
     - HTML 文件预览
     - 分子结构文件 3D 可视化（.xyz、.pdb、.mol 等）
   - 文件变更实时监听

3. **终端集成**
   - 工具调用结果展示（ToolResultDisplay）
   - 命令执行状态显示
   - 支持 ANSI 颜色代码

4. **Bohrium 集成**
   - 项目列表动态获取
   - Project ID 选择器（下拉列表）
   - AccessKey 自动捕获（部署模式）
   - 项目状态实时更新
   - 错误重试机制



