import os
import click
import subprocess
import sys
import shutil
from pathlib import Path
import signal
import uuid
import requests

# 加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    # 查找 .env 文件：先在当前目录，再在项目根目录
    env_file = Path('.env')
    if not env_file.exists():
        # 尝试在包的根目录查找
        env_file = Path(__file__).parent.parent.parent.parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # dotenv 未安装，忽略
    pass

from ..server.storage import storage_dict
from .templates.ui.ui_utils import UIConfigManager, UIProcessManager

@click.group()
def cli():
    """DP Agent CLI tool for managing science agent tasks."""
    pass

@cli.group()
def fetch():
    """Fetch resources for the science agent."""
    pass

@fetch.command()
@click.option('--type', 
              default='calculation',
              type=click.Choice(['calculation', 'device'], case_sensitive=False),
              help='Scaffolding type (calculation/device)')
def scaffolding(type):
    """Fetch scaffolding for the science agent."""
    click.echo(f"Generating {type} project scaffold...")
    
    # 获取模板目录路径
    templates_dir = Path(__file__).parent / 'templates'
    
    # 获取用户当前工作目录
    current_dir = Path.cwd()
    
    
    # Create necessary directory structure
    if type == 'device':
        project_dirs = ['cloud', 'device']
    elif type == 'calculation':
        project_dirs = ['calculation']
        
    for dir_name in project_dirs:
        dst_dir = current_dir / dir_name
        
        if dst_dir.exists():
            click.echo(f"Warning: {dir_name} already exists, skipping...")
            click.echo(f"To create a new scaffold, please delete the existing folder first.")
            continue
            
        # Create directory only
        dst_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files to make directories Python packages
    for dir_name in project_dirs:
        init_file = current_dir / dir_name / '__init__.py'
        if not init_file.exists():
            init_file.write_text('')
    
    # Create main.py from template
    main_template = templates_dir / 'main.py.template'
    main_file = current_dir / 'main.py'
    if not main_file.exists():
        shutil.copy2(main_template, main_file)
    
    
    if type == 'device':
        tescan_template = templates_dir / 'device' / 'tescan_device.py.template'
        tescan_file = current_dir / 'device' / 'tescan_device.py'
        if not tescan_file.exists():
            shutil.copy2(tescan_template, tescan_file)
            click.echo("\nCreated TescanDevice example implementation in device/tescan_device.py")
            click.echo("Please modify this file according to your actual device control requirements.")
    elif type == 'calculation':
        calculation_template = templates_dir / 'calculation' / 'simple.py.template'
        calculation_file = current_dir / 'calculation' / 'simple.py'
        if not calculation_file.exists():
            shutil.copy2(calculation_template, calculation_file)
            click.echo("\nCreated calculation example implementation in calculation/simple.py")
            click.echo("Please modify this file according to your actual calculation requirements.")
    
    click.echo("\nSuccessfully created scaffold!")
    click.echo("Now you can use dp-agent run tool cloud/device/calculation to run this project!")

@fetch.command()
def config():
    """Fetch configuration files for the science agent.
    
    Downloads .env file and replaces dynamic variables like MQTT_DEVICE_ID.
    Note: This command is only available in internal network environments.
    """
    click.echo("Fetching configuration...")
    
    
    remote_env_url = 'https://openfiles.mlops.dp.tech/projects/bohrium-agent/69b192c8c9774a8b860ecb174a218c0b/env-public'
    env_file = Path.cwd() / '.env'
    
    if env_file.exists():
        click.echo("Warning: .env file already exists. Skipping...")
        click.echo("If you want to create a new .env file, please delete the existing one first.")
    else:
        response = requests.get(remote_env_url)
        with open(env_file, 'w') as f:
            f.write(response.text)
        click.echo("Configuration file .env has been created.")
        click.echo("\nIMPORTANT: Please update the following configurations in your .env file:")
        click.echo("1. MQTT_INSTANCE_ID - Your Aliyun MQTT instance ID")
        click.echo("2. MQTT_ENDPOINT - Your Aliyun MQTT endpoint")
        click.echo("3. MQTT_DEVICE_ID - Your device ID")
        click.echo("4. MQTT_GROUP_ID - Your group ID")
        click.echo("5. MQTT_AK - Your Access Key")
        click.echo("6. MQTT_SK - Your Secret Key")
        click.echo("\nFor local development, you may also need to update:")
        click.echo("- MQTT_BROKER and MQTT_PORT")
        click.echo("- TESCAN_API_BASE")
    
    click.echo("\nConfiguration setup completed.")

