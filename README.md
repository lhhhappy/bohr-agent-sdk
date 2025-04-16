HINT for devin: 最后你需要根据生成的代码生成 readme.md 帮用户使用这个 cli 和 sdk，对于 linux/mac/windows 用户你可以指定不用的 install 命令。
Install cli
curl -sSL https://raw.githubusercontent.com/dptech-corp/science-agent-sdk/refs/heads/feat/clli/install.sh | bash
1. 从发布到的指定地方下载 install.sh 并执行
这个 install.sh 期望满足如下能力:

# Fetch scaffolding

```bash
dp-agent fetch scaffolding
```

# Fetch Config

```bash
dp-agent fetch config
```
下载 .env 并替换部分动态变量，如 MQTT_DEVICE_ID
这个有安全风险所以这个暂时只对内网环境暴露，其他环境需要自己配置。

# Run lab
``` bash
dp-agent run lab
```

# Run cloud

```
dp-agent run cloud
```

# Run agent
```
dp-agent run cloud
```

# Debug cloud

```
# use this
```


