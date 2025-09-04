#!/usr/bin/env python3
"""测试文件下载功能"""

import os
import sys
import time
import tempfile
import requests
from pathlib import Path

def test_download_api():
    """测试下载 API"""
    
    # API 基础地址
    base_url = "http://localhost:8001"
    
    print("=" * 60)
    print("文件下载功能测试")
    print("=" * 60)
    
    # 1. 创建测试文件
    test_dir = Path(tempfile.gettempdir()) / "download_test"
    test_dir.mkdir(exist_ok=True)
    
    # 创建测试文件
    test_file = test_dir / "test.txt"
    test_file.write_text("This is a test file for download functionality.\n测试文件下载功能。")
    
    test_json = test_dir / "data.json"
    test_json.write_text('{"name": "test", "value": 123}')
    
    # 创建子目录和文件
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir(exist_ok=True)
    (sub_dir / "file1.txt").write_text("File 1 content")
    (sub_dir / "file2.txt").write_text("File 2 content")
    
    print(f"✅ 测试文件已创建在: {test_dir}")
    print()
    
    # 2. 测试单文件下载
    print("测试单文件下载...")
    try:
        # 模拟文件下载请求
        file_path = str(test_file)
        download_url = f"{base_url}/api/download/file{file_path}"
        
        print(f"  下载 URL: {download_url}")
        print(f"  预期结果: 文件应该可以正常下载")
        print()
        
        # 注意：实际测试需要运行服务器并通过浏览器或 curl 测试
        print("  💡 请在浏览器中打开以下链接测试下载:")
        print(f"     {download_url}")
        print()
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        print()
    
    # 3. 测试文件夹下载
    print("测试文件夹下载...")
    try:
        # 模拟文件夹下载请求
        folder_path = str(sub_dir)
        download_url = f"{base_url}/api/download/folder{folder_path}"
        
        print(f"  下载 URL: {download_url}")
        print(f"  预期结果: 文件夹应打包为 zip 下载")
        print()
        
        print("  💡 请在浏览器中打开以下链接测试下载:")
        print(f"     {download_url}")
        print()
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        print()
    
    # 4. 测试说明
    print("=" * 60)
    print("测试说明:")
    print("1. 确保 Agent UI 服务正在运行 (端口 8001)")
    print("2. 在浏览器中打开文件浏览器")
    print("3. 测试以下功能:")
    print("   - 点击文件旁的下载图标下载单个文件")
    print("   - 点击文件夹旁的下载图标下载整个文件夹（zip格式）")
    print("   - 在文件预览界面点击下载按钮")
    print("4. 验证下载的文件内容是否正确")
    print("=" * 60)
    
    # 清理测试文件（可选）
    # import shutil
    # shutil.rmtree(test_dir)
    # print(f"\n✅ 测试文件已清理")

if __name__ == "__main__":
    test_download_api()