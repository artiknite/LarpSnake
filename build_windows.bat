@echo off
title Building Terminal Snake
color 0A

echo.
echo ========================================
echo   Building Terminal Snake for Windows
echo ========================================
echo.

if not exist "snake.py" (
    echo [ERROR] snake.py not found!
    echo.
    echo Put this .bat file in the same folder as snake.py
    echo.
    pause
    exit /b 1
)

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found!
    echo.
    echo 1. Download Python from https://www.python.org/downloads/
    echo 2. During install CHECK the box "Add python.exe to PATH"
    echo 3. Close this window and open it again after install
    echo.
    pause
    exit /b 1
)

python --version
echo.

echo [2/4] Installing libraries...
python -m pip install --upgrade pip
python -m pip install windows-curses pyinstaller
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install libraries.
    pause
    exit /b 1
)
echo.

echo [3/4] Cleaning old build...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "snake.spec" del /q snake.spec
echo.

echo [4/4] Building snake.exe ...
echo Please wait 20-60 seconds...
echo.
python -m PyInstaller --onefile --name snake snake.py

echo.
echo ========================================
if exist "dist\snake.exe" (
    echo   SUCCESS!
    echo.
    echo   File created: dist\snake.exe
    echo.
    echo   You can run it by double-click.
) else (
    echo   BUILD FAILED.
    echo   Check the messages above.
)
echo ========================================
echo.
pause
