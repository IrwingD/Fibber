@echo off
echo Installing build dependencies...
pip install -r requirements.txt

echo.
echo Building portable app...
python -m PyInstaller build.spec --noconfirm

echo.
echo Done. Your portable app folder is:
echo   dist\SyntheticDataStudio\
echo.
echo Zip that folder, or copy it to a USB stick, and run SyntheticDataStudio.exe
echo on any Windows machine -- nothing else needs to be installed.
pause
