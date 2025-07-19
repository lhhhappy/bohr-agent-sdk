#!/bin/bash
# 打包前构建 UI 的脚本

echo "=== 开始打包 bohr-agent-sdk ==="

# 1. 构建前端
echo "1. 构建前端静态文件..."
python build_ui.py
if [ $? -ne 0 ]; then
    echo "前端构建失败!"
    exit 1
fi

# 2. 清理旧的构建文件
echo "2. 清理旧的构建文件..."
rm -rf dist/ build/ src/*.egg-info

# 3. 构建 Python 包
echo "3. 构建 Python 包..."
python -m build

# 4. 显示构建结果
echo "4. 构建完成！"
ls -la dist/

echo "=== 打包完成 ==="
echo "可以使用以下命令上传到 PyPI："
echo "twine upload dist/*"