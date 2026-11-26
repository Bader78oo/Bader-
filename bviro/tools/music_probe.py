"""Describe a music cue in numbers, for placing it against picture without guessing.

usage: python3 -I music_probe.py FILE [FILE ...]
For each file: length, loudness, a loudness track (one digit per 0.1 s, 9 = the loudest moment, each step 4 dB down),
note onsets with their strength, tempo from the spacing of onsets, the most likely key (Krumhansl profiles on a
chroma of the whole cue), the share of energy under 200 Hz, 200-2000 Hz and above, and whether the cue starts and
ends on sound or on silence. It cannot tell good music from bad: that is for ears.
"""
import subprocess
import sys

import numpy as np
from scipy.signal import find_peaks, stft

SR = 22050
NOTES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def probe(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    dur = len(x) / SR
    hop = SR // 10
    fr = x[: len(x) // hop * hop].reshape(-1, hop)
    e = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    track = "".join(str(int(max(0, min(9, 9 + (v - e.max()) / 4)))) for v in e)
    f, t, Z = stft(x, fs=SR, nperseg=2048, noverlap=2048 - 256)
    mag = np.abs(Z)
    flux = np.maximum(np.diff(np.log1p(40 * mag), axis=1), 0).sum(0)
    flux = flux / (flux.max() + 1e-9)
    step = 256 / SR
    peaks, props = find_peaks(flux, height=0.18, distance=int(0.09 / step))
    onsets = [(round(float(t[p + 1]), 2), round(float(props["peak_heights"][k]), 2)) for k, p in enumerate(peaks)]
    # tempo: autocorrelation of the onset curve between 50 and 160 BPM
    ac = np.correlate(flux - flux.mean(), flux - flux.mean(), "full")[len(flux) - 1:]
    lags = np.arange(len(ac)) * step
    ok = (lags > 60 / 160) & (lags < 60 / 50)
    bpm = 60 / lags[ok][np.argmax(ac[ok])] if ok.any() else 0
    # key: chroma from the spectrum between 65 Hz and 2 kHz
    chroma = np.zeros(12)
    band = (f > 65) & (f < 2000)
    pitch = np.round(12 * np.log2(f[band] / 440.0) + 69).astype(int) % 12
    power = (mag[band] ** 2).sum(1)
    for p, v in zip(pitch, power):
        chroma[p] += v
    chroma /= chroma.sum() + 1e-12
    scores = []
    for k in range(12):
        scores.append((np.corrcoef(np.roll(MAJOR, k), chroma)[0, 1], NOTES[k] + " major"))
        scores.append((np.corrcoef(np.roll(MINOR, k), chroma)[0, 1], NOTES[k] + " minor"))
    scores.sort(reverse=True)
    spec = (mag ** 2).sum(1)
    low, mid, high = spec[f < 200].sum(), spec[(f >= 200) & (f < 2000)].sum(), spec[f >= 2000].sum()
    tot = low + mid + high + 1e-12
    quiet = e.max() - 30
    lead = next((i for i, v in enumerate(e) if v > quiet), 0) / 10
    tail = next((i for i, v in enumerate(e[::-1]) if v > quiet), 0) / 10
    print(f"== {path}")
    print(f"   length {dur:.2f} s | mean level {10 * np.log10((x ** 2).mean() + 1e-12):.1f} dBFS | peak {20 * np.log10(np.abs(x).max() + 1e-9):.1f} dBFS")
    for i in range(0, len(track), 50):
        print(f"   {i / 10:5.1f}s  {track[i:i + 50]}")
    print("   onsets (time, strength):", " ".join(f"{a}({b})" for a, b in onsets))
    print(f"   tempo about {bpm:.0f} BPM | key: {scores[0][1]} ({scores[0][0]:.2f}), then {scores[1][1]} ({scores[1][0]:.2f}), {scores[2][1]} ({scores[2][0]:.2f})")
    print("   strongest pitch classes:", " ".join(f"{NOTES[i]} {chroma[i]:.2f}" for i in np.argsort(-chroma)[:5]))
    print(f"   energy: under 200 Hz {low / tot:.0%}, 200-2000 Hz {mid / tot:.0%}, above {high / tot:.0%}")
    print(f"   silence before the first sound {lead:.1f} s, after the last {tail:.1f} s")


for p in sys.argv[1:]:
    probe(p)
