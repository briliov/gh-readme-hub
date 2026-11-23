# Banner Builder

CLI utility to generate multi-stop gradient SVG banners (`banner.svg`) and Zsh greetings (`banner.zsh`) using local `FIGlet` fonts.

## Two Ways to Use

### 1. Integrated with `gh-readme-hub` (GitHub Profile Mode)
Use this mode to automatically save generated banners into `assets/banner/` for your GitHub profile `README.md`.

1. **Run the installer** from the repository root:
   ```bash
   ./builders/banner/install.sh
   source ~/.zshrc
   ```
   *(This installs `figlet` if missing, sets `BANNER_OUT_DIR` to `assets/banner`, and adds the `set-banner` alias).*

2. **Generate or update your profile banner** from anywhere:
   ```bash
   set-banner -t "YOUR_NAME" -f ansi_shadow -p steel
   ```

3. **Preview in terminal**:
   ```bash
   zsh "\$BANNER_OUT_DIR/banner.zsh"
   ```

---

### 2. Standalone Mode (Any Project or Zsh Greeting)
Use the script independently without touching `gh-readme-hub` assets — save banners to any folder or render a custom Zsh welcome message on terminal startup.

* **Generate a banner inside another repository:**
  ```bash
  python3 builders/banner/build.py -t "MY API" -p cyber -o ./docs/assets
  ```

* **Use as an automatic Zsh terminal greeting** (add to `~/.zshrc`):
  ```zsh
  [[ -f "\$BANNER_OUT_DIR/banner.zsh" ]] && source "\$BANNER_OUT_DIR/banner.zsh"
  ```

---

## Common Commands

* **Switch preset:**
  ```bash
  set-banner -p ocean
  ```
* **Custom gradient (any number of HEX colors) & save to `presets.json`:**
  ```bash
  set-banner -c '#ffffff,#38bdf8,#1d4ed8' --save-preset ice
  ```
* **Adjust gradient direction (`horizontal`, `vertical`, `diagonal`) and outer padding:**
  ```bash
  set-banner -d vertical --pad 2
  ```
* **List or install FIGlet fonts:**
  ```bash
  set-banner -l
  set-banner -l install "ANSI Shadow"
  ```

## CLI Flags

| Flag | Default | Description |
| :--- | :--- | :--- |
| `-t, --text` | *cached* | Text to render via `figlet` (reuses `banner.txt` if omitted). |
| `-f, --font` | `standard` | Local FIGlet font name. |
| `-p, --preset` | `steel` | Theme from `builders/banner/presets.json`. |
| `-c, --colors` | — | Custom HEX colors separated by comma or space. |
| `--save-preset` | — | Save current colors into `presets.json`. |
| `-d, --direction` | `diagonal` | Gradient flow: `horizontal`, `vertical`, `diagonal`. |
| `-s, --size` | `16` | SVG font size in pixels. |
| `--pad` | `1` | Uniform padding around banner (lines/spaces and SVG margins). |
| `-o, --out` | `$BANNER_OUT_DIR` | Target output directory (defaults to current working dir). |
| `-l, --list-fonts` | — | Show fonts or install via `-l install <FONT>`. |
