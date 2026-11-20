"""National Day film «خفّاق»: cinematic shots cut to the owner's voice, with an original score.

No presenter character in this film (owner's decision). The Sultan's photograph is used unaltered: only a slow
camera push-in, never an AI edit or animation. The flag is checked in every shot that shows it.

usage: python3 -I film_khaffaq.py WORK_DIR OUT_MP4 [--sample]
  WORK_DIR/clips/  S*.mp4   animated shots (24 fps)
  WORK_DIR/src/    sultan.jpg (owner-supplied photo)
  WORK_DIR/voice/  voice_main.wav, music.mp3
  --sample         only the shots listed in SAMPLE_SHOTS, voice faded out after them (look test)
"""
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "avatar", "tools"))
from reel_kit import DARK, WHITE, cairo, draw_line, ease_io, ease_out, faded, handle_layer, paste_clip  # noqa: E402

WORK, OUT = sys.argv[1], sys.argv[2]
SAMPLE = "--sample" in sys.argv[3:]
W, H, FPS = 1080, 1920, 24  # 24 fps: the animated shots are native 24, and it is the cinema frame rate
GOLD = (244, 214, 140)
PRE = 0.25  # picture before the first word
VOICE_END = 37.95
END = 42.40  # film end, in voice time
MUSIC_SKIP = 1.20  # seconds trimmed from the start of the score so that its final hit lands as the voice ends
SR = 48000

# name, kind, source, start, end (voice time), clip in-point (s), zoom from/to, focus (x, y), dissolve-in frames
SHOTS = [
    ("S1", "clip", "S1.mp4", -PRE, 4.10, 0.20, (1.00, 1.10), (560, 330), 0),
    ("S2", "clip", "S2.mp4", 4.10, 8.82, 0.10, (1.00, 1.03), (540, 800), 5),
    ("S3", "clip", "S3.mp4", 8.82, 11.64, 0.30, (1.00, 1.04), (540, 800), 5),
    ("S4", "clip", "S4.mp4", 11.64, 12.95, 0.60, (1.00, 1.03), (540, 760), 4),
    ("S5", "clip", "S5.mp4", 12.95, 16.50, 0.30, (1.00, 1.04), (540, 900), 0),
    ("S6", "clip", "S6.mp4", 16.50, 17.95, 1.00, (1.00, 1.03), (540, 900), 0),
    ("S9", "clip", "S9.mp4", 17.95, 19.36, 1.00, (1.00, 1.03), (540, 900), 0),
    ("S7", "clip", "S7.mp4", 19.36, 20.94, 0.20, (1.02, 1.06), (520, 700), 0),
    ("S8", "clip", "S8.mp4", 20.94, 22.62, 1.00, (1.00, 1.03), (540, 900), 0),
    ("S10a", "clip", "S10a.mp4", 22.62, 25.42, 0.40, (1.00, 1.04), (540, 900), 4),
    ("S10b", "clip", "S10b.mp4", 25.42, 26.66, 1.00, (1.00, 1.03), (540, 800), 0),
    ("S11", "clip", "S11.mp4", 26.66, 27.90, 1.00, (1.00, 1.03), (540, 760), 0),
    ("S12", "clip", "S12.mp4", 27.90, 30.88, 0.40, (1.00, 1.04), (540, 760), 4),
    ("SULTAN", "photo", "sultan.jpg", 30.88, 34.70, 0.0, (1.00, 1.07), (560, 560), 6),
    ("S14", "clip", "S14.mp4", 34.70, END, 0.10, (1.00, 1.05), (540, 620), 6),
]
SAMPLE_SHOTS = [("S1", -PRE, 4.10), ("S2", 4.10, 8.82), ("S7", 8.82, 11.80)]
SAMPLE_VOICE_END = 8.80

# captions: lines of (text, colour), start, end, size
CAPS = [
    ([[("هذا العلم..", WHITE)], [("ما يرفعه الهوا بس", WHITE)]], -PRE, 2.52, 76),
    ([[("يرفعه تاريخ", GOLD)]], 2.56, 4.02, 104),
    ([[("بحّار عُماني شقّ البحر", WHITE)]], 4.30, 6.48, 66),
    ([[("لين الهند والصين وأفريقيا", WHITE)]], 6.52, 8.74, 66),
    ([[("ولبان عطّر الدنيا", WHITE)], [("من قديم الزمان", GOLD)]], 8.92, 11.50, 66),
    ([[("قلاع وقفت", WHITE)]], 11.80, 12.92, 66),
    ([[("وأفلاج سقت", WHITE)]], 12.98, 14.00, 66),
    ([[("وأهل ما تركوا أرضهم يوم", GOLD)]], 14.06, 16.40, 66),
    ([[("من خيران مسندم", WHITE)]], 16.60, 17.92, 66),
    ([[("لين خريف ظفار", WHITE)]], 17.98, 19.30, 66),
    ([[("من ورد الجبل الأخضر", WHITE)]], 19.42, 20.90, 66),
    ([[("لين رمال الشرقية", WHITE)]], 20.98, 22.50, 66),
    ([[("نفس اليد اللي بنت السفينة", WHITE)]], 23.00, 25.34, 66),
    ([[("تبني الميناء والمصنع والتقنية", GOLD)]], 25.46, 27.80, 62),
    ([[("شعب وفيّ", WHITE)]], 27.96, 28.80, 76),
    ([[("وسلطان يقود المسيرة", WHITE)]], 28.88, 30.80, 66),
    ([[("جلالة السلطان هيثم بن طارق", WHITE)], [("حفظه الله ورعاه", GOLD)]], 31.06, 34.56, 62),
    ([[("كل عام وعُمان شامخة", WHITE)]], 34.96, 36.44, 70),
    ([[("وعلمها خفّاق", GOLD)]], 36.50, 38.10, 92),
]


