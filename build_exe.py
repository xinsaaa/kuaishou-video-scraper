#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快手视频信息爬取工具 - PyInstaller 打包脚本
适配 conda 环境: kuaishou
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 项目配置
PROJECT_NAME = "快手视频信息爬取工具"
MAIN_SCRIPT = "gui_app.py"
CONDA_ENV = "kuaishou"
ICON_FILE = "icon.ico"  # 如果有图标文件的话

# 打包配置
PYINSTALLER_OPTIONS = {
    'name': PROJECT_NAME,
    'onefile': True,  # 打包成单个exe文件
    'windowed': True,  # 不显示控制台窗口
    'clean': True,    # 清理临时文件
    'noconfirm': True,  # 不询问覆盖
}

def check_conda_env():
    """检查conda环境是否存在"""
    print(f"🔍 检查 conda 环境: {CONDA_ENV}")
    
    try:
        result = subprocess.run(
            ['conda', 'env', 'list'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        if CONDA_ENV in result.stdout:
            print(f"✅ 找到 conda 环境: {CONDA_ENV}")
            return True
        else:
            print(f"❌ 未找到 conda 环境: {CONDA_ENV}")
            print("可用的环境:")
            print(result.stdout)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 检查 conda 环境失败: {e}")
        return False
    except FileNotFoundError:
        print("❌ 未找到 conda 命令，请确保 conda 已正确安装并添加到 PATH")
        return False

def activate_conda_env():
    """激活conda环境"""
    print(f"🔄 激活 conda 环境: {CONDA_ENV}")
    
    # 获取conda环境的Python路径
    try:
        result = subprocess.run(
            ['conda', 'run', '-n', CONDA_ENV, 'python', '-c', 'import sys; print(sys.executable)'],
            capture_output=True,
            text=True,
            check=True
        )
        python_path = result.stdout.strip()
        print(f"✅ 环境Python路径: {python_path}")
        return python_path
    except subprocess.CalledProcessError as e:
        print(f"❌ 激活环境失败: {e}")
        return None

def check_dependencies():
    """检查依赖包是否安装"""
    print("🔍 检查依赖包...")
    
    required_packages = [
        'PyInstaller',
        'PyQt6', 
        'pandas',
        'aiohttp',
        'openpyxl',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            result = subprocess.run(
                ['conda', 'run', '-n', CONDA_ENV, 'python', '-c', f'import {package.lower().replace("-", "_")}'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ {package}")
            else:
                missing_packages.append(package)
                print(f"❌ {package}")
        except:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    return missing_packages

def install_missing_packages(missing_packages):
    """安装缺失的包"""
    if not missing_packages:
        return True
        
    print(f"📦 安装缺失的包: {', '.join(missing_packages)}")
    
    try:
        # 先尝试用conda安装
        for package in missing_packages:
            print(f"正在安装 {package}...")
            result = subprocess.run(
                ['conda', 'install', '-n', CONDA_ENV, '-c', 'conda-forge', package, '-y'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # conda安装失败，尝试pip
                print(f"conda安装失败，尝试pip安装 {package}...")
                pip_result = subprocess.run(
                    ['conda', 'run', '-n', CONDA_ENV, 'pip', 'install', package],
                    capture_output=True,
                    text=True
                )
                
                if pip_result.returncode != 0:
                    print(f"❌ 安装 {package} 失败")
                    return False
                else:
                    print(f"✅ 通过pip安装 {package} 成功")
            else:
                print(f"✅ 通过conda安装 {package} 成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 安装包时出错: {e}")
        return False

def create_spec_file():
    """创建PyInstaller spec文件"""
    print("📝 创建 .spec 文件...")
    
    # 获取当前目录下的所有Python文件
    python_files = list(Path('.').glob('*.py'))
    data_files = []
    
    # 添加数据文件
    if Path('requirements.txt').exists():
        data_files.append(('requirements.txt', '.'))
    
    # 检查是否有图标文件
    icon_path = None
    for ext in ['.ico', '.png', '.jpg']:
        if Path(f'icon{ext}').exists():
            icon_path = f'icon{ext}'
            break
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=[],
    binaries=[],
    datas={data_files},
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'pandas',
        'openpyxl',
        'aiohttp',
        'asyncio',
        'json',
        're',
        'random',
        'urllib.parse'
    ],
    hookspath=[],
    hooksconfig={{}},
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{PROJECT_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {'icon="' + icon_path + '",' if icon_path else ''}
)
'''
    
    spec_file = f"{PROJECT_NAME}.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✅ 创建 {spec_file} 成功")
    return spec_file

def build_executable(spec_file):
    """使用PyInstaller构建可执行文件"""
    print("🔨 开始构建可执行文件...")
    
    try:
        cmd = [
            'conda', 'run', '-n', CONDA_ENV,
            'pyinstaller',
            '--clean',
            '--noconfirm',
            spec_file
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            capture_output=False,  # 显示实时输出
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 构建成功!")
            return True
        else:
            print(f"❌ 构建失败，返回码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ 构建过程中出错: {e}")
        return False

def clean_build_files():
    """清理构建文件"""
    print("🧹 清理构建文件...")
    
    dirs_to_clean = ['build', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"删除目录: {dir_name}")
    
    for pattern in files_to_clean:
        for file_path in Path('.').glob(pattern):
            file_path.unlink()
            print(f"删除文件: {file_path}")

def main():
    """主函数"""
    print("=" * 60)
    print(f"🚀 {PROJECT_NAME} - 打包脚本")
    print("=" * 60)
    
    # 检查主脚本是否存在
    if not Path(MAIN_SCRIPT).exists():
        print(f"❌ 主脚本 {MAIN_SCRIPT} 不存在!")
        return False
    
    # 1. 检查conda环境
    if not check_conda_env():
        return False
    
    # 2. 激活环境
    python_path = activate_conda_env()
    if not python_path:
        return False
    
    # 3. 检查依赖
    missing_packages = check_dependencies()
    
    # 4. 安装缺失的包
    if missing_packages:
        if not install_missing_packages(missing_packages):
            print("❌ 安装依赖包失败，请手动安装后重试")
            return False
    
    # 5. 创建spec文件
    spec_file = create_spec_file()
    
    # 6. 构建可执行文件
    if build_executable(spec_file):
        print("\n" + "=" * 60)
        print("🎉 打包完成!")
        
        # 检查输出文件
        exe_path = Path('dist') / f"{PROJECT_NAME}.exe"
        if exe_path.exists():
            print(f"📁 可执行文件位置: {exe_path.absolute()}")
            print(f"📊 文件大小: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        print("=" * 60)
        
        # 询问是否清理构建文件
        response = input("是否清理构建文件? (y/n): ").lower().strip()
        if response in ['y', 'yes', '是']:
            clean_build_files()
        
        return True
    else:
        print("❌ 打包失败!")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ 所有操作完成!")
        else:
            print("\n❌ 操作失败!")
        
        input("\n按回车键退出...")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {e}")
        input("\n按回车键退出...")
