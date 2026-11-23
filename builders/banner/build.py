#!/usr/bin/env python3
"""Offline/online CLI utility to generate Zsh and SVG banners with local presets."""

import argparse
import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_FONT = 'standard'
DEFAULT_PRESET = 'steel'
DEFAULT_DIRECTION = 'diagonal'
DEFAULT_FONT_SIZE = 16
DEFAULT_PAD = 1

DEFAULT_PRESETS: dict[str, list[str]] = {
    'fire': ['#ff0000', '#ff5f00', '#ffaf00', '#ffd700'],
    'cyber': ['#9d00ff', '#ff007f', '#00f0ff'],
    'emerald': ['#00875f', '#00d787', '#afff00'],
    'mono': ['#585858', '#9e9e9e', '#ffffff'],
    'ocean': ['#0033ff', '#0099ff', '#00ffff'],
    'steel': ['#cbd5e1', '#64748b', '#38bdf8'],
}

REMOTE_FONTS_API = (
    'https://' + '://github.com'
)
REMOTE_FONTS_RAW = (
    'https://' + '://githubusercontent.com'
)


def resolve_out_dir(cli_out: Path | None, push: bool = False) -> Path:
    """Resolve output directory: repo assets/banner if --push, else CLI -> env -> cwd."""
    if push:
        hub_env = os.environ.get('GH_HUB_DIR')
        repo_root = Path(hub_env).expanduser().resolve() if hub_env else Path(__file__).resolve().parents
        return repo_root / 'assets' / 'banner'
    if cli_out is not None:
        return cli_out.expanduser().resolve()
    env_out = os.environ.get('BANNER_OUT_DIR')
    if env_out:
        return Path(env_out).expanduser().resolve()
    return Path.cwd()

def load_local_presets(out_dir: Path) -> dict[str, list[str]]:
    """Load presets from presets.json in out_dir, initializing defaults if missing."""
    presets_file = Path(__file__).resolve().parent / 'presets.json'
    if not presets_file.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
        presets_file.write_text(
            json.dumps(DEFAULT_PRESETS, indent=2) + '\n',
            encoding='utf-8',
        )
        return dict(DEFAULT_PRESETS)

    try:
        data = json.loads(presets_file.read_text(encoding='utf-8'))
        if isinstance(data, dict):
            return {str(k): list(v) for k, v in data.items()}
    except (json.JSONDecodeError, TypeError) as exc:
        sys.exit(f"Error reading '{presets_file}': {exc}")
    return dict(DEFAULT_PRESETS)


def save_local_preset(out_dir: Path, name: str, colors: list[str]) -> None:
    """Save or update a named color preset inside out_dir/presets.json."""
    presets = load_local_presets(out_dir)
    presets[name] = colors
    presets_file = Path(__file__).resolve().parent / 'presets.json'
    presets_file.write_text(
        json.dumps(presets, indent=2) + '\n',
        encoding='utf-8',
    )
    print(f"Saved preset '{name}' ({', '.join(colors)}) -> {presets_file}")


