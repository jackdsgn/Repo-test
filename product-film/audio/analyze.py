#!/usr/bin/env python3
"""Measure the beat grid and transient peaks of track.wav with librosa.

Outputs

beats.json
  duration     length of the film in seconds (from the audio)
  bpm          60 / mean measured beat interval
  beats        48 beat times (s); beat 0 = bar 1 downbeat ≈ t 0
  measured     which of those beats have their own transient (bar 11 beat 4 is a
               deliberate drop-out and bar 12 rings out, so those come from the fit)
  peaks        onset-strength peaks (s) — UI sounds snap to these
  downbeat_check  chroma-novelty score per bar phase (chords change on beat 1)

timeline.json  (read by film.html and mix.py)
  every row of events.json placed on the measured grid and snapped to the
  nearest measured peak within ±35 ms
"""
import json
from pathlib import Path

import librosa
import numpy as np

HERE = Path(__file__).resolve().parent
N_BEATS = 48
y, sr = librosa.load(HERE / "track.wav", sr=None, mono=True)
duration = len(y) / sr
hop = 128

onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop, aggregate=np.median)
# Tempo and phase come from the intro and phrase A (bars 1-6 + the success
# downbeat), where the kick is the strongest onset. In phrase B the open hats and
# offbeat bass are louder than the kick and the tracker slips half a beat; the
# drop-out and the ring-out have no pulse at all. Every grid beat is then snapped
# to its own measured transient below.
groove = int(12.6 * sr / hop)
tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env[:groove], sr=sr, hop_length=hop,
                                             start_bpm=120, tightness=400, trim=False, units="frames")
beat_t = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)
peak_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop,
                                         backtrack=False, units="frames")
peak_t = librosa.frames_to_time(peak_frames, sr=sr, hop_length=hop)


def snap(t, window):
    near = peak_t[np.abs(peak_t - t) <= window]
    if not len(near):
        return None
    strengths = onset_env[librosa.time_to_frames(near, sr=sr, hop_length=hop)]
    return float(near[np.argmax(strengths)])


refined = np.array([snap(b, 0.040) or b for b in beat_t])

# Grid: a straight line t = a + b·n through the tracked beats, refitted on inliers.
idx = np.round((refined - refined[0]) / 0.5).astype(int)
b_fit, a_fit = np.polyfit(idx, refined, 1)
for _ in range(3):
    n_all = np.round((refined - a_fit) / b_fit).astype(int)
    inl = np.abs(refined - (a_fit + b_fit * n_all)) < 0.04
    b_fit, a_fit = np.polyfit(n_all[inl], refined[inl], 1)
# every grid beat across the whole film, measured from its own transient
refined = np.array([snap(a_fit + b_fit * n, 0.04) or np.nan for n in range(N_BEATS + 4)])
refined = refined[np.isfinite(refined)]
k0 = int(np.ceil((-0.06 - a_fit) / b_fit))      # first grid index at t ≥ −60 ms (the downbeat at 0)
beats, measured = [], []
for n in range(k0, k0 + N_BEATS + 4):
    t_fit = a_fit + b_fit * n
    hit = refined[np.abs(refined - t_fit) <= 0.04]
    beats.append(max(0.0, float(hit[0]) if len(hit) else t_fit))
    measured.append(bool(len(hit)))
beats, measured = np.array(beats), np.array(measured)

# bar phase: chords change on beat 1, so beat-synchronous chroma changes most there
# (explicit per-beat medians: librosa.util.sync drops its pad column when the
# first edge is frame 0, which would shift every index by one)
chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
edges = librosa.time_to_frames(beats[:45], sr=sr, hop_length=512)
per_beat = np.stack([np.median(chroma[:, a:b], axis=1) for a, b in zip(edges[:-1], edges[1:])], axis=1)
per_beat /= np.linalg.norm(per_beat, axis=0, keepdims=True) + 1e-9
novelty = np.r_[0.0, np.linalg.norm(np.diff(per_beat, axis=1), axis=0)]   # novelty[k]: change into beat k
phase_score = [float(np.mean(novelty[p:44:4][novelty[p:44:4] > 0] if p == 0 else novelty[p:44:4])) for p in range(4)]
phase = int(np.argmax(phase_score))
beats, measured = beats[phase: phase + N_BEATS], measured[phase: phase + N_BEATS]
if phase != 0 or beats[0] > 0.05:
    raise SystemExit(f"track must start on a downbeat; got phase {phase}, first beat {beats[0]:.3f}s")

peaks = np.sort(peak_t)
out = {
    "source": "audio/track.wav",
    "duration": round(duration, 6),
    "bpm": round(60.0 / b_fit, 3),
    "bpm_librosa_estimate": round(float(np.atleast_1d(tempo)[0]), 3),
    "downbeat_offset": round(float(beats[0]), 6),
    "beats": [round(float(b), 6) for b in beats],
    "measured": [bool(m) for m in measured],
    "downbeats": [round(float(b), 6) for b in beats[::4]],
    "peaks": [round(float(p), 6) for p in peaks],
    "downbeat_check": {"phase_scores": [round(s, 3) for s in phase_score], "chosen_phase": phase},
}
(HERE / "beats.json").write_text(json.dumps(out, indent=1))

dev = beats - (beats[0] + 0.5 * np.arange(N_BEATS))
print(f"duration {duration:.3f}s · bpm {out['bpm']} · downbeat {beats[0] * 1000:.1f} ms · "
      f"{int(measured.sum())}/{N_BEATS} beats measured")
print(f"deviation from a 0.5 s grid: max {np.max(np.abs(dev)) * 1000:.1f} ms, mean {np.mean(np.abs(dev)) * 1000:.1f} ms")
print(f"phase scores {out['downbeat_check']['phase_scores']} → phase {phase} · {len(peaks)} peaks")


# ---------------------------------------------------------------- timeline --
def grid_time(beat):
    i = int(np.floor(beat))
    return float(beats[i] + (beat - i) * (beats[i + 1] - beats[i]))


events, sounds = {}, []
for ev in json.loads((HERE / "events.json").read_text())["events"]:
    t = grid_time(ev["beat"])
    t = snap(t, 0.035) or t
    events[ev["id"]] = round(t, 6)
    if ev["sound"]:
        sounds.append({"t": events[ev["id"]], "type": ev["sound"], "id": ev["id"]})

timeline = {"duration": out["duration"], "bpm": out["bpm"], "beats": out["beats"],
            "events": events, "sounds": sounds}
(HERE / "timeline.json").write_text(json.dumps(timeline, indent=1))
print(f"timeline: {len(events)} events, {len(sounds)} UI sounds")
