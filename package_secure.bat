@echo off
setlocal
chcp 65001 >nul
set "APP_DIST_DIR=dist\VisionSeed"
echo VisionSeed Secure Packaging
echo =========================

if not exist "visionseed.spec" (
    echo Error: visionseed.spec not found
    pause
    exit /b 1
)

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: python not found in PATH
    pause
    exit /b 1
)

echo Cleaning build directories...
if exist "build" rmdir /s /q "build"
if exist "%APP_DIST_DIR%" rmdir /s /q "%APP_DIST_DIR%"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "build_smoke2" rmdir /s /q "build_smoke2"
if exist "dist_smoke2" rmdir /s /q "dist_smoke2"

echo Running PyInstaller...
python -m PyInstaller visionseed.spec --distpath dist --workpath build --noconfirm

if %errorlevel% neq 0 (
    echo Error: Packaging failed
    pause
    exit /b 1
)

set "APP_EXE_PATH="
for %%F in ("%APP_DIST_DIR%\*.exe") do if not defined APP_EXE_PATH set "APP_EXE_PATH=%%~fF"

if defined APP_EXE_PATH (
    echo(
    echo [OK] Executable created successfully ^(one-folder^)
    dir "%APP_EXE_PATH%"
) else (
    echo Error: Executable not found
    pause
    exit /b 1
)

echo(
echo Creating zip package in dist directory...
set "VERSION=v0.0.0"
for /f "delims=" %%i in ('git describe --tags --abbrev^=0 2^>nul') do set "VERSION=%%i"

set "ARCH=%PROCESSOR_ARCHITECTURE%"
if /I "%ARCH%"=="AMD64" set "ARCH=x64"
if /I "%ARCH%"=="X86" set "ARCH=x86"
if /I "%ARCH%"=="ARM64" set "ARCH=arm64"

set "ZIP_NAME=shiya-%VERSION%-windows-%ARCH%.zip"
set "ZIP_PATH=dist\%ZIP_NAME%"
if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\\VisionSeed\\*' -DestinationPath '%ZIP_PATH%' -Force"

if %errorlevel% neq 0 (
    echo Error: Failed to create zip package
    pause
    exit /b 1
)

echo(
echo [OK] Zip package created
dir "%ZIP_PATH%"

echo Cleaning temporary build directories...
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"

echo(
echo Packaging completed!
pause
endlocal
