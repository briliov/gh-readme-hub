![BRILIOV](./data/banner.svg)

# Dynamic Banner CLI

Offline Python CLI utility to render colored Zsh terminal banners (`banner.zsh`) and transparent vector graphics (`banner.svg`) from ASCII art or local FIGlet fonts.

## Requirements

* **Python 3.10+** (standard library only, zero external packages)
* **FIGlet** *(optional, required only when generating new text via `-t`)*:
  ```bash
  brew install figlet
  ```

## Directory Layout

```text
banner/
├── data/
│   ├── banner.txt    # Source ASCII art template
│   ├── banner.zsh    # Generated Zsh script with 24-bit HEX colors
│   └── banner.svg    # Generated transparent SVG banner
└── build.py          # Executable CLI generator
```

## Usage

Make the script executable once:
```bash
chmod +x build.py
```

### Commands & Examples

* **Apply a built-in gradient preset** (`fire`, `cyber`, `emerald`, `mono`, `ocean`):
  ```bash
  ./build.py -p cyber
  ```

* **Set custom HEX color stops and gradient direction** (`horizontal`, `vertical`, `diagonal`):
  ```bash
  ./build.py -c "#ff0055,#7700ff,#00ffff" -d vertical
  ```

* **Generate new ASCII text using a local FIGlet font:**
  ```bash
  ./build.py -t "BRILIOV" -f Bloody -p fire
  ```

* **Customize SVG font size and terminal vertical padding:**
  ```bash
  ./build.py -p emerald -s 18 --pad-top 0 --pad-bottom 1
  ```

* **Inspect available presets, fonts, and CLI flags:**
  ```bash
  ./build.py --list-presets
  ./build.py --list-fonts
  ./build.py --help
  ```

## Zsh Integration

Add this to your `.zshrc` to display the banner on shell startup and expose the `set-banner` helper:

```zsh
source ~/.dotfiles/src/banner/data/banner.zsh

set-banner() {
  ~/.dotfiles/src/banner/build.py "\$@" && source ~/.dotfiles/src/banner/data/banner.zsh
}
```
