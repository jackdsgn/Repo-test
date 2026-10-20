"""Efeitos sonoros sincronizados com film.html → audio/sfx.wav (48 kHz, estéreo).

Mesmos sons aprovados no vídeo anterior (audio/sfx/):
  pop-grave_495.mp3  pop grave curto            → pulso de abertura, entrada de formas
  clique_503.mp3     clique brilhante           → pedido, ticks dos exemplos, prévia
  whooshes_864.mp3   5 whooshes                 → expansão, percurso, wipe

Deixas em segundos do vídeo, nos pontos que a ficha de áudio de cada cena pede. O pico de cada som cai
no momento visual da ação.

  python3 audio/sfx_mix.py [fim]
"""
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR = 48000
DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else float(re.search(r'const DURATION = ([\d.]+)', (ROOT / 'film.html').read_text()).group(1))


def decode(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)


# ---------- amostras: recorte e pico ----------
src = {k: decode(ROOT / 'audio/sfx' / f) for k, f in
       [('pop', 'pop-grave_495.mp3'), ('clk', 'clique_503.mp3'), ('wh', 'whooshes_864.mp3')]}
SLICES = {   # nome: (fonte, início, fim, pico) em segundos
    'pop': ('pop', 0.05, 0.40, 0.10),
    'clk': ('clk', 0.74, 1.30, 0.84),
    'wh0': ('wh', 0.02, 0.50, 0.095),
    'wh1': ('wh', 0.94, 1.46, 1.05),
    'wh2': ('wh', 2.53, 3.06, 2.67),
    'wh3': ('wh', 4.50, 5.16, 4.78),
    'wh4': ('wh', 6.14, 6.84, 6.425),
}
LEVEL = {'pop': -17.0, 'clk': -15.0, 'wh': -19.0}   # pico RMS (janela de 5 ms) de cada som, em dBFS


def sample(name):
    s, a, b, pk = SLICES[name]
    x = src[s][int(a * SR):int(b * SR)].copy()
    fade = int(0.004 * SR)
    x[:fade] *= np.linspace(0, 1, fade)[:, None]
    x[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))[:, None]
    w = int(0.005 * SR)
    peak = max(np.sqrt(np.mean(x[i:i + w] ** 2)) for i in range(0, len(x) - w, w))
    x *= 10 ** (LEVEL[s] / 20) / peak
    return x, pk - a


def pitch(x, semis):
    """Troca de tom por reamostragem (o som fica um pouco mais curto quando sobe)."""
    if not semis:
        return x
    r = 2 ** (semis / 12)
    idx = np.arange(0, len(x) - 1, r)
    i0 = idx.astype(int)
    f = (idx - i0)[:, None]
    return x[i0] * (1 - f) + x[i0 + 1] * f


# ---------- deixas (segundos do vídeo, momento do pico) ----------
CUES = [   # (tempo, som, ganho dB, semitons)
    # 01 · pulso discreto no início; clique suave ao mostrar o pedido; o quadrado surge
    (0.08, 'pop', -2, -2),
    (0.70, 'clk', -7, 2),
    (1.62, 'pop', -2, 0),
    (4.85, 'wh1', -4, 0),           # o quadrado expande em card
    # 02 · um tick sutil por exemplo, quando a voz o nomeia
    (6.30, 'clk', -10, 5),          # fade in
    (9.00, 'clk', -10, 5),          # slide in
    (10.90, 'clk', -10, 6),         # stagger
    (13.45, 'wh3', -8, 2),          # contêineres viram pistas
    # 03 · whoosh leve no primeiro percurso; a repetição fica sem efeito
    (16.90, 'wh2', -7, 0),
    # 04 · som curto no fim da contagem
    (27.95, 'clk', -6, 3),
    # 05 · whoosh curto no wipe final, sem som no morph
    (37.00, 'wh4', -3, 0),
    # 06 · clique único ao iniciar a prévia
    (42.97, 'clk', -5, 1),
    # 07 · o marcador entra
    (49.35, 'pop', -5, 0),
]
MASTER_DB = 0.0   # o nível final dos efeitos sob a voz é definido em audio/mix.py

# ---------- mixagem ----------
bus = np.zeros((int(DURATION * SR) + SR, 2))
cache = {}
for o, name, gain, semis in CUES:
    if o > DURATION: continue
    if name not in cache:
        cache[name] = sample(name)
    x, pk = cache[name]
    r = 2 ** (semis / 12)
    y = pitch(x, semis) * 10 ** (gain / 20)
    start = int((o - pk / r) * SR)
    bus[max(0, start):start + len(y)] += y[max(0, -start):][:len(bus) - max(0, start)]
bus = bus[:int(DURATION * SR)] * 10 ** (MASTER_DB / 20)

tmp = ROOT / 'audio/sfx_raw.wav'
out = ROOT / 'audio/sfx.wav'
pcm = (np.clip(bus, -1, 1) * 32767).astype('<i2')
with wave.open(str(tmp), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
# limitador de segurança: true peak abaixo de −1 dBTP
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(tmp), '-af', 'alimiter=limit=0.85:level=false',
                '-ar', str(SR), '-c:a', 'pcm_s16le', str(out)], check=True)
tmp.unlink()
print(f'{out.relative_to(ROOT)} · {len(CUES)} deixas · {DURATION:.2f} s')
