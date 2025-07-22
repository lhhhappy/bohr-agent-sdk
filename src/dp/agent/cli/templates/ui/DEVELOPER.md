# UI 开发者指南

本文档说明如何开发和拓展 bohr-agent-sdk 的前端 UI。

## 目录结构

```
ui/
├── frontend/                  # React 前端源码
│   ├── src/                  # 源代码目录
│   │   ├── components/       # UI 组件
│   │   │   ├── ChatInterface.tsx    # 聊天界面主组件
│   │   │   ├── FileExplorer.tsx    # 文件浏览器
│   │   │   ├── ShellTerminal.tsx   # 终端组件
│   │   │   ├── MoleculeViewer.tsx  # 分子查看器
│   │   │   └── ...                 # 其他组件
│   │   ├── api/             # API 客户端
│   │   ├── hooks/           # React Hooks
│   │   ├── services/        # 服务层（WebSocket、配置等）
│   │   ├── types/           # TypeScript 类型定义
│   │   └── App.tsx          # 应用主入口
│   ├── public/              # 静态资源
│   ├── ui-static/           # 构建输出（git 已忽略）
│   └── package.json         # 前端依赖
├── config/                  # 配置文件
│   ├── agent-config.default.json  # 默认配置模板
│   └── agent_config.py           # 配置解析器
├── scripts/                 # 构建脚本
│   ├── build_ui.py         # 前端构建脚本
│   └── package_with_ui.sh  # 完整打包脚本
├── websocket-server.py      # WebSocket 服务端
└── ui_utils.py             # UI 启动管理器
```

## 前置要求

### 对于普通用户（只使用 UI）
- Python 3.8+
- pip

### 对于 UI 开发者（修改前端代码）
- Node.js 16+ 和 npm/yarn
- Python 3.8+
- Git

## 安装指南

### 1. 对于普通用户

```bash
# 直接通过 pip 安装即可，已包含预构建的静态文件
pip install git+https://github.com/lhhhappy/bohr-agent-sdk.git@main #目前
```

### 2. 使用 UI

```bash
# 使用配置文件运行
dp-agent run agent --config agent-config.json
```

## 如何拓展 UI

### 1. 添加新组件

在 `frontend/src/components/` 目录下创建新组件：

```tsx
// 例如: frontend/src/components/MyNewComponent.tsx
import React from 'react';

interface MyNewComponentProps {
  title: string;
  onAction?: () => void;
}

export const MyNewComponent: React.FC<MyNewComponentProps> = ({ title, onAction }) => {
  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h3 className="text-lg font-semibold">{title}</h3>
      <button 
        onClick={onAction}
        className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Action
      </button>
    </div>
  );
};
```

### 2. 集成新功能

#### 2.1 添加 API 调用

在 `frontend/src/api/client.ts` 中添加新的 API 方法：

```typescript
export const apiClient = {
  // 现有方法...
  
  // 添加新方法
  async myNewApiCall(params: any) {
    const response = await axios.post('/api/my-endpoint', params);
    return response.data;
  }
};
```

#### 2.2 添加 WebSocket 事件

在 `frontend/src/services/websocket.ts` 中处理新的事件：

```typescript
socket.on('my_new_event', (data) => {
  console.log('Received new event:', data);
  // 处理事件
});
```

### 3. 自定义主题和样式

修改 `frontend/src/styles/index.css` 或使用 Tailwind CSS 类：

```css
/* 自定义主题变量 */
:root {
  --primary-color: #3b82f6;
  --secondary-color: #10b981;
  --background-color: #f3f4f6;
}

/* 自定义组件样式 */
.my-custom-class {
  background-color: var(--primary-color);
  /* ... */
}
```

## 开发流程（仅限 UI 开发者）

### 1. 开发环境设置

```bash
# 克隆项目
git clone https://github.com/lhhhappy/bohr-agent-sdk.git
cd bohr-agent-sdk

# 安装开发依赖
pip install -e .

# 进入前端目录
cd src/dp/agent/cli/templates/ui/frontend
npm install
```

### 2. 开发和测试

```bash
# 在前端目录开发
npm run dev  # 启动开发服务器，支持热重载

# 构建前端
npm run build
```
