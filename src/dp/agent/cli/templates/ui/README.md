# DP Agent UI Template

这是 DP Agent SDK 的 Web UI 模板，提供了一个基于 WebSocket 的交互界面。

## 快速开始

1. **安装依赖**
   ```bash
   # Python 依赖
   pip install -r requirements.txt
   
   # 前端依赖
   cd frontend && npm install && cd ..
   ```

2. **配置 Agent**
   - 编辑 `agent/agent.py` 实现您的 Agent 逻辑
   - 修改 `agent-config.json` 自定义配置（会自动从 `config/agent-config.default.json` 生成）

3. **运行**
   ```bash
   dp-agent run agent
   ```

## 目录结构

```
├── agent/                 # Agent 实现
│   └── agent_template.py  # Agent 模板文件
├── config/                # 配置文件
│   ├── agent_config.py    # 配置加载器
│   └── agent-config.default.json  # 默认配置
├── frontend/              # React 前端应用
│   └── src/              # 前端源代码
├── websocket-server.py    # WebSocket 服务器
├── ui_utils.py           # UI 工具函数
└── requirements.txt      # Python 依赖
```

## 配置说明

`agent-config.json` 主要配置项：

```json
{
  "agent": {
    "module": "agent.agent",      // Agent 模块路径
    "rootAgent": "root_agent",    // Agent 变量名
    "name": "DP Agent Assistant"  // Agent 名称
  },
  "server": {
    "port": 50002                 // 前端服务端口
  },
  "websocket": {
    "port": 8000                  // WebSocket 端口
  }
}
```

## 开发指南

- **自定义 Agent**：修改 `agent/agent.py`，实现您的业务逻辑
- **修改界面**：前端代码在 `frontend/src/` 目录
- **添加工具**：在 Agent 中通过 ADK 框架添加自定义工具

更多详情请访问 [DP Agent SDK 文档](https://github.com/dptech-corp/Bohrium-Agent-SDK)