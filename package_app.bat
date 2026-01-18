@echo off
chcp 65001 >nul
echo ===================================================
echo   Houdini Render Copilot - EXE Packaging Script
echo ===================================================
echo.

:: Check for Conda
echo [1/3] Checking Conda environment...
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Conda was not found in your system PATH.
    echo Please make sure you are running this from a "Conda Prompt"
    echo or that Conda is added to your environment variables.
    echo.
    pause
    exit /b
)

:: Check if environment exists
call conda env list | findstr /C:"youtube" >nul
if %errorlevel% neq 0 (
    echo [ERROR] Conda environment "youtube" not found.
    echo Please check your environment name.
    pause
    exit /b
)

echo [2/3] Verifying dependencies in conda environment "youtube"...
call conda run -n youtube python -m pip install PySide6 psutil pyinstaller --upgrade

if %errorlevel% neq 0 (
    echo [WARNING] Dependency update might have failed, attempting build anyway...
)

echo.
echo [3/3] Building Standalone EXE...
echo This may take a few minutes...
call conda run -n youtube python -m PyInstaller --onefile --windowed --name "HoudiniRenderCopilot" ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import PySide6.QtGui ^
    --clean ^
    HoudiniRenderManager.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed. Please check the error messages above.
    pause
    exit /b
)

echo.
echo [DONE] Executable created in: dist\HoudiniRenderCopilot.exe
echo.
pause
