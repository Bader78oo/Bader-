"""Tell a real Qaf from a «گ» in a recorded line, by ear's own cue: voicing before the burst.

A Qaf is voiceless: the 60 ms before its burst are silent. A g (the way some voices read ق) is voiced: those 60 ms
carry a low hum at the speaker's pitch. Works for a Qaf that starts a phrase, after a pause.

usage: python3 -I check_qaf.py AUDIO BURST_TIME [BURST_TIME ...]
BURST_TIME: roughly when the Qaf is released, in seconds (within 0.1 s); the exact burst is located from it.
Prints for each: the hum level before the burst against the room noise, and how periodic it is.
Reading: under 4 times the noise, or periodicity under 0.4, is a Qaf; 8 times and periodic is a g.
"""
import subprocess
import sys

import numpy as np
from scipy.signal import butter, sosfiltfilt

SR = 16000
path, marks = sys.argv[1], [float(v) for v in sys.argv[2:]]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32).astype(np.float64)
mid = sosfiltfilt(butter(4, [300, 3000], btype="band", fs=SR, output="sos"), x)
e = np.sqrt(np.convolve(mid * mid, np.ones(32) / 32, mode="same"))
frame = int(0.02 * SR)
levels = np.sqrt(np.convolve(x * x, np.ones(frame) / frame, mode="same"))
noise = max(np.percentile(levels, 3), 1e-5)          # the quietest stretch of the recording


def periodicity(seg):
    seg = seg - seg.mean()
    if np.abs(seg).max() < 1e-5:
        return 0.0, 0.0
    ac = np.correlate(seg, seg, "full")[len(seg) - 1:]
    ac /= ac[0] + 1e-12
    lo, hi = int(SR / 260), int(SR / 75)
    k = lo + int(np.argmax(ac[lo:hi]))
    return float(ac[k]), SR / k


print("==", path, "| noise floor %.5f" % noise)
for t in marks:
    i0, i1 = int((t - 0.10) * SR), int((t + 0.10) * SR)
    thr = 0.25 * e[i0:i1].max()
    tb = (i0 + int(np.argmax(e[i0:i1] > thr))) / SR
    seg = x[int((tb - 0.060) * SR):int((tb - 0.005) * SR)]
    rms = float(np.sqrt((seg ** 2).mean()))
    p, f0 = periodicity(seg)
    verdict = "Qaf" if rms < 4 * noise or p < 0.4 else "g" if rms > 8 * noise else "unclear"
    print("  burst %.3f s: hum before it %.1f times the noise, periodicity %.2f at %.0f Hz  ->  %s" % (tb, rms / noise, p, f0, verdict))
