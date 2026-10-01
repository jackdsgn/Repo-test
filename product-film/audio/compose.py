#!/usr/bin/env python3
"""FIN JACK · product film — original 120 BPM track, composed in code.

Everything here is synthesized from scratch with numpy/scipy, so the track is
royalty-free by construction.

Output: track.wav — 48 kHz, stereo, 24-bit, 12 bars = 24.000 s, F major.

Form (4-on-the-floor):
  bars 1-3   intro     the Home tour     kick · hats · EP, then bass (bar 2), clap (bar 3)
  bars 4-6   phrase A  "ação"            full groove; bar 6 Bb → C sets up the success
             riser 11.0 → 12.0 s under the loader
  bars 7-11  phrase B  "resultado"       + open hats · shaker · pad · pluck motif;
             success on the bar 7 downbeat (F) with a soft impact
  bar 10     Bbmaj9 lift as the Previsibilidade screen opens
  bar 11     Gm9 → C; beat 4 drops out: the cursor clicks Home in the silence
  bar 12     resolution on Fmaj9 under the logo: impact, sting, ring-out, fade

On backbeats where the cursor clicks, the clap drops to 30 % and the click itself
becomes the backbeat.
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
BARS = 12
FILM_SEC = BARS * BAR      # 24.0 s
END = 11 * BAR             # 22.0 s: the final downbeat (bar 12)
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
G_MIN9 = (43, [58, 62, 65, 69])
C_MAJ = (36, [55, 60, 64])

# bars 1-11 × 2 half-bars; bar 12 is the final chord
HARMONY = [
    (F_MAJ9, F_MAJ9), (A_MIN7, A_MIN7), (D_MIN9, D_MIN9), (BB_MAJ9, C_MAJ),     # Home tour
    (F_MAJ9, F_MAJ9), (BB_MAJ9, C_MAJ),                                          # task → loader
    (F_MAJ9, F_MAJ9), (A_MIN7, A_MIN7), (D_MIN9, D_MIN9),                        # success → chart
    (BB_MAJ9, BB_MAJ9), (G_MIN9, C_MAJ),                                         # forecast → Home
]
INTRO_BARS = 3   # Home tour: no bass in bar 1, no clap before bar 3
PHRASE_B = 6     # bar 7 on: open hats, shaker, pad, pluck

# pluck motif for phrase B (beat offset within bar, midi)
MOTIF = {
    6: [(0.5, 72), (1.0, 69), (1.5, 67), (2.5, 69), (3.0, 72), (3.5, 76)],
    7: [(0.5, 76), (1.0, 72), (1.5, 69), (2.5, 72), (3.0, 76), (3.5, 79)],
    8: [(0.5, 77), (1.0, 76), (1.5, 72), (2.5, 69), (3.0, 72), (3.5, 74)],
    9: [(0.5, 74), (1.0, 72), (1.5, 69), (2.5, 65), (3.0, 69), (3.5, 72)],
    10: [(0.5, 70), (1.0, 74), (1.5, 77), (2.5, 76), (3.0, 79)],
}
DROP = (10, 3)  # bar 11, beat 4: drums, bass and keys rest — the Home click sounds alone


def bell(midi, vel=1.0):
    """FM bell for the closing sting."""
    t = tvec(2.2)
    f = hz(midi)
    x = np.sin(2 * np.pi * f * t + 1.1 * np.exp(-t / 0.25) * np.sin(2 * np.pi * 3.5 * f * t))
    return x * np.minimum(1.0, t / 0.002) * np.exp(-t / 0.7) * vel


def arrange(buses):
    d, b, k, pd, pl, fx = (buses[n] for n in ("drums", "bass", "keys", "pad", "pluck", "fx"))
    kicks = []
    for bar in range(BARS - 1):
        tb = bar * BAR
        phrase_b = bar >= PHRASE_B
        for beat in range(4):
            if (bar, beat) == DROP:
                continue
            tt = tb + beat * BEAT
            d.add(tt, kick(), 0.80)
            kicks.append(tt)
            if beat in (1, 3) and bar >= INTRO_BARS - 1:
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
            for s in (0.5, 1.5):  # offbeat 8th bass (from bar 2)
                if bar >= 1 and (bar, half * 2 + int(s)) != DROP:
                    b.add(th + s * BEAT, bass(root, 0.36 * BEAT * 2), 0.24)
            hits = [(0.0, 1.35, 0.85), (1.5, 0.4, 0.6)]
            for (st, du, ve) in hits:
                if (bar, half * 2 + int(st)) == DROP:
                    continue
                for i, m in enumerate(voicing):
                    k.add(th + st * BEAT, ep(m, du * BEAT, ve + (0.08 if phrase_b else 0.0)),
                          0.075, p=(-0.25 + 0.5 * i / max(1, len(voicing) - 1)))
            if phrase_b:
                pd.add(th, pad([m + 12 for m in voicing[:3]], 2 * BEAT), 0.06)
        if bar in MOTIF:
            for (st, m) in MOTIF[bar]:
                pl.add(tb + st * BEAT, pluck(m, 0.9), 0.15, p=0.15)
    # transitions
    fx.add(11.0, riser(1.0), 0.20)                     # loader → success
    fx.add(12.0, impact(), 0.30)                       # success downbeat
    fx.add(END - 1.0, riser(1.0), 0.30)                # into the reveal
    # bar 10: resolution under the logo
    d.add(END, kick(), 0.85)
    kicks.append(END)
    fx.add(END, impact(), 0.42)
    b.add(END, bass(F_MAJ9[0], 1.6), 0.26)
    for i, m in enumerate(F_MAJ9[1]):
        k.add(END, ep(m, 1.8, 0.95), 0.08, p=-0.25 + 0.5 * i / 3)
    pd.add(END, pad([m + 12 for m in F_MAJ9[1][:3]], 1.6), 0.08)
    for i, m in enumerate((81, 84, 89)):               # sting: A5 · C6 · F6
        fx.add(END + 0.02 + i * 0.07, bell(m), 0.10, p=(-0.2, 0.0, 0.2)[i])
    return kicks


# ------------------------------------------------------------------ mixing --
def make_ir(rt60=1.45, pre=0.016):
    t = tvec(rt60 * 1.15)
    dec = np.exp(-6.91 * t / rt60)
    ir = np.stack([lp(rng.standard_normal(len(t)) * dec, 5200, 1),
                   lp(rng.standard_normal(len(t)) * dec, 5200, 1)], axis=1)
    ir = np.concatenate([np.zeros((int(pre * SR), 2)), ir])
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def conv(x, ir):
    return np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)


def delay(x, t_d, fb=0.38, taps=6):
    """Ping-pong delay."""
    y = np.zeros_like(x)
    n_d = int(round(t_d * SR))
    for i in range(1, taps + 1):
        src = x[:, ::-1] if i % 2 else x
        y[i * n_d:] += fb ** i * src[: len(x) - i * n_d]
    return y


def duck_env(n, kicks, depth, rel=0.13):
    """Sidechain gain from the kick times."""
    t = np.arange(n) / SR
    g = np.ones(n)
    for tk in kicks:
        dt = t - tk
        m = (dt >= 0) & (dt < 6 * rel)
        att = np.minimum(1.0, dt[m] / 0.004)
        g[m] = np.minimum(g[m], 1 - depth * att * np.exp(-dt[m] / rel))
    return g[:, None]


def master(x):
    x = hp(x, 28, 2)
    x = x / np.max(np.abs(x)) * 0.95
    x = np.tanh(1.35 * x) / np.tanh(1.35)
    rms = np.sqrt(np.mean(x[int(6 * SR): int(END * SR)] ** 2))   # level set on the full groove
    x = x * min(10 ** (-14.5 / 20) / rms, 0.98 / np.max(np.abs(x)))
    fade = int(0.7 * SR)                                     # ring-out fades into the last frame
    x[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
    return x


def mixdown(buses, kicks, n):
    dry = {k: v.buf[:n] for k, v in buses.items()}
    g_soft = duck_env(n, kicks, 0.42)
    g_bass = duck_env(n, kicks, 0.65, rel=0.09)
    keys = dry["keys"] * g_soft
    padb = dry["pad"] * g_soft
    plk = (dry["pluck"] + 0.55 * delay(dry["pluck"], 0.375)) * g_soft
    send = 0.10 * dry["drums"] + 0.28 * keys + 0.45 * padb + 0.35 * plk + 0.5 * dry["fx"]
    wet = conv(send, make_ir())
    mix = dry["drums"] + dry["bass"] * g_bass + keys + padb + plk + dry["fx"] + 0.22 * wet
    return master(mix)


def render():
    n = int(round(FILM_SEC * SR))
    buses = {name: Bus(FILM_SEC + 3.0) for name in ("drums", "bass", "keys", "pad", "pluck", "fx")}
    kicks = arrange(buses)
    return mixdown(buses, kicks, n)


if __name__ == "__main__":
    track = render()
    sf.write(OUT / "track.wav", track, SR, subtype="PCM_24")
    print(f"track.wav {len(track) / SR:.3f}s  peak {np.max(np.abs(track)):.3f}  "
          f"rms {20 * np.log10(np.sqrt(np.mean(track[int(6 * SR): int(END * SR)] ** 2))):.1f} dBFS (bars 4-11)")
