#!/usr/bin/env python3
"""Offline CLI utility to generate Zsh and SVG banners using local FIGlet."""

import argparse
import html
import os
from pathlib import Path
import shutil
import subprocess
import sys

# =======================================================================
# DEFAULT VALUES
# =======================================================================
DEFAULT_FONT = 'standard'
DEFAULT_PRESET = 'fire'
DEFAULT_DIRECTION = 'diagonal'
DEFAULT_FONT_SIZE = 16
DEFAULT_PAD_TOP = 1
DEFAULT_PAD_BOTTOM = 1

PRESETS: dict[str, list[str]] = {
    'fire': ['#ff0000', '#ff5f00', '#ffaf00', '#ffd700'],
    'cyber': ['#9d00ff', '#ff007f', '#00f0ff'],
    'emerald': ['#00875f', '#00d787', '#afff00'],
    'mono': ['#585858', '#9e9e9e', '#ffffff'],
    'ocean': ['#0033ff', '#0099ff', '#00ffff'],
    'steel': ['#cbd5e1', '#64748b', '#38bdf8'],
}


def resolve_out_dir(cli_out: Path | None) -> Path:
    """Resolve output directory from CLI flag, env var, or current working directory."""
    if cli_out is not None:
        return cli_out.expanduser().resolve()
    env_out = os.environ.get('BANNER_OUT_DIR')
    if env_out:
        return Path(env_out).expanduser().resolve()
    return Path.cwd()


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


def list_local_fonts() -> None:
    """Print all locally available FIGlet fonts."""
    figlet_bin = shutil.which('figlet')
    if not figlet_bin:
        sys.exit("Error: 'figlet' is not installed.")

    res = subprocess.run(
        [figlet_bin, '-I', '2'],
        capture_output=True,
        text=True,
        check=True,
    )
    font_dir = Path(res.stdout.strip())
    if font_dir.exists():
        fonts = sorted(p.stem for p in font_dir.glob('*.flf'))
        print('Available local fonts:', ', '.join(fonts))


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
    """Interpolate a color across RGB stops at normalized position t."""
    t = max(0.0, min(1.0, t))
    if len(colors) == 1:
        first_color = next(iter(colors))
        return rgb_to_hex(first_color)
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


def build(args: argparse.Namespace) -> None:
    """Generate banner.txt, banner.zsh, and banner.svg in the chosen directory."""
    if args.colors:
        raw_colors = [c.strip() for c in args.colors.split(',') if c.strip()]
        theme_label = f'custom ({args.colors})'
    else:
        if args.preset not in PRESETS:
            available = ', '.join(PRESETS.keys())
            sys.exit(f"Unknown preset '{args.preset}'. Available: {available}")
        raw_colors = PRESETS[args.preset]
        theme_label = args.preset

    out_dir = resolve_out_dir(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

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

    for y, line in enumerate(lines):
        zsh_row = []
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
        y_pos = round((y + 0.85) * line_h, 2)
        svg_rows.append(
            f'  <text x="0" y="{y_pos}" xml:space="preserve">{"".join(svg_spans)}</text>',
        )

    top_pad = '\n' * args.pad_top
    bot_pad = '\n' * args.pad_bottom
    zsh_content = (
        f'print -P \\\n"{top_pad}' + '\n'.join(zsh_lines) + f'{bot_pad}"\n'
    )
    zsh_out.write_text(zsh_content, encoding='utf-8')

    svg_w = round(width * char_w, 2)
    svg_h = round(height * line_h, 2)
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
        f'Done! Saved to {out_dir} | Theme: {theme_label} | Direction: {args.direction} | Size: {args.size}px'
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for full banner customization."""
    parser = argparse.ArgumentParser(
        description='Configure and build Zsh + SVG banners offline.',
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
        help=f'Color preset ({", ".join(PRESETS.keys())})',
    )
    parser.add_argument(
        '-c',
        '--colors',
        help="Custom comma-separated HEX colors (e.g. '#ff0055,#00ffcc')",
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
        '-o',
        '--out',
        type=Path,
        help='Output directory (defaults to BANNER_OUT_DIR env var or current dir)',
    )
    parser.add_argument(
        '--pad-top', type=int, default=DEFAULT_PAD_TOP, help='Zsh top padding'
    )
    parser.add_argument(
        '--pad-bottom',
        type=int,
        default=DEFAULT_PAD_BOTTOM,
        help='Zsh bottom padding',
    )
    parser.add_argument(
        '--list-fonts',
        action='store_true',
        help='List available local FIGlet fonts and exit',
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    if args.list_fonts:
        list_local_fonts()
        return
    build(args)


if __name__ == '__main__':
    main()
