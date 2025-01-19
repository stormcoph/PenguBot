@echo off
setlocal enabledelayedexpansion

title PenguBot Complete Setup

echo ========================================
echo PenguBot Installation Helper
echo ========================================
echo.

:: Check if running with admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script requires administrator privileges
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Create temporary directory for downloads
set "TEMP_DIR=%TEMP%\pengubot_setup"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Python not found, downloading Python 3.10...
    powershell -Command "& {$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe' -OutFile '%TEMP_DIR%\python_installer.exe'}"
    
    if not exist "%TEMP_DIR%\python_installer.exe" (
        echo [ERROR] Failed to download Python installer
        pause
        exit /b 1
    )
    
    echo [INFO] Installing Python 3.10...
    start /wait "" "%TEMP_DIR%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1
    
    :: Verify Python installation
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python installation failed
        pause
        exit /b 1
    )
)

echo [INFO] Python is installed
python --version

:: Check pip installation
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] pip not found, installing pip...
    curl https://bootstrap.pypa.io/get-pip.py -o "%TEMP_DIR%\get-pip.py"
    python "%TEMP_DIR%\get-pip.py" --no-warn-script-location
    
    :: Verify pip installation
    python -m pip --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] pip installation failed
        pause
        exit /b 1
    )
)

echo [INFO] pip is installed
python -m pip --version

:: Check CUDA installation
if not exist "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8" (
    echo [INFO] CUDA 11.8 not found, downloading installer...
    powershell -Command "& {$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_522.06_windows.exe' -OutFile '%TEMP_DIR%\cuda_installer.exe'}"
    
    if not exist "%TEMP_DIR%\cuda_installer.exe" (
        echo [ERROR] Failed to download CUDA installer
        pause
        exit /b 1
    )
    
    echo [INFO] Installing CUDA 11.8...
    echo This may take several minutes...
    start /wait "" "%TEMP_DIR%\cuda_installer.exe" /s
    
    :: Check if installation was successful
    if not exist "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\nvcc.exe" (
        echo [ERROR] CUDA installation failed
        pause
        exit /b 1
    )
    
    :: Update PATH environment variable for CUDA
    echo [INFO] Updating CUDA system PATH...
    set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
    setx CUDA_PATH "%CUDA_PATH%" /M
    setx PATH "%PATH%;%CUDA_PATH%\bin;%CUDA_PATH%\libnvvp" /M
)

echo [INFO] CUDA 11.8 is installed

:: Create and activate virtual environment
echo [INFO] Setting up Python virtual environment...
if exist PenguBot (
    echo [INFO] Removing existing environment...
    rmdir /s /q PenguBot
)

python -m venv PenguBot
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

call PenguBot\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

:: Upgrade pip in virtual environment
python -m pip install --upgrade pip

:: Install PyTorch with CUDA support
echo [INFO] Installing PyTorch with CUDA support...
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118

:: Install other requirements if requirements.txt exists
if exist requirements.txt (
    echo [INFO] Installing other requirements...
    pip install -r requirements.txt
)

:: Cleanup
echo [INFO] Cleaning up temporary files...
rmdir /s /q "%TEMP_DIR%"

:: Deactivate virtual environment
call PenguBot\Scripts\deactivate.bat

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo All components have been installed:
echo - Python 3.10
echo - pip (latest version)
echo - CUDA 11.8
echo - PyTorch with CUDA support
echo - Virtual environment 'PenguBot'
echo.
echo Please restart your computer to ensure all PATH updates take effect.
echo.
choice /C YN /M "Do you want to restart now?"
if !errorlevel! equ 1 shutdown /r /t 10 /c "Restarting to complete installation..."

exit /b 0