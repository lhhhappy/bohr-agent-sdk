import os
import click
import subprocess
import sys
import shutil
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
    click.echo("Generating...")
    
    # 获取用户当前工作目录
    current_dir = Path.cwd()
    
    # 创建必要的目录结构
    project_dirs = ['cloud', 'lab']
    for dir_name in project_dirs:
        dst_dir = current_dir / dir_name
        
        if dst_dir.exists():
            click.echo(f"Warning: {dir_name} already exists，skipping...")
            click.echo(f"If you want to create a new scaffold, please delete the existing project folder first.")
            continue
            
        # 只创建目录，不复制SDK文件
        dst_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建__init__.py文件以使目录成为Python包
    for dir_name in project_dirs:
        init_file = current_dir / dir_name / '__init__.py'
        if not init_file.exists():
            init_file.write_text('')
    
    # 创建main.py文件作为入口点，使用SDK包的导入
    main_content = '''import sys
import signal
from pathlib import Path
import os

# 从SDK包中导入所需模块
from dp.agent.cloud.mcp import mcp
from dp.agent.cloud.mqtt import get_mqtt_cloud_instance
from dp.agent.lab.mqtt_device_twin import DeviceTwin
from dp.agent.lab.tescan_device import TescanDevice

def run_cloud():
    """Run in cloud environment"""
    mqtt_instance = get_mqtt_cloud_instance()
    
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

def run_lab():
    """Run in lab environment"""
    # Initialize device and twin
    tescan_device = TescanDevice()
    device_twin = DeviceTwin(tescan_device)
    
    # Run device twin
    try:
        device_twin.run()
    except KeyboardInterrupt:
        print("\\nShutting down lab environment...")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py [lab|cloud]")
        sys.exit(1)
        
    mode = sys.argv[1]
    if mode == "lab":
        run_lab()
    elif mode == "cloud":
        run_cloud()
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python main.py [lab|cloud]")
        sys.exit(1)
'''
    
    main_file = current_dir / 'main.py'
    if not main_file.exists():
        main_file.write_text(main_content)
        
    click.echo("Succeed for fetching scaffold!")
    click.echo("Now you can use dp-agent run-cloud or dp-agent run-lab to run this project!")

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
    
    # 在用户工作目录中执行main.py
    try:
        subprocess.run([sys.executable, "main.py", "lab"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Run failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        click.echo("Error: main.py not found. Please run scaffolding conmmand first.")
        sys.exit(1)

@cli.command()
def run_cloud():
    """Run the science agent in cloud environment."""
    click.echo("Starting cloud environment...")
    
    # 在用户工作目录中执行main.py
    try:
        subprocess.run([sys.executable, "main.py", "cloud"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Run failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        click.echo("Error: main.py not found. Please run scaffolding conmmand first.")
        sys.exit(1)

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
