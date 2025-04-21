import os
import click
import subprocess
import sys
from pathlib import Path
import signal

@click.group()
def cli():
    """DP Agent CLI tool for managing science agent tasks."""
    pass

@cli.group()
def fetch():
    """Fetch resources for the science agent."""
    pass

@fetch.command()
def scaffolding():
    """Fetch scaffolding for the science agent."""
    click.echo("Fetching scaffolding...")
    click.echo("Scaffolding fetched successfully.")

@fetch.command()
def config():
    """Fetch configuration files for the science agent.
    
    Downloads .env file and replaces dynamic variables like MQTT_DEVICE_ID.
    Note: This command is only available in internal network environments.
    """
    click.echo("Fetching configuration...")
    click.echo("Configuration fetched successfully.")

@cli.command()
def run_lab():
    """Run the science agent in lab environment."""
    click.echo("Starting lab environment...")
    
    from ..lab.mqtt_device_twin import DeviceTwin
    from ..lab.tescan_device import TescanDevice
    
    # Create device instance
    tescan_device = TescanDevice()
    
    # Create device twin
    device_twin = DeviceTwin(tescan_device)
    
    # Run device twin
    device_twin.run()
    
    click.echo("Lab environment started.")

@cli.command()
def run_cloud():
    """Run the science agent in cloud environment."""
    click.echo("Starting cloud environment...")
    
    from ..cloud.mcp import mcp
    from ..cloud.mqtt import get_mqtt_cloud_instance
    
    def signal_handler(sig, frame):
        """Handle SIGINT signal to gracefully shutdown."""
        click.echo("Shutting down...")
        get_mqtt_cloud_instance().stop()
        sys.exit(0)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start MCP server
    click.echo("Starting MCP server...")
    mcp.run(transport="sse")
    
    click.echo("Cloud environment started.")

@cli.command()
def run_agent():
    """Run the science agent."""
    click.echo("Starting agent...")
    click.echo("Agent started.")

@cli.command()
def debug_cloud():
    """Debug the science agent in cloud environment."""
    click.echo("Starting cloud environment in debug mode...")
    click.echo("Cloud environment debug mode started.")

def main():
    cli()

if __name__ == "__main__":
    main()