@cli.group()
def run():
    """Run the science agent in different environments."""
    pass

@run.group()
def tool():
    """Run specific tool environment."""
    pass

@tool.command()
def cloud():
    """Run the science agent in cloud environment."""
    click.echo("Starting cloud environment...")
    
    try:
        subprocess.run([sys.executable, "main.py", "cloud"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Run failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        click.echo("Error: main.py not found. Please run scaffolding command first.")
        sys.exit(1)

@tool.command()
def device():
    """Run the science agent in device environment."""
    click.echo("Starting device environment...")
    
    try:
        subprocess.run([sys.executable, "main.py", "device"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Run failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        click.echo("Error: main.py not found. Please run scaffolding command first.")
        sys.exit(1)

@tool.command()
def calculation():
    """Run the science agent in calculation environment."""
    click.echo("Starting calculation environment...")
    
    try:
        subprocess.run([sys.executable, "main.py", "calculation"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Run failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        click.echo("Error: main.py not found. Please run scaffolding command first.")
        sys.exit(1)

@run.command()
@click.option('--ui/--no-ui', default=True, help='Enable/disable Web UI interface')
@click.option('--config', help='Configuration file path (default: agent-config.json)')
@click.option('--port', type=int, help='Server port (default from config)')
@click.option('--module', help='Agent module path (default: agent)')
@click.option('--agent-name', help='Agent variable name (default: root_agent)')
@click.option('--dev/--prod', default=False, help='Development mode (default: production)')
def agent(ui, config, port, module, agent_name, dev):
    """Run the science agent with optional UI interface."""
    if not ui:
        # 无 UI 模式 - 简单运行
        click.echo("Starting agent in console mode...")
        # TODO: 实现控制台模式
        click.echo("Console mode not yet implemented.")
        return
    
    # UI 模式 - 简化输出
    
    # 查找项目根目录的 agent
    current_dir = Path.cwd()
    
    # 加载配置以获取模块路径
    config_path = Path(config) if config else current_dir / "agent-config.json"
    config_manager = UIConfigManager(config_path if config_path.exists() else None)
    
    # 如果提供了 module 参数，使用它；否则使用配置中的 module
    if module:
        config_manager.config['agent']['module'] = module
    
    agent_module = config_manager.config['agent']['module']
    
    # 检查是否是文件路径（包含 / 或 \ 或以 .py 结尾）
    if '/' in agent_module or '\\' in agent_module or agent_module.endswith('.py'):
        # 作为文件路径处理
        file_path = Path(agent_module)
        
        # 如果是相对路径，基于当前目录解析
        if not file_path.is_absolute():
            file_path = current_dir / file_path
        
        # 检查文件是否存在
        if not file_path.exists():
            click.echo(f"错误: 找不到 agent 文件: {file_path}")
            click.echo("\n请确保:")
            click.echo("1. 文件路径正确")
            click.echo("2. 文件存在并可访问")
            sys.exit(1)
    else:
        # 作为模块路径处理（原有逻辑）
        module_parts = agent_module.split('.')
        module_dir = current_dir / Path(*module_parts[:-1])
        module_file = current_dir / Path(*module_parts[:-1]) / f"{module_parts[-1]}.py"
        module_init = module_dir / "__init__.py"
        
        # 检查模块是否存在
        if not (module_dir.exists() or module_file.exists()):
            click.echo(f"错误: 找不到 {agent_module} 模块。")
            click.echo(f"尝试查找: {module_dir} 或 {module_file}")
            click.echo("\n请确保:")
            click.echo("1. 您已经创建了 agent 模块")
            click.echo("2. 在 config.json 中正确配置了 'agent.module' 路径")
            click.echo("3. 或使用 --module 参数指定正确的模块路径")
            sys.exit(1)
    
    # 智能检测 UI 模板路径
    # 1. 优先使用环境变量指定的路径
    if os.environ.get('UI_TEMPLATE_DIR'):
        ui_dir = Path(os.environ.get('UI_TEMPLATE_DIR'))
    else:
        # 2. 检查是否在开发模式（editable install）
        try:
            # 尝试通过当前文件路径判断
            current_file = Path(__file__).resolve()
            
            # 如果当前文件在 site-packages 中，说明是正常安装
            if 'site-packages' in str(current_file):
                # 使用安装包中的模板
                ui_dir = Path(__file__).parent / "templates" / "ui"
            else:
                # 开发模式，使用源代码中的模板
                ui_dir = current_file.parent / "templates" / "ui"
                click.echo(f"🔧 检测到开发模式，使用源代码路径: {ui_dir}")
                
        except Exception:
            # 降级到默认路径
            ui_dir = Path(__file__).parent / "templates" / "ui"
    
    if not ui_dir.exists():
        click.echo(f"错误: 找不到 UI 模板目录: {ui_dir}")
        click.echo("提示: 可以通过环境变量 UI_TEMPLATE_DIR 指定模板路径")
        sys.exit(1)
    
    # 更新其他配置参数
    if agent_name:
        config_manager.config['agent']['rootAgent'] = agent_name
    if port:
        config_manager.config['server']['port'] = port
    
    # 创建临时配置文件
    temp_config = ui_dir / "config" / "agent-config.temp.json"
    config_manager.save_config(temp_config)
    
    # 设置环境变量
    os.environ['AGENT_CONFIG_PATH'] = str(temp_config)
    os.environ['PYTHONPATH'] = f"{current_dir}:{os.environ.get('PYTHONPATH', '')}"
    
    try:
        # 创建进程管理器
        process_manager = UIProcessManager(ui_dir, config_manager.config)
        
        # 启动服务
        process_manager.start_websocket_server()
        process_manager.start_frontend_server(dev_mode=dev)
        
        # 等待进程
        click.echo("\n按 Ctrl+C 停止服务...")
        process_manager.wait_for_processes()
        
    except KeyboardInterrupt:
        click.echo("\n正在关闭服务...")
        if 'process_manager' in locals():
            process_manager.cleanup()
        sys.exit(0)  # Exit immediately after cleanup
    except Exception as e:
        click.echo(f"错误: {e}")
        if 'process_manager' in locals():
            process_manager.cleanup()
        sys.exit(1)
    finally:
        # 清理临时配置文件
        if 'temp_config' in locals() and temp_config.exists():
            temp_config.unlink()


@cli.group()
def artifact():
    """Manipulate the artifacts."""
    pass

@artifact.command()
@click.argument("path")
@click.option("-p", "--prefix", default=None,
              help="Prefix in the artifact repository where the artifact uploaded to, 'upload/<uuid>' by default")
@click.option("-s", "--scheme", default=None, help="Storage scheme, 'local' by default")
def upload(**kwargs):
    """Upload a file/directory from local to artifact repository"""
    path = kwargs["path"]
    prefix = kwargs["prefix"]
    scheme = kwargs["scheme"]
    if prefix and "://" in prefix:
        offset = prefix.find("://")
        scheme = prefix[:offset]
        prefix = prefix[offset+3:]
    if scheme is None:
        scheme = "local"
    if prefix is None:
        prefix = "upload/%s" % uuid.uuid4()
    storage = storage_dict[scheme]()
    key = storage.upload(prefix, path)
    uri = "%s://%s" % (scheme, key)
    click.echo("%s has been uploaded to %s" % (path, uri))

@artifact.command()
@click.argument("uri")
@click.option("-p", "--path", default=".", help="Path where the artifact downloaded to, '.' by default")
def download(**kwargs):
    """Download an artifact from artifact repository to local"""
    uri = kwargs["uri"]
    path = kwargs["path"]
    if "://" in uri:
        offset = uri.find("://")
        scheme = uri[:offset]
        key = uri[offset+3:]
    else:
        scheme = "local"
        key = uri
    storage = storage_dict[scheme]()
    path = storage.download(key, path)
    click.echo("%s has been downloaded to %s" % (uri, path))


def main():
    cli()

if __name__ == "__main__":
    main()
