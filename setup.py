from setuptools import setup, find_packages

setup(
    name="science-agent-sdk",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "click",
        "mcp",  # 基于现有代码推断可能需要的依赖
    ],
    entry_points={
        "console_scripts": [
            "dp-agent=dp.agent.cli.cli:main",
        ],
    },
)
