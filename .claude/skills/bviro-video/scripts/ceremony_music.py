#!/usr/bin/env python3
"""Majestic opening/ceremony score (procedural, no samples, no licences): D-major strings, brass swells,
timpani, celesta arpeggios and hall reverb. Sections are placed on the edit's cut points.

Usage: python3 ceremony_music.py out.wav --dur 30 --enter 4.5 --soft 9.5 --march 13.5 --finale 24 [--bpm 84]
  enter   big entrance (timpani hit + brass + full strings), e.g. the ceremony shot
  soft    lighter section (strings + bells)
  march   steady majestic section with timpani on every bar
  finale  final swell + tonic chord that rings out
"""
import argparse, wave
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--dur", type=float, default=30)
ap.add_argument("--enter", type=float, default=4.5); ap.add_argument("--soft", type=float, default=9.5)
ap.add_argument("--march", type=float, default=13.5); ap.add_argument("--finale", type=float, default=24)
ap.add_argument("--bpm", type=float, default=84); ap.add_argument("--seed", type=int, default=4)
a = ap.parse_args()
SR = 44100; N = int(a.dur * SR); rng = np.random.default_rng(a.seed)
L = np.zeros(N); R = np.zeros(N); beat = 60 / a.bpm; bar = 4 * beat
hz = lambda m: 440 * 2 ** ((m - 69) / 12)

def add(sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N: return
    s = sig[:N - i] * g
    L[i:i + len(s)] += s * np.sqrt(0.5 * (1 - pan)); R[i:i + len(s)] += s * np.sqrt(0.5 * (1 + pan))

def strings(f, n, bright=8, vib=0.004):
    x = np.arange(n) / SR; out = np.zeros(n)
    for d in (-0.0035, 0.0, 0.0035):
        ph = 2 * np.pi * f * (1 + d) * (x + vib / (2 * np.pi * 5.3) * np.sin(2 * np.pi * 5.3 * x + rng.random() * 6))
        for k in range(1, bright + 1):
            out += np.sin(k * ph + rng.random()) / k ** 1.35
    return out / 3

def env(n, att, rel):
    x = np.arange(n) / SR; e = np.minimum(x / att, 1)
    return e * np.clip((n / SR - x) / rel, 0, 1)

def brass(f, n):
    x = np.arange(n) / SR; out = np.zeros(n)
    for k in range(1, 7):
        out += np.sin(2 * np.pi * f * k * x * (1 + 0.002 * np.sin(2 * np.pi * 4.8 * x))) / k ** 1.05
    return np.tanh(out * 1.4)

def bell(f, n):
    x = np.arange(n) / SR
    return sum(a_ * np.sin(2 * np.pi * f * r * x) * np.exp(-x / d) for r, a_, d in ((1, 1, 1.2), (2.76, 0.45, 0.5), (5.4, 0.25, 0.25), (8.93, 0.12, 0.12)))

def timp(f=46, n=None, g=1.0):
    n = n or int(1.6 * SR); x = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.25 * np.exp(-x * 18))) / SR) * np.exp(-x / 0.55)
    hit = np.convolve(rng.standard_normal(n), np.ones(30) / 30, "same") * np.exp(-x / 0.03)
    return (body + hit * 0.8) * g

def swell(n):
    x = np.arange(n) / SR; w = rng.standard_normal(n)
    w = w - np.convolve(w, np.ones(12) / 12, "same")
    return w * (x / x[-1]) ** 3 * 0.25

