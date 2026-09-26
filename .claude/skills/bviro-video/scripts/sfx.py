#!/usr/bin/env python3
"""Procedural sound-design track (no samples, no licences): one stereo WAV holding every effect.

Usage: python3 sfx.py sfx.wav --dur 39 --events '[{"t":0.05,"type":"impact"},{"t":15.8,"type":"riser","len":1.4}]'

Types (t = the moment the effect lands):
  impact   deep boom + noise hit           (hook start, open loops, end card)
  riser    noise + rising sweep ENDING at t (len = build-up seconds, default 1.2)
  whoosh   air swell peaking at t           (text flying in)
  ding     soft two-tone UI chime            (checklist / feature cards)
  shimmer  sparkly bell arpeggio             (brand name, reveal)
  pop      short bubbly click                (stickers)
Optional per event: gain (default 1.0).
"""
import argparse, json, wave

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--dur", type=float, required=True); ap.add_argument("--events", required=True)
a = ap.parse_args()
SR = 48000; N = int(a.dur * SR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(3)

def env(n, att, dec):
    x = np.arange(n) / SR
    return np.minimum(x / max(att, 1e-4), 1) * np.exp(-x / dec)

def lp(x, k):  # crude low-pass (moving average)
    return np.convolve(x, np.ones(k) / k, "same")

def place(sig, start, gain, width=0.0):
    i = int(round(start * SR))
    if i < 0: sig, i = sig[-i:], 0
    if i >= N: return
    s = sig[:N - i] * gain
    L[i:i + len(s)] += s * (1 - width); R[i:i + len(s)] += s * (1 + width)

def impact():
    n = int(1.8 * SR); x = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-x * 9)) / SR) * env(n, 0.003, 0.55)
    hit = lp(rng.standard_normal(n), 6) * env(n, 0.001, 0.05) * 0.5
    return (boom + hit) * 0.9

def riser(length):
    n = int(length * SR); x = np.arange(n) / SR; u = x / length
    sweep = np.sin(2 * np.pi * np.cumsum(220 + 1800 * u ** 2) / SR) * 0.18
    noise = rng.standard_normal(n); noise = noise - lp(noise, 40)  # keep the airy top
    return (noise * 0.25 * (0.3 + u) + sweep) * u ** 2.2 * np.minimum(1, (1 - u) * 60 + 0.02)

def whoosh():
    n = int(0.7 * SR); x = np.arange(n) / SR
    w = lp(rng.standard_normal(n), 10) - lp(rng.standard_normal(n), 60)
    shape = np.exp(-((x - 0.45) / 0.14) ** 2)
    return w * shape * 0.5

def ding():
    n = int(0.9 * SR); x = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1318.5 * x) + 0.6 * np.sin(2 * np.pi * 1975.5 * x) * np.exp(-x * 4)
         + 0.25 * np.sin(2 * np.pi * 2637 * x) * np.exp(-x * 9))
    return s * env(n, 0.002, 0.28) * 0.28

def shimmer():
    out = np.zeros(int(1.6 * SR))
    for k, f in enumerate([1568, 1976, 2349, 2637, 3136, 3951]):
        n = int(1.2 * SR); x = np.arange(n) / SR
        tone = np.sin(2 * np.pi * f * x) * env(n, 0.003, 0.35) * (0.14 - k * 0.012)
        i = int(k * 0.055 * SR); out[i:i + n] += tone[:len(out) - i]
    return out

def pop():
    n = int(0.12 * SR); x = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(900 - 5000 * x) / SR) * env(n, 0.001, 0.025) * 0.5

for i, e in enumerate(json.loads(a.events)):
    t, g, typ = e["t"], e.get("gain", 1.0), e["type"]
    pan = 0.25 if i % 2 else -0.25
    if typ == "impact":  place(impact(), t, g)
    elif typ == "riser": ln = e.get("len", 1.2); place(riser(ln), t - ln, g, pan * 0.5)
    elif typ == "whoosh": place(whoosh(), t - 0.45, g, pan)
    elif typ == "ding":  place(ding(), t, g, pan)
    elif typ == "shimmer": place(shimmer(), t, g, pan * 0.5)
    elif typ == "pop":   place(pop(), t, g, pan)
    else: raise SystemExit(f"unknown sfx type {typ}")

mix = np.stack([L, R], 1)
peak = np.abs(mix).max()
if peak > 0.98: mix *= 0.98 / peak
with wave.open(a.out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("sfx ->", a.out, f"{len(json.loads(a.events))} events")
