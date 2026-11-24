"""Prepare one e-paper still from the upstream Jollybot animation at build time."""
import hashlib
from pathlib import Path
import re
from urllib.request import urlopen

Import("env")  # PlatformIO/SCons
commit = "18dcce3d9b6eb845c7ab859a33488be66a58fba2"
digest = "547e5201bcf8667a6603d3323d4f973059bbf605f20461bc09f67b30a34c5c21"
url = f"https://raw.githubusercontent.com/facebookincubator/muse-gadget-sdk/{commit}/esp32/avatar/happy_anim.c"
cache = Path(env.subst("$PROJECT_DIR")) / ".pio" / "muse-assets"
cache.mkdir(exist_ok=True, parents=True)
source = cache / f"{commit}.c"
data = source.read_bytes() if source.exists() else b""
if hashlib.sha256(data).hexdigest() != digest:
    with urlopen(url, timeout=30) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("Unexpected upstream Jollybot asset checksum")
    source.write_bytes(data)
text = data.decode()
palette = []
for rgb in re.findall(r"// #([0-9a-f]{6})", text):
    r, g, b = bytes.fromhex(rgb)
    palette.append(round((0.299 * r + 0.587 * g + 0.114 * b) / 17))
palette[0] = 15  # The upstream background becomes e-paper white.
first = text.split("const uint8_t happy_anim_frames")[1].split("= {", 1)[1].split("}", 1)[0]
pixels = [palette[int(i)] for i in re.findall(r"\d+", first)]
if len(pixels) != 56 * 59:
    raise ValueError("Unexpected upstream frame size")
rows = []
for y in range(59):
    row = pixels[y * 56:(y + 1) * 56]
    rows.append(", ".join(f"0x{a * 16 + b:02x}" for a, b in zip(row[::2], row[1::2])))
header = "// Jollybot, copyright Meta Platforms, Inc. and affiliates.\n#pragma once\n"
header += "static constexpr uint8_t museStill[59][28] = {\n" + ",\n".join("    {" + row + "}" for row in rows) + "\n};\n"
output = cache / "muse_still.h"
if not output.exists() or output.read_text() != header:
    output.write_text(header)
env.Append(CPPPATH=[str(cache)])
