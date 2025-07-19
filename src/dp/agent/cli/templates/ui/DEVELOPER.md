# UI 开发者指南

本文档说明如何开发和更新 bohr-agent-sdk 的前端 UI。

## 目录结构

```
ui/
├── frontend/           # React 前端源码
│   ├── src/           # 源代码
│   ├── public/        # 静态资源
│   ├── dist/          # 构建输出（git 已忽略）
│   └── package.json   # 前端依赖
├── scripts/           # 构建脚本
│   ├── build_ui.py    # 前端构建脚本
│   └── package_with_ui.sh # 完整打包脚本
├── websocket-server.py # WebSocket 服务端
└── ui_utils.py        # UI 启动管理器

```

## 开发流程

### 1. 本地开发

```bash
# 进入前端目录
cd src/dp/agent/cli/templates/ui/frontend

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev
```

然后在另一个终端启动后端：

```bash
# 在项目根目录
dp-agent run agent --dev
```

### 2. 更新前端

#### 2.1 修改代码

在 `frontend/src` 下修改相应的组件或页面。

#### 2.2 测试修改

```bash
# 开发模式测试
dp-agent run agent --dev

# 生产模式测试（需要先构建）
cd src/dp/agent/cli/templates/ui/frontend
npm run build
dp-agent run agent  # 默认使用生产模式
```

#### 2.3 构建前端

```bash
# 方式1：直接在前端目录构建
cd src/dp/agent/cli/templates/ui/frontend
npm run build

# 方式2：使用构建脚本
python src/dp/agent/cli/templates/ui/scripts/build_ui.py
```

### 3. 发布新版本

#### 3.1 完整发布流程

```bash
# 1. 更新版本号
# 编辑 pyproject.toml 或 setup.py，增加版本号

# 2. 构建并打包
bash src/dp/agent/cli/templates/ui/scripts/package_with_ui.sh

# 3. 上传到 PyPI
twine upload dist/*

# 4. 创建 Git tag
git tag v0.1.13
git push origin v0.1.13
```

#### 3.2 快速更新（仅前端改动）

如果只是前端的小改动：

```bash
# 1. 构建前端
cd src/dp/agent/cli/templates/ui/frontend
npm run build

# 2. 更新补丁版本号 (如 0.1.12 -> 0.1.13)
# 编辑 pyproject.toml

# 3. 重新打包发布
cd 项目根目录
python -m build
twine upload dist/*
```

## 注意事项

1. **不要提交 dist 目录**：前端构建产物已在 .gitignore 中，打包时会自动构建。

2. **版本管理**：即使是前端的小改动，也需要更新 Python 包版本号。

3. **依赖更新**：如果更新了前端依赖，记得提交 `package-lock.json`。

4. **测试**：发布前请在生产模式下测试。

## 常见问题

### Q: 为什么前端改动需要发布整个包？

A: 这是当前的设计决策，确保用户获得一致的体验。未来可能会支持独立的前端更新机制。

### Q: 如何调试前端？

A: 使用 `--dev` 模式运行，前端会启动在开发模式，支持热重载和调试。

### Q: 构建失败怎么办？

A: 检查 Node.js 版本（建议 16+），清理 node_modules 重新安装：
```bash
rm -rf node_modules package-lock.json
npm install
```