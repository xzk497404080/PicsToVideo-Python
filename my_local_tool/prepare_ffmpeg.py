import os
import sys
import requests
import zipfile
import shutil
from tqdm import tqdm

def download_ffmpeg():
    """下载对应平台的 ffmpeg"""
    if sys.platform == 'darwin':
        # macOS 版本 - 使用静态构建版本
        url = 'https://evermeet.cx/ffmpeg/getrelease/zip'
        output = 'ffmpeg.zip'
    elif sys.platform == 'win32':
        # Windows 版本
        url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
        output = 'ffmpeg.zip'
    else:
        raise Exception("Unsupported platform")

    print(f"下载 FFmpeg...")
    # 下载文件
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output, 'wb') as f, tqdm(
        desc=output,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            pbar.update(size)
    
    print("解压文件...")
    # 创建 bin 目录
    os.makedirs('bin', exist_ok=True)
    
    # 解压文件
    if sys.platform == 'darwin':
        with zipfile.ZipFile(output, 'r') as zip_ref:
            zip_ref.extractall('bin')
        # 确保文件有执行权限
        ffmpeg_path = os.path.join('bin', 'ffmpeg')
        os.chmod(ffmpeg_path, 0o755)
    elif sys.platform == 'win32':
        with zipfile.ZipFile(output, 'r') as zip_ref:
            zip_ref.extractall('bin')
        # 找到 ffmpeg.exe 并移动
        for root, dirs, files in os.walk('bin'):
            if 'ffmpeg.exe' in files:
                src = os.path.join(root, 'ffmpeg.exe')
                dst = os.path.join('bin', 'ffmpeg.exe')
                if src != dst:
                    shutil.move(src, dst)
                break
    
    # 清理临时文件
    os.remove(output)
    
    print("FFmpeg 准备完成！")
    return os.path.abspath(os.path.join('bin', 'ffmpeg' + ('.exe' if sys.platform == 'win32' else '')))

if __name__ == '__main__':
    try:
        ffmpeg_path = download_ffmpeg()
        print(f"FFmpeg 路径: {ffmpeg_path}")
    except Exception as e:
        print(f"错误: {e}") 