"""Efeitos sonoros sincronizados com film.html → audio/sfx.wav (48 kHz, estéreo).

Os sons de audio/sfx/ foram enviados para o projeto:
  pop-grave_495.mp3  pop grave curto (pico em 0,10 s)            → entrada de cards
  clique_503.mp3     clique brilhante (pico em 0,84 s)           → envio, checks, acentos
  whooshes_864.mp3   5 whooshes (picos em 0,10/1,05/2,67/4,78/6,43 s) → troca de cena

Cada deixa é escrita no tempo do roteiro (40 s), como em seek(). O tempo final vem da lista PACE
lida do próprio film.html, então mudar o ritmo leva os sons junto. O pico de cada som cai no
momento visual da ação. Nas cascatas (miniaturas, chips, checks) o tom sobe a cada item e o volume
baixa, para não repetir o mesmo som.

  python3 audio/sfx_mix.py
"""
import subprocess

import numpy as np

from timeline import DURATION, ROOT, SR, at, decode


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


# ---------- deixas (tempo do roteiro, momento do pico) ----------
CUES = []   # (tempo do roteiro, som, ganho dB, semitons)
WH = ['wh0', 'wh1', 'wh2', 'wh3', 'wh4']
for i, o in enumerate([0.10, 2.08, 4.08, 6.10, 10.10, 14.10, 18.60, 21.10, 26.60, 30.60, 33.10, 34.12, 36.12]):
    CUES.append((o, WH[i % 5], -1.5 * (i % 2), 0))      # troca de cena / título

CUES += [   # cards e painéis entrando
    (4.35, 'pop', 0, 0),            # 03 chat
    (6.35, 'pop', 0, 0),            # 04 guia
    (10.35, 'pop', 0, 0),           # 05 SKILL.md
    (16.30, 'pop', -1, 1),          # 06 Imagens
    (16.75, 'pop', -1, 3),          # 06 Áudios
    (25.25, 'pop', 0, 2),           # 08 pedido vira balão
    (25.72, 'pop', -4, 5),          # 08 "Preparando a prévia…"
    (26.85, 'pop', -1, 0),          # 09 círculo
    (30.78, 'pop', -2, 0),          # 10 chat
    (31.20, 'pop', -1, 2),          # 10 pedido de ajuste
    (31.95, 'pop', -1, 4),          # 10 retorno
    (34.95, 'pop', -3, 3),          # 12 "Para testar depois."
]
CUES += [(8.10 + 0.15 * i, 'pop', -3, 2 * i) for i in range(3)]              # 04 referências
CUES += [(14.35 + 0.10 * i, 'pop', -6, i) for i in range(6)]                 # 06 miniaturas
CUES += [(19.05 + 0.18 * i, 'pop', -4, i) for i in range(5)]                 # 07 anexos
CUES += [(24.47 + 0.08 * i, 'pop', -9, 3 + i) for i in range(4)]             # 08 tags
CUES += [(36.65 + 0.18 * i, 'pop', -2, 2 * i) for i in range(3)]             # 13 chips

CUES += [   # cliques e confirmações
    (2.70, 'clk', -2, -3),          # 02 o 7 assenta
    (25.00, 'clk', 0, 0),           # 08 enviar
    (29.70, 'clk', 0, 2),           # 09 check
    (32.08, 'clk', -2, 3),          # 10 ajuste concluído
    (34.30, 'clk', -1, -4),         # 12 marcador
]
CUES += [(6.94 + 0.12 * i, 'clk', -11, 3 + i) for i in range(5)]             # 04 checks do guia
CUES += [   # 14 · assinatura JACK (começa em 40,35 no roteiro)
    (40.35 + 0.30, 'wh2', 0, 0),     # K surge girando
    (40.35 + 1.05, 'wh4', -4, 2),    # K desliza
]
CUES += [(40.35 + 1.10 + 0.13 * i, 'pop', -3, 2 * i) for i in range(3)]      # J, A, C sobem
CUES += [(40.35 + 1.75, 'clk', -2, -2)]                                      # JACK completo
CUES += [(33.33 + 0.06 * i, 'clk', -8, 2 + i) for i in range(7)]             # 11 checks do resumo

# ---------- mixagem ----------
bus = np.zeros((int(DURATION * SR) + SR, 2))
cache = {}
for o, name, gain, semis in CUES:
    if name not in cache:
        cache[name] = sample(name)
    x, pk = cache[name]
    r = 2 ** (semis / 12)
    y = pitch(x, semis) * 10 ** (gain / 20)
    start = int((at(o) - pk / r) * SR)
    bus[max(0, start):start + len(y)] += y[max(0, -start):][:len(bus) - max(0, start)]
bus = bus[:int(DURATION * SR)]

tmp = ROOT / 'audio/sfx_raw.wav'
out = ROOT / 'audio/sfx.wav'
pcm = (np.clip(bus, -1, 1) * 32767).astype('<i2')
import wave
with wave.open(str(tmp), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
# limitador de segurança: true peak abaixo de −1 dBTP
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(tmp), '-af', 'alimiter=limit=0.85:level=false',
                '-ar', str(SR), '-c:a', 'pcm_s16le', str(out)], check=True)
tmp.unlink()
print(f'{out.relative_to(ROOT)} · {len(CUES)} deixas · {DURATION:.2f} s')
