"""Narração → audio/voz.wav (posicionada nas cenas) e audio/legendas.js (legendas palavra a palavra).

audio/narracao.mp3 (ElevenLabs, 34,35 s) é cortada nas pausas: o silencedetect encontra 23 trechos de
fala, que batem com o roteiro em ordem e em duração (5–7 sílabas/s). A frase final do roteiro
("Na hora de criar…") não está no arquivo, então a cena 13 fica sem fala.

A fala de cada cena começa no início dela (tempo do roteiro, convertido por at()), mantendo as pausas
naturais entre os trechos da mesma cena. Entre uma cena e outra fica o silêncio que o ritmo pede.

Legendas: o texto é o que a voz diz, em grupos de 2–6 palavras. Dentro de cada trecho, o tempo de
cada palavra é proporcional às sílabas, preso às bordas medidas do trecho. Sem transcrição automática
neste ambiente, esse é o encaixe por palavra; as bordas de cada trecho são medidas.

  python3 audio/narracao.py
"""
import json
import re
import subprocess
import wave

import numpy as np

from timeline import DURATION, ROOT, SR, at, decode

SRC = ROOT / 'audio/narracao.mp3'

# texto de cada trecho de fala, na ordem do arquivo
CHUNKS = [
    'Quer editar vídeos com Claude?', 'Comece por estes sete passos.', 'Um:', 'abra o Claude.',
    'Dois:', 'defina o estilo.', 'Prepare seu guia visual e as referências.',
    'Três:', 'se tiver uma skill de edição,', 'ative-a.', 'Quatro: separe os vídeos, as imagens e os áudios.',
    'Cinco:', 'envie os arquivos e as instruções.',
    'Seis:', 'explique o resultado que você quer:', 'formato, duração, ritmo e animações.',
    'Sete:', 'aguarde a prévia.', 'O tempo varia conforme o projeto.',
    'Precisa ajustar?', 'Diga exatamente o que mudar.', 'Pronto.', 'Salve este passo a passo.',
]
# cena: trechos, início e fim no tempo do roteiro, palavras por linha de legenda
SCENES = [
    ([0], 0.15, 1.95, [5]),
    ([1], 2.05, 3.95, [5]),
    ([2, 3], 4.05, 5.95, [4]),
    ([4, 5, 6], 6.05, 9.95, [4, 4, 3]),
    ([7, 8, 9], 10.05, 13.95, [5, 3]),
    ([10], 14.05, 18.45, [4, 5]),
    ([11, 12], 18.55, 20.95, [4, 3]),
    ([13, 14, 15], 21.05, 26.45, [4, 3, 2, 3]),
    ([16, 17, 18], 26.55, 30.45, [4, 6]),
    ([19, 20], 30.55, 32.95, [2, 5]),
    ([21], 33.05, 33.95, [1]),
    ([22], 34.05, 35.95, [5]),
]


def speech_chunks():
    log = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(SRC), '-af', 'silencedetect=noise=-38dB:d=0.18', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
    total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(SRC)],
                                 capture_output=True, text=True).stdout)
    bounds = [0.0] + ends
    stops = starts + ([total] if len(starts) == len(ends) else [])
    return [(a, b) for a, b in zip(bounds, stops) if b - a > 0.05]


def syllables(word):
    w = word.lower().replace('claude', 'clód').replace('skill', 'squil')
    return max(1, len(re.findall(r'[aeiouáéíóúâêôãõà]+', w)))


chunks = speech_chunks()
assert len(chunks) == len(CHUNKS), f'{len(chunks)} trechos de fala, esperados {len(CHUNKS)}'

voice = decode(SRC)
bus = np.zeros((int(DURATION * SR) + SR, 2))
captions, placed = [], []
for idx, o_start, o_end, lines in SCENES:
    t0 = at(o_start)                     # a primeira palavra da cena cai aqui
    src0 = chunks[idx[0]][0]
    # áudio da cena: do primeiro ao último trecho, com as pausas internas
    a, b = max(0.0, src0 - 0.04), chunks[idx[-1]][1] + 0.12
    seg = voice[int(a * SR):int(b * SR)].copy()
    f = int(0.01 * SR)
    seg[:f] *= np.linspace(0, 1, f)[:, None]
    seg[-f:] *= np.linspace(1, 0, f)[:, None]
    pos = int((t0 - (src0 - a)) * SR)
    bus[pos:pos + len(seg)] += seg
    placed.append((t0, t0 + chunks[idx[-1]][1] - src0))
    # palavras com tempo
    words = []
    for k in idx:
        ca, cb = chunks[k]
        ws = CHUNKS[k].split()
        syl = np.array([syllables(w) for w in ws], float)
        edges = ca + (cb - ca) * np.concatenate([[0], np.cumsum(syl) / syl.sum()])
        words += [(w, t0 + s - src0, t0 + e - src0) for w, s, e in zip(ws, edges[:-1], edges[1:])]
    assert sum(lines) == len(words), (CHUNKS[idx[0]], sum(lines), len(words))
    scene_end = at(o_end)
    i = 0
    for j, n in enumerate(lines):
        grp = words[i:i + n]; i += n
        nxt = words[i][1] if i < len(words) else None
        show_a = grp[0][1] - 0.12
        show_b = (nxt - 0.06) if nxt is not None else min(grp[-1][2] + 1.4, scene_end)
        captions.append({'a': round(show_a, 3), 'b': round(show_b, 3),
                         'words': [{'w': w, 's': round(s, 3), 'e': round(e, 3)} for w, s, e in grp]})

for (s0, e0), (s1, _) in zip(placed, placed[1:]):
    assert e0 < s1, f'fala sobreposta em {s0:.2f} s'

out = ROOT / 'audio/voz.wav'
pcm = (np.clip(bus[:int(DURATION * SR)], -1, 1) * 32767).astype('<i2')
with wave.open(str(out), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
(ROOT / 'audio/legendas.js').write_text(
    '// gerado por audio/narracao.py: legendas no tempo do vídeo (s), palavra a palavra\n'
    'window.LEGENDAS = ' + json.dumps(captions, ensure_ascii=False, indent=1) + ';\n', encoding='utf-8')
print(f'audio/voz.wav · {len(chunks)} trechos em {len(SCENES)} cenas · audio/legendas.js · {len(captions)} linhas')
for (s0, e0), (idx, *_ ) in zip(placed, SCENES):
    print(f'  {s0:6.2f}–{e0:6.2f} s  {" ".join(CHUNKS[k] for k in idx)}')
