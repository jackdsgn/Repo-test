"""Tempo do vídeo a partir de film.html: a mesma regra de seek() (PACE → KNOTS) para os scripts de áudio.

Os sons e a voz são posicionados no tempo do roteiro (o mesmo de seek()) e convertidos por at().
"""
import re
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR = 48000


def decode(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)


html = (ROOT / 'film.html').read_text(encoding='utf-8')
pace_src = re.search(r'const PACE = \[(.*?)\];', html, re.S).group(1)
knots = [(0.0, 0.0)]   # (novo, roteiro)
for m in re.finditer(r'\{ *(at: *([\d.]+), *hold: *([\d.]+)|a: *([\d.]+), *b: *([\d.]+), *len: *([\d.]+)) *\}', pace_src):
    n, o = knots[-1]
    if m.group(2):
        at, hold = float(m.group(2)), float(m.group(3))
        n0 = n + at - o
        knots += [(n0, at), (n0 + hold, at)]
    else:
        a, b, ln = float(m.group(4)), float(m.group(5)), float(m.group(6))
        n0 = n + a - o
        knots += [(n0, a), (n0 + ln, b)]
END = float(re.search(r'const END = ([\d.]+)', html).group(1))
n, o = knots[-1]
knots.append((n + END - o, END))
DURATION = knots[-1][0]


def at(o):
    """Tempo do roteiro → tempo do vídeo (antes de uma pausa, nunca dentro dela)."""
    for (n0, o0), (n1, o1) in zip(knots, knots[1:]):
        if o1 > o0 and o0 <= o <= o1:
            return n0 + (o - o0) * (n1 - n0) / (o1 - o0)
    raise ValueError(o)


