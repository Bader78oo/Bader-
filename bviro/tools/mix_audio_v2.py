"""Soundtrack for Reel v2 (18.75 s). Same voice takes, re-laid to the tighter cut.
usage: python3 -I mix_audio_v2.py OUT.wav"""
import subprocess, sys, wave
import numpy as np

S = "/tmp/claude-0/-home-user-Bader-/871f84b2-2289-5b97-9b32-a74e478b68cd/scratchpad/bviro"
SR, DUR = 48000, 18.75
N = int(SR * DUR)
CUT = [c / 24 for c in (0, 66, 114, 162, 230, 292, 356, 450)]
db = lambda x: 10 ** (x / 20)


def load(path, start=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start}"] + (["-t", f"{dur}"] if dur else []) + ["-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)


def fade(x, fi=0.02, fo=0.02):
    x = x.copy(); a, b = int(fi * SR), int(fo * SR)
    if a: x[:a] *= np.linspace(0, 1, a)[:, None]
    if b: x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x


def place(mix, x, t0):
    i = int(round(t0 * SR)); x = x[: max(0, N - i)]
    mix[i:i + len(x)] += x


def rms(x):
    return np.sqrt((x ** 2).mean()) + 1e-9


# --- voice: one gain per source file so the takes stay matched (levelled on the active speech of each file)
def active_gain(path, target=-19):
    x = load(path).mean(1); fr = x[: len(x) // 480 * 480].reshape(-1, 480); e = np.sqrt((fr ** 2).mean(1)); act = e[e > db(-45)]
    return db(target) / (np.sqrt((act ** 2).mean()) + 1e-9)
gh, gb = active_gain(f"{S}/audio/hook_c.mp3"), active_gain(f"{S}/audio/vo_b.mp3")
vo = np.zeros((N, 2))
place(vo, fade(load(f"{S}/audio/hook_c.mp3", 0.06, 2.90) * gh, 0.005, 0.04), 0.0)
for src0, src1, t0 in [(3.10, 5.26, 2.90),      # حتى راعيها ما فاهم ايش صاير (chuckle dropped)
                       (5.72, 10.09, 5.18),     # هي الحين في خريف صلالة… خضرة، وضباب، وشلالات
                       (10.40, 12.33, 9.73),    # وهي ما تحركت من الرمل
                       (12.50, 15.03, 12.13),   # [laugh] والحين… دور راعيها
                       (15.43, 18.95, 14.93)]:  # بيفيرو… نودّيك أي مكان، وانت في مكانك
    place(vo, fade(load(f"{S}/audio/vo_b.mp3", src0, src1 - src0) * gb, 0.025, 0.04), t0)

# --- ambience (camel / wind / waterfall); none of the clips with generated speech are used
amb = np.zeros((N, 2))
for (src, s0, lvl), t0, t1 in zip([("v1", 2.3, -31), ("v8", 0.0, -37), ("v6", 0.6, -31), ("v6", 2.2, -30), ("v8", 1.6, -34), ("v8", 0.4, -37), ("v1", 0.2, -34)],
                                  CUT[:-1], CUT[1:]):
    seg = load(f"{S}/audio/sfx_{src}.wav", s0, t1 - t0 + 0.12)
    place(amb, fade(seg * db(lvl) / rms(seg), 0.06, 0.12), max(0, t0 - 0.03))

rng = np.random.default_rng(3)
def whoosh(dur=0.55, lvl=-20):
    n = int(dur * SR); spec = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((np.log2(np.maximum(f, 1)) - np.log2(1400)) ** 2) / 1.2)
    w = np.fft.irfft(spec, n); t = np.linspace(0, 1, n); w *= np.sin(np.pi * t) ** 2 * (0.6 + 0.4 * t)
    w = w / (np.abs(w).max() + 1e-9) * db(lvl)
    return np.stack([w * (1 - 0.3 * t), w * (0.7 + 0.3 * t)], 1)
fx = np.zeros((N, 2))
place(fx, whoosh(), CUT[2] - 0.30); place(fx, whoosh(), CUT[4] - 0.30)
place(fx, whoosh(0.3, -24), CUT[4] + 22 / 24 - 0.12)          # snap-zoom on the sand gag

mus = load(f"{S}/audio/music.mp3", 0, DUR)
mus = np.pad(mus, ((0, max(0, N - len(mus))), (0, 0)))[:N]
mus *= db(-19) / rms(mus[: int(17 * SR)])
e = np.abs(vo).max(1); win = int(0.08 * SR); e = np.convolve(e, np.ones(win) / win, mode="same")
act = (e > db(-38)).astype(np.float64); rel = int(0.35 * SR)
act = np.clip(np.convolve(act, np.ones(rel) / rel, mode="same") * 1.6, 0, 1)
mus *= (db(-11) ** act)[:, None]
mus[-int(0.6 * SR):] *= np.linspace(1, 0, int(0.6 * SR))[:, None] ** 1.5
mus[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]

mix = vo + amb + fx + mus
mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix *= db(-1.5) / (np.abs(mix).max() + 1e-9)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
lvl = lambda x: 20 * np.log10(rms(x))
print(f"wrote {sys.argv[1]} | rms vo {lvl(vo):.1f} amb {lvl(amb):.1f} music {lvl(mus):.1f}; voice ends {np.nonzero(np.abs(vo).max(1) > db(-40))[0].max() / SR:.2f}s")
