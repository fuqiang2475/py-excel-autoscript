@echo off
:: 切换编码为UTF-8（屏蔽多余输出）
chcp 65001 > nul
:: 清屏
cls
echo 启动日报表处理系统...
echo.

:: 1. 激活虚拟环境（极简版：存在则激活，无任何多余判断）
if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat

:: 2. 检查依赖并询问用户（完全去掉嵌套的复杂判断，改用goto跳转）
python -c "import docx, openpyxl" > nul 2>&1
if errorlevel 1 goto InstallDeps
goto RunProgram

:InstallDeps
echo 缺少必要依赖包：python-docx、openpyxl
echo.
set "user_confirm=N"
set /p user_confirm=是否自动安装依赖包？(Y/N，默认N)：
if /i "%user_confirm%"=="Y" (
    echo.
    echo 正在安装依赖包...
    pip install python-docx openpyxl
    echo.
    echo 依赖包安装完成！
    echo.
) else (
    echo.
    echo 未安装依赖包，程序无法运行！
    pause
    exit /b 1
)

:RunProgram
:: 3. 运行主程序
python run.py

:: 4. 等待退出
pause