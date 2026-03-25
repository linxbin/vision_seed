# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

# 获取项目根目录
block_cipher = None
cv2_binaries = collect_dynamic_libs('cv2')
cv2_hiddenimports = collect_submodules('cv2')

# 主要分析选项
a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=cv2_binaries,
    datas=[
        # 包含必要的资源目录
        ('assets', 'assets'),
        ('config/user_preferences.example.json', 'config'),
        # 注意：不包含 data 目录，保护用户隐私！
    ],
    hiddenimports=cv2_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不必要的模块以减小体积
        'tkinter',
        'pydoc',
        'doctest',
        'pdb',
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
    [],
    exclude_binaries=True,
    name='视芽',
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
    icon='assets/branding/shiya_app_icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='VisionSeed',
)
