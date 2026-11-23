#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT_DIR="$REPO_ROOT/assets/banner"
BUILDER_PATH="$SCRIPT_DIR/build.py"
ZSHRC="$HOME/.zshrc"

# 1. Проверка и установка figlet через Homebrew
if ! command -v figlet >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installing figlet via Homebrew..."
    brew install figlet
  else
    echo "Error: 'figlet' is not installed. Please install it first."
    exit 1
  fi
fi

mkdir -p "$OUT_DIR"
chmod +x "$BUILDER_PATH"

# 2. Добавление настроек в ~/.zshrc (если еще не добавлены)
touch "$ZSHRC"
if ! grep -q "# >>> gh-readme-hub banner >>>" "$ZSHRC"; then
  cat <<ZSH >> "$ZSHRC"

# >>> gh-readme-hub banner >>>
export BANNER_OUT_DIR="$OUT_DIR"
alias set-banner="python3 $BUILDER_PATH"
# <<< gh-readme-hub banner <<<
ZSH
  echo "Added 'set-banner' alias and BANNER_OUT_DIR to $ZSHRC"
else
  echo "Zsh configuration already exists in $ZSHRC"
fi

echo "Done! Run 'source ~/.zshrc' and try: set-banner -t \"HELLO\""
