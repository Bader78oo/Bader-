"""Acoustic check of the stop in «ناقة»: voiceless /q/ shows a near-silent closure (low AND voicing band collapse);
voiced /g/ keeps a voicing bar (100-400 Hz energy) through the closure.
usage: closure.py file t0 t1 [file t0 t1 ...]  -> per-10ms table of total dB, voicing-band dB, high-band dB"""
import subprocess, sys
import numpy as np
SR = 16000
def load(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)
args = sys.argv[1:]
for k in range(0, len(args), 3):
    f, t0, t1 = args[k], float(args[k + 1]), float(args[k + 2])
    x = load(f)
    n, hop = 400, 160
    freqs = np.fft.rfftfreq(n, 1 / SR)
    rows = []
    for i in range(int(t0 * SR), int(t1 * SR) - n, hop):
        s = np.abs(np.fft.rfft(x[i:i + n] * np.hanning(n))) ** 2
        tot = 10 * np.log10(s.sum() + 1e-12)
        vo = 10 * np.log10(s[(freqs >= 80) & (freqs <= 400)].sum() + 1e-12)
        hi = 10 * np.log10(s[freqs >= 3500].sum() + 1e-12)
        rows.append((i / SR, tot, vo, hi))
    peak = max(r[1] for r in rows)
    print("==", f, f"(peak {peak:.0f} dB; columns: time, total rel dB, voicing-band rel dB, high-band rel dB)")
    line = []
    for t, tot, vo, hi in rows:
        tag = "S" if hi - tot > -6 else ("." if tot - peak < -30 else ("v" if vo - peak > -22 else "x"))
        line.append(f"{t:.2f}:{tot - peak:4.0f}/{vo - peak:4.0f}{tag}")
    for j in range(0, len(line), 8):
        print("  " + "  ".join(line[j:j + 8]))
