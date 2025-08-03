#!/bin/bash
set -e

CLI_SRC="keymapuino-cli/keymapuino-cli.py"
GUI_SRC="keymapuino-gui/keymapuino-gui.py"

RELEASE_DIR="release"
CLI_OUT="$RELEASE_DIR/bin"
GUI_OUT="$RELEASE_DIR"

rm -rf dist build *.spec

echo "Building keymapuino-cli..."
pyinstaller --onefile --distpath "$CLI_OUT" --name keymapuino-cli "$CLI_SRC"

echo "Building keymapuino-gui..."
pyinstaller --onefile --distpath "$GUI_OUT" --name keymapuino-gui "$GUI_SRC"

chmod +x "$CLI_OUT/keymapuino-cli"
chmod +x "$GUI_OUT/keymapuino-gui"

echo "Build complete. Files are in $RELEASE_DIR"
