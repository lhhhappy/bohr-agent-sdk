"""
文件相关 API
"""
import os
import json
import logging
from pathlib import Path
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse

from config.agent_config import agentconfig

logger = logging.getLogger(__name__)


async def get_file_tree(path: str = None):
    """获取文件树结构"""
    try:
        user_working_dir = os.environ.get('USER_WORKING_DIR', Path.cwd())
        files_config = agentconfig.get_files_config()
        
        def build_tree(directory: Path):
            items = []
            try:
                for item in sorted(directory.iterdir()):
                    if item.name.startswith('.'):
                        continue
                        
                    node = {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file"
                    }
                    
                    if item.is_dir():
                        node["children"] = build_tree(item)
                    else:
                        node["size"] = item.stat().st_size
                        
                    items.append(node)
            except PermissionError:
                pass
            return items
        
        if path is None:
            # Return all watched directories
            watch_directories = files_config.get("watchDirectories", files_config.get("watch_directories", []))
            
            logger.info(f"Files config: {files_config}")
            logger.info(f"Watch directories: {watch_directories}")
            logger.info(f"Full agent config: {agentconfig.config}")
            logger.info(f"Config path: {os.environ.get('AGENT_CONFIG_PATH', 'Not set')}")
            
            # Use watch directories
            all_directories = set(watch_directories)
            
            logger.info(f"All directories to show: {all_directories}")
            
            # Build tree for all directories
            tree = []
            for dir_path in sorted(all_directories):
                # Handle relative paths
                if not os.path.isabs(dir_path):
                    full_path = Path(user_working_dir) / dir_path
                else:
                    full_path = Path(dir_path)
                    
                if not full_path.exists():
                    full_path.mkdir(parents=True, exist_ok=True)
                    
                if full_path.is_dir():
                    dir_node = {
                        "name": dir_path.replace("./", ""),
                        "path": str(full_path),
                        "type": "directory",
                        "isExpanded": True,
                        "children": build_tree(full_path)
                    }
                    tree.append(dir_node)
                    
            logger.info(f"返回的文件树: {json.dumps(tree, indent=2)}")
            return JSONResponse(content=tree)
        else:
            # Handle specific path request
            base_path = Path(user_working_dir) / path
            if not base_path.exists():
                base_path.mkdir(parents=True, exist_ok=True)
            return JSONResponse(content=build_tree(base_path))
        
    except Exception as e:
        logger.error(f"获取文件树错误: {e}")
        return JSONResponse(content=[], status_code=500)


async def get_file_content(file_path: str):
    """获取文件内容"""
    try:
        # Handle absolute paths that were returned by file tree
        if file_path.startswith('/'):
            file = Path(file_path)
        else:
            # Handle relative paths
            user_working_dir = os.environ.get('USER_WORKING_DIR', Path.cwd())
            file = Path(user_working_dir) / file_path
            
        if not file.exists() or not file.is_file():
            return JSONResponse(
                content={"error": "文件未找到"},
                status_code=404
            )
        
        # 判断文件类型
        suffix = file.suffix.lower()
        
        # 文本文件
        if suffix in ['.json', '.md', '.txt', '.csv', '.py', '.js', '.ts', '.log', '.xml', '.yaml', '.yml']:
            try:
                content = file.read_text(encoding='utf-8')
                return PlainTextResponse(content)
            except UnicodeDecodeError:
                return JSONResponse(
                    content={"error": "无法解码文件内容"},
                    status_code=400
                )
        else:
            # 二进制文件
            return FileResponse(file)
            
    except Exception as e:
        logger.error(f"读取文件错误: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )