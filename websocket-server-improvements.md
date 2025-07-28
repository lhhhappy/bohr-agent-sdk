# WebSocket Server 并发安全与会话持久化改进

## 实施的改进内容

### 1. 并发安全的环境变量管理

**问题**：原代码使用 `os.environ["AK"]` 存储用户的访问密钥，在多用户并发访问时会导致竞态条件。

**解决方案**：
- 使用 `threading.Lock` 实现线程安全的环境变量操作
- 创建 `temporary_env_var` 上下文管理器，确保环境变量的设置和恢复是原子操作
- 修改 `process_message` 方法使用上下文管理器包装所有处理逻辑

### 2. 基于AK的会话持久化

**功能特性**：
- 有AK的用户：自动保存和恢复会话历史
- 无AK的用户：临时会话，关闭后不保存

**存储结构**：
```
USER_WORKING_DIR/
├── .agent_sessions/
│   ├── ak_sessions/
│   │   └── {ak_hash}/          # 使用SHA256哈希值（前16位）
│   │       ├── metadata.json    # 用户元信息
│   │       └── sessions/        # 会话文件
│   │           └── {session_id}.json
```

**实现细节**：
- 创建 `PersistentSessionManager` 类管理会话持久化
- 连接时自动加载历史会话
- 消息处理后自动保存
- 断开连接时保存所有会话

### 3. 会话管理API

新增了三个API端点：

#### GET /api/config
- 增强版本，返回用户类型（registered/temporary）

#### DELETE /api/sessions/clear
- 清除当前用户的所有历史会话
- 仅限有AK的用户使用

#### GET /api/sessions/export
- 导出当前用户的所有会话为JSON文件
- 仅限有AK的用户使用

## 安全考虑

1. **AK哈希存储**：不直接存储AK原文，使用SHA256哈希
2. **用户隔离**：每个用户的会话完全隔离
3. **并发安全**：使用线程锁保护共享资源

## 使用效果

### 有AK用户
- 首次访问：创建新会话
- 再次访问：自动恢复历史会话
- 可以管理和导出会话

### 临时用户
- 正常使用所有功能
- 关闭后数据不保存
- 前端显示"临时会话"提示

## 测试建议

1. **并发测试**：
   ```bash
   # 使用不同的AK同时访问
   curl --cookie "appAccessKey=key1" http://localhost:8000/ws
   curl --cookie "appAccessKey=key2" http://localhost:8000/ws
   ```

2. **持久化测试**：
   - 创建会话并发送消息
   - 关闭浏览器
   - 使用相同AK重新连接
   - 验证历史会话恢复

3. **API测试**：
   ```bash
   # 导出会话
   curl --cookie "appAccessKey=key1" http://localhost:8000/api/sessions/export
   
   # 清除会话
   curl -X DELETE --cookie "appAccessKey=key1" http://localhost:8000/api/sessions/clear
   ```