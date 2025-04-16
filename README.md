# Science Agent SDK

这是DP Tech的Science Agent SDK，提供了一个命令行工具dp-agent，用于管理科学计算任务。

## 安装

### Linux/Mac

```bash
curl -sSL https://raw.githubusercontent.com/dptech-corp/science-agent-sdk/refs/heads/feat/clli/install.sh | bash
```

### Windows

在PowerShell中运行：

```powershell
Invoke-WebRequest -Uri https://raw.githubusercontent.com/dptech-corp/science-agent-sdk/refs/heads/feat/clli/install.sh -OutFile install.sh
bash install.sh
```

## 使用方法

安装后，您可以使用以下命令：

### 获取基础代码结构

```bash
dp-agent fetch-scaffolding
```

### 获取配置文件

```bash
dp-agent fetch-config
```

此命令会下载 .env 配置文件并替换部分动态变量，如 MQTT_DEVICE_ID。
注意：出于安全考虑，此功能仅在内网环境可用。其他环境需要手动配置。

### 运行实验环境

```bash
dp-agent run-lab
```

### 运行云环境

```bash
dp-agent run-cloud
```

### 运行代理

```bash
dp-agent run-agent
```

### 调试云环境

```bash
dp-agent debug-cloud
```

## 开发说明

本SDK提供了一个客户端-服务器架构，用于提交和管理科学计算任务。详细的API文档请参考代码中的注释。
