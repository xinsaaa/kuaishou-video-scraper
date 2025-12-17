@echo off
chcp 65001 >nul
title 快手视频信息爬取工具 - 打包脚本

echo.
echo ========================================
echo   快手视频信息爬取工具 - 自动打包
echo ========================================
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未找到，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

REM 检查conda是否可用
conda --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Conda 未找到，请确保Anaconda/Miniconda已安装并添加到PATH
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

REM 运行打包脚本
echo 🚀 开始执行打包脚本...
echo.
python build_exe.py

echo.
echo 打包脚本执行完成
pause
