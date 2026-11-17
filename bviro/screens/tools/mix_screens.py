"""Final sound for the screens reel: cleaned music bed + the voice converted to Bader's voice, at the old voice's level.
usage: python3 -I mix_screens.py BED.wav NEW_VOICE.mp3 ISO_VOICE.mp3 OUT.wav"""
import subprocess, sys
import numpy as np

SR = 48000


def load(path, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).astype(np.float64)


def voiced_rms(x):
    return np.sqrt((x[np.abs(x) > 0.01] ** 2).mean())


bed, new, iso, out = sys.argv[1:5]
b = load(bed, 2); n = load(new, 1)[:, 0]; i = load(iso, 1)[:, 0]
L = min(len(b), len(n)); b = b[:L]; n = n[:L]
VOICE_IN_MIX = 1.107                      # level of the isolated old voice inside the original mix (measured by bed.py)
g = VOICE_IN_MIX * voiced_rms(i) / voiced_rms(n)
n = np.roll(n, 9)                         # same 9-sample alignment the isolated voice needed
mix = b + (g * n)[:, None]
peak = np.abs(mix).max()
print(f"new-voice gain {g:.3f}; mix peak {20*np.log10(peak):.1f} dBFS")
raw = (np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", out], input=raw, check=True)
