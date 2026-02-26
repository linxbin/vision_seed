@echo off
echo VisionSeed Secure Packaging
echo =========================

if not exist "visionseed.spec" (
    echo Error: visionseed.spec not found
    pause
    exit /b 1
)

echo Cleaning build directories...
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"

echo Running PyInstaller...
pyinstaller visionseed.spec

if %errorlevel% neq 0 (
    echo Error: Packaging failed
    pause
    exit /b 1
)

if exist "dist\VisionSeed.exe" (
    echo Success: VisionSeed.exe created successfully (single file)
    dir "dist\VisionSeed.exe"
) else (
    echo Error: Executable not found
    pause
    exit /b 1
)

echo Packaging completed!
pause