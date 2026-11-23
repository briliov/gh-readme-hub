"""Unit tests for builders/banner/build.py."""

import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / 'builders' / 'banner' / 'build.py'
spec = importlib.util.spec_from_file_location('banner_build', MODULE_PATH)
banner_build = importlib.util.module_from_spec(spec)
sys.modules['banner_build'] = banner_build
spec.loader.exec_module(banner_build)


def test_hex_to_rgb_and_back() -> None:
    """Verify HEX to RGB and RGB to HEX conversions."""
    rgb = banner_build.hex_to_rgb('#38bdf8')
    assert rgb == (56, 189, 248)
    assert banner_build.rgb_to_hex(rgb) == '#38bdf8'


def test_hex_to_rgb_invalid() -> None:
    """Verify invalid HEX string triggers sys.exit."""
    with pytest.raises(SystemExit):
        banner_build.hex_to_rgb('#123')


def test_interpolate_color_multi_stop() -> None:
    """Verify multi-stop color interpolation at start, middle, and end."""
    stops = [(0, 0, 0), (100, 100, 100), (200, 200, 200)]
    assert banner_build.interpolate_color(stops, 0.0) == '#000000'
    assert banner_build.interpolate_color(stops, 0.5) == '#646464'
    assert banner_build.interpolate_color(stops, 1.0) == '#c8c8c8'


def test_parse_color_list() -> None:
    """Verify parsing comma- and space-separated HEX colors."""
    colors = banner_build.parse_color_list('#ff0000, 00ff00 #0000ff')
    assert colors == ['#ff0000', '#00ff00', '#0000ff']


def test_presets_init_and_save(tmp_path: Path) -> None:
    """Verify presets.json initialization and custom preset saving."""
    presets = banner_build.load_local_presets(tmp_path)
    assert 'steel' in presets
    assert (tmp_path / 'presets.json').exists()

    banner_build.save_local_preset(tmp_path, 'custom_neon', ['#ff0055', '#00ffcc'])
    saved_data = json.loads((tmp_path / 'presets.json').read_text(encoding='utf-8'))
    assert saved_data['custom_neon'] == ['#ff0055', '#00ffcc']


def test_resolve_out_dir_priority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify CLI flag overrides BANNER_OUT_DIR env var."""
    env_dir = tmp_path / 'env_out'
    cli_dir = tmp_path / 'cli_out'
    monkeypatch.setenv('BANNER_OUT_DIR', str(env_dir))

    assert banner_build.resolve_out_dir(None) == env_dir.resolve()
    assert banner_build.resolve_out_dir(cli_dir) == cli_dir.resolve()


def test_build_generates_zsh_and_svg_with_padding(tmp_path: Path) -> None:
    """Verify full build flow creates banner.txt, banner.zsh, and banner.svg with uniform padding."""
    fake_art = 'AB\nCD\n'
    test_argv = [
        'build.py',
        '-t', 'TEST',
        '-c', '#ff0000,#0000ff',
        '--pad', '2',
        '-o', str(tmp_path),
    ]

    with (
        patch.object(banner_build, 'generate_figlet', return_value=fake_art),
        patch.object(sys, 'argv', test_argv),
    ):
        banner_build.main()

    txt_file = tmp_path / 'banner.txt'
    zsh_file = tmp_path / 'banner.zsh'
    svg_file = tmp_path / 'banner.svg'

    assert txt_file.read_text(encoding='utf-8') == fake_art
    zsh_text = zsh_file.read_text(encoding='utf-8')
    svg_text = svg_file.read_text(encoding='utf-8')

    # Проверка вертикального отступа (--pad 2 -> 2 переноса строки в начале)
    assert zsh_text.startswith('print -P \\\n"\n\n  %F{')
    # Проверка горизонтального отступа (--pad 2 -> 2 пробела перед символами)
    assert '  %F{#ff0000}A' in zsh_text
    # Проверка размеров SVG с учетом pad=2 (width = 2 + 4 = 6 символов, height = 2 + 4 = 6 строк)
    assert 'width="' in svg_text
    assert '<tspan fill="#ff0000">A</tspan>' in svg_text
