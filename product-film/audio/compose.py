#!/usr/bin/env python3
"""FIN JACK · product film — original 120 BPM track, composed in code.

Everything here is synthesized from scratch with numpy/scipy, so the track is
royalty-free by construction.

Output (48 kHz, stereo, 24-bit WAV):
  track_loop.wav  8 bars = 16.000 s. Circular render: every reverb/delay tail
                  that runs past bar 8 is folded back onto bar 1, so the file
                  loops with no seam.

Form (bars 1-8, F major, 4-on-the-floor):
  1-4  phrase A  "acao"      kick · clap · closed hats · offbeat bass · EP
  5-8  phrase B  "resultado" + open hats · shaker · pad · pluck motif
  riser 7.0→8.0 s into the success downbeat (bar 5) + soft impact on 8.0 s
  bar 8 beat 4: clap roll + riser that lands on the loop point
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

SR = 48_000
BPM = 120.0
BEAT = 60.0 / BPM          # 0.5 s
BAR = 4 * BEAT             # 2.0 s
LOOP_BARS = 8
LOOP_SEC = LOOP_BARS * BAR  # 16.0 s
OUT = Path(__file__).resolve().parent

rng = np.random.default_rng(20260925)

# The arrangement leaves room for the UI: on backbeats where the cursor clicks,
# the clap drops to 30 % and the click itself becomes the backbeat.
_EVENTS = json.loads((OUT / "events.json").read_text())["events"]
CLICK_BACKBEATS = {int(e["beat"]) for e in _EVENTS
                   if e["sound"] in ("click", "select") and float(e["beat"]).is_integer() and int(e["beat"]) % 4 in (1, 3)}


# ----------------------------------------------------------------- helpers --
def hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def tvec(sec):
    return np.arange(int(round(sec * SR))) / SR


def _sos(kind, fc, order=2):
    nyq = SR / 2
    if kind == "band":
        return signal.butter(order, [fc[0] / nyq, fc[1] / nyq], "band", output="sos")
    return signal.butter(order, fc / nyq, kind, output="sos")


def lp(x, fc, order=2):
    return signal.sosfilt(_sos("low", fc, order), x, axis=0)


def hp(x, fc, order=2):
    return signal.sosfilt(_sos("high", fc, order), x, axis=0)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("band", (lo, hi), order), x, axis=0)


def fade_edges(x, a=0.002, r=0.01):
    n = len(x)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    env = np.ones(n)
    env[:na] = np.linspace(0, 1, na)
    env[-nr:] *= np.linspace(1, 0, nr)
    return x * env


def pan(mono, p):
    """Constant-power pan, p in [-1, 1]."""
    ang = (p + 1) * np.pi / 4
    return np.stack([mono * np.cos(ang), mono * np.sin(ang)], axis=1)


class Bus:
    """Stereo buffer with room for tails; events are placed by time in seconds."""

    def __init__(self, sec):
        self.buf = np.zeros((int(round(sec * SR)), 2))

    def add(self, t, sig, gain=1.0, p=0.0):
        if sig.ndim == 1:
            sig = pan(sig, p)
        i = int(round(t * SR))
        if i < 0:
            sig, i = sig[-i:], 0
        j = min(len(self.buf), i + len(sig))
        if j > i:
            self.buf[i:j] += gain * sig[: j - i]


# ------------------------------------------------------------- instruments --
def kick(vel=1.0):
    t = tvec(0.55)
    f = 50 + 110 * np.exp(-t / 0.024) + 45 * np.exp(-t / 0.005)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.19)
    body *= np.minimum(1.0, t / 0.0012)
    click = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t / 0.0035) * 0.22
    x = np.tanh(1.7 * (body + click)) / np.tanh(1.7)
    return fade_edges(x, r=0.03) * vel


def clap(vel=1.0):
    t = tvec(0.4)
    env = np.zeros_like(t)
    for k, off in enumerate((0.0, 0.0085, 0.0185, 0.027)):
        m = t >= off
        env[m] += np.exp(-(t[m] - off) / 0.0052) * (0.75 if k < 3 else 1.0)
    m = t >= 0.027
    env[m] += 0.5 * np.exp(-(t[m] - 0.027) / 0.10)
    x = bp(rng.standard_normal(len(t)), 950, 5200, 2) * env
    return fade_edges(x / np.max(np.abs(x)), a=0.0005) * vel


def hat(vel=1.0, open_=False):
    dur, tau = (0.42, 0.15) if open_ else (0.09, 0.024)
    t = tvec(dur)
    # 808-style metallic base: six detuned square partials + noise
    metal = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (205.3, 304.4, 369.6, 522.7, 540.0, 800.0))
    x = hp(0.35 * metal / 6 + rng.standard_normal(len(t)), 7200, 4) * np.exp(-t / tau)
    return fade_edges(x / np.max(np.abs(x)), a=0.0004) * vel


def shaker(vel=1.0):
    t = tvec(0.07)
    env = np.minimum(1.0, t / 0.004) * np.exp(-t / 0.016)
    x = bp(rng.standard_normal(len(t)), 5200, 11000, 2) * env
    return fade_edges(x / np.max(np.abs(x)), a=0.001) * vel


def bass(midi, dur, vel=1.0):
    t = tvec(dur + 0.06)
    f = hz(midi)
    ph = 2 * np.pi * f * t
    x = 0.8 * np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.18 * np.sin(3 * ph)  # harmonics read on phone speakers
    saw = 2 * ((f * t) % 1.0) - 1
    x += 0.2 * lp(saw, 420, 2)
    env = np.minimum(1.0, t / 0.004) * (0.72 + 0.28 * np.exp(-t / 0.07))
    env *= np.clip((dur + 0.06 - t) / 0.06, 0, 1)
    return np.tanh(1.3 * x * env) * vel


def ep(midi, dur, vel=1.0):
    """FM electric piano: 1:1 carrier/modulator + a short 14:1 tine on the attack."""
    t = tvec(dur + 0.9)
    f = hz(midi)
    index = (1.7 * vel + 0.35) * np.exp(-t / 0.32) + 0.22
    car = np.sin(2 * np.pi * f * t + index * np.sin(2 * np.pi * f * t))
    tine = 0.16 * vel * np.sin(2 * np.pi * 14 * f * t) * np.exp(-t / 0.011)
    amp = np.minimum(1.0, t / 0.003) * np.exp(-t / 1.5)
    amp *= np.clip((dur + 0.9 - t) / 0.9, 0, 1) ** 2 * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.12))
    return (car + tine) * amp * vel


def pad(midis, dur):
    t = tvec(dur + 0.7)
    x = np.zeros_like(t)
    for m in midis:
        for cents in (-8, 0, 8):
            f = hz(m) * 2 ** (cents / 1200)
            ph0 = rng.random()
            x += 2 * ((f * t + ph0) % 1.0) - 1
    x = lp(x / (3 * len(midis)), 1500, 2)
    env = np.minimum(1.0, t / 0.28) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.22))
    return x * env


def pluck(midi, vel=1.0):
    t = tvec(0.6)
    f = hz(midi)
    x = 2 * ((f * t) % 1.0) - 1 + 0.5 * np.sign(np.sin(2 * np.pi * 2 * f * t))
    # cutoff envelope: bright attack, closes fast
    chunks = np.array_split(x, 12)
    y = np.concatenate([lp(c, 900 + 4200 * np.exp(-k / 2.2), 2) for k, c in enumerate(chunks)])
    env = np.minimum(1.0, t / 0.002) * np.exp(-t / 0.13)
    return fade_edges(y * env, r=0.05) * vel


def riser(dur):
    t = tvec(dur)
    u = t / dur
    noise = rng.standard_normal(len(t))
    chunks = np.array_split(noise, 16)
    y = np.concatenate([bp(c, 1800 + 6000 * (k / 15) ** 1.6, 12000, 2) for k, c in enumerate(chunks)])
    return y * u ** 2.6 * 0.9


def impact():
    t = tvec(1.6)
    boom = np.sin(2 * np.pi * (52 + 30 * np.exp(-t / 0.05)) * t) * np.exp(-t / 0.5)
    air = hp(rng.standard_normal(len(t)), 4500, 2) * np.exp(-t / 0.7) * 0.25
    return fade_edges(boom * 0.8 + air, a=0.001, r=0.2)


# ------------------------------------------------------------- arrangement --
# chord per half-bar: (bass midi, EP voicing)
F_MAJ9 = (41, [57, 60, 64, 67])
A_MIN7 = (45, [55, 60, 64, 69])
D_MIN9 = (38, [53, 57, 60, 64])
BB_MAJ9 = (34, [57, 60, 62, 65])
C_SUS = (36, [55, 60, 65])
C_MAJ = (36, [55, 60, 64])

# 8 bars × 2 half-bars
HARMONY = [
    (F_MAJ9, F_MAJ9), (A_MIN7, A_MIN7), (D_MIN9, D_MIN9), (BB_MAJ9, C_MAJ),
    (F_MAJ9, F_MAJ9), (A_MIN7, A_MIN7), (D_MIN9, D_MIN9), (BB_MAJ9, C_SUS),
]

# pluck motif for phrase B (beat offset within bar, midi)
MOTIF = {
    4: [(0.5, 72), (1.0, 69), (1.5, 67), (2.5, 69), (3.0, 72), (3.5, 76)],
    5: [(0.5, 76), (1.0, 72), (1.5, 69), (2.5, 72), (3.0, 76), (3.5, 79)],
    6: [(0.5, 77), (1.0, 76), (1.5, 72), (2.5, 69), (3.0, 72), (3.5, 74)],
    7: [(0.5, 74), (1.0, 72), (1.5, 69), (2.5, 67), (3.0, 72), (3.5, 76)],
}


def arrange(t0, buses, bars=range(LOOP_BARS)):
    """Place the 8-bar groove starting at t0 seconds."""
    d, b, k, pd, pl, fx = (buses[n] for n in ("drums", "bass", "keys", "pad", "pluck", "fx"))
    kicks = []
    for bar in bars:
        tb = t0 + bar * BAR
        phrase_b = bar >= 4
        for beat in range(4):
            tt = tb + beat * BEAT
            d.add(tt, kick(), 0.80)
            kicks.append(tt)
            if beat in (1, 3):
                duck = 0.3 if bar * 4 + beat in CLICK_BACKBEATS else 1.0
                d.add(tt, clap(), (0.42 if not phrase_b else 0.50) * duck, p=0.05)
            off = tt + BEAT / 2
            if phrase_b:
                d.add(off, hat(open_=True), 0.16, p=0.25)
                for s in (0.25, 0.75):
                    d.add(tt + s * BEAT, shaker(), 0.07 + 0.02 * (s == 0.75), p=-0.35)
            else:
                d.add(off, hat(), 0.22, p=0.2)
            if beat in (0, 2):
                d.add(tt + 0.25 * BEAT, hat(0.5), 0.08, p=-0.2)
        # harmony: two halves per bar
        for half, (root, voicing) in enumerate(HARMONY[bar]):
            th = tb + half * 2 * BEAT
            for s in (0.5, 1.5):  # offbeat 8th bass
                b.add(th + s * BEAT, bass(root, 0.36 * BEAT * 2), 0.24)
            hits = [(0.0, 1.35, 0.85), (1.5, 0.4, 0.6)]
            for (st, du, ve) in hits:
                for i, m in enumerate(voicing):
                    k.add(th + st * BEAT, ep(m, du * BEAT, ve + (0.08 if phrase_b else 0.0)),
                          0.075, p=(-0.25 + 0.5 * i / max(1, len(voicing) - 1)))
            if phrase_b:
                pd.add(th, pad([m + 12 for m in voicing[:3]], 2 * BEAT), 0.06)
        if bar in MOTIF:
            for (st, m) in MOTIF[bar]:
                pl.add(tb + st * BEAT, pluck(m, 0.9), 0.15, p=0.15)
    # transitions
    fx.add(t0 + 7.0, riser(1.0), 0.20)                 # loader → success
    fx.add(t0 + 8.0, impact(), 0.30)                   # success downbeat
    roll_t = t0 + 15.5
    for i in range(4):                                 # bar 8, beat 4: clap roll
        d.add(roll_t + i * BEAT / 4, clap(0.45 + 0.15 * i), 0.22, p=0.05)
    fx.add(t0 + 15.0, riser(1.0), 0.12)                # lands on the loop point
    return kicks


# ------------------------------------------------------------------ mixing --
def make_ir(rt60=1.45, pre=0.016):
    t = tvec(rt60 * 1.15)
    dec = np.exp(-6.91 * t / rt60)
    ir = np.stack([lp(rng.standard_normal(len(t)) * dec, 5200, 1),
                   lp(rng.standard_normal(len(t)) * dec, 5200, 1)], axis=1)
    ir = np.concatenate([np.zeros((int(pre * SR), 2)), ir])
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def conv_circular(x, ir):
    """Circular convolution (FFT size = loop length): reverb tails wrap onto bar 1."""
    n = len(x)
    return np.stack([np.fft.irfft(np.fft.rfft(x[:, c], n) * np.fft.rfft(ir[:, c], n), n)
                     for c in range(2)], axis=1)


def delay_circular(x, t_d, fb=0.38, taps=6):
    """Ping-pong delay whose repeats wrap around the loop."""
    y = np.zeros_like(x)
    n_d = int(round(t_d * SR))
    for i in range(1, taps + 1):
        src = x[:, ::-1] if i % 2 else x
        y += fb ** i * np.roll(src, i * n_d, axis=0)
    return y


def duck_env(n, kicks, depth, rel=0.13):
    """Sidechain gain from the kick times, evaluated on the circle."""
    t = np.arange(n) / SR
    loop = n / SR
    g = np.ones(n)
    for tk in kicks:
        for off in (-loop, 0.0, loop):
            dt = t - (tk + off)
            m = (dt >= 0) & (dt < 6 * rel)
            att = np.minimum(1.0, dt[m] / 0.004)
            g[m] = np.minimum(g[m], 1 - depth * att * np.exp(-dt[m] / rel))
    return g[:, None]


def fold(buf, n):
    """Wrap everything past n samples back onto the start (circular loop)."""
    out = buf[:n].copy()
    for i in range(n, len(buf), n):
        seg = buf[i:i + n]
        out[: len(seg)] += seg
    return out


def master(x):
    n = len(x)
    x = hp(np.tile(x, (3, 1)), 28, 2)[n:2 * n]  # filter state wraps too: no seam
    x = x / np.max(np.abs(x)) * 0.95
    x = np.tanh(1.35 * x) / np.tanh(1.35)
    rms = np.sqrt(np.mean(x ** 2))
    return x * min(10 ** (-14.5 / 20) / rms, 0.98 / np.max(np.abs(x)))


def mixdown(buses, kicks, n):
    dry = {k: fold(v.buf, n) for k, v in buses.items()}
    g_soft = duck_env(n, kicks, 0.42)
    g_bass = duck_env(n, kicks, 0.65, rel=0.09)
    keys = dry["keys"] * g_soft
    padb = dry["pad"] * g_soft
    plk = (dry["pluck"] + 0.55 * delay_circular(dry["pluck"], 0.375)) * g_soft
    send = 0.10 * dry["drums"] + 0.28 * keys + 0.45 * padb + 0.35 * plk + 0.5 * dry["fx"]
    wet = conv_circular(send, make_ir())
    mix = dry["drums"] + dry["bass"] * g_bass + keys + padb + plk + dry["fx"] + 0.22 * wet
    return master(mix)


def new_buses(sec):
    return {n: Bus(sec) for n in ("drums", "bass", "keys", "pad", "pluck", "fx")}


def render_loop():
    n = int(round(LOOP_SEC * SR))
    buses = new_buses(LOOP_SEC + 4.0)
    kicks = arrange(0.0, buses)
    return mixdown(buses, kicks, n)


if __name__ == "__main__":
    loop = render_loop()
    sf.write(OUT / "track_loop.wav", loop, SR, subtype="PCM_24")
    print(f"track_loop.wav {len(loop) / SR:.3f}s  peak {np.max(np.abs(loop)):.3f}  "
          f"rms {20 * np.log10(np.sqrt(np.mean(loop ** 2))):.1f} dBFS")
