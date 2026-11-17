"""List speech segments (non-silent runs) of an audio file. usage: segs.py FILE [thresh_db=-38] [min_gap=0.18]"""
import subprocess, sys
import numpy as np
f = sys.argv[1]; th = float(sys.argv[2]) if len(sys.argv) > 2 else -38.0; gap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.18
sr = 16000
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
a = np.frombuffer(raw, np.float32)
hop = 160
n = len(a) // hop
rms = np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
db = 20 * np.log10(rms / (np.abs(a).max() + 1e-9) + 1e-9)
on = db > th
segs = []; i = 0
while i < n:
    if on[i]:
        j = i
        while j < n and on[j]: j += 1
        segs.append([i * hop / sr, j * hop / sr]); i = j
    else: i += 1
merged = []
for s in segs:
    if merged and s[0] - merged[-1][1] < gap: merged[-1][1] = s[1]
    else: merged.append(s)
merged = [s for s in merged if s[1] - s[0] > 0.06]
print(f, round(len(a) / sr, 2), "s")
for s in merged: print(f"  {s[0]:6.2f} - {s[1]:6.2f}  ({s[1]-s[0]:.2f})")
