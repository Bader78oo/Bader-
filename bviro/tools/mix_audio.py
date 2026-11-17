"""Mix the Reel soundtrack (20.0 s, 48 kHz stereo): Bader's ElevenLabs voice + nature/camel ambience from the clips
+ generated music bed (ducked under the voice) + two soft whooshes on the VR cuts.
usage: python3 -I mix_audio.py OUT.wav"""
import subprocess, sys, wave
import numpy as np

S = "/tmp/claude-0/-home-user-Bader-/871f84b2-2289-5b97-9b32-a74e478b68cd/scratchpad/bviro"
SR, DUR = 48000, 20.0
N = int(SR * DUR)
CUT = [c / 24 for c in (0, 73, 143, 188, 259, 311, 379, 480)]


def load(path, start=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start}"] + (["-t", f"{dur}"] if dur else []) + ["-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)


def db(x):
    return 10 ** (x / 20)


def active_rms(x):
    m = x.mean(1)
    fr = m[: len(m) // 480 * 480].reshape(-1, 480)
    e = np.sqrt((fr ** 2).mean(1))
    act = e[e > db(-45)]
    return np.sqrt((act ** 2).mean()) if len(act) else 1e-9


def fade(x, fi=0.02, fo=0.02):
    x = x.copy()
    a, b = int(fi * SR), int(fo * SR)
    if a: x[:a] *= np.linspace(0, 1, a)[:, None]
    if b: x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x


def place(mix, x, t0):
    i = int(round(t0 * SR)); x = x[: max(0, N - i)]
    mix[i:i + len(x)] += x


def norm(x, target_db, active=False):
    r = active_rms(x) if active else np.sqrt((x ** 2).mean()) + 1e-9
    return x * db(target_db) / r


# --- voice
vo = np.zeros((N, 2))
hook = norm(fade(load(f"{S}/audio/hook_c.mp3", 0, 2.98), 0.005, 0.04), -19, active=True)
body = norm(fade(load(f"{S}/audio/vo_b.mp3", 2.45), 0.02, 0.05), -19, active=True)
place(vo, hook, 0.03)
place(vo, body, 3.00)

# --- ambience per shot (no generated speech: the two shots with the man use plain desert wind)
amb = np.zeros((N, 2))
for (src, s0, lvl), t0, t1 in zip([("v1", 2.0, -31), ("v8", 0.0, -37), ("v6", 0.6, -31), ("v6", 2.4, -30), ("v8", 2.0, -35), ("v8", 0.4, -37)],
                                  CUT[:-2], CUT[1:-1]):
    seg = load(f"{S}/audio/sfx_{src}.wav", s0, t1 - t0 + 0.12)
    place(amb, fade(norm(seg, lvl), 0.06, 0.12), max(0, t0 - 0.03))

# --- whoosh on entering / leaving the headset world
rng = np.random.default_rng(3)
def whoosh(dur=0.55, lvl=-20):
    n = int(dur * SR); noise = rng.standard_normal(n)
    spec = np.fft.rfft(noise); f = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((np.log2(np.maximum(f, 1)) - np.log2(1400)) ** 2) / 1.2)
    w = np.fft.irfft(spec, n); t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 2 * (0.6 + 0.4 * t)
    w = w * env; w = w / (np.abs(w).max() + 1e-9) * db(lvl)
    return np.stack([w * (1 - 0.3 * t), w * (0.7 + 0.3 * t)], 1)
fx = np.zeros((N, 2))
place(fx, whoosh(), CUT[2] - 0.30)
place(fx, whoosh(), CUT[4] - 0.30)

# --- music, ducked under the voice
mus = load(f"{S}/audio/music.mp3", 0, DUR)
mus = np.pad(mus, ((0, max(0, N - len(mus))), (0, 0)))[:N]
mus = mus * db(-19) / (np.sqrt((mus[: int(18 * SR)] ** 2).mean()) + 1e-9)      # bed at -19 dBFS rms before ducking
e = np.abs(vo).max(1)
win = int(0.08 * SR); e = np.convolve(e, np.ones(win) / win, mode="same")
act = (e > db(-38)).astype(np.float64)
rel = int(0.35 * SR); act = np.convolve(act, np.ones(rel) / rel, mode="same")           # smooth attack/release
act = np.clip(act * 1.6, 0, 1)
duck = db(-11) ** act                                                                    # -11 dB while the voice speaks
mus = mus * duck[:, None]
mus[-int(0.5 * SR):] *= np.linspace(1, 0, int(0.5 * SR))[:, None] ** 1.5
mus[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]

mix = vo + amb + fx + mus
peak = np.abs(mix).max()
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix *= db(-1.5) / (np.abs(mix).max() + 1e-9)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
def lvl(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
print(f"wrote {sys.argv[1]}  pre-limit peak {20*np.log10(peak):.1f} dBFS | rms vo {lvl(vo):.1f} amb {lvl(amb):.1f} music {lvl(mus):.1f} fx {lvl(fx):.1f}")
print("voice ends at", round(np.nonzero(np.abs(vo).max(1) > db(-40))[0].max() / SR, 2), "s")
