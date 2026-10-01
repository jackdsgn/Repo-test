#!/usr/bin/env python3
"""Keep film.html a single self-contained file: embed the font and the measured timeline.

  python3 tools/inject.py      (run after audio/analyze.py)
"""
import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
html_path = ROOT / "film.html"
html = html_path.read_text()

font = base64.b64encode((ROOT / "assets" / "InterTight-latin.woff2").read_bytes()).decode()
html, n_font = re.subn(r'src:url\("data:font/woff2;base64,[^"]*"\)',
                       f'src:url("data:font/woff2;base64,{font}")', html, count=1)

timeline = (ROOT / "audio" / "timeline.json").read_text().strip()
html, n_tl = re.subn(r'(<script id="timeline" type="application/json">)(.*?)(</script>)',
                     lambda m: m.group(1) + timeline + m.group(3), html, count=1, flags=re.S)

if not (n_font and n_tl):
    raise SystemExit(f"inject failed: font={n_font} timeline={n_tl}")
html_path.write_text(html)
print(f"film.html: font {len(font) // 1024} KB base64 · timeline {len(timeline) // 1024} KB")
