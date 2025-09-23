#!/usr/bin/env python3
"""
构建前端静态文件的脚本
在打包发布前运行此脚本以生成静态文件
"""
import os
import subprocess
from pathlib import Path

def build_frontend():
    """构建前端静态文件"""
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    # frontend 在上一级目录
    frontend_dir = script_dir.parent / "frontend"
    
    if not frontend_dir.exists():
        print(f"错误: 找不到前端目录 {frontend_dir}")
        return False
    
    print(f"开始构建前端...")
    os.chdir(frontend_dir)
    
    # 检查是否安装了依赖
    if not (frontend_dir / "node_modules").exists():
        print("安装前端依赖...")
        result = subprocess.run(["npm", "install"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"安装依赖失败: {result.stderr}")
            return False
    
    # 构建前端
    print("构建前端项目...")
    result = subprocess.run(["npm", "run", "build"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"构建失败: {result.stderr}")
        return False
    
    # 检查构建输出
    dist_dir = frontend_dir / "ui-static"
    if not dist_dir.exists():
        print("错误: 构建输出目录不存在")
        return False
    
    print(f"构建成功! 输出目录: {dist_dir}")
    
    # 列出构建的文件
    files = list(dist_dir.rglob("*"))
    print(f"构建了 {len([f for f in files if f.is_file()])} 个文件")
    
    return True

if __name__ == "__main__":
    import sys
    success = build_frontend()
    sys.exit(0 if success else 1)