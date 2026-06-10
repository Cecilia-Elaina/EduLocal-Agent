"""
EduLocal Agent 打包脚本
使用 PyInstaller 打包成可执行文件
"""

import os
import sys
import shutil
from pathlib import Path


def clean_build():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            logger.info(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)


def build_exe():
    """构建可执行文件"""
    import PyInstaller.__main__

    logger.info("开始构建...")

    PyInstaller.__main__.run([
        'pyinstaller.spec',
        '--clean',
        '--noconfirm',
    ])

    logger.info("构建完成！")


def create_installer_info():
    """创建安装说明"""
    readme_content = """
# EduLocal Agent 安装说明

## 系统要求
- Windows 10/11 (64-bit)
- 4GB+ RAM
- 2GB+ 可用磁盘空间

## 安装步骤

1. 解压 EduLocal 文件夹到任意位置
2. 双击运行 `EduLocal.exe`
3. 首次运行会自动创建数据目录 `~/EduLocalData/`
4. 在设置页面配置 API Key

## 使用说明

1. 启动后访问 http://localhost:3000
2. 在设置中配置 DeepSeek/OpenAI API Key
3. 上传教材到知识库
4. 开始对话

## 数据目录

所有数据存储在: `C:\\Users\\你的用户名\\EduLocalData\\`

- `chroma_db/` - 向量数据库
- `sqlite/` - 对话历史
- `configs/` - 配置文件
- `knowledge_base/` - 上传的教材

## 常见问题

### Q: 启动后无法访问网页？
A: 检查端口 3000 是否被占用，或检查防火墙设置。

### Q: 如何使用本地模型？
A: 安装 Ollama (https://ollama.ai)，然后在设置中选择 Ollama。

### Q: API Key 存储在哪里？
A: 存储在 `~/EduLocalData/configs/settings.yaml`，不会上传到任何服务器。
"""
    with open('dist/INSTALL.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)


if __name__ == '__main__':
    from loguru import logger

    logger.info("=" * 50)
    logger.info("EduLocal Agent 打包工具")
    logger.info("=" * 50)

    # 清理旧构建
    clean_build()

    # 构建
    build_exe()

    # 创建安装说明
    create_installer_info()

    logger.info("=" * 50)
    logger.info("打包完成！可执行文件位于 dist/EduLocal/")
    logger.info("=" * 50)
