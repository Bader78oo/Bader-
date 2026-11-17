"""Sound for Reel 2. usage: python3 -I mix_r2.py VARIANT(A|B|C) OUT.wav
Voice (take A) placed line by line, a playful music bed and clip ambience under the snow world, everything cut dead at the reveal
(one remote beep, then a quiet room with a faint air-conditioner hum), and a short riser into the loop point."""
import os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_r2 as T

SR = 48000


def load(path, t0=0.0, t1=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}"] + (["-t", f"{t1 - t0:.3f}"] if t1 is not None else []) + \
          ["-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()


def db(x):
    return 10 ** (x / 20)


def rms_db(x):
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)


def to_rms(x, target):
    return x * db(target - rms_db(x))


def fade(x, a=0.005, b=0.03):
    x = x.copy(); na, nb = int(a * SR), int(b * SR)
    if na: x[:na] *= np.linspace(0, 1, na)[:, None]
    if nb: x[-nb:] *= np.linspace(1, 0, nb)[:, None]
    return x


def place(buf, x, t):
    i = int(round(t * SR)); n = min(len(x), len(buf) - i)
    if n > 0: buf[i:i + n] += x[:n]


def main():
    variant, out = sys.argv[1], sys.argv[2]
    shots, total = T.shots(variant)
    dur = total / T.FPS
    N = int(round(dur * SR))
    vo, bed = np.zeros((N, 2), np.float32), np.zeros((N, 2), np.float32)
    reveal = next(s["start"] for s in shots if s["name"] == "reveal") / T.FPS

    full = load(f"{T.R}/audio/vo2_a.mp3")
    g = db(-19.0 - rms_db(full[np.abs(full).max(1) > 0.02]))          # voice level from its voiced samples
    for s in shots:
        t0 = s["start"] / T.FPS
        for line, at in s["vo"]:
            a, b = T.VO[line]
            place(vo, fade(full[int(a * SR):int(b * SR)] * g, 0.008, 0.05), t0 + at)
        if s.get("amb"):
            src, gain = s["amb"]
            a = s["f0"] / T.FPS
            seg = load(f"{T.R}/audio/sfx_{src}.wav", a, a + s["n"] / T.FPS * max(1.0, s["speed"]))[: int(s["n"] / T.FPS * SR)]
            place(bed, fade(to_rms(seg, -24.0) * db(gain), 0.01, 0.02), t0)

    # music under the snow world only, cut dead on the reveal
    mus = load(f"{T.R}/audio/music2.mp3", 0.0, reveal)
    place(bed, fade(to_rms(mus, -30.0), 0.004, 0.012), 0.0)

    # the reveal: one air-conditioner remote beep exactly on the cut
    t = np.arange(int(0.16 * SR)) / SR
    beep = (np.sin(2 * np.pi * 2350 * t) * np.exp(-t * 16) * np.minimum(1, t / 0.003)).astype(np.float32) * db(-13)
    place(bed, np.stack([beep, beep], 1), reveal)

    # quiet room: faint low air-conditioner hum + air noise until the end
    n = N - int(reveal * SR)
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(n).astype(np.float32)
    lp = np.zeros(n, np.float32); acc = 0.0
    k = 0.02
    for i in range(n):                                             # one-pole low-pass (soft air rush)
        acc += k * (noise[i] - acc); lp[i] = acc
    tt = np.arange(n) / SR
    room = lp / (np.abs(lp).max() + 1e-9) * db(-36) + (np.sin(2 * np.pi * 100 * tt) * db(-46) + np.sin(2 * np.pi * 200 * tt) * db(-52)).astype(np.float32)
    room *= np.minimum(1, tt / 0.25)
    place(bed, np.stack([room, room], 1).astype(np.float32), reveal)

    # short riser into the loop point (the music restarts at frame 0)
    rn = int(0.55 * SR); tr = np.arange(rn) / SR
    rise = rng.standard_normal(rn).astype(np.float32)
    hp = np.diff(rise, prepend=0)                                  # brighter noise
    env = (tr / tr[-1]) ** 3
    riser = (hp / (np.abs(hp).max() + 1e-9) * env * db(-20)).astype(np.float32)
    place(bed, np.stack([riser, riser], 1), dur - 0.55)

    # duck the bed a little under the voice
    win = int(0.04 * SR)
    e = np.sqrt(np.convolve((vo ** 2).mean(1), np.ones(win) / win, mode="same"))
    duck = 1 - 0.45 * np.clip(e / 0.05, 0, 1)
    mix = vo + bed * duck[:, None]
    peak = np.abs(mix).max()
    if peak > 0.89: mix *= 0.89 / peak
    mix[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))[:, None]      # avoid a click on the loop cut
    raw = (np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", out], input=raw, check=True)
    print("wrote", out, round(dur, 3), "s; reveal at", round(reveal, 3), "; voice rms", round(rms_db(vo[np.abs(vo).max(1) > 0.01]), 1), "bed rms(head)", round(rms_db(bed[: int(reveal * SR)]), 1))


main()
