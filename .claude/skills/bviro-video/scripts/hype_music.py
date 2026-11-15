#!/usr/bin/env python3
"""Procedural *bright, energetic* teaser music (major key, no dark braams): an impact at 0.0, a filtered
pumping intro, a full four-on-the-floor drop with offbeat bass, claps, 16th hats and a supersaw-ish
pluck arp, a snare-roll + riser build, a short gap and a final slam with a ringing chord for the
"coming soon" card. Everything is synthesised (no samples, no licences).

Usage: python3 hype_music.py out.wav --dur 22 --drop 3.87 --build 14.5 --slam 16.4 [--bpm 124] [--seed 5]
Chords: D - A - Bm - G (one per bar). Output: 48 kHz stereo WAV, peak -1 dBFS.
"""
import argparse, wave

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--dur", type=float, default=22)
ap.add_argument("--drop", type=float, default=3.87); ap.add_argument("--build", type=float, default=14.5)
ap.add_argument("--slam", type=float, default=16.4); ap.add_argument("--bpm", type=float, default=124)
ap.add_argument("--seed", type=int, default=5)
a = ap.parse_args()
SR = 48000; N = int(a.dur * SR); rng = np.random.default_rng(a.seed)
L = np.zeros(N); R = np.zeros(N); beat = 60 / a.bpm; s16 = beat / 4; bar = beat * 4

def env(n, att, dec):
    x = np.arange(n) / SR
    return np.minimum(x / max(att, 1e-4), 1) * np.exp(-x / dec)
def add(sig, t, g=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= N or i < 0: return
    s = sig[: N - i] * g
    L[i:i + len(s)] += s * (1 - max(pan, 0)); R[i:i + len(s)] += s * (1 + min(pan, 0))
def onepole(x, fc):
    k = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); z = 0.0
    for i in range(len(x)): z = (1 - k) * x[i] + k * z; y[i] = z
    return y
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def saw(f, n, det=(0, 0.11, -0.13, 0.07, -0.05)):
    x = np.arange(n) / SR; out = np.zeros(n)
    for d in det:
        ph = rng.random(); out += 2 * ((x * f * 2 ** (d / 12) + ph) % 1) - 1
    return out / len(det)

def kick(g=1.0):
    n = int(0.32 * SR); x = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(50 + 140 * np.exp(-x * 30)) / SR
    return np.sin(ph) * np.exp(-x * 9) * g + rng.standard_normal(n) * np.exp(-x * 300) * 0.15
def clap():
    n = int(0.22 * SR); x = np.arange(n) / SR; nz = rng.standard_normal(n)
    e = sum(np.exp(-np.clip(x - d, 0, None) * 60) * (x >= d) for d in (0, 0.008, 0.017))
    return np.convolve(nz, [1, -0.9], "same") * e * 0.35
def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR); nz = rng.standard_normal(n)
    return np.diff(np.concatenate([[0], nz])) * env(n, 0.001, 0.06 if open_ else 0.012) * 0.18
def snare():
    n = int(0.15 * SR); x = np.arange(n) / SR
    return (rng.standard_normal(n) * 0.5 + np.sin(2 * np.pi * 190 * x)) * np.exp(-x * 30) * 0.3
def impact(g=1.0):
    n = int(2.2 * SR); x = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-x * 7)) / SR) * np.exp(-x * 2.2)
    return (body + onepole(rng.standard_normal(n), 900) * np.exp(-x * 5) * 0.8) * g
def riser(d):
    n = int(d * SR); x = np.arange(n) / SR
    nz = rng.standard_normal(n); out = np.zeros(n); seg = 2048
    for i in range(0, n, seg):
        fc = 300 + 7000 * (i / n) ** 2; out[i:i + seg] = onepole(nz[i:i + seg], fc)
    sw = np.sin(2 * np.pi * np.cumsum(200 + 1400 * (x / d) ** 2) / SR) * 0.25
    return (out + sw) * (x / d) ** 2 * 0.5

chords = [[62, 66, 69], [57, 61, 64], [59, 62, 66], [55, 59, 62]]  # D A Bm G
roots = [38, 33, 35, 31]
def chord_at(t): return int(t // bar) % 4

# impact at 0.0 (sound at frame 0) + slam
add(impact(1.1), 0.0); add(impact(1.2), a.slam)
# pumping pad everywhere until build, filtered in intro
t = 0.0
while t < a.slam + 3.0:
    c = chord_at(t); n = int(bar * SR)
    pad = sum(saw(hz(m), n) for m in chords[c]) / 3
    fc = 900 if t < a.drop else 3200
    pad = onepole(pad, fc)
    x = np.arange(n) / SR; pump = 1 - 0.75 * np.exp(-((x % beat) / 0.09))
    g = 0.30 if t < a.slam else 0.0
    if t < a.slam or True: add(pad * pump * env(n, 0.02, 99), t, g)
    t += bar
# final ringing chord for the card
n = int((a.dur - a.slam) * SR); x = np.arange(n) / SR
ring = sum(saw(hz(m), n) + 0.5 * np.sin(2 * np.pi * hz(m + 12) * x) for m in [62, 66, 69, 74]) / 4
add(onepole(ring, 2500) * np.exp(-x * 0.5) * np.minimum(x / 0.01, 1), a.slam, 0.32)
# intro: kick on beats from 1st bar half, hats, riser into drop
add(riser(a.drop - 0.2), 0.2, 0.7)
t = 0.0
while t < a.drop - 1e-6:
    add(hat(), t + beat / 2, 0.8); t += beat
add(snare(), a.drop - 2 * s16, 0.8); add(snare(), a.drop - s16, 1.0)
# drop
t = a.drop
while t < a.build - 1e-6:
    k = round((t - a.drop) / beat)
    add(kick(), t, 0.9)
    if k % 2 == 1: add(clap(), t, 1.0, 0.0)
    add(hat(True), t + beat / 2, 0.7, 0.2)
    for j in (1, 3): add(hat(), t + j * s16, 0.6, -0.2)
    # offbeat bass
    c = chord_at(t); nb = int(beat / 2 * SR); xb = np.arange(nb) / SR
    bass = onepole(saw(hz(roots[c]), nb, (0, 0.05)), 600) * env(nb, 0.005, 0.12)
    add(bass + 0.6 * np.sin(2 * np.pi * hz(roots[c]) * xb) * env(nb, 0.005, 0.12), t + beat / 2, 0.55)
    # pluck arp (16ths)
    for j in range(4):
        notes = chords[c] + [chords[c][0] + 12]
        m = notes[(k * 4 + j) % 4] + 12; npk = int(s16 * 1.6 * SR)
        add(onepole(saw(hz(m), npk), 4000) * env(npk, 0.002, 0.09), t + j * s16, 0.16, 0.35 if j % 2 else -0.35)
    t += beat
# build: accelerating snare roll + riser, gap 0.2 s before slam
add(riser(a.slam - a.build - 0.2), a.build, 0.9)
t = a.build; step = beat / 2
while t < a.slam - 0.22:
    add(snare(), t, 0.5 + 0.6 * (t - a.build) / (a.slam - a.build)); add(kick(0.6), t) if step >= beat / 2 else None
    t += step; step = max(step * 0.82, s16 / 2)

mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.6) / 1.6
# small room
for d, g in ((0.031, 0.18), (0.047, 0.14), (0.071, 0.1)):
    k = int(d * SR); mix[k:, 0] += mix[:-k, 1] * g; mix[k:, 1] += mix[:-k, 0] * g
fade = int(0.6 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix *= 10 ** (-1 / 20) / np.abs(mix).max()
with wave.open(a.out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("wrote", a.out)
