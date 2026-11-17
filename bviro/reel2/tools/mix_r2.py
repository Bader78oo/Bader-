"""Sound for Reel 2, cut v4. usage: python3 -I mix_r2.py VARIANT OUT.wav
Narrator (Bader), the friend's spoken line (Omani library voice) and the brand line are placed piece by piece from the
timeline. A playful music bed and clip ambience run under the snow world and stop dead when the picture leaves the
headset; a quiet room with a faint air-conditioner hum follows, one remote beep sits on the AC shot, and a short riser
leads into the loop point. (The v3 mixer is kept as mix_r2_v3.py.)"""
import os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_r2 as T

SR = 48000
VOICE_RMS = -19.0


def load(path, t0=0.0, t1=None, lp=None):
    af = ["-af", f"lowpass=f={lp}"] if lp else []
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}"] + (["-t", f"{t1 - t0:.3f}"] if t1 is not None else []) + \
          ["-i", path] + af + ["-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()


def db(x):
    return 10 ** (x / 20)


def rms_db(x):
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)


def voiced_db(x):
    v = x[np.abs(x).max(1) > 0.02]
    return rms_db(v) if len(v) else -60.0


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
    at = {s["name"]: s["start"] / T.FPS for s in shots}
    music_end, beep_t = at[T.MUSIC_UNTIL], at[T.BEEP_AT]

    gains = {}                                                   # one level per source file, measured on its voiced samples
    for s in shots:
        t0 = s["start"] / T.FPS
        for line, when in s["vo"]:
            path, a, b, off, lp = T.VO[line]
            if path not in gains:
                gains[path] = db(VOICE_RMS - voiced_db(load(path)))
            place(vo, fade(load(path, a, b, lp) * gains[path] * db(off), 0.008, 0.05), t0 + when)
        if s.get("amb"):
            src, gain = s["amb"]
            a = s["f0"] / T.FPS
            seg = load(f"{T.R}/audio/sfx_{src}.wav", a, a + s["n"] / T.FPS * max(1.0, s["speed"]))[: int(s["n"] / T.FPS * SR)]
            place(bed, fade(to_rms(seg, -24.0) * db(gain), 0.01, 0.02), t0)

    place(bed, fade(to_rms(load(f"{T.R}/audio/music2.mp3", 0.0, music_end), -30.0), 0.004, 0.012), 0.0)

    t = np.arange(int(0.16 * SR)) / SR                            # one air-conditioner remote beep on the AC shot
    beep = (np.sin(2 * np.pi * 2350 * t) * np.exp(-t * 16) * np.minimum(1, t / 0.003)).astype(np.float32) * db(-13)
    place(bed, np.stack([beep, beep], 1), beep_t)

    n = N - int(music_end * SR)                                   # quiet room: soft air rush + low hum until the end
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(n).astype(np.float32)
    lp = np.zeros(n, np.float32); acc = 0.0
    for i in range(n):
        acc += 0.02 * (noise[i] - acc); lp[i] = acc
    tt = np.arange(n) / SR
    room = lp / (np.abs(lp).max() + 1e-9) * db(-36) + (np.sin(2 * np.pi * 100 * tt) * db(-46) + np.sin(2 * np.pi * 200 * tt) * db(-52)).astype(np.float32)
    room *= np.minimum(1, tt / 0.25)
    place(bed, np.stack([room, room], 1).astype(np.float32), music_end)

    rn = int(0.55 * SR); tr = np.arange(rn) / SR                  # short riser into the loop point
    hp = np.diff(rng.standard_normal(rn).astype(np.float32), prepend=0)
    riser = (hp / (np.abs(hp).max() + 1e-9) * (tr / tr[-1]) ** 3 * db(-14)).astype(np.float32)
    place(bed, np.stack([riser, riser], 1), dur - 0.55)

    win = int(0.04 * SR)                                          # duck the bed under any voice
    e = np.sqrt(np.convolve((vo ** 2).mean(1), np.ones(win) / win, mode="same"))
    mix = vo + bed * (1 - 0.5 * np.clip(e / 0.05, 0, 1))[:, None]
    peak = np.abs(mix).max()
    if peak > 0.89: mix *= 0.89 / peak
    mix[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))[:, None]
    raw = (np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", out], input=raw, check=True)
    print("wrote", out, round(dur, 3), "s; music until", round(music_end, 3), "; beep at", round(beep_t, 3),
          "; voice gains dB", {os.path.basename(k): round(20 * np.log10(v), 1) for k, v in gains.items()})


main()
