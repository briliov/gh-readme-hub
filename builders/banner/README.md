# Banner Builder

Simple CLI utility to generate gradient SVG banners (`banner.svg`) and Zsh greetings (`banner.zsh`).

## Quick Start

1. **Run the installer** from the repository root:
   ```bash
   ./builders/banner/install.sh
   source ~/.zshrc
   ```

2. **Generate your first banner**:
   ```bash
   set-banner -t "YOUR_NAME" -p steel
   ```

3. **Preview in terminal**:
   ```bash
   zsh "\$BANNER_OUT_DIR/banner.zsh"
   ```

## Common Commands

* **Change colors (using a preset):**
  ```bash
  set-banner -p cyber
  ```
* **Custom gradient (any number of HEX colors) & save as preset:**
  ```bash
  set-banner -c '#ffffff,#38bdf8,#1d4ed8' --save-preset ice
  ```
* **Change direction (`horizontal`, `vertical`, `diagonal`) and outer padding:**
  ```bash
  set-banner -d vertical --pad 2
  ```
* **List or install FIGlet fonts:**
  ```bash
  set-banner -l
  set-banner -l install "ANSI Shadow"
  ```
* **Save to a custom folder (overrides `BANNER_OUT_DIR`):**
  ```bash
  set-banner -t "DOCS" -o ./my-folder
  ```

## CLI Flags

| Flag | Default | Description |
| :--- | :--- | :--- |
| `-t, --text` | *cached* | Text to render via `figlet` (reuses `banner.txt` if omitted). |
| `-f, --font` | `standard` | Local FIGlet font name. |
| `-p, --preset` | `steel` | Theme from `builders/banner/presets.json`. |
| `-c, --colors` | — | Custom HEX colors separated by comma or space. |
| `--save-preset` | — | Save current colors to `presets.json`. |
| `-d, --direction` | `diagonal` | Gradient flow: `horizontal`, `vertical`, `diagonal`. |
| `-s, --size` | `16` | SVG font size in pixels. |
| `--pad` | `1` | Uniform padding around banner (lines/spaces and SVG margins). |
| `-o, --out` | `$BANNER_OUT_DIR` | Target output directory. |
| `-l, --list-fonts` | — | Show fonts or install via `-l install <FONT>`. |
