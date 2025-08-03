@echo off
setlocal

REM Ścieżki źródłowe
set CLI_SRC=keymapuino-cli\keymapuino-cli.py
set GUI_SRC=keymapuino-gui\keymapuino-gui.py

REM Ścieżki wyjściowe
set RELEASE_DIR=release\windows
set CLI_OUT=%RELEASE_DIR%\bin
set GUI_OUT=%RELEASE_DIR%

REM Czyszczenie poprzednich buildów
rd /s /q dist
rd /s /q build
del /q *.spec

echo Building keymapuino-cli...
pyinstaller --onefile --distpath "%CLI_OUT%" --name keymapuino-cli %CLI_SRC%

echo Building keymapuino-gui...
pyinstaller --onefile --windowed --distpath "%GUI_OUT%" --name keymapuino-gui %GUI_SRC%

echo Build complete. Files are in %RELEASE_DIR%

REM Czyszczenie buildów
rd /s /q dist
rd /s /q build
del /q *.spec
endlocal