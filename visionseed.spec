# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# 获取项目根目录
block_cipher = None

# 主要分析选项
a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[
        # 包含必要的资源目录
        ('assets', 'assets'),
        ('config', 'config'),
        ('core', 'core'),
        ('scenes', 'scenes'),
        # 注意：不包含 data 目录，保护用户隐私！
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不必要的模块以减小体积
        'tkinter',
        'unittest',
        'email',
        'http',
        'urllib',
        'xml',
        'pydoc',
        'doctest',
        'argparse',
        'calendar',
        'pdb',
        'pickle',
        'multiprocessing',
        'concurrent',
        'distutils',
        'setuptools',
        'pkg_resources',
        'numpy.random._pickle',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 生成可执行文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建可执行文件（无控制台窗口）
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VisionSeed',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico'  # 移除图标引用，因为不存在
)