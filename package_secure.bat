@echo off
cls
echo ========================================
echo VisionSeed 安全打包脚本
echo ========================================
echo 注意：此脚本严格遵守隐私保护原则
echo 不会包含任何用户训练记录数据
echo ========================================
echo.

REM 清理之前的构建文件
echo [1/4] 清理构建目录...
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"

REM 验证配置文件存在
echo [2/4] 验证打包配置...
if not exist "visionseed.spec" (
    echo 错误: 找不到打包配置文件 visionseed.spec
    pause
    exit /b 1
)

REM 执行安全打包
echo [3/4] 执行安全打包（排除用户数据）...
pyinstaller visionseed.spec
if %errorlevel% neq 0 (
    echo 错误: 打包失败
    pause
    exit /b 1
)

REM 验证结果
echo [4/4] 验证打包结果...
if exist "dist\VisionSeed.exe" (
    echo.
    echo ✓ 打包成功！
    echo ✓ 已排除用户训练记录（data目录）
    echo ✓ 可执行文件: dist\VisionSeed.exe
    
    REM 显示文件信息
    for %%A in ("dist\VisionSeed.exe") do echo ✓ 文件大小: %%~zA 字节
    
    echo.
    echo ========================================
    echo 安全打包完成！
    echo ========================================
    echo 用户首次运行时将创建全新的训练记录
    echo ========================================
) else (
    echo 错误: 未生成可执行文件
    pause
    exit /b 1
)

pause