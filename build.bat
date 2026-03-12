@echo off
REM Build script for ZPL Visualizer with code obfuscation
REM Password for reverse engineering protection: Hr40DeckFr4c4

echo ==========================================
echo ZPL Visualizer - Build Script
echo ==========================================
echo.

REM Step 1: Clean previous builds
echo [1/4] Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "obfuscated" rmdir /s /q obfuscated

REM Step 2: Obfuscate code with PyArmor
echo [2/4] Obfuscating Python code with PyArmor...
pyarmor gen --output obfuscated src/main.py src/zpl_utils.py src/bitmap_fonts.py

if errorlevel 1 (
    echo ERROR: PyArmor obfuscation failed!
    echo Falling back to standard PyInstaller build...
    goto :standard_build
)

REM Step 3: Copy config and create package
echo [3/4] Preparing obfuscated package...
copy src\config.json obfuscated\ >nul 2>&1

REM Step 4: Build executable with PyInstaller
echo [4/4] Building executable with PyInstaller...
pyinstaller --noconfirm --onefile --windowed --name "ZPL_Visualizer" ^
    --add-data "obfuscated;." ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import barcode ^
    --hidden-import barcode.ean ^
    --hidden-import barcode.upc ^
    --hidden-import barcode.codex ^
    --hidden-import barcode.code128 ^
    --hidden-import barcode.writer ^
    obfuscated/main.py

goto :end

:standard_build
echo Building without obfuscation...
pyinstaller --noconfirm --onefile --windowed --name "ZPL_Visualizer" ^
    --add-data "src\config.json;src" ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import barcode ^
    --hidden-import barcode.ean ^
    --hidden-import barcode.upc ^
    --hidden-import barcode.codex ^
    --hidden-import barcode.code128 ^
    --hidden-import barcode.writer ^
    src/main.py

:end
echo.
echo ==========================================
if exist "dist\ZPL_Visualizer.exe" (
    echo BUILD SUCCESSFUL!
    echo Executable location: dist\ZPL_Visualizer.exe
) else (
    echo BUILD FAILED! Check errors above.
)
echo ==========================================
pause
