"""Rebuild the music bed of the screens reel without the old voice.
The isolated old voice (ElevenLabs voice isolator) is used as a guide: time-align it to the original mix, then remove its
energy from the mix in the STFT domain (over-subtraction with a soft floor, mask smoothed in time and frequency).
usage: python3 -I bed.py ORIG.wav ISO_VOICE.mp3 OUT_BED.wav [alpha=2.0] [floor=0.06]"""
import subprocess, sys
import numpy as np

SR = 48000
N, HOP = 2048, 512


def load(path, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).astype(np.float64)


def stft(x):
    w = np.hanning(N + 1)[:-1]
    pad = np.concatenate([np.zeros(N), x, np.zeros(N)])
    nfr = 1 + (len(pad) - N) // HOP
    idx = np.arange(N)[None, :] + HOP * np.arange(nfr)[:, None]
    return np.fft.rfft(pad[idx] * w, axis=1)


def istft(X, length):
    w = np.hanning(N + 1)[:-1]
    fr = np.fft.irfft(X, n=N, axis=1) * w
    out = np.zeros(N + HOP * (len(X) - 1)); norm = np.zeros_like(out)
    for i in range(len(X)):
        out[i * HOP:i * HOP + N] += fr[i]; norm[i * HOP:i * HOP + N] += w * w
    out /= np.maximum(norm, 1e-8)
    return out[N:N + length]


def smooth2d(m, kt=3, kf=5):
    k = np.ones(kt) / kt
    m = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, m)
    k = np.ones(kf) / kf
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, m)


def main():
    orig, iso, out = sys.argv[1], sys.argv[2], sys.argv[3]
    alpha = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
    floor = float(sys.argv[5]) if len(sys.argv) > 5 else 0.06
    o = load(orig, 2); v = load(iso, 1)[:, 0]
    L = min(len(o), len(v)); o = o[:L]; v = v[:L]
    mid = o.mean(1)
    # fine alignment on a speech-heavy stretch
    a, b = mid[SR * 2:SR * 9], v[SR * 2:SR * 9]
    lags = range(-1500, 1501, 3)
    best = max(lags, key=lambda k: float(np.dot(a[1500:-1500], b[1500 + k:len(b) - 1500 + k])))
    v = np.roll(v, -best)
    print("alignment lag samples", best)
    V = stft(v)
    Pv = np.abs(V) ** 2
    bed = np.zeros_like(o)
    for c in range(2):
        M = stft(o[:, c]); Pm = np.abs(M) ** 2
        strong = Pv > np.percentile(Pv, 97)
        g = float(np.sqrt((Pm[strong] * 1.0).sum() / (Pv[strong].sum() + 1e-12)))     # isolated-voice level inside the mix
        # dilate the voice estimate a little in time and frequency so onsets, tails and sibilance are covered,
        # then a Wiener-style gain with over-subtraction and a low amplitude floor
        Pd = Pv.copy()
        for dt in (-2, -1, 1, 2):
            Pd = np.maximum(Pd, np.roll(Pv, dt, axis=0) * (0.7 if abs(dt) == 1 else 0.4))
        for df in (-2, -1, 1, 2):
            Pd = np.maximum(Pd, np.roll(Pv, df, axis=1) * (0.7 if abs(df) == 1 else 0.4))
        mask = np.sqrt(np.clip(1.0 - alpha * (g * g) * Pd / (Pm + 1e-10), floor * floor, 1.0))
        bed[:, c] = istft(M * mask, L)
        print(f"ch{c} voice gain in mix {g:.3f}")
    raw = (np.clip(bed, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", out], input=raw, check=True)
    step = SR // 2
    def prof(x): return " ".join(f"{20*np.log10(np.sqrt((x[i:i+step]**2).mean())+1e-9):5.1f}" for i in range(0, len(x) - step + 1, step))
    print("orig level per 0.5 s:", prof(o.mean(1)))
    print("bed  level per 0.5 s:", prof(bed.mean(1)))


main()