def get_figlet_font_dir() -> Path:
    """Return local FIGlet fonts directory path."""
    figlet_bin = shutil.which('figlet')
    if not figlet_bin:
        sys.exit("Error: 'figlet' is not installed. Run: brew install figlet")

    res = subprocess.run(
        [figlet_bin, '-I', '2'],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(res.stdout.strip())


def fetch_remote_font_names() -> list[str]:
    """Fetch available .flf font stems from xero/figlet-fonts via GitHub API."""
    req = urllib.request.Request(
        REMOTE_FONTS_API,
        headers={'User-Agent': 'gh-readme-hub-banner'},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        tree = data.get('tree', [])
        return sorted(
            Path(item['path']).stem
            for item in tree
            if item.get('path', '').endswith('.flf')
        )
    except (urllib.error.URLError, json.JSONDecodeError):
        return []


def list_fonts() -> None:
    """Print locally installed fonts and available remote fonts to install."""
    font_dir = get_figlet_font_dir()
    local_fonts = (
        sorted(p.stem for p in font_dir.glob('*.flf'))
        if font_dir.exists()
        else []
    )
    print(f'Installed locally ({len(local_fonts)}):')
    print(' ', ', '.join(local_fonts) if local_fonts else 'None')

    remote_fonts = fetch_remote_font_names()
    if remote_fonts:
        local_lower = {f.lower() for f in local_fonts}
        available = [f for f in remote_fonts if f.lower() not in local_lower]
        print(f'\nAvailable to install ({len(available)}):')
        print(' ', ', '.join(available[:60]))
        if len(available) > 60:
            print(f'  ... and {len(available) - 60} more')
        print("\nInstall any font with: --install-font 'FONT_NAME'")
    else:
        print('\nRemote font catalog unavailable (offline mode).')


def install_font(font_name: str) -> None:
    """Download and install a .flf font from xero/figlet-fonts into local FIGlet dir."""
    font_dir = get_figlet_font_dir()
    font_dir.mkdir(parents=True, exist_ok=True)

    clean_stem = font_name.removesuffix('.flf')
    encoded_file = urllib.parse.quote(f'{clean_stem}.flf')
    url = f'{REMOTE_FONTS_RAW}/{encoded_file}'
    local_name = clean_stem.lower().replace(' ', '_') + '.flf'
    target_path = font_dir / local_name

    req = urllib.request.Request(
        url, headers={'User-Agent': 'gh-readme-hub-banner'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
    except urllib.error.HTTPError as exc:
        sys.exit(
            f"Font '{clean_stem}' not found in remote repository (HTTP {exc.code})."
        )
    except urllib.error.URLError as exc:
        sys.exit(f'Network error while downloading font: {exc.reason}')

    if not content.startswith(b'flf2'):
        sys.exit(
            f"Downloaded file for '{clean_stem}' is not a valid FIGlet font."
        )

    target_path.write_bytes(content)
    print(
        f"Installed '{clean_stem}' -> {target_path} (use with: -f {target_path.stem})"
    )


def generate_figlet(text: str, font: str) -> str:
    """Generate ASCII art text using locally installed figlet."""
    figlet_bin = shutil.which('figlet')
    if not figlet_bin:
        sys.exit("Error: 'figlet' is not installed. Run: brew install figlet")

    res = subprocess.run(
        [figlet_bin, '-f', font, '-w', '200', text],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        sys.exit(f'FIGlet error: {res.stderr.strip()}')
    return res.stdout


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a HEX color string to an RGB tuple."""
    value = hex_color.lstrip('#')
    if len(value) != 6:
        sys.exit(f"Invalid HEX color: '{hex_color}'. Expected format: #RRGGBB")
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert an RGB tuple to a HEX color string."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def interpolate_color(colors: list[tuple[int, int, int]], t: float) -> str:
    """Interpolate a color across any number of RGB stops at position t."""
    t = max(0.0, min(1.0, t))
    if len(colors) == 1:
        return rgb_to_hex(colors[0])
    scaled = t * (len(colors) - 1)
    idx = min(int(scaled), len(colors) - 2)
    frac = scaled - idx
    c1, c2 = colors[idx], colors[idx + 1]
    blended = (
        round(c1[0] + (c2[0] - c1[0]) * frac),
        round(c1[1] + (c2[1] - c1[1]) * frac),
        round(c1[2] + (c2[2] - c1[2]) * frac),
    )
    return rgb_to_hex(blended)


def get_progress(
    x: int, y: int, width: int, height: int, direction: str
) -> float:
    """Calculate normalized gradient progress for a character coordinate."""
    nx = x / max(1, width - 1)
    ny = y / max(1, height - 1)
    if direction == 'vertical':
        return ny
    if direction == 'diagonal':
        return (nx * 0.75) + (ny * 0.25)
    return nx


def parse_color_list(raw: str) -> list[str]:
    """Parse comma- or space-separated HEX colors into a normalized list."""
    tokens = raw.replace(',', ' ').split()
    normalized = []
    for token in tokens:
        color = token if token.startswith('#') else f'#{token}'
        hex_to_rgb(color)
        normalized.append(color.lower())
    if not normalized:
        sys.exit('Error: At least one HEX color is required.')
    return normalized


def build(args: argparse.Namespace) -> None:
    """Generate banner.txt, banner.zsh, and banner.svg in the target directory."""
    out_dir = resolve_out_dir(args.out, args.push)
    out_dir.mkdir(parents=True, exist_ok=True)
    presets = load_local_presets(out_dir)

    if args.colors:
        raw_colors = parse_color_list(args.colors)
        theme_label = f'custom ({len(raw_colors)} colors)'
    else:
        if args.preset not in presets:
            available = ', '.join(presets.keys())
            sys.exit(
                f"Unknown preset '{args.preset}' in {Path(__file__).resolve().parent / 'presets.json'}. Available: {available}"
            )
        raw_colors = presets[args.preset]
        theme_label = args.preset

    if args.save_preset:
        save_local_preset(out_dir, args.save_preset, raw_colors)
        theme_label = args.save_preset

    art_path = out_dir / 'banner.txt'
    zsh_out = out_dir / 'banner.zsh'
    svg_out = out_dir / 'banner.svg'

    if args.text:
        art_raw = generate_figlet(args.text, args.font)
        art_path.write_text(art_raw, encoding='utf-8')
    elif not art_path.exists():
        sys.exit(
            f"No '{art_path}' found. Pass -t 'YOUR_TEXT' to generate one."
        )

    colors = [hex_to_rgb(c) for c in raw_colors]

    raw_lines = art_path.read_text(encoding='utf-8').splitlines()
    while raw_lines and not raw_lines[0].strip():
        raw_lines.pop(0)
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()

    height = len(raw_lines)
    width = max(len(line) for line in raw_lines)
    lines = [line.ljust(width) for line in raw_lines]

    zsh_lines = []
    svg_rows = []
    char_w = args.size * 0.601
    line_h = args.size * 1.18
    pad = max(0, args.pad)
    x_offset = round(pad * char_w, 2)
    h_pad_str = ' ' * pad

    for y, line in enumerate(lines):
        zsh_row = [h_pad_str] if pad else []
        svg_spans = []
        last_hex = None
        buffer = []

        for x, ch in enumerate(line):
            if ch == ' ':
                if buffer and last_hex:
                    svg_spans.append(
                        f'<tspan fill="{last_hex}">{html.escape("".join(buffer))}</tspan>',
                    )
                    buffer.clear()
                zsh_row.append(' ')
                svg_spans.append('<tspan> </tspan>')
                continue

            hex_c = interpolate_color(
                colors,
                get_progress(x, y, width, height, args.direction),
            )
            if hex_c != last_hex:
                if buffer and last_hex:
                    svg_spans.append(
                        f'<tspan fill="{last_hex}">{html.escape("".join(buffer))}</tspan>',
                    )
                    buffer.clear()
                zsh_row.append(f'%F{{{hex_c}}}')
                last_hex = hex_c

            zsh_row.append(ch)
            buffer.append(ch)

        if buffer and last_hex:
            svg_spans.append(
                f'<tspan fill="{last_hex}">{html.escape("".join(buffer))}</tspan>',
            )

        zsh_lines.append(''.join(zsh_row) + '%f')
        y_pos = round((y + pad + 0.85) * line_h, 2)
        svg_rows.append(
            f'  <text x="{x_offset}" y="{y_pos}" xml:space="preserve">{"".join(svg_spans)}</text>',
        )

    v_pad = '\n' * pad
    zsh_content = (
        f'print -P \\\n"{v_pad}' + '\n'.join(zsh_lines) + f'{v_pad}"\n'
    )
    zsh_out.write_text(zsh_content, encoding='utf-8')

    svg_w = round((width + pad * 2) * char_w, 2)
    svg_h = round((height + pad * 2) * line_h, 2)
    svg_ns = 'http://' + 'www.w3.org' + '/2000/svg'
    svg_content = (
        f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" '
        f'xmlns="{svg_ns}">\n'
        f'  <g font-family="JetBrains Mono, Menlo, Monaco, Consolas, monospace" '
        f'font-size="{args.size}px">\n'
        + '\n'.join(svg_rows)
        + '\n  </g>\n</svg>\n'
    )
    svg_out.write_text(svg_content, encoding='utf-8')
    print(
        f'Done! Saved to {out_dir} | Theme: {theme_label} | Direction: {args.direction} | Pad: {pad}'
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for banner customization and preset management."""
    parser = argparse.ArgumentParser(
        description='Configure and build Zsh + SVG banners with local presets.',
    )
    parser.add_argument(
        '-t',
        '--text',
        help='Generate new ASCII art with FIGlet (if omitted, uses banner.txt in output dir)',
    )
    parser.add_argument(
        '-f', '--font', default=DEFAULT_FONT, help='Local FIGlet font'
    )
    parser.add_argument(
        '-p',
        '--preset',
        default=DEFAULT_PRESET,
        help='Preset name from presets.json in output directory',
    )
    parser.add_argument(
        '-c',
        '--colors',
        help="Any number of comma/space-separated HEX colors (e.g. '#ff0055,#ff8800,#00ffcc,#38bdf8')",
    )
    parser.add_argument(
        '--save-preset',
        metavar='NAME',
        help='Save current colors into out_dir/presets.json under NAME',
    )
    parser.add_argument(
        '-d',
        '--direction',
        choices=['horizontal', 'vertical', 'diagonal'],
        default=DEFAULT_DIRECTION,
        help='Gradient direction',
    )
    parser.add_argument(
        '-s',
        '--size',
        type=int,
        default=DEFAULT_FONT_SIZE,
        help='SVG font size in px',
    )
    parser.add_argument(
        '--pad',
        type=int,
        default=DEFAULT_PAD,
        help='Uniform padding around the banner (Zsh lines/spaces and SVG margins)',
    )
    parser.add_argument(
        '-o',
        '--out',
        type=Path,
        help='Output directory (defaults to BANNER_OUT_DIR env var or current dir)',
    )
    parser.add_argument(
        '-l',
        '--list-fonts',
        nargs='*',
        metavar='FONT',
        help="List fonts, or install one: -l 'ANSI Shadow' / -l install 'ANSI Shadow'",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    if args.list_fonts is not None:
        if not args.list_fonts:
            list_fonts()
        else:
            tokens = (
                args.list_fonts[1:]
                if args.list_fonts[0].lower() == 'install'
                else args.list_fonts
            )
            if not tokens:
                sys.exit("Specify a font name, e.g.: -l install 'ANSI Shadow'")
            install_font(' '.join(tokens))
        return
    build(args)


if __name__ == '__main__':
    main()
