#!/usr/bin/env python3
"""Procedural *trailer* music for teasers: heartbeat + ticking intro, a braam on the hook hit, a driving
130 BPM section (pumping sub bass, punchy drums, 16th arps), an accelerating snare build, a short silence
and a final slam. Everything is synthesised (no samples, no licences).

Usage: python3 trailer_music.py out.wav --dur 20 --hit 2.0 --lift 10.2 --build 14.2 --final 16.5 [--bpm 130] [--seed 3]
  hit    the hook impact (intro ends, drive starts)
  lift   lighter half-time section starts (e.g. partner logos)
  build  snare-roll build starts (ends with a 0.2 s gap before --final)
  final  final slam + braam; drums stop, tail rings out
"""
import argparse, wave

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--dur", type=float, default=20)
ap.add_argument("--hit", type=float, default=2.0); ap.add_argument("--lift", type=float, default=10.0)
ap.add_argument("--build", type=float, default=14.0); ap.add_argument("--final", type=float, default=16.5)
ap.add_argument("--bpm", type=float, default=130); ap.add_argument("--seed", type=int, default=3)
a = ap.parse_args()
SR = 48000; N = int(a.dur * SR); rng = np.random.default_rng(a.seed)
L = np.zeros(N); R = np.zeros(N); beat = 60 / a.bpm; s16 = beat / 4

def env(n, att, dec):
    x = np.arange(n) / SR
    return np.minimum(x / max(att, 1e-4), 1) * np.exp(-x / dec)
def lp(x, k): return np.convolve(x, np.ones(k) / k, "same")
def add(sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(sig) <= 0: return
    if i < 0: sig, i = sig[-i:], 0
    s = sig[:N - i] * g
    L[i:i + len(s)] += s * (1 - max(pan, 0)); R[i:i + len(s)] += s * (1 + min(pan, 0))
def saw(f, n, det=0.0):
    x = np.arange(n) / SR
    return sum(2 * ((f * (1 + d) * x) % 1) - 1 for d in (-det, 0, det)) / 3

def kick(g=1.0):
    n = int(0.45 * SR); x = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(45 + 140 * np.exp(-x * 30)) / SR) * env(n, 0.001, 0.25)
    return np.tanh(s * 2.2) * g
def snare():
    n = int(0.3 * SR); x = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 190 * x) * env(n, 0.001, 0.06)
    noise = (rng.standard_normal(n) - lp(rng.standard_normal(n), 6)) * env(n, 0.001, 0.12)
    return (tone * 0.6 + noise * 0.8) * 0.7
def hat(o=False):
    n = int((0.16 if o else 0.04) * SR); w = rng.standard_normal(n); w = w - lp(w, 3)
    return w * env(n, 0.0005, 0.05 if o else 0.012) * 0.3
def heartbeat():
    out = np.zeros(int(0.7 * SR))
    for t0, g in ((0, 1.0), (0.22, 0.7)):
        n = int(0.3 * SR); x = np.arange(n) / SR
        b = np.sin(2 * np.pi * np.cumsum(38 + 50 * np.exp(-x * 25)) / SR) * env(n, 0.003, 0.09) * g
        i = int(t0 * SR); out[i:i + n] += b
    return np.tanh(out * 2.5)
def tick():
    n = int(0.03 * SR); return np.sin(2 * np.pi * 2600 * np.arange(n) / SR) * env(n, 0.0005, 0.006) * 0.35
def braam(f=55.0, length=2.4):
    n = int(length * SR); x = np.arange(n) / SR
    s = saw(f, n, 0.012) + 0.6 * saw(f * 2, n, 0.008) + 0.35 * saw(f * 1.5, n, 0.01)
    s = lp(s, 18) * np.minimum(x / 0.04, 1) * np.exp(-x / (length * 0.45))
    sub = np.sin(2 * np.pi * np.cumsum(f * 0.5 + 30 * np.exp(-x * 6)) / SR) * env(n, 0.002, 0.9)
    return np.tanh((s * 1.6 + sub * 1.2)) * 0.9
def riser(length):
    n = int(length * SR); x = np.arange(n) / SR; u = x / length
    w = rng.standard_normal(n); w = w - lp(w, 30)
    sweep = np.sin(2 * np.pi * np.cumsum(200 + 2400 * u ** 2.5) / SR)
    return (w * 0.35 + sweep * 0.25) * u ** 2.4
def bass_note(f, n):
    x = np.arange(n) / SR
    return np.tanh(lp(saw(f, n, 0.004), 30) * 2.4 + np.sin(2 * np.pi * f * x) * 0.8) * env(n, 0.003, 0.11)

ROOTS = [55.0, 55.0, 43.65, 49.0]   # A A F G — dark, driving
# 1) intro: heartbeat + accelerating ticks + reverse swell into the hit
for t in np.arange(0.0, a.hit - 0.3, 0.75): add(heartbeat(), t, 0.9)
t, gap = 0.1, 0.25
while t < a.hit - 0.05:
    add(tick(), t, 1.0, 0.3); t += gap; gap = max(0.06, gap * 0.82)
add(riser(min(1.6, a.hit)), a.hit - min(1.6, a.hit), 0.9)
# 2) hit
add(braam(55, 2.6), a.hit, 1.0); add(kick(1.4), a.hit, 1.0)
# 3) drive + lift: drums, pumping bass, arps
t = a.hit; k = 0
while t < a.build:
    lift = t >= a.lift; pos = k % 16
    root = ROOTS[int((t - a.hit) / (beat * 4)) % 4]
    duck = 1.0
    if pos % 4 == 0 and (not lift or pos == 0):
        add(kick(), t); duck = 0.35
    if pos in (4, 12) and not lift: add(snare(), t, 0.9)
    if lift and pos == 8: add(snare(), t, 0.7)
    add(hat(o=(pos % 4 == 2)), t, 0.7 if not lift else 0.45, 0.25)
    add(bass_note(root * (2 if pos % 2 else 1), int(s16 * SR * 0.95)), t, 0.32 * (0.6 if pos % 4 == 0 else 1.0))
    if pos % 2 == 0:  # 8th-note arp, an octave and a fifth up
        f = root * 4 * (1, 1.5, 2, 1.5)[(pos // 2) % 4]
        n = int(s16 * 2 * SR); add(np.sin(2 * np.pi * f * np.arange(n) / SR) * env(n, 0.002, 0.08), t, 0.09 if not lift else 0.13, -0.3 if pos % 4 else 0.3)
    t += s16; k += 1
# 4) build: accelerating snare roll + riser, then a 0.2 s gap
t, step = a.build, beat / 2
while t < a.final - 0.25:
    add(snare(), t, 0.4 + 0.6 * (t - a.build) / max(a.final - a.build, 0.1)); step = max(s16 / 2, step * 0.88); t += step
add(riser(a.final - 0.2 - a.build), a.build, 1.0)
# 5) final slam + braam, then a second hit a beat later
add(braam(41.2, 3.2), a.final, 1.1); add(kick(1.6), a.final, 1.0)
add(braam(49.0, 2.4), a.final + 1.1, 0.8); add(kick(1.3), a.final + 1.1, 1.0)

mix = np.stack([L, R], 1)
fade = np.clip((a.dur - np.arange(N) / SR) / 0.6, 0, 1)[:, None]; mix *= fade
mix = np.tanh(mix * 1.1); mix *= 10 ** (-1 / 20) / (np.abs(mix).max() + 1e-9)
with wave.open(a.out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("trailer music ->", a.out)
