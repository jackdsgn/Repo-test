"""Narração → tempos por palavra (audio/palavras.json) e legendas (out/legendas.srt).

audio/narracao.mp3 (ElevenLabs, 54,05 s) fica contínua, do início ao fim: as cenas é que se
ajustam à fala. O silencedetect corta 24 trechos de fala, que batem com o roteiro do storyboard em
ordem e em duração (5–7 sílabas/s). Dentro de cada trecho, o tempo de cada palavra é proporcional às
sílabas, preso às bordas medidas do trecho. Os tempos das ações em film.html vêm destes valores.

As legendas saem em .srt (para a plataforma), não gravadas na imagem: o storyboard pede para não
sobrepor legendas aos rótulos das demonstrações.

  python3 audio/narracao.py
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'audio/narracao.mp3'

CHUNKS = [
    'Pedir um vídeo dinâmico não explica o movimento.', 'Dê direção.',
    'Comece pela entrada.', 'Fade in revela pela opacidade.', 'Slide in desliza.',
    'Stagger distribui as entradas em sequência.',
    'Depois, defina o ritmo.', 'Ease in-out acelera e desacelera.',
    'Mola e quique são escolhas de linguagem, não obrigação.',
    'No texto,', 'revele palavras para guiar a leitura.', 'Use contagem para números e destaque apenas', 'o que importa.',
    'Para conectar cenas, transforme uma forma com morph', 'ou revele a próxima com wipe.', 'Preserve a continuidade.',
    'Agora, escreva:', 'revele o título com fade in em meio segundo.', 'Mantenha dois segundos para leitura.',
    'Especifique o elemento, a ação e o tempo.', 'Depois, confira a prévia.',
    'Salve para consultar.', 'No próximo prompt,', 'descreva o movimento com intenção.',
]
# legendas: palavras por linha, por trecho (2–6 palavras)
LINES = [[4, 4], [2], [3], [5], [3], [2, 4], [4], [2, 3], [5, 4], [2], [3, 3], [4, 3], [3],
         [3, 5], [3, 3], [3], [2], [4, 5], [5], [3, 5], [4], [3], [3], [5]]


def speech_chunks():
    log = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(SRC), '-af', 'silencedetect=noise=-38dB:d=0.18', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
    total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(SRC)],
                                 capture_output=True, text=True).stdout)
    stops = starts + ([total] if len(starts) == len(ends) else [])
    return [(a, b) for a, b in zip([0.0] + ends, stops) if b - a > 0.05]


def syllables(word):
    w = word.lower()
    for a, b in [('fade', 'fêid'), ('slide', 'slaid'), ('stagger', 'stéguer'), ('ease', 'iz'), ('in-out', 'in-aut'),
                 ('morph', 'morf'), ('wipe', 'uaip'), ('prompt', 'prómpt')]:
        w = w.replace(a, b)
    return max(1, len(re.findall(r'[aeiouáéíóúâêôãõà]+', w)))


chunks = speech_chunks()
assert len(chunks) == len(CHUNKS), f'{len(chunks)} trechos de fala, esperados {len(CHUNKS)}'

words, lines = [], []
for (a, b), text, split in zip(chunks, CHUNKS, LINES):
    ws = text.split()
    syl = [syllables(w) for w in ws]
    total, acc, cw = sum(syl), 0, []
    for w, n in zip(ws, syl):
        s = a + (b - a) * acc / total; acc += n
        cw.append({'w': w, 's': round(s, 3), 'e': round(a + (b - a) * acc / total, 3)})
    words += cw
    assert sum(split) == len(cw), (text, split)
    i = 0
    for n in split:
        lines.append(cw[i:i + n]); i += n

(ROOT / 'audio/palavras.json').write_text(json.dumps(words, ensure_ascii=False, indent=0), encoding='utf-8')


def ts(x):
    ms = int(round(x * 1000))
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


srt = []
for k, ln in enumerate(lines):
    nxt = lines[k + 1][0]['s'] if k + 1 < len(lines) else ln[-1]['e'] + 1.0
    srt.append(f"{k + 1}\n{ts(ln[0]['s'])} --> {ts(min(ln[-1]['e'] + 0.6, nxt - 0.04))}\n{' '.join(w['w'] for w in ln)}\n")
(ROOT / 'out').mkdir(exist_ok=True)
(ROOT / 'out/legendas.srt').write_text('\n'.join(srt), encoding='utf-8')
print(f'{len(chunks)} trechos · {len(words)} palavras · {len(lines)} legendas → audio/palavras.json, out/legendas.srt')
