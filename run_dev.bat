@echo off
echo Installing dependencies (first run only)...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Dependency install failed -- see errors above.
    pause
    exit /b 1
)

echo.
echo Starting Synthetic Data Studio...
python app.py

echo.
echo App closed. If that was unexpected, scroll up for errors.
pause
