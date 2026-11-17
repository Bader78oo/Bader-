"""Rough prosody numbers for a voice track: pitch level and range (autocorrelation F0), loudness dynamics, speech rate proxy.
A livelier read shows a higher median pitch, a wider pitch range and bigger level swings. usage: prosody.py file ..."""
import subprocess, sys
import numpy as np
SR = 16000
def load(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
for f in sys.argv[1:]:
    x = load(f); n, hop = 640, 160
    f0, lev = [], []
    peak = np.abs(x).max()
    for i in range(0, len(x) - n, hop):
        fr = x[i:i + n]; e = np.sqrt((fr ** 2).mean())
        if e < peak * 0.03: continue
        fr = fr - fr.mean(); ac = np.correlate(fr, fr, "full")[n - 1:]
        lo, hi = SR // 350, SR // 70
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] / (ac[0] + 1e-12) > 0.45:
            f0.append(SR / k); lev.append(20 * np.log10(e))
    f0 = np.array(f0); st = 12 * np.log2(f0 / np.median(f0))
    voiced_s = len(f0) * hop / SR
    print(f"{f:28s} median F0 {np.median(f0):5.0f} Hz | 10-90% range {np.percentile(st,90)-np.percentile(st,10):4.1f} st | F0 sd {st.std():4.1f} st | level sd {np.std(lev):4.1f} dB | voiced {voiced_s:4.1f} s")
