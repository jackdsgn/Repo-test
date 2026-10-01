#!/usr/bin/env python3
"""UI sounds on measured peaks + final mix.

Reads track_loop.wav and timeline.json (event times already snapped to the
measured peaks by analyze.py — the same times film.html animates on), synthesizes
every UI sound in code, places them on the circle and writes:

  mix_loop.wav   48 kHz / 24-bit, 16.000 s, seamless, −14 LUFS integrated
"""
import json
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy import signal

HERE = Path(__file__).resolve().parent
SR = 48_000
rng = np.random.default_rng(1186)


def tvec(sec):
    return np.arange(int(round(sec * SR))) / SR


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band", output="sos"), x)


def env(t, a, d):
    return np.minimum(1.0, t / a) * np.exp(-t / d)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


# ------------------------------------------------------------- UI sounds --
def click():
    t = tvec(0.09)
    noise = bp(rng.standard_normal(len(t)), 1800, 7000) * env(t, 0.0003, 0.0022)
    tok = np.sin(2 * np.pi * 1650 * t) * env(t, 0.0005, 0.011)
    body = np.sin(2 * np.pi * (210 - 60 * t / 0.09) * t) * env(t, 0.001, 0.018)
    return 0.55 * noise / np.max(np.abs(noise)) + 0.45 * tok + 0.35 * body


def key(i):
    t = tvec(0.06)
    f = 2500 * 2 ** ((rng.random() - 0.5) * 0.25)
    noise = bp(rng.standard_normal(len(t)), 3000, 9000) * env(t, 0.0002, 0.0018)
    tick = np.sin(2 * np.pi * f * t) * env(t, 0.0004, 0.007)
    thock = np.sin(2 * np.pi * 320 * t) * env(t, 0.0008, 0.012)
    return 0.5 * noise / np.max(np.abs(noise)) + 0.35 * tick + 0.25 * thock


def hover():
    t = tvec(0.03)
    return np.sin(2 * np.pi * 3400 * t) * env(t, 0.0004, 0.005)


def tick():
    t = tvec(0.05)
    return np.sin(2 * np.pi * 2200 * t) * env(t, 0.0004, 0.009) + 0.3 * np.sin(2 * np.pi * 4400 * t) * env(t, 0.0003, 0.004)


def pop():
    t = tvec(0.09)
    f = 380 + 420 * (1 - np.exp(-t / 0.02))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(t, 0.002, 0.025)


def select():
    out = np.zeros(int(0.2 * SR))
    for k, m in enumerate((84, 91)):          # C6 → G6 (in key: F major)
        t = tvec(0.12)
        s = np.sin(2 * np.pi * hz(m) * t) * env(t, 0.001, 0.035)
        i = int(k * 0.045 * SR)
        out[i:i + len(s)] += s[: len(out) - i]
    return out


def success():
    """Short F-major chime (A5 · C6 · F6) — sits on the track's key."""
    out = np.zeros(int(1.0 * SR))
    for k, m in enumerate((81, 84, 89)):
        t = tvec(0.9)
        f = hz(m)
        bell = np.sin(2 * np.pi * f * t + 0.9 * np.exp(-t / 0.15) * np.sin(2 * np.pi * 2 * f * t))
        s = bell * env(t, 0.002, 0.32) * (0.9 if k < 2 else 1.0)
        i = int(k * 0.042 * SR)
        out[i:i + len(s)] += s[: len(out) - i]
    return out


def roll():
    """Odometer: six ticks, spacing widening as the wheels slow down."""
    out = np.zeros(int(0.5 * SR))
    tt = 0.0
    for k in range(6):
        s = tick() * (1.0 - 0.1 * k)
        i = int(tt * SR)
        out[i:i + len(s)] += s[: len(out) - i]
        tt += 0.045 + 0.018 * k
    return out


def blip():
    t = tvec(0.12)
    f = 600 * 2 ** (t / 0.12)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(t, 0.003, 0.04)


def fold():
    t = tvec(0.1)
    f = 320 - 140 * (1 - np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(t, 0.002, 0.03)


VOICE = {  # sound → (generator, gain)
    "click": (click, 0.38), "key": (key, 0.20), "hover": (hover, 0.045), "tick": (tick, 0.09),
    "pop": (pop, 0.15), "select": (select, 0.15), "success": (success, 0.16), "roll": (roll, 0.07),
    "blip": (blip, 0.08), "fold": (fold, 0.12),
}


def main():
    music, sr = sf.read(HERE / "track_loop.wav")
    assert sr == SR
    n = len(music)
    tl = json.loads((HERE / "timeline.json").read_text())
    ui = np.zeros(n + SR)
    keys = 0
    for s in tl["sounds"]:
        gen, gain = VOICE[s["type"]]
        x = gen(keys) if s["type"] == "key" else gen()
        keys += s["type"] == "key"
        i = int(round(s["t"] * SR))
        ui[i:i + len(x)] += gain * x
    ui = ui[:n] + np.pad(ui[n:], (0, n - len(ui[n:])))       # wrap tails onto bar 1
    # UI sits slightly right of centre, a touch of width from a 9 ms Haas copy
    ui_st = np.stack([ui * 0.92, np.roll(ui, int(0.009 * SR)) * 0.8], axis=1)
    # music ducks under each UI hit (fast attack, 90 ms release) so a click on a
    # backbeat isn't masked by the clap it lands on
    lvl = np.abs(ui)
    att, rel = np.exp(-1 / (0.002 * SR)), np.exp(-1 / (0.09 * SR))
    e = np.zeros(n)
    acc = 0.0
    for _ in range(2):                                        # second pass: wrap-around state
        for i in range(n):
            x = lvl[i]
            acc = att * acc + (1 - att) * x if x > acc else rel * acc + (1 - rel) * x
            e[i] = acc
    duck = 1 - 0.37 * np.clip(e / 0.05, 0, 1)                  # up to −4 dB
    mix = music * 0.9 * duck[:, None] + ui_st
    meter = pyln.Meter(SR)
    loud = meter.integrated_loudness(np.tile(mix, (2, 1)))
    mix = mix * 10 ** ((-14.0 - loud) / 20)
    peak = np.max(np.abs(mix))
    if peak > 0.89:                                           # keep ≤ −1 dBFS
        mix = np.tanh(mix / peak * 1.2) / np.tanh(1.2) * 0.89
    sf.write(HERE / "mix_loop.wav", mix, SR, subtype="PCM_24")
    print(f"mix_loop.wav {n / SR:.3f}s · {len(tl['sounds'])} UI sounds · "
          f"{meter.integrated_loudness(np.tile(mix, (2, 1))):.1f} LUFS · peak {20 * np.log10(np.max(np.abs(mix))):.1f} dBFS")


if __name__ == "__main__":
    main()
