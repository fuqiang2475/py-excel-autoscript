@echo off
setlocal enabledelayedexpansion
:: 切换到脚本所在目录（确保读取当前目录的requirements.txt）
cd /d "%~dp0"

echo 开始运行化工日报表数据生成器...
echo.

:: 1. 检查Python是否安装
python --version 2>&1 >nul
if %errorlevel% neq 0 (
    echo 错误：未检测到Python环境，请先安装Python 3.7+
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

:: 2. 从当前目录的requirements.txt中提取依赖名称（仅提取库名，忽略版本号）
set "deps="
set "req_file=requirements.txt"
if exist "!req_file!" (
    :: 读取requirements.txt，提取每行的库名（处理格式：numpy>=1.21.6 或 numpy==1.21.6）
    for /f "tokens=1 delims=>=<>= " %%d in (!req_file!) do (
        :: 去重（避免requirements.txt中有重复库名）
        if "!deps!"=="" (
            set "deps=%%d"
        ) else if "!deps:%%d=!"=="!deps!" (
            set "deps=!deps! %%d"
        )
    )
) else (
    :: 未找到requirements.txt时，使用默认依赖（data_produce的核心依赖）
    set "deps=numpy pandas"
    echo 未找到data_produce专属的requirements.txt，将验证默认依赖：!deps!
)

:: 3. 逐个验证依赖是否已安装（核心：先验证，不盲目下载）
set "missing_deps="
echo 验证已安装的Python依赖...
for %%d in (!deps!) do (
    :: 检查依赖是否能正常导入
    python -c "import %%d" 2>&1 >nul
    if !errorlevel! neq 0 (
        set "missing_deps=!missing_deps! %%d"
        echo  缺失：%%d
    ) else (
        echo  已安装：%%d
    )
)

:: 4. 仅当依赖缺失时，才询问是否安装（全程用户可控）
if not "!missing_deps!"=="" (
    echo.
    set /p "install_choice=检测到缺失依赖：!missing_deps!，是否通过requirements.txt安装？(Y/N)："
    :: 处理用户直接回车的情况（默认不安装）
    if "!install_choice!"=="" set "install_choice=N"
    
    if /i "!install_choice!"=="Y" (
        echo.
        :: 优先使用当前目录的requirements.txt安装（保证依赖版本匹配）
        if exist "!req_file!" (
            echo 正在通过data_produce的requirements.txt安装缺失依赖...
            pip install -r !req_file!
        ) else (
            echo 正在安装默认缺失依赖：!missing_deps!
            pip install !missing_deps!
        )
        
        :: 检查安装结果
        if !errorlevel! neq 0 (
            echo.
            echo 错误：依赖安装失败！请手动执行以下命令：
            if exist "!req_file!" (
                echo pip install -r !req_file!
            ) else (
                echo pip install !missing_deps!
            )
            echo 按任意键退出...
            pause >nul
            exit /b 1
        ) else (
            echo.
            echo 缺失依赖安装成功！
        )
    ) else (
        echo.
        echo 取消安装，依赖缺失将导致脚本无法运行！
        echo 按任意键退出...
        pause >nul
        exit /b 1
    )
) else (
    echo.
    echo 所有依赖均已安装，无需额外下载~
)

:: 5. 运行数据生成脚本
echo.
echo 正在生成数据...
python data_produce.py 2>&1

:: 6. 检查运行结果
if %errorlevel% equ 0 (
    echo.
    echo ======================================
    echo 数据生成成功！
    echo 生成的TXT文件已保存到当前目录
    echo ======================================
) else (
    echo.
    echo 错误：数据生成失败，请检查脚本语法或依赖是否正确！
)

echo.
echo 按任意键退出...
pause >nul
endlocal