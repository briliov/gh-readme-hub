#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE}")" && pwd)"
BUILDER_PATH="$SCRIPT_DIR/build.py"
BIN_DIR="$HOME/.local/bin"
TARGET_LINK="$BIN_DIR/set-banner"

# 1. Проверяем наличие figlet
if ! command -v figlet >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installing figlet via Homebrew..."
    brew install figlet
  else
    echo "Error: 'figlet' is not installed. Please install it first."
    exit 1
  fi
fi

# 2. Делаем build.py исполняемым и создаем симлинк в ~/.local/bin/set-banner
chmod +x "$BUILDER_PATH"
mkdir -p "$BIN_DIR"
ln -sf "$BUILDER_PATH" "$TARGET_LINK"

echo "Linked: $TARGET_LINK -> $BUILDER_PATH"
echo "Done! Try running: set-banner --help"
