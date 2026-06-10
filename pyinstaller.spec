# -*- mode: python ; coding: utf-8 -*-
"""
EduLocal Agent PyInstaller 打包配置
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(SPEC))

# 收集 LangChain 相关数据
langchain_datas = collect_data_files('langchain')
langchain_imports = collect_submodules('langchain')

# 收集 ChromaDB 数据
chromadb_datas = collect_data_files('chromadb')

a = Analysis(
    ['backend/main.py'],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=[
        # 配置文件
        ('configs/settings.yaml', 'configs'),
        # 前端构建产物（如果有的话）
        # ('frontend/dist', 'frontend/dist'),
    ] + langchain_datas + chromadb_datas,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # LangChain 相关
        'langchain',
        'langchain_core',
        'langchain_community',
        'langchain_text_splitters',
        # FastAPI 相关
        'fastapi',
        'starlette',
        'pydantic',
        # 数据库相关
        'sqlite3',
        # Embedding 相关
        'sentence_transformers',
        'chromadb',
    ] + langchain_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'notebook',
        'jupyter',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EduLocal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 保留控制台用于查看日志
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EduLocal',
)