def caption_img(lines, size, cy=1490, lead=1.42):
    font = cairo(size, 800)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    step = int(size * lead)
    y0 = cy - step * (len(lines) - 1) / 2
    for i, segs in enumerate(lines):
        draw_line(layer, segs, font, y0 + i * step, stroke=max(4, size // 12), max_w=980)
    # the dark outline of reel_kit is brand purple; here it is replaced by a neutral soft black for a film look
    a = layer.getchannel("A")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow.paste((0, 0, 0, 255), (0, 6), a.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.75)))
    full = Image.alpha_composite(glow, layer)
    box = full.getbbox()
    return full.crop(box), box


def end_card(k):
    """«كل عام وعُمان بخير» with a thin tricolour rule; k = 0..1 appearance."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f = cairo(104, 900)
    draw_line(layer, [("كل عام وعُمان بخير", WHITE)], f, 1260, stroke=6, max_w=1000)
    d = ImageDraw.Draw(layer)
    wd = int(360 * k)
    x0, y0 = 540 - wd // 2, 1362
    for i, col in enumerate(((255, 255, 255), (219, 22, 27), (0, 128, 0))):
        d.rectangle([x0 + i * wd / 3, y0, x0 + (i + 1) * wd / 3, y0 + 8], fill=(*col, 255))
    draw_line(layer, [("20 نوفمبر", GOLD)], cairo(54, 700), 1432, stroke=4, max_w=900)
    a = layer.getchannel("A")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow.paste((0, 0, 0, 255), (0, 6), a.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.8)))
    return faded(Image.alpha_composite(glow, layer), k)


class Reader:
    """Sequential frames of a clip from an in-point; holds the last frame when the clip runs out."""

    def __init__(self, path, t_in):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t_in:.4f}", "-i", path, "-vf",
                                   f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}",
                                   "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.last, self.held = None, 0

    def read(self):
        raw = self.p.stdout.read(W * H * 3)
        if len(raw) == W * H * 3:
            self.last = Image.frombuffer("RGB", (W, H), raw, "raw", "RGB", 0, 1).copy()
        else:
            self.held += 1
        assert self.last is not None, "clip gave no frames"
        return self.last

    def close(self):
        self.p.kill()
        self.p.stdout.close()
        self.p.wait()


class Photo:
    def __init__(self, path):
        im = Image.open(path).convert("RGB")
        s = max(W / im.size[0], H / im.size[1])
        im = im.resize((int(im.size[0] * s + 1), int(im.size[1] * s + 1)), Image.LANCZOS)
        x, y = (im.size[0] - W) // 2, (im.size[1] - H) // 2
        self.im = im.crop((x, y, x + W, y + H))
        self.held = 0

    def read(self):
        return self.im

    def close(self):
        pass


def push(im, z, focus):
    if z <= 1.0005:
        return im
    cx, cy = focus
    w, h = W / z, H / z
    x0 = min(max(cx - w * (cx / W), 0), W - w)
    y0 = min(max(cy - h * (cy / H), 0), H - h)
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))


def finishing():
    """Bottom shade for the captions and a soft vignette, as one RGBA overlay."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    shade = np.clip((yy - 1150) / 770, 0, 1) ** 1.5 * 120
    r = np.hypot((xx - W / 2) / (W * 0.75), (yy - H / 2) / (H * 0.75))
    vig = np.clip((r - 0.55) / 0.6, 0, 1) ** 2 * 90
    a = np.clip(shade + vig, 0, 200).astype(np.uint8)
    ov = np.zeros((H, W, 4), np.uint8)
    ov[..., 3] = a
    return Image.fromarray(ov, "RGBA")


