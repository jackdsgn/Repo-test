#!/usr/bin/env python3
"""Measure the beat grid and transient peaks of track_loop.wav with librosa.

The loop is tiled 3× before analysis so the tracker sees steady context at both
edges; the middle copy is the measurement. Outputs:

beats.json

  period      loop length in seconds (measured from the audio, not assumed)
  bpm         tempo measured by librosa
  beats       32 beat times (s), beat 0 = bar 1 downbeat = t 0
  downbeats   8 bar starts
  peaks       onset-strength peaks (s) — UI sounds snap to these
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
y, sr = librosa.load(HERE / "track_loop.wav", sr=None, mono=True)
period = len(y) / sr
tiled = np.tile(y, 3)
hop = 128

onset_env = librosa.onset.onset_strength(y=tiled, sr=sr, hop_length=hop, aggregate=np.median)
tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop,
                                             start_bpm=120, tightness=400, units="frames")
beat_t = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)

# transient peaks (time of the onset-strength maximum, not backtracked)
peak_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop,
                                         backtrack=False, units="frames")
peak_t = librosa.frames_to_time(peak_frames, sr=sr, hop_length=hop)

# refine every tracked beat to the strongest transient within ±40 ms
refined = []
for bt in beat_t:
    near = peak_t[np.abs(peak_t - bt) <= 0.040]
    if len(near):
        strengths = onset_env[librosa.time_to_frames(near, sr=sr, hop_length=hop)]
        refined.append(float(near[np.argmax(strengths)]))
    else:
        refined.append(float(bt))
refined = np.array(refined)

# middle copy only, wrapped to [0, period)
mid = refined[(refined >= period - 0.25) & (refined < 2 * period - 0.25)] - period
mid = np.sort(np.mod(mid, period))
if len(mid) != 32:
    raise SystemExit(f"expected 32 beats, measured {len(mid)}: {mid}")

# bar phase: chords change on beat 1 of every bar, so the beat-synchronous
# chroma changes most at downbeats (claps on 2 & 4 would fool an energy test).
chroma = librosa.feature.chroma_cqt(y=tiled, sr=sr, hop_length=512)
edges = librosa.time_to_frames(np.concatenate([mid, mid + period, mid + 2 * period]), sr=sr, hop_length=512)
sync = librosa.util.sync(chroma, edges, aggregate=np.median)
sync = librosa.util.normalize(sync, norm=2, axis=0)
# sync pads a segment before the first edge, so column k+1 is beat k and
# novelty[k] (column k → k+1) is the change into beat k.
novelty = np.linalg.norm(np.diff(sync, axis=1), axis=0)
nov_mid = novelty[32:64]                                           # middle copy, beat 0..31
phase_score = [float(np.mean(nov_mid[p::4])) for p in range(4)]
phase = int(np.argmax(phase_score))
beats = np.roll(mid, -phase)
beats = np.mod(beats - beats[0], period) + beats[0]
offset = float(beats[0])  # measured downbeat time (≈ kick transient latency)

peaks_mid = peak_t[(peak_t >= period) & (peak_t < 2 * period)] - period

out = {
    "source": "audio/track_loop.wav",
    "period": round(period, 6),
    "bpm": round(60.0 / float(np.mean(np.diff(beats))), 3),
    "bpm_librosa_estimate": round(float(np.atleast_1d(tempo)[0]), 3),
    "downbeat_offset": round(offset, 6),
    "beats": [round(float(b), 6) for b in beats],
    "downbeats": [round(float(b), 6) for b in beats[::4]],
    "peaks": [round(float(p), 6) for p in np.sort(peaks_mid)],
    "downbeat_check": {"phase_scores": [round(s, 3) for s in phase_score], "chosen_phase": phase},
}
(HERE / "beats.json").write_text(json.dumps(out, indent=1))

nominal = np.arange(32) * 0.5
dev = (beats - beats[0]) - nominal
print(f"period {period:.4f}s · bpm {out['bpm']} · downbeat offset {offset * 1000:.1f} ms")
print(f"beat deviation from 0.5 s grid: max {np.max(np.abs(dev)) * 1000:.1f} ms, mean {np.mean(np.abs(dev)) * 1000:.1f} ms")
print(f"phase scores {out['downbeat_check']['phase_scores']} → phase {phase}")
print(f"{len(out['peaks'])} peaks")


# ---------------------------------------------------------------- timeline --
def grid_time(beat):
    """Measured time of a (possibly fractional) beat index, on the circle."""
    ext = np.append(beats, beats[0] + period)
    i = int(np.floor(beat)) % 32
    f = beat - np.floor(beat)
    return float(ext[i] + f * (ext[i + 1] - ext[i]))


peaks_arr = np.array(out["peaks"])
events, sounds = {}, []
for ev in json.loads((HERE / "events.json").read_text())["events"]:
    t = grid_time(ev["beat"])
    d = (peaks_arr - t + period / 2) % period - period / 2   # circular distance
    j = int(np.argmin(np.abs(d)))
    if abs(d[j]) <= 0.035:
        t = float(peaks_arr[j])
    events[ev["id"]] = round(t % period, 6)
    if ev["sound"]:
        sounds.append({"t": events[ev["id"]], "type": ev["sound"], "id": ev["id"]})

timeline = {"period": out["period"], "bpm": out["bpm"], "beats": out["beats"],
            "events": events, "sounds": sounds}
(HERE / "timeline.json").write_text(json.dumps(timeline, indent=1))
print(f"timeline: {len(events)} events, {len(sounds)} UI sounds")

