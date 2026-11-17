"""Lay an enthusiastic TTS take onto the caption timing of the screens reel.
Each spoken phrase of the take is cut out, slowed a little where the original read was slower (never below TEMPO_MIN,
pitch preserved with ffmpeg atempo) and placed at the moment the same phrase starts in the original voice, so the
word-by-word captions burned into the video still follow the speech. Long phrases are split at a natural dip between
words when one exists, so the second half lands on its own caption.
usage: python3 -I fit_voice.py TAKE.mp3 OUT_VOICE.wav"""
import subprocess, sys
import numpy as np

SR = 48000
TEMPO_MIN = 0.88
TEMPO_MIN_FOR = {"يديرها نظام واحد!": 0.80}      # the original read of this line was much slower; keep its captions close
DUR = 27.97

# (phrase, take-A window, [original onsets of the sub-phrases], [whisper word boundary inside the take for a possible split])
PHRASES = [
    ("شايفين هالفتحة في الجدار؟", (0.03, 1.49), [0.00], []),
    ("هنا…", (2.07, 2.53), [1.96], []),
    ("بتتركّب شاشة ذكية!", (2.73, 4.23), [2.54, 3.22], [3.28]),
    ("نقيس بدقّة", (4.68, 5.63), [4.80], []),
    ("نجهّز الجدار", (6.12, 7.16), [5.98], []),
    ("ونمدّ التمديدات", (7.50, 8.61), [7.48], []),
    ("شاشة ورا شاشة!", (9.09, 10.47), [9.39, 10.06], [9.66]),
    ("والأقوى؟", (10.85, 11.45), [11.37], []),
    ("كل الشاشات…", (11.84, 12.71), [12.15], []),
    ("يديرها نظام واحد!", (12.92, 14.30), [13.41, 14.20], [13.40]),
    ("أول نظام مبتكر في السلطنة…", (14.82, 16.66), [15.81, 17.40], [15.92]),
    ("لإدارة المحتوى!", (16.93, 18.02), [18.61], []),
    ("ترقّبوا…", (18.51, 19.07), [20.36], []),
    ("قريبًا من بيفيرو!", (19.37, 20.54), [21.22], []),
]
ORIG_END = [1.76, 2.35, 4.62, 5.78, 7.34, 9.21, 11.17, 11.95, 13.20, 15.60, 18.42, 20.16, 21.04, 22.97]


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def stretch(x, tempo):
    if abs(tempo - 1) < 0.01:
        return x
    raw = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", f"atempo={tempo:.4f}", "-f", "f32le", "-"],
                         input=x.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def fade(x, a=0.006, b=0.03):
    x = x.copy(); na, nb = int(a * SR), int(b * SR)
    x[:na] *= np.linspace(0, 1, na); x[-nb:] *= np.linspace(1, 0, nb)
    return x


def find_dip(x, t, win=0.14):
    """lowest 20 ms of energy near t; returned only when it is a real dip (>= 9 dB under the surrounding speech)"""
    hop = int(0.005 * SR); n = int(0.02 * SR)
    ts = np.arange(t - win, t + win, 0.005)
    e = np.array([10 * np.log10((x[int(u * SR):int(u * SR) + n] ** 2).mean() + 1e-12) for u in ts])
    k = int(np.argmin(e))
    around = 10 * np.log10((x[int((t - 0.35) * SR):int((t + 0.35) * SR)] ** 2).mean() + 1e-12)
    return (float(ts[k]) + 0.01, around - e[k]) if around - e[k] >= 9 else (None, around - e[k])


def main():
    take, out = sys.argv[1], sys.argv[2]
    x = load(take)
    voice = np.zeros(int(DUR * SR))
    for (name, (a, b), onsets, bounds), oend in zip(PHRASES, ORIG_END):
        pieces = [(a, b, onsets[0])]
        if bounds:
            dip, depth = find_dip(x, bounds[0])
            if dip is not None and a + 0.15 < dip < b - 0.15:
                pieces = [(a, dip, onsets[0]), (dip, b, onsets[1])]
            print(f"  split check for «{name}»: dip depth {depth:.1f} dB -> {'split at %.2f' % dip if len(pieces) == 2 else 'kept whole'}")
        for j, (p0, p1, start) in enumerate(pieces):
            limit = (pieces[j + 1][2] if j + 1 < len(pieces) else oend) - start      # room the original gave this piece
            d = p1 - p0
            tempo = min(1.0, max(TEMPO_MIN_FOR.get(name, TEMPO_MIN), d / max(limit, 0.05)))
            y = fade(stretch(x[int((p0 - 0.02) * SR):int((p1 + 0.05) * SR)], tempo))
            i0 = int(max(0.0, start - 0.02 / tempo) * SR)
            n = min(len(y), len(voice) - i0)
            voice[i0:i0 + n] += y[:n]
            print(f"«{name}» piece {j + 1}: take {p0:.2f}-{p1:.2f} ({d:.2f}s) -> at {start:.2f}, tempo {tempo:.2f}, lasts {d / tempo:.2f}s (original span {limit:.2f}s)")
    raw = (np.clip(voice, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", out], input=raw, check=True)


main()
