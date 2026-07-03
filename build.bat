@echo off
echo Installing build dependencies...
pip install -r requirements.txt

echo.
echo Building portable app...
python -m PyInstaller build.spec --noconfirm
if errorlevel 1 (
    echo.
    echo Build failed -- see errors above.
    pause
    exit /b 1
)

echo.
echo Done. Your app is:
echo   dist\Fibber.exe
echo.
echo That single file is the whole app. Upload it to a GitHub Release for
echo distribution -- don't commit it into the repo itself (dist\ is
echo gitignored on purpose; binaries don't belong in git history).
pause