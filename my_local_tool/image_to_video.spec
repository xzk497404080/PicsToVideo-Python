# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# 获取 ffmpeg 路径
if sys.platform == 'win32':
    ffmpeg_path = os.path.abspath('bin/ffmpeg.exe')
else:
    ffmpeg_path = os.path.abspath('bin/ffmpeg')

if not os.path.exists(ffmpeg_path):
    raise Exception(f"找不到 FFmpeg: {ffmpeg_path}\n请先运行 prepare_ffmpeg.py")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[(ffmpeg_path, '.')],  # 添加 ffmpeg 到二进制文件列表
    datas=[],
    hiddenimports=['cv2', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='图片转视频工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,  # macOS 需要这个
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='图片转视频工具',
)

# macOS 特定配置
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='图片转视频工具.app',
        icon=None,  # 如果有图标文件，在这里指定路径
        bundle_identifier=None,
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
            'NSRequiresAquaSystemAppearance': 'False',
        },
    ) 