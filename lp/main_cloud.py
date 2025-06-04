import sys
import signal

# 从SDK包中导入所需模块
from dp.agent.cloud.mcp import mcp
from dp.agent.cloud.mqtt import get_mqtt_cloud_instance
from device.tescan_device import TescanDevice

def run_cloud():
    """Run in cloud environment"""
    mqtt_instance = get_mqtt_cloud_instance()
    from dp.agent.device.device.device import register_mcp_tools
    register_mcp_tools(mcp, TescanDevice())
    def signal_handler(sig, frame):
        """Handle SIGINT signal to gracefully shutdown."""
        print("Shutting down...")
        mqtt_instance.stop()
        sys.exit(0)
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start MCP server
    print("Starting MCP server...")
    mcp.run(transport="sse")

if __name__ == "__main__":
    run_cloud()
