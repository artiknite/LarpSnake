#!/bin/bash
set -e

echo "========================================"
echo " Building Terminal Snake for Linux"
echo "========================================"
echo

python3 --version

echo "Installing dependencies..."
pip3 install --user pyinstaller

echo
echo "Building binary..."
pyinstaller --onefile --name snake snake.py

echo
if [ -f dist/snake ]; then
    echo "========================================"
    echo " SUCCESS!"
    echo " File created: dist/snake"
    echo "========================================"
    chmod +x dist/snake
else
    echo "[ERROR] Build failed."
    exit 1
fi
