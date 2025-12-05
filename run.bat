@echo off
chcp 65001 >nul
cls
echo 启动日报表处理系统...
echo.

REM 1. 检查是否在虚拟环境中
python -c "import sys; sys.exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)"
if errorlevel 1 (
    echo 正在激活虚拟环境...
    call venv\Scripts\activate.bat
)

REM 2. 检查依赖
python -c "import docx, openpyxl" 2>nul
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
)

REM 3. 运行主程序
python run.py

REM 4. 等待退出
pause