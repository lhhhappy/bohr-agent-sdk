"""
Agent Configuration Loader

This module provides a centralized configuration system for different agent implementations.
To switch between different agents, modify the agent-config.json file.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
import importlib

class AgentConfig:
    def __init__(self, config_path: str = None):
        # 优先使用环境变量中的配置路径
        if config_path is None:
            env_path = os.environ.get('AGENT_CONFIG_PATH', 'config/agent-config.json')
            self.config_path = Path(env_path)
        else:
            self.config_path = Path(config_path)
        
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            # Fallback to default config if file doesn't exist
            return self._get_default_config()
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Provide default configuration for Agent"""
        # 使用环境变量提供的端口，如果没有则使用默认值
        default_port = int(os.environ.get('AGENT_SERVER_PORT', '50002'))
        
        return {
            "agent": {
                "name": "My Agent",
                "description": "Agent",
                "welcomeMessage": "welcome to chat with me",
                "module": "agent.subagent",
                "rootAgent": "rootagent"
            },
            "ui": {
                "title": "Agent",
                "features": {
                    "showFileExplorer": True,
                    "showSessionList": True
                }
            },
            "files": {
                "watchDirectories": ["./output"]
            },
            "server": {
                "host": ["localhost", "127.0.0.1"],
                "port": default_port
            }
        }
    
    def get_agent(self, ak: str = None):
        """Dynamically import and return the configured agent
        
        Args:
            ak: Optional access key to pass to the agent
        """
        agentconfig = self.config.get("agent", {})
        module_name = agentconfig.get("module", "agent.subagent")
        agentname = agentconfig.get("rootAgent", "rootagent")
        
        try:
            module = importlib.import_module(module_name)
            
            # 检查是否有 create_agent 函数（推荐的方式）
            if hasattr(module, 'create_agent'):
                # 使用工厂函数创建新的 agent 实例
                # 检查函数是否接受 ak 参数
                import inspect
                sig = inspect.signature(module.create_agent)
                if 'ak' in sig.parameters:
                    return module.create_agent(ak=ak)
                else:
                    # 后向兼容：不接受 ak 参数
                    return module.create_agent()
            else:
                # 后向兼容：直接返回模块级别的 agent
                return getattr(module, agentname)
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Failed to load agent {agentname} from {module_name}: {e}")
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI-specific configuration"""
        return self.config.get("ui", {})
    
    def get_files_config(self) -> Dict[str, Any]:
        """Get file handling configuration"""
        return self.config.get("files", {})
    
    def get_websocket_config(self) -> Dict[str, Any]:
        """Get WebSocket configuration"""
        return self.config.get("websocket", {})
    
    def get_tool_display_name(self, tool_name: str) -> str:
        """Get display name for a tool"""
        tools_config = self.config.get("tools", {})
        display_names = tools_config.get("displayNames", {})
        return display_names.get(tool_name, tool_name)
    
    def is_long_running_tool(self, tool_name: str) -> bool:
        """Check if a tool is marked as long-running"""
        tools_config = self.config.get("tools", {})
        long_running = tools_config.get("longRunningTools", [])
        return tool_name in long_running
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration including port and allowed hosts"""
        # 默认主机始终被允许
        default_hosts = ["localhost", "127.0.0.1", "0.0.0.0"]
        
        server_config = self.config.get("server", {})
        
        # 支持 "host" 字段（用户配置）和 "allowedHosts"（向后兼容）
        user_hosts = server_config.get("host", server_config.get("allowedHosts", []))
        
        # 确保 user_hosts 是列表
        if isinstance(user_hosts, str):
            user_hosts = [user_hosts]
        elif not isinstance(user_hosts, list):
            user_hosts = []
            
        # 合并默认主机和用户定义的额外主机
        all_hosts = list(set(default_hosts + user_hosts))  # 使用 set 去重
        
        # 使用环境变量或配置的端口，最后使用默认端口
        default_port = int(os.environ.get('AGENT_SERVER_PORT', '50002'))
        port = server_config.get("port", default_port)
        
        return {
            "port": port,
            "allowedHosts": all_hosts
        }

# Singleton instance
agentconfig = AgentConfig()