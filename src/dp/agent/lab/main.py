#!/usr/bin/env python
# coding=utf-8
"""
Main entry point for the lab component.

This script starts the MQTT device twin service.
"""
from .mqtt_device_twin import DeviceTwin
from .tescan_device import TescanDevice

def main():
    """Start the lab services."""
    print("Starting Device Twin Lab Services...")
    
    tescan_device = TescanDevice()
    
    device_twin = DeviceTwin(tescan_device)
    
    device_twin.run()

if __name__ == "__main__":
    main()
