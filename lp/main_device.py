import sys

# 从SDK包中导入所需模块
from dp.agent.device.mqtt_device_twin import DeviceTwin
# 从本地导入 TescanDevice
from device.tescan_device import TescanDevice
def run_device():
    """Run in lab environment"""
    # Initialize device and twin
    tescan_device = TescanDevice()
    device_twin = DeviceTwin(tescan_device)
    
    # Run device twin
    try:
        device_twin.run()
    except KeyboardInterrupt:
        print("\nShutting down lab environment...")
        sys.exit(0)

if __name__ == "__main__":
    run_device()
