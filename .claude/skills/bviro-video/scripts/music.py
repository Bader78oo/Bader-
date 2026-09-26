#!/usr/bin/env python3
"""Procedural tech-promo music bed that follows the reel's sections (no samples, no licences).

Usage: python3 music.py out.wav --dur 40 --bpm 100 --sections 0,3,10,20,30,36 [--seed 7]

Sections: intro hit at 0, then each boundary gets a riser into a downbeat hit; the energy
(drums/bass density) builds section by section and drops to pad + hit at the last one (CTA).
Chords: Am - F - C - G (one per bar). Output: 48 kHz stereo WAV, peak-normalised to -3 dBFS.
"""
import argparse, wave

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--dur", type=float, default=40); ap.add_argument("--bpm", type=float, default=100)
ap.add_argument("--sections", default="0,3,10,20,30,36"); ap.add_argument("--seed", type=int, default=7)
a = ap.parse_args()
SR = 48000; N = int(a.dur * SR); t = np.arange(N) / SR
rng = np.random.default_rng(a.seed)
beat = 60 / a.bpm; bar = beat * 4
secs = [float(x) for x in a.sections.split(",")]
L = np.zeros(N); R = np.zeros(N)

def env(n, attack, decay):
    x = np.arange(n) / SR
    return np.minimum(x / max(attack, 1e-4), 1) * np.exp(-x / decay)

def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N: return
    s = sig[: N - i] * gain
    L[i:i + len(s)] += s * (1 - max(pan, 0)); R[i:i + len(s)] += s * (1 + min(pan, 0))

def section_of(time):
    return max(k for k, s in enumerate(secs) if time >= s - 1e-6)

# instruments
def kick():
    n = int(0.35 * SR); x = np.arange(n) / SR
    f = 110 * np.exp(-x * 18) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.18)
def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    w = rng.standard_normal(n); w = np.diff(np.concatenate([[0], w]))  # crude high-pass
    return w * env(n, 0.001, 0.06 if open_ else 0.015) * 0.35
def clap():
    n = int(0.25 * SR); w = rng.standard_normal(n)
    e = sum(env(n, 0.001, 0.02) * (np.arange(n) >= int(d * SR)) for d in (0, 0.012, 0.024)) + env(n, 0.001, 0.12) * 0.5
    return np.convolve(w, np.ones(8) / 8, "same") * e * 0.5
def tone(freq, dur, wave_="saw", a_=0.01, d_=0.4):
    n = int(dur * SR); x = np.arange(n) / SR
    ph = 2 * np.pi * freq * x
    s = {"sin": np.sin(ph), "saw": 2 * ((freq * x) % 1) - 1, "sq": np.sign(np.sin(ph))}[wave_]
    return s * env(n, a_, d_)
def riser(dur):
    n = int(dur * SR); x = np.arange(n) / SR
    w = rng.standard_normal(n); w = np.convolve(w, np.ones(4) / 4, "same")
    sweep = np.sin(2 * np.pi * np.cumsum(300 + 2500 * (x / dur) ** 2) / SR)
    return (w * 0.4 + sweep * 0.2) * (x / dur) ** 2
def impact():
    n = int(2.0 * SR); x = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(60 * np.exp(-x * 3) + 30) / SR) * env(n, 0.002, 0.7)
    return boom + rng.standard_normal(n) * env(n, 0.001, 0.08) * 0.4

CHORDS = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]  # Am F C G (MIDI)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)

# pads: soft detuned saws per bar, always on (quieter in section 0)
b = 0
while b * bar < a.dur:
    st = b * bar; ch = CHORDS[b % 4]
    for m in ch:
        for det in (-0.12, 0.12):
            add(np.convolve(tone(hz(m + 12) * (1 + det / 100), bar + 0.3, "saw", 0.4, 1.8), np.ones(24) / 24, "same"),
                st, 0.035 if section_of(st) else 0.02, pan=det * 4)
    b += 1

# rhythm by section energy
last = len(secs) - 1
k = 0
while k * beat < a.dur:
    st = k * beat; s = section_of(st); pos = k % 4
    energy = 0 if s == 0 else (1 if s == 1 else (3 if s == last else 2))
    if s == last and st > secs[last] + 0.5:
        energy = 0
    if energy >= 1 and pos in (0, 2): add(kick(), st, 0.9)
    if energy >= 2 and pos in (1, 3): add(clap(), st, 0.55)
    if energy >= 1:
        for h in (0, 0.5): add(hat(open_=(h == 0.5 and energy >= 2)), st + h * beat, 0.5, pan=0.3)
    if energy >= 1:  # bass: root of the current chord, 8ths
        root = CHORDS[int(st // bar) % 4][0] - 24
        for h in (0, 0.5):
            add(np.convolve(tone(hz(root), beat * 0.45, "sq", 0.005, 0.12), np.ones(40) / 40, "same"), st + h * beat, 0.16)
    k += 1

# arpeggio sparkle in the body sections
k = 0
while k * beat / 2 < a.dur:
    st = k * beat / 2; s = section_of(st)
    if 2 <= s < last:
        ch = CHORDS[int(st // bar) % 4]
        add(tone(hz(ch[k % 3] + 24), 0.22, "sin", 0.003, 0.12), st, 0.08, pan=0.4 if k % 2 else -0.4)
    k += 1

# transitions: riser into each boundary + impact on it
for s in secs:
    if s > 0.5: add(riser(min(1.5, s - 0.2)), s - min(1.5, s - 0.2), 0.35)
    add(impact(), s, 0.8)

mix = np.stack([L, R], 1)
fade = np.minimum(1, (a.dur - t) / 1.2)[:, None]; mix *= np.clip(fade, 0, 1)
mix = np.tanh(mix * 1.2)                                      # gentle glue / soft clip
mix *= 10 ** (-3 / 20) / (np.abs(mix).max() + 1e-9)
with wave.open(a.out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print(a.out, f"{a.dur}s @ {a.bpm} BPM, sections {secs}")
