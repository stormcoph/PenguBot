@echo off
echo Starting PenguBot...
echo ========================================

:: Activate the virtual environment
call PenguBot\Scripts\activate.bat

:: Run the main script
python Main.py

:: Keep the window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo Error occurred while running PenguBot
    pause
)

:: Deactivate the virtual environment
call PenguBot\Scripts\deactivate.bat