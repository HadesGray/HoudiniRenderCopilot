@echo off
chcp 65001 >nul
echo ===================================================
echo   Houdini Render Copilot - EXE Packaging Script
echo ===================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+ and add it to your PATH.
    pause
    exit /b
)

echo [1/2] Verifying dependencies...
python -m pip install PySide6 psutil pyinstaller --upgrade

echo.
echo [2/2] Building Standalone EXE...
echo This may take a few minutes...
python -m PyInstaller --onefile --windowed --name "HoudiniRenderCopilot" ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import PySide6.QtGui ^
    --clean ^
    HoudiniRenderManager.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed. Please check if all dependencies are installed correctly.
    pause
    exit /b
)

echo.
echo [DONE] Executable created in: dist/HoudiniRenderCopilot.exe
echo.
pause