def mix_audio(path, total, voice_end):
    def load(p):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    n = int(total * SR)
    v = load(f"{WORK}/voice/voice_main.wav")
    v = v / max(np.abs(v).max(), 1e-6) * 0.89
    ve = int(voice_end * SR)
    v = v[:ve]
    f = int(0.25 * SR)
    v[-f:] *= np.linspace(1, 0, f)[:, None] if SAMPLE else 1.0
    voice = np.zeros((n, 2), np.float32)
    s = int(PRE * SR)
    voice[s:s + len(v)] = v[: n - s]
    m = load(f"{WORK}/voice/music.mp3")[int(MUSIC_SKIP * SR):]
    m = m / max(np.abs(m).max(), 1e-6)
    music = np.zeros((n, 2), np.float32)
    music[: min(n, len(m))] = m[:n]
    t = np.arange(n) / SR - PRE  # voice time
    duck, full = 0.30, 0.80
    g = np.full(n, duck, np.float32)
    g = np.where(t < 0.6, duck + (0.55 - duck) * np.clip(1 - t / 0.6, 0, 1), g)  # the opening note is a little louder
    rise = np.clip((t - (voice_end - 0.35)) / 0.9, 0, 1)
    g = g + (full - duck) * rise
    fade = np.clip((total - PRE - t) / 1.6, 0, 1) if not SAMPLE else np.clip((total - PRE - t) / 0.8, 0, 1)
    g = g * np.minimum(fade, np.clip((t + PRE) / 0.3, 0, 1))
    out = voice + music * g[:, None]
    out = np.clip(out, -1, 1)
    w = wave.open(path, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((out * 32767).astype("<i2").tobytes())
    w.close()


def main():
    shots = SHOTS
    end, voice_end = END, VOICE_END
    if SAMPLE:
        by = {s[0]: s for s in SHOTS}
        shots = [(n, by[n][1], by[n][2], a, b, by[n][5], by[n][6], by[n][7], by[n][8]) for n, a, b in SAMPLE_SHOTS]
        end, voice_end = SAMPLE_SHOTS[-1][2], SAMPLE_VOICE_END
    nframes = int(round((PRE + end) * FPS))
    total = nframes / FPS
    mix = OUT + ".mix.wav"
    mix_audio(mix, total, voice_end)
    caps = [(caption_img(lines, size), a, b) for lines, a, b, size in CAPS if a < voice_end]
    fin = finishing()
    handle = handle_layer()
    rng = np.random.default_rng(3)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", mix, "-filter_complex", "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]", "-map", "0:v", "-map", "[a]",
                            "-t", f"{total:.4f}", "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    readers = {}

    def reader(i):
        if i not in readers:
            name, kind, src = shots[i][:3]
            readers[i] = Photo(f"{WORK}/src/{src}") if kind == "photo" else Reader(f"{WORK}/clips/{src}", shots[i][5])
        return readers[i]

    def shot_frame(i, t):
        name, kind, src, a, b, t_in, (z0, z1), focus, _ = shots[i]
        x = min(max((t - a) / max(b - a, 1e-6), 0), 1.15)
        return push(reader(i).read(), z0 + (z1 - z0) * x, focus)

    for n in range(nframes):
        t = n / FPS - PRE
        i = max([k for k in range(len(shots)) if t >= shots[k][3]] or [0])
        fr = shot_frame(i, t)
        d = shots[i][8]
        if i > 0 and d and t < shots[i][3] + d / FPS:
            k = ease_io((t - shots[i][3]) * FPS / d)
            fr = Image.blend(shot_frame(i - 1, t), fr, k)
        for j in list(readers):
            if j < i - 1 or (j == i - 1 and not (d and t < shots[i][3] + d / FPS)):
                readers.pop(j).close()
        fr = fr.convert("RGBA")
        fr.alpha_composite(fin)
        for (img, box), a, b in caps:
            if a <= t < b:
                k = min(ease_out((t - a) / 0.22) if a > -PRE else 1.0, ease_out((b - t) / 0.16))
                fr.alpha_composite(faded(img, k) if k < 1 else img, (box[0], box[1] + int(14 * (1 - k))))
        if not SAMPLE and t > voice_end + 0.15:
            fr.alpha_composite(end_card(ease_out((t - voice_end - 0.15) / 0.6)))
            fr.alpha_composite(faded(handle, ease_out((t - voice_end - 0.9) / 0.5)))
        arr = np.asarray(fr.convert("RGB"), np.int16) + rng.normal(0, 2.2, (H, W, 1)).astype(np.int16)  # light film grain
        enc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    held = {shots[j][0]: r.held for j, r in readers.items() if r.held}
    for r in readers.values():
        r.close()
    enc.stdin.close()
    assert enc.wait() == 0
    os.remove(mix)
    print("ok", OUT, nframes, "frames", round(total, 3), "s", "| shots that ran out of frames:", held or "none")


if __name__ == "__main__":
    main()
