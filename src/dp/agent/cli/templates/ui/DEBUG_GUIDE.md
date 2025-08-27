# 调试指南

## 问题：会话初始化失败

如果你遇到"会话初始化失败"的错误，现在可以通过以下方式查看详细错误信息：

### 1. 查看日志文件

所有错误信息都会记录在：
```
/Users/lhappy/workbench/bohr-agent-sdk/websocket.log
```

运行服务后，如果出现错误，可以查看这个文件获取详细信息：
```bash
tail -f /Users/lhappy/workbench/bohr-agent-sdk/websocket.log
```

### 2. 日志内容说明

日志中会包含以下信息：
- 🚀 **Runner 初始化过程**：显示每一步的状态
- 📦 **Agent 创建**：显示配置加载和模块导入过程  
- ❌ **错误详情**：如果失败，会显示完整的错误堆栈

### 3. 常见问题

#### Agent 模块文件不存在
```
❌ Agent模块文件不存在: /path/to/agent.py
```
**解决方法**：检查 `config/agent-config.json` 中的 `module` 路径是否正确

#### 模块导入失败
```
❌ 导入错误: No module named 'xxx'
```
**解决方法**：确保所需的依赖已安装

#### Project ID 无效
```
❌ Runner 初始化失败: Invalid project_id
```
**解决方法**：检查环境变量 `BOHR_PROJECT_ID` 或在 UI 中设置正确的 Project ID

### 4. 调试 API（可选）

如果需要更详细的调试信息，可以设置环境变量启用调试 API：

```bash
export DEBUG=true
python run_server.py
```

然后访问：
- http://localhost:50002/debug.html - 调试面板
- http://localhost:50002/api/debug/config - 配置状态
- http://localhost:50002/api/debug/test-agent - 测试 Agent 创建
- http://localhost:50002/api/debug/runners - Runner 状态
- http://localhost:50002/api/debug/sessions - 会话状态

### 5. 清理日志

日志文件会持续增长，定期清理：
```bash
> /Users/lhappy/workbench/bohr-agent-sdk/websocket.log
```

或者删除旧日志：
```bash
rm /Users/lhappy/workbench/bohr-agent-sdk/websocket.log
```