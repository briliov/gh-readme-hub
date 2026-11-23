from __future__ import annotations

import base64
import colorsys
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from profile_sync.config import BADGES_DIR, SVG_NS

ET.register_namespace('', SVG_NS)


def adjust_universal_color(hex_str: str) -> str:
    clean_hex = hex_str.lstrip('#')
    if len(clean_hex) != 6:
        return '#7d8590'

    r, g, b = (int(clean_hex[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    if s < 0.15:
        return '#7d8590'

    l = max(0.42, min(0.54, l))
    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return f'#{int(nr * 255):02x}{int(ng * 255):02x}{int(nb * 255):02x}'


def colorize_svg(svg_bytes: bytes, hex_color: str) -> str:
    try:
        ET.register_namespace('', SVG_NS)
        root = ET.fromstring(svg_bytes)
        root.set('fill', hex_color)
        shapes = ('path', 'circle', 'rect', 'polygon', 'ellipse')
        for elem in root.iter():
            if elem.tag.endswith('style'):
                elem.text = ''
            if 'style' in elem.attrib:
                del elem.attrib['style']
            tag_name = elem.tag.split('}')[-1]
            fill_val = elem.attrib.get('fill', '').lower()
            if fill_val not in ('none', 'transparent'):
                if fill_val or tag_name in shapes:
                    elem.set('fill', hex_color)
            stroke_val = elem.attrib.get('stroke', '').lower()
            if stroke_val and stroke_val not in ('none', 'transparent'):
                elem.set('stroke', hex_color)
        encoded = base64.b64encode(ET.tostring(root, encoding='utf-8')).decode(
            'ascii'
        )
        return f'data:image/svg+xml;base64,{encoded}'
    except ET.ParseError:
        encoded = base64.b64encode(svg_bytes).decode('ascii')
        return f'data:image/svg+xml;base64,{encoded}'


def _inline_svg_icon(data_uri: str, raw_color: str) -> str:
    prefix = 'data:image/svg+xml;base64,'
    if not data_uri.startswith(prefix):
        return f'<image x="12" y="7.5" width="15" height="15" href="{data_uri}" />'

    svg_bytes = base64.b64decode(data_uri[len(prefix) :])
    universal_hex = (
        adjust_universal_color(raw_color)
        if raw_color.startswith('#')
        else '#7d8590'
    )
    colored_uri = colorize_svg(svg_bytes, universal_hex)
    colored_xml = base64.b64decode(colored_uri[len(prefix) :]).decode('utf-8')

    ET.register_namespace('', SVG_NS)
    root = ET.fromstring(colored_xml)
    vb = root.attrib.get('viewBox')
    if not vb:
        w = re.sub(r'[^0-9.]', '', root.attrib.get('width', '24')) or '24'
        h = re.sub(r'[^0-9.]', '', root.attrib.get('height', '24')) or '24'
        vb = f'0 0 {w} {h}'

    inner_parts = []
    for child in root:
        tag = child.tag.split('}')[-1]
        if tag in ('title', 'desc', 'metadata', 'style'):
            continue
        raw_child = ET.tostring(child, encoding='unicode')
        raw_child = re.sub(r'\s+xmlns(?::\w+)?=\"[^\"]+\"', '', raw_child)
        raw_child = re.sub(r'<(/?)ns\d+:', r'<\1', raw_child)
        inner_parts.append(raw_child)

    inner_xml = ''.join(inner_parts)
    return f'<svg x="12" y="7.5" width="15" height="15" viewBox="{vb}">{inner_xml}</svg>'


def create_svg_badge(
    topic: str,
    icon_data: str,
    raw_color: str,
    display_label: str | None = None,
) -> Path:
    label = (display_label or topic.replace('-', ' ')).upper()
    char_width = 9.2
    text_width = int(len(label) * char_width)
    icon_offset = 25
    total_width = text_width + icon_offset + 28
    text_x = (13 + icon_offset) + (text_width / 2)

    inline_icon = _inline_svg_icon(icon_data, raw_color)
    lines = [
        f'<svg xmlns="{SVG_NS}" width="{total_width}" height="30" role="img" aria-label="{label}">',
        f'  <rect x="0.5" y="0.5" width="{total_width - 1}" height="29" rx="6" '
        f'fill="#8b949e" fill-opacity="0.14" stroke="#8b949e" stroke-opacity="0.32" stroke-width="1" />',
        f'  {inline_icon}',
        f'  <text x="{text_x:.1f}" y="19" fill="#7d8590" '
        f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" '
        f'font-size="11" font-weight="800" text-anchor="middle" letter-spacing="1.5">{label}</text>',
        '</svg>',
    ]
    badge_path = BADGES_DIR / f'{topic}.svg'
    badge_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return badge_path
