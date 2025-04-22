"""
Example of using the science-agent-sdk cloud functionality.
"""
import signal
import sys
from src.dp.agent.cloud import mcp, get_mqtt_cloud_instance, register_device_tools
from src.dp.agent.device import TescanDevice

def signal_handler(sig, frame):
    """Handle SIGINT signal to gracefully shutdown."""
    print("Shutting down...")
    get_mqtt_cloud_instance().stop()
    sys.exit(0)

def main():
    """Start the cloud services."""
    print("Starting Tescan Device Twin Cloud Services...")
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create device instance
    device = TescanDevice()
    
    # Register device tools
    register_device_tools(device)
    
    # Start MCP server
    print("Starting MCP server...")
    mcp.run(transport="sse")

if __name__ == "__main__":
    main() 