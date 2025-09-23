# Bohrium Science Agent SDK

[English](README.md) | [简体中文](README_CN.md)

**Transform Scientific Software into AI Assistants — 3 Steps to Intelligent Transformation**

## 📖 Introduction

The Bohrium platform introduces the **bohr-agent-sdk Scientific Agent Development Kit**, enabling AI systems to truly execute professional scientific tasks and helping developers quickly build their own specialized research agents. Through a three-step process — **Invoking MCP Tools, Orchestrating Agent Workflows, and Deploying Services** — any scientific software can be rapidly transformed into an AI assistant.

## ✨ Core Features

### 🎯 Intelligent Task Management: Simplified Development, Standardized Output
With a decorator pattern, just a few annotations can quickly transform scientific computing programs into MCP standard services. Built-in application templates turn scattered research code into standardized, reusable intelligent components.

### 🔧 Multi-Backend Framework Support
Supports mainstream Agent open frameworks including Google ADK, Langraph, and Camel, providing flexible choices for developers familiar with different technology stacks.

### ☁️ Flexible Deployment: Local Development, Cloud Production
Dual-mode architecture supports seamless transition between development and production. Local environments enable rapid iteration and feature validation, while Bohrium's cloud GPU clusters handle production-grade computing tasks. The SDK automatically manages the complete workflow of task scheduling, status monitoring, and result collection, with built-in file transfer mechanisms for handling large-scale data uploads and downloads. Developers focus on core algorithm implementation while infrastructure management is fully automated.

### 🖼️ Visual Interactive Interface: Professional Presentation, Intuitive Operation
Based on the modern React framework, deploy fully-featured web applications with one click. Built-in 3D molecular visualization engine supports multiple structure formats and rendering modes for interactive molecular structure display. Real-time data synchronization ensures instant computing status updates, while multi-session management supports parallel task processing. Integrated with enterprise-grade features including file management, project switching, and permission control. Transform command-line tools into professional visual applications, significantly enhancing user experience and tool usability.

## 🖼️ Interface Showcase

### Scientific Computing Master Console
<div align="center">

![SCIMaster](image/SCIMaster.PNG)

*Powerful scientific computing task management and monitoring platform*

</div>

### Visual Interactive Interface
<div align="center">

![UI](image/UI.png)

*Modern web application interface providing intuitive user experience*

</div>

## 🚀 Quick Start

### Installation

```bash
pip install bohr-agent-sdk -i https://pypi.org/simple --upgrade
```

### Build Your Research Agent in 3 Steps

#### Step 1: Get Project Templates

```bash
# Get calculation project template
dp-agent fetch scaffolding --type=calculation

# Get device control project template
dp-agent fetch scaffolding --type=device

# Get configuration file
dp-agent fetch config
```

#### Step 2: Develop Your Agent

**Lab Mode Development Example**

```python
from typing import Dict, TypedDict
from dp.agent.device.device import Device, action, BaseParams, SuccessResult

class TakePictureParams(BaseParams):
    """Picture taking parameters"""
    horizontal_width: str  # Image horizontal width

class PictureData(TypedDict):
    """Picture data structure"""
    image_id: str

class PictureResult(SuccessResult):
    """Picture taking result"""
    data: PictureData

class MyDevice(Device):
    """Custom device class"""
    device_name = "my_device"

    @action("take_picture")
    def take_picture(self, params: TakePictureParams) -> PictureResult:
        """
        Execute picture taking action

        Through the @action decorator, automatically register this method as an MCP standard service
        """
        hw = params.get("horizontal_width", "default")
        # Execute actual device control logic
        return PictureResult(
            message=f"Picture taken with {self.device_name}",
            data={"image_id": "image_123"}
        )
```

**Cloud Mode Development Example**

```python
"""
MCP protocol-based cloud device control example
"""
import signal
import sys
from dp.agent.cloud import mcp, get_mqtt_cloud_instance
from dp.agent.device.device import TescanDevice, register_mcp_tools

def signal_handler(sig, frame):
    """Graceful shutdown handling"""
    print("Shutting down...")
    get_mqtt_cloud_instance().stop()
    sys.exit(0)

def main():
    """Start cloud services"""
    print("Starting Tescan Device Twin Cloud Services...")

    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Create device instance
    device = TescanDevice(mcp, device)

    # Automatically register device tools to MCP server
    # register_mcp_tools implements automatic registration through Python introspection
    register_mcp_tools(device)

    # Start MCP server
    print("Starting MCP server...")
    mcp.run(transport="sse")

if __name__ == "__main__":
    main()
```

#### Step 3: Run and Deploy

```bash
# Local lab environment
dp-agent run tool device

# Cloud computing environment
dp-agent run tool cloud

# Scientific calculation mode
dp-agent run tool calculation

# Start agent (with Web UI)
dp-agent run agent --config

# Debug mode
dp-agent run debug
```

## 🏗️ Project Structure

After running `dp-agent fetch scaffolding`, you'll get a standardized project structure:

```
your-project/
├── lab/                    # Lab mode
│   ├── __init__.py
│   └── tescan_device.py    # Device control implementation
├── cloud/                  # Cloud mode
│   ├── __init__.py
│   └── mcp_server.py       # MCP service implementation
├── calculation/            # Calculation mode
│   └── __init__.py
├── .env                    # Environment configuration
└── main.py                 # Main program entry
```

## ⚙️ Configuration

Configure necessary environment variables in the `.env` file:

```bash
# MQTT connection configuration
MQTT_INSTANCE_ID=your_instance_id
MQTT_ENDPOINT=your_endpoint
MQTT_DEVICE_ID=your_device_id
MQTT_GROUP_ID=your_group_id
MQTT_AK=your_access_key
MQTT_SK=your_secret_key

# Computing resource configuration
BOHRIUM_USERNAME=your_username
BOHRIUM_PASSWORD=your_password
```

Note: The `dp-agent fetch config` command automatically downloads configuration files and replaces dynamic variables (such as MQTT_DEVICE_ID). For security reasons, this feature is only available in internal network environments.

## 🎯 Application Scenarios

- **Materials Science Computing**: Molecular dynamics simulation, first-principles calculations
- **Bioinformatics Analysis**: Gene sequence analysis, protein structure prediction
- **Laboratory Equipment Control**: Intelligent control of research equipment such as electron microscopes and X-ray diffractometers
- **Data Processing Workflows**: Automated data cleaning, analysis, and visualization
- **Machine Learning Training**: Model training, hyperparameter optimization, result evaluation

## 🔧 Advanced Features

### File Management

```bash
# Upload files to cloud
dp-agent artifact upload <path>

# Download cloud files
dp-agent artifact download <artifact_id>
```

### Task Monitoring

The SDK provides real-time task status monitoring, supporting:
- Task queue management
- Computing resource scheduling
- Automatic result collection
- Exception handling and retry mechanisms

## 📚 Documentation & Support

- 📖 [Detailed Documentation](https://dptechnology.feishu.cn/wiki/ZSj9wbLJEiwdNek0Iu7cKsFanuW)

