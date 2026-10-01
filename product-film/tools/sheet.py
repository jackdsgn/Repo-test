#!/usr/bin/env python3
"""Contact sheet of PNG frames: python3 tools/sheet.py in_dir out.png [cols] [scale]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

src, out = Path(sys.argv[1]), sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 5
scale = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25
files = sorted(src.glob("*.png"))
ims = [Image.open(f).convert("RGB") for f in files]
w, h = int(ims[0].width * scale), int(ims[0].height * scale)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (w + 8) + 8, rows * (h + 34) + 8), "#d9d9d6")
d = ImageDraw.Draw(sheet)
for i, (f, im) in enumerate(zip(files, ims)):
    x, y = 8 + (i % cols) * (w + 8), 8 + (i // cols) * (h + 34)
    sheet.paste(im.resize((w, h), Image.LANCZOS), (x, y + 26))
    d.text((x + 2, y + 6), f.stem, fill="#111708")
sheet.save(out)
print(out, sheet.size)