# chords per bar: D, A, Bm, G  (midi triads + bass)
CH = [([62, 66, 69], 38), ([61, 64, 69], 45), ([62, 66, 71], 47), ([62, 67, 71], 43)]
t = 0.0; bi = 0
while t < a.finale:
    tri, bass = CH[bi % 4]; n = int((bar + 0.6) * SR)
    loud = 0.55 if t < a.enter else (1.0 if (a.enter <= t < a.soft or t >= a.march) else 0.7)
    e = env(n, 0.5 if t < a.enter else 0.15, 0.6)
    for m in tri:
        add(strings(hz(m), n) * e, t, 0.05 * loud, (m - 66) / 10)
        add(strings(hz(m + 12), n, bright=5) * e, t, 0.025 * loud, -(m - 66) / 10)
    add(strings(hz(bass), n, bright=10, vib=0.002) * e, t, 0.07 * loud)
    if t >= a.enter and not (a.soft <= t < a.march):
        add(brass(hz(tri[0]), n) * env(n, 0.35, 0.8), t, 0.035, -0.3)
        add(brass(hz(tri[2] - 12), n) * env(n, 0.35, 0.8), t, 0.03, 0.3)
    if t >= a.march:
        add(timp(hz(bass + 12) / 2 * 2), t, 0.35)
        add(timp(hz(bass + 12) / 2 * 2, g=0.5), t + 2 * beat, 0.25)
    t += bar; bi += 1
# celesta arpeggio 8ths from 0.8 s to the finale (lighter in the big sections)
t = 0.8; k = 0
while t < a.finale - 0.2:
    tri, _ = CH[int(t / bar) % 4]; seq = [tri[0] + 12, tri[1] + 12, tri[2] + 12, tri[1] + 24]
    g = 0.05 if (t < a.enter or a.soft <= t < a.march) else 0.03
    add(bell(hz(seq[k % 4]), int(1.5 * SR)), t, g, 0.5 if k % 2 else -0.5); t += beat / 2; k += 1
# entrance: cymbal swell into a timpani + brass hit
sw = int(1.8 * SR); add(swell(sw), a.enter - 1.8, 0.8); add(timp(46, g=1.4), a.enter, 0.6)
add(brass(hz(50), int(2.2 * SR)) * env(int(2.2 * SR), 0.05, 1.2), a.enter, 0.06)
# finale: roll + swell, then the tonic chord ringing out
tt = a.finale - 1.6; gap = 0.12
while tt < a.finale - 0.05:
    add(timp(46, int(0.4 * SR), g=0.3 + 0.7 * (tt - a.finale + 1.6) / 1.6), tt, 0.3); tt += gap; gap = max(0.05, gap * 0.9)
add(swell(sw), a.finale - 1.8, 0.9); add(timp(46, g=1.6), a.finale, 0.7)
n = int((a.dur - a.finale) * SR); e = env(n, 0.05, 2.5)
for m in (50, 57, 62, 66, 69, 74, 78):
    add(strings(hz(m), n) * e, a.finale, 0.05)
add(brass(hz(62), n) * e, a.finale, 0.04, -0.2); add(brass(hz(57), n) * e, a.finale, 0.035, 0.2)
add(bell(hz(86), int(2.5 * SR)), a.finale + 0.05, 0.08); add(bell(hz(90), int(2.5 * SR)), a.finale + 0.35, 0.06)
# hall reverb (stereo exponential-noise IR, FFT convolution)
def reverb(x, seed):
    r = np.random.default_rng(seed); ln = int(2.4 * SR); xi = np.arange(ln) / SR
    ir = r.standard_normal(ln) * np.exp(-xi / 0.55); ir[:int(0.02 * SR)] = 0; ir /= np.sqrt(np.sum(ir ** 2))
    m = 1 << int(np.ceil(np.log2(len(x) + ln)))
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[:len(x)]
Lw, Rw = reverb(L, 1), reverb(R, 2)
mix = np.stack([L * 0.75 + Lw * 0.45, R * 0.75 + Rw * 0.45], 1)
fade = np.clip((a.dur - np.arange(N) / SR) / 1.2, 0, 1)[:, None]
mix = np.tanh(mix * fade * 1.3); mix *= 10 ** (-1 / 20) / (np.abs(mix).max() + 1e-9)
with wave.open(a.out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ceremony music ->", a.out)
