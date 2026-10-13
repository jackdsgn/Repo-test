"""Voz + efeitos → audio/mix.wav (48 kHz, estéreo): −16 LUFS integrado, true peak abaixo de −1 dBTP.

Os efeitos ficam 7 dB abaixo da voz e abaixam mais 6 dB enquanto ela fala (ducking com ataque de
20 ms e soltura de 250 ms), para nunca competir com a narração.

  python3 audio/narracao.py && python3 audio/sfx_mix.py && python3 audio/mix.py
"""
import subprocess
import wave

import numpy as np

from timeline import ROOT, SR, decode

SFX_DB, DUCK_DB = -7.0, -6.0


def lufs(x):
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2').tobytes()
    log = subprocess.run(['ffmpeg', '-v', 'info', '-f', 's16le', '-ar', str(SR), '-ac', '2', '-i', '-', '-af', 'ebur128', '-f', 'null', '-'],
                         input=pcm, capture_output=True).stderr.decode()
    return float(log.rsplit('I:', 1)[1].split('LUFS')[0])


voice, sfx = decode(ROOT / 'audio/voz.wav'), decode(ROOT / 'audio/sfx.wav')
n = min(len(voice), len(sfx)); voice, sfx = voice[:n], sfx[:n]

# voz em −16 LUFS; efeitos no mesmo nível de referência e depois abaixo dela
voice *= 10 ** ((-16 - lufs(voice)) / 20)
sfx *= 10 ** ((-16 - lufs(sfx) + SFX_DB) / 20)

# ducking: envelope da voz (ataque 20 ms, soltura 250 ms) → redução de até DUCK_DB nos efeitos
env = np.abs(voice).max(1)
hop = int(0.005 * SR)
blocks = env[:len(env) // hop * hop].reshape(-1, hop).max(1)
on = (20 * np.log10(blocks + 1e-9) > -40).astype(float)
g = np.zeros_like(on); a_c, r_c = np.exp(-0.005 / 0.02), np.exp(-0.005 / 0.25)
for i in range(1, len(on)):
    c = a_c if on[i] > g[i - 1] else r_c
    g[i] = c * g[i - 1] + (1 - c) * on[i]
duck = 10 ** (DUCK_DB * np.repeat(g, hop) / 20)
duck = np.concatenate([duck, np.full(n - len(duck), duck[-1])])
mix = voice + sfx * duck[:, None]
mix *= 10 ** ((-16 - lufs(mix)) / 20)

tmp = ROOT / 'audio/mix_raw.wav'
with wave.open(str(tmp), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
# limitador de pico (o loudness já está em −16 LUFS)
out = ROOT / 'audio/mix.wav'
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(tmp), '-af',
                'alimiter=limit=0.85:attack=2:release=60:level=false', '-ar', str(SR), '-c:a', 'pcm_s16le', str(out)],
               check=True)
tmp.unlink()
log = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(out), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
I = log.rsplit('I:', 1)[1].split('LUFS')[0].strip(); P = log.rsplit('Peak:', 1)[1].split('dBFS')[0].strip()
print(f'audio/mix.wav · {I} LUFS · true peak {P} dBFS')
