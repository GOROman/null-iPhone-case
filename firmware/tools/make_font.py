"""Render NULL FONT outlines at 4x resolution into native-size M5GFX VLW glyphs."""
from math import ceil, floor
from pathlib import Path
import struct
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[2]
source = root / "null-font/NULLFont-Regular.ttf"
license_text = (root / "null-font/OFL.txt").read_bytes()
scale = 4
for size, alphabet in [(24, "CODEX WEEKLYCLAUDEMUSAVO6728%"), (30, "0123456789%SYNC-"), (36, "NULL PAPER")]:
    font = ImageFont.truetype(source, size * scale)
    chars = sorted(set(alphabet))
    ascent, descent = (ceil(n / scale) for n in font.getmetrics())
    records = bytearray(struct.pack(">6I", len(chars), 11, size, 0, ascent, descent))
    pixels = bytearray()
    for char in chars:
        left, top, right, bottom = font.getbbox(char, anchor="ls")
        left, top = floor(left / scale), floor(top / scale)
        width, height = ceil(right / scale) - left, ceil(bottom / scale) - top
        advance = round(font.getlength(char) / scale)
        records.extend(struct.pack(">7i", ord(char), height, width, advance, -top, left, 0))
        if width and height:
            tile = Image.new("L", (width * scale, height * scale))
            ImageDraw.Draw(tile).text((-left * scale, -top * scale), char, 255, font=font, anchor="ls")
            pixels.extend(tile.resize((width, height), Image.Resampling.LANCZOS).tobytes())
    target = root / f"firmware/assets/null_regular_{size}.vlw"
    target.write_bytes(records + pixels + license_text)
