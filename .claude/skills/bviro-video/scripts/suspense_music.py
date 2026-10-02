#!/usr/bin/env python3
"""Calm suspense bed for teasers: a slow evolving minor pad, sub drone, soft pulse and sparse piano-like
notes; a gentle swell into a soft cinematic boom at --reveal, then a warm resolving chord. No samples.

Usage: python3 suspense_music.py out.wav --dur 35 --reveal 27.3 [--pulse 10] [--seed 5]
  pulse   time the soft low pulse (heartbeat-tempo) starts, adding tension
"""
import argparse, wave
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--dur", type=float, default=35)
ap.add_argument("--reveal", type=float, default=27.3); ap.add_argument("--pulse", type=float, default=10)
ap.add_argument("--seed", type=int, default=5)
a = ap.parse_args()
SR = 48000; N = int(a.dur * SR); t = np.arange(N) / SR; rng = np.random.default_rng(a.seed)
L = np.zeros(N); R = np.zeros(N)

def lp(x, k): return np.convolve(x, np.ones(k) / k, "same")
def add(sig, t0, g=1.0, pan=0.0):
    i = int(t0 * SR); s = sig[:max(0, N - i)] * g
    L[i:i + len(s)] += s * (1 - max(pan, 0)); R[i:i + len(s)] += s * (1 + min(pan, 0))
def env(n, att, dec):
    x = np.arange(n) / SR; return np.minimum(x / max(att, 1e-4), 1) * np.exp(-x / dec)

# 1) pad: A minor add9 -> F maj7 -> D minor -> E sus, detuned sines + soft 3rd harmonic, slow fades
chords = [[110, 130.81, 164.81, 246.94], [87.31, 130.81, 174.61, 220], [73.42, 146.83, 174.61, 220], [82.41, 123.47, 164.81, 220]]
seg = a.reveal / 4
for ci, ch in enumerate(chords):
    s0, n = ci * seg, int((seg + 2.5) * SR)
    x = np.arange(n) / SR; e = np.minimum(x / 2.2, 1) * np.minimum(np.maximum((seg + 2.5 - x) / 2.5, 0), 1)
    for k, f in enumerate(ch):
        for d, p in ((-0.003, -0.5), (0.003, 0.5)):
            w = np.sin(2 * np.pi * f * (1 + d) * x + k) + 0.18 * np.sin(2 * np.pi * 3 * f * (1 + d) * x)
            add(w * e * (1 + 0.15 * np.sin(2 * np.pi * 0.2 * x + k)), s0, 0.05, p)
# 2) sub drone on A, swelling toward the reveal
drone = np.sin(2 * np.pi * 55 * t) * np.clip(t / 4, 0, 1) * (0.5 + 0.5 * np.clip(t / a.reveal, 0, 1)) * (t < a.reveal)
add(drone, 0, 0.12)
# 3) airy noise bed (filtered), very low
air = lp(rng.standard_normal(N), 40) - lp(rng.standard_normal(N), 400)
add(air * np.clip(t / 6, 0, 1), 0, 0.05)
# 4) sparse piano-like notes (A minor pentatonic, high), with a soft echo
notes = [880, 659.25, 783.99, 587.33, 880, 1046.5, 987.77, 659.25]
tt = 1.2
for i, f in enumerate(notes * 4):
    if tt > a.reveal - 1.5: break
    n = int(2.5 * SR); x = np.arange(n) / SR
    p = (np.sin(2 * np.pi * f * x) + 0.35 * np.sin(4 * np.pi * f * x) + 0.12 * np.sin(6 * np.pi * f * x)) * env(n, 0.004, 0.55)
    pan = 0.4 if i % 2 else -0.4
    add(p, tt, 0.06, pan); add(p, tt + 0.38, 0.025, -pan)
    tt += 2.1 if tt < a.pulse else 1.4
# 5) soft low pulse (two beats like a heartbeat, but muffled) from --pulse to the reveal, getting faster
tt, gap = a.pulse, 1.3
while tt < a.reveal - 0.6:
    for o, g in ((0, 1.0), (0.24, 0.6)):
        n = int(0.35 * SR); x = np.arange(n) / SR
        b = np.sin(2 * np.pi * np.cumsum(42 + 30 * np.exp(-x * 20)) / SR) * env(n, 0.005, 0.12)
        add(b, tt + o, 0.35 * g * (0.6 + 0.4 * (tt - a.pulse) / max(a.reveal - a.pulse, 1)))
    tt += gap; gap = max(0.75, gap * 0.95)
# 6) reverse swell into the reveal, then a soft boom + warm resolving chord (A major add9)
sw = int(2.2 * SR); x = np.arange(sw) / SR
swell = (lp(rng.standard_normal(sw), 8) * 0.5 + np.sin(2 * np.pi * (220 + 220 * (x / 2.2) ** 2) * x) * 0.3) * (x / 2.2) ** 3
add(swell, a.reveal - 2.2, 0.35)
n = int(4 * SR); x = np.arange(n) / SR
boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-x * 8)) / SR) * env(n, 0.003, 0.9) + lp(rng.standard_normal(n), 30) * env(n, 0.002, 0.25) * 0.6
add(np.tanh(boom * 1.5), a.reveal, 0.7)
rest = a.dur - a.reveal; n = int(rest * SR); x = np.arange(n) / SR
e = np.minimum(x / 0.8, 1) * np.clip((rest - x) / 2.0, 0, 1)
for k, f in enumerate([110, 138.59, 164.81, 246.94, 329.63]):
    for d, p in ((-0.003, -0.5), (0.003, 0.5)):
        add((np.sin(2 * np.pi * f * (1 + d) * x + k) + 0.15 * np.sin(6 * np.pi * f * x)) * e, a.reveal + 0.1, 0.045, p)
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.2); mix *= 10 ** (-1 / 20) / (np.abs(mix).max() + 1e-9)
with wave.open(a.out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("suspense music ->", a.out)
