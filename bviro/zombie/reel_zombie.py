"""Reel «الشايب والزومبي»: the family gives the grandfather a VR zombie game; he scolds the zombies for walking in
without calling «هود هود», sits them down and pours them coffee.

Photoreal shots (Kling from stills), the grandson's lines in Bader's voice, the grandfather's in a library elder
voice. Seen from outside the headset the zombies are turquoise holograms, because only he sees them. The game
interface on the picture is drawn here, never generated.

usage: python3 -I reel_zombie.py WORK_DIR OUT_MP4 [--frames 0,24,...] [--cover COVER_JPG] [--parts voice,music,...]
  WORK_DIR/clips/  A.mp4 (he looks around)  B2.mp4 (inside the headset)  C2.mp4 (he scolds them, seated)
                   E3.mp4 (coffee)  F3.mp4 (the cup is shaken)  B.mp4 (first take of the headset view: its sound only)
  WORK_DIR/img/    K3b_calm.png (cover)
  WORK_DIR/voice/  kid_1.mp3  hook_2.mp3  old_1.mp3  hood_a.mp3  music.mp3
"""
import math
import os
import re
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import minimum_filter1d, uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "avatar", "tools"))
from reel_kit import (CHIP, DARK, PURPLE, TCHIP, TURQ, WHITE, cairo, caption_layer, ease_io, ease_out, faded, handle_layer,  # noqa: E402
                      paste_clip, pill, punch, tajawal)

WORK, OUT = sys.argv[1], sys.argv[2]


def opt(name):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


ONLY = [int(v) for v in opt("--frames").split(",")] if opt("--frames") else None
COVER = opt("--cover")
PARTS = tuple(opt("--parts").split(",")) if opt("--parts") else ("voice", "music", "ambience", "effects")
W, H, FPS, SR = 1080, 1920, 24, 48000
END = 25.2
T_END_PANEL = 21.5
os.makedirs(f"{WORK}/check", exist_ok=True)

# Lines: (speaker, source file, cut from, cut to, starts at) in seconds. Cuts sit in the pauses of each take.
LINES = [("kid", "hook_2.mp3", 0.00, 1.51, 0.10),   # عطينا جدي لعبة زومبي.. (re-recorded: it said «الشايب» before)
         ("kid", "kid_1.mp3", 1.79, 2.72, 1.89),    # شوفوا ايش صار! (the first take, joined at the pause; at 1.83 a
                                                    # plucked note of the music fell on its first sound)
         ("kid", "kid_1.mp3", 2.99, 5.16, 3.25),    # جدي! جايينك! اضربهم!
         ("old", "hood_a.mp3", 0.00, 2.95, 7.35),   # هيه! جايين من دون هود هود؟ عيب عليكم! (third take: «دون» is clear)
         ("old", "old_1.mp3", 2.99, 3.44, 11.30),   # اجلسوا!
         ("kid", "kid_1.mp3", 5.52, 8.37, 12.75),   # جدي.. هذي لعبة! لازم تضربهم!
         ("old", "old_1.mp3", 3.95, 5.95, 15.95),   # الضيف ما ينضرب.. تفضّلوا! (the last word is soft: cut at the file's end)
         ("kid", "kid_1.mp3", 8.78, 11.30, 18.35)]  # حتى الزومبي.. هزّ الفنجان!
# (clip, from, to, first frame of the clip). The view from inside the headset uses the end of its clip, where the
# first zombie reaches him and takes his hand.
SHOTS = [("A", 0.00, 3.00, 0), ("B2", 3.00, 7.20, 19), ("C2", 7.20, 12.20, 0), ("E3", 12.20, 17.30, 0), ("F3", 17.30, END, 0)]
SKIP = {"B2": {82}}  # one frame of the lunge where the model smeared the zombie's face
T_STOP, T_BACK = 7.10, 12.20  # the music stops dead just before he shouts, and comes back when they sit
# The music is made of phrases about 4.8 s long with a short rest between them. Coming back on the phrase that starts
# at 9.60 s of the file puts its rests on «الضيف ما ينضرب» and right after «هزّ الفنجان», and its ending on the last card.
MUSIC_BACK = 9.60


def fno(t):
    return int(round(t * FPS))


def seg(x, a, b):
    return min(max((x - a) / (b - a), 0.0), 1.0)


def load_clip(name):
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{WORK}/clips/{name}.mp4", "-vf", vf, "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


# ---- captions, speaker tags and the game interface -----------------------------------------------------------------
KID, OLD = "kid", "old"
CARDS = [  # (speaker, lines, from, to, caption_layer options)
    (KID, [[("عطينا جدي", WHITE)], [("لعبة زومبي..", TCHIP)]], 0.00, 1.85, {"size": 104}),
    (KID, [[("شوفوا ايش صار!", WHITE)]], 1.87, 3.00, {}),
    (KID, [[("جدي! جايينك!", WHITE)]], 3.25, 4.82, {"cy": 470}),
    (KID, [[("اضربهم!", CHIP)]], 4.85, 5.95, {"size": 112, "cy": 470}),
    (OLD, [[("هيه!", WHITE)]], 7.35, 8.05, {"size": 112}),
    (OLD, [[("جايين من دون", WHITE)], [("هود هود؟", TCHIP)]], 8.08, 9.55, {}),
    (OLD, [[("عيب عليكم!", CHIP)]], 9.62, 10.85, {"size": 112}),
    (OLD, [[("اجلسوا!", TCHIP)]], 11.30, 12.20, {"size": 124}),
    (KID, [[("جدي.. هذي لعبة!", WHITE)]], 12.75, 14.55, {}),
    (KID, [[("لازم تضربهم!", CHIP)]], 14.60, 15.85, {"size": 104}),
    (OLD, [[("الضيف ما ينضرب..", WHITE)]], 16.10, 17.25, {}),
    (OLD, [[("تفضّلوا!", TCHIP)]], 17.30, 18.25, {"size": 112}),
    (KID, [[("حتى الزومبي..", WHITE)]], 18.35, 20.05, {}),
    (KID, [[("هزّ الفنجان!", TCHIP)]], 20.10, 21.15, {"size": 108}),
]
TAGS = {KID: pill("الحفيد", size=40, outline=PURPLE), OLD: pill("الجد", size=40, outline=TURQ)}
CTA = pill("أرسل VR في الخاص", size=46, icon="send")


def hud_text(t):
    """The line of the game interface under the account pill, or None outside the game."""
    if 3.00 <= t < 7.20:
        return "لعبة الزومبي · الموجة 1"
    if 7.20 <= t < 12.20:
        return "الموجة 1 · الضربات: 0"
    if 12.20 <= t < T_END_PANEL:
        # four guests already hold their cups when the shot opens; the count turns to five when he finishes pouring the
        # one cup that is filled on screen, so the counter never claims a cup that was not seen
        cups = 4 if t < 13.95 else 5
        return f"الضربات: 0 · الفناجين: {cups}"
    return None


_pills = {}


def hud_pill(text):
    if text not in _pills:
        _pills[text] = pill(text, size=44, fill=(8, 40, 52), outline=TURQ)
    return _pills[text]


def weapon_label():
    """«السلاح: عصا»: a slot of the game interface that sits just above the walking stick."""
    p = pill("السلاح: عصا", size=42, fill=(8, 40, 52), outline=TURQ)
    im = Image.new("RGBA", (p.size[0], p.size[1] + 26), (0, 0, 0, 0))
    im.alpha_composite(p, (0, 0))
    cx = p.size[0] * 0.62
    ImageDraw.Draw(im).polygon([(cx - 15, p.size[1] - 3), (cx + 15, p.size[1] - 3), (cx, p.size[1] + 22)], fill=(*TURQ, 255))
    return im


WEAPON = weapon_label()


def corner_brackets(alpha):
    """Thin game-view brackets in the corners of the frame."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    m, n = 46, 110
    for cx, cy, sx, sy in ((m, 300, 1, 1), (W - m, 300, -1, 1), (m, 1480, 1, -1), (W - m, 1480, -1, -1)):
        d.line([(cx, cy + sy * n), (cx, cy), (cx + sx * n, cy)], fill=(*TURQ, 230), width=6)
    return faded(layer, alpha)


def end_panel(t):
    """«انتهت اللعبة» with the score and the call to action."""
    u = t - T_END_PANEL
    layer = Image.new("RGBA", (W, H), (20, 0, 45, int(165 * ease_out(u / 0.35))))
    rows = [(0.10, [[("انتهت اللعبة", WHITE)]], {"size": 124, "cy": 600}),
            (0.35, [[("الضربات: 0", CHIP)]], {"size": 92, "cy": 800}),
            (0.60, [[("الفناجين: 5", TCHIP)]], {"size": 92, "cy": 930}),
            (0.90, [[("الفائز:", WHITE), ("كرم جدي", TCHIP)]], {"size": 84, "cy": 1090}),
            (1.25, [[("عندك مشروع في عُمان؟", WHITE)]], {"size": 76, "cy": 1320})]
    for a, lines, o in rows:
        if u >= a:
            im, box = caption_layer(lines, **o)
            k = ease_out((u - a) / 0.16)
            s = 0.86 + 0.14 * k
            im2 = faded(im.resize((max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s))), Image.LANCZOS), k)
            paste_clip(layer, im2, int((box[0] + box[2]) / 2 - im2.size[0] / 2), int((box[1] + box[3]) / 2 - im2.size[1] / 2))
    if u >= 1.40:
        big = pill("أرسل VR في الخاص", size=70, fill=PURPLE, outline=WHITE, icon="send")
        k = ease_out((u - 1.40) / 0.2)
        pulse = 1.0 + 0.03 * math.sin(2 * math.pi * 1.6 * (u - 1.40))
        b2 = faded(big.resize((int(big.size[0] * pulse), int(big.size[1] * pulse)), Image.LANCZOS), k)
        paste_clip(layer, b2, (W - b2.size[0]) // 2, int(1460 - b2.size[1] / 2))
    return layer


def zoom(name, t):
    """Push-ins added in the edit: (zoom, centre x, centre y)."""
    if name == "A":
        return 1.0 + 0.07 * ease_io(t / 3.0), 420.0, 700.0
    if name == "B2":  # a short push toward the hand at the moment the first zombie takes hold of it (5.6 s)
        return 1.0 + 0.09 * ease_out(seg(t, 5.50, 5.72)) - 0.03 * ease_io(seg(t, 5.95, 6.50)), 430.0, 1265.0
    if name == "C2":  # a slow push-in while he tells them off: his reaction is calm, so the camera is too
        return 1.0 + 0.07 * ease_io((t - 7.20) / 5.0), 480.0, 800.0
    if name == "E3":
        return 1.0 + 0.05 * ease_io((t - 12.20) / 5.1), 470.0, 1000.0
    if name == "F3":
        return 1.0 + 0.06 * ease_io((t - 17.30) / 3.6), 560.0, 820.0
    return 1.0, 540.0, 960.0


def overlays():
    caps = []
    for who, lines, a, b, o in CARDS:
        im, box = caption_layer(lines, **o)
        caps.append((who, im, box, a, b))
    return caps, handle_layer()


def decorate(img, t, caps, handle):
    hud = hud_text(t)
    if 3.00 <= t < 7.20:  # inside the headset
        img.alpha_composite(corner_brackets(min(ease_out((t - 3.00) / 0.2), 1.0)))
        k = min(ease_out((t - 3.9) / 0.25), ease_out((5.45 - t) / 0.2))  # gone before the zombies crowd the frame
        if t >= 3.9 and k > 0:
            paste_clip(img, faded(WEAPON, k), W - 70 - WEAPON.size[0], 600)
    if hud:
        p = hud_pill(hud)
        paste_clip(img, p, (W - p.size[0]) // 2, 150)
    if 12.60 <= t < 17.20:  # the written call to action in the middle
        k = min(ease_out((t - 12.60) / 0.25), ease_out((17.20 - t) / 0.2))
        q = faded(CTA, k)
        paste_clip(img, q, (W - q.size[0]) // 2, int(250 - 20 * (1 - k)))
    if t >= T_END_PANEL:
        img.alpha_composite(end_panel(t))
    else:
        for who, im, box, a, b in caps:
            if a <= t < b:
                k = ease_out((t - a) / 0.14) if a > 0 else 1.0
                s = 0.84 + 0.16 * k
                im2 = faded(im.resize((max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s))), Image.LANCZOS), k) if k < 1 else im
                cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                paste_clip(img, im2, int(cx - im2.size[0] / 2), int(cy - im2.size[1] / 2))
                tag = faded(TAGS[who], k)
                paste_clip(img, tag, (W - tag.size[0]) // 2, box[1] - tag.size[1] - 14)
    img.alpha_composite(handle)
    return img


# ---- sound ---------------------------------------------------------------------------------------------------------
def limit(x, thr=0.55, win=0.010):
    """Look-ahead peak limiter: the gain dips smoothly around a peak, so shouted words keep their shape."""
    k = int(win * SR) | 1
    g = np.minimum(1.0, thr / np.maximum(np.abs(x).max(axis=1), 1e-9))
    g = uniform_filter1d(minimum_filter1d(g, size=k, mode="nearest"), size=k, mode="nearest")
    return x * g[:, None]


def master(path, target=-14.2, ceiling=0.84):
    """Bring the finished mix to the usual loudness with one fixed gain and a peak ceiling of -1.5 dBFS."""
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True).stderr.decode()
    before = float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", log)[-1])
    w = wave.open(path, "rb")
    x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32).reshape(-1, 2) / 32767.0
    w.close()
    y = limit(x * 10 ** ((target - before) / 20), thr=ceiling)
    w = wave.open(path, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())
    w.close()
    print("master: mix was %.1f LUFS, gain %+.1f dB, peak now %.2f" % (before, target - before, float(np.abs(y).max())), flush=True)


def mix_audio(path, total, parts=PARTS):
    n = int(total * SR)

    def load(p, start=0.0, dur=None):
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}"] + (["-t", f"{dur:.3f}"] if dur else []) + ["-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
        return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()

    def rms(x):
        return float(np.sqrt((x ** 2).mean()) + 1e-9)

    def fade(x, a=0.02, b=0.02):
        x = x.copy()
        na, nb = max(int(a * SR), 1), max(int(b * SR), 1)
        x[:na] *= np.linspace(0, 1, na)[:, None]
        x[-nb:] *= np.linspace(1, 0, nb)[:, None]
        return x

    def place(buf, x, t):
        i = max(int(t * SR), 0)
        m = min(len(x), n - i)
        if m > 0:
            buf[i:i + m] += x[:m]

    db = lambda v: 10 ** (v / 20)
    speech = db(-18.5)  # every line is brought to this level, so the two voices match
    voice = np.zeros((n, 2), np.float32)
    for who, src, a, b, t0 in LINES:
        x = fade(load(f"{WORK}/voice/{src}", max(a - 0.04, 0.0), b - a + 0.14))
        act = x[np.abs(x[:, 0]) > 0.01]
        place(voice, limit(x * speech / rms(act)), t0)
    # music: the sneaky opening, silence while he scolds, the warm part when they sit
    m = load(f"{WORK}/voice/music.mp3")
    m = m / max(np.abs(m).max(), 1e-6)
    g = speech * db(-15.5) / rms(m[: int(20 * SR)])
    music = np.zeros((n, 2), np.float32)
    first = m[: int(T_STOP * SR)] * g
    tm = np.arange(len(first)) / SR
    first *= (db(-5) + (1 - db(-5)) * np.clip((tm - 0.5) / 0.5, 0, 1))[:, None]  # its loud first note sits under the hook's first word
    place(music, fade(first, 0.02, 0.05), 0.0)
    back = m[int(MUSIC_BACK * SR):]
    back = back[: n - int(T_BACK * SR)]
    place(music, fade(back * g, 0.08, 0.4), T_BACK)
    # the bed comes up by 4.5 dB wherever nobody speaks for a moment (the zombies' approach, the last card)
    said = (np.abs(voice[:, 0]) > 0.02).astype(np.int64)
    c = np.concatenate([[0], np.cumsum(said)])
    idx = np.arange(n)
    busy = (c[np.clip(idx + int(0.25 * SR), 0, n)] - c[np.clip(idx - int(0.35 * SR), 0, n)]) > 0
    lift = uniform_filter1d((~busy).astype(np.float32), size=int(0.3 * SR), mode="nearest")
    music *= (1 + (db(4.5) - 1) * lift)[:, None]
    # ambience: the zombies' groans. They come from the first take of the headset view (B.mp4), which the owner heard
    # in the draft; the sound generated with the second take has sounds that an automatic transcription reads as
    # English words, so it is not used.
    amb = np.zeros((n, 2), np.float32)
    b_snd = load(f"{WORK}/clips/B.mp4", 20 / FPS)[: int(4.1 * SR)]
    place(amb, fade(b_snd * db(-30) / rms(b_snd), 0.15, 0.12), 3.00)
    # effects, only where nobody is speaking
    fx = np.zeros((n, 2), np.float32)
    tt = np.arange(int(0.22 * SR)) / SR
    zip_ = np.sin(2 * np.pi * (620 * tt - 1050 * tt ** 2)) * np.exp(-tt / 0.09) * db(-22)  # the music is yanked away
    place(fx, np.stack([zip_, zip_], 1).astype(np.float32), T_STOP)
    for k, f0 in enumerate((784.0, 1046.5)):  # two-note chime for the score card
        tt = np.arange(int(0.6 * SR)) / SR
        note = np.sin(2 * np.pi * f0 * tt) * np.exp(-tt / 0.18) * db(-23)
        place(fx, np.stack([note, note], 1).astype(np.float32), T_END_PANEL + 0.08 + 0.16 * k)
    stems = {"voice": voice, "music": music, "ambience": amb, "effects": fx}
    said = np.abs(voice[:, 0]) > 0.02
    print("levels dBFS  speech %.1f  music under speech %.1f  groans %.1f  effects peak %.1f" % (
        20 * np.log10(rms(voice[said])), 20 * np.log10(rms(music[said])), 20 * np.log10(rms(amb[int(3.2 * SR): int(7.0 * SR)])),
        20 * np.log10(np.abs(fx).max() + 1e-9)), flush=True)
    out = np.clip(sum(stems[k] for k in parts), -1, 1)
    w = wave.open(path, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((out * 32767).astype("<i2").tobytes())
    w.close()


def make_cover(path, handle):
    """Cover: the grandfather, calm, with the hologram zombies holding his hand: it raises the question without giving
    the coffee away."""
    im = Image.open(f"{WORK}/img/K3b_calm.png").convert("RGB")
    s = max(W / im.size[0], H / im.size[1])
    im = im.resize((int(im.size[0] * s + 0.5), int(im.size[1] * s + 0.5)), Image.LANCZOS)
    x0, y0 = (im.size[0] - W) // 2, (im.size[1] - H) // 2
    img = im.crop((x0, y0, x0 + W, y0 + H)).convert("RGBA")
    cap, box = caption_layer([[("عطينا جدي", WHITE)], [("لعبة زومبي!", TCHIP)]], size=116, cy=1500)
    img.alpha_composite(cap, (box[0], box[1]))
    img.alpha_composite(handle)
    img.convert("RGB").save(path, quality=93)


def main():
    caps, handle = overlays()
    total = fno(END) / FPS
    if COVER:
        make_cover(COVER, handle)
    enc = None
    if ONLY is None:
        mixp = OUT + ".mix.wav"
        mix_audio(mixp, total)
        master(mixp)
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-i", mixp, "-map", "0:v", "-map", "1:a",
                                "-t", f"{total:.4f}", "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-maxrate", "12M", "-bufsize", "24M",
                                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    for name, t0, t1, first in SHOTS:
        n0, n1 = fno(t0), fno(t1)
        want = [n for n in range(n0, n1) if ONLY is None or n in ONLY]
        if not want:
            continue
        fr = load_clip(name)
        order = [k for k in range(first, len(fr)) if k not in SKIP.get(name, ())]
        for n in want:
            t = n / FPS
            src = Image.fromarray(fr[order[min(n - n0, len(order) - 1)]])
            z, cx, cy = zoom(name, t)
            img = decorate(punch(src, z, cy=cy, cx=cx).convert("RGBA"), t, caps, handle).convert("RGB")
            if enc:
                enc.stdin.write(img.tobytes())
            else:
                img.save(f"{WORK}/check/dbg_{n:04d}.jpg", quality=90)
        del fr
    if enc:
        enc.stdin.close()
        assert enc.wait() == 0
        os.remove(OUT + ".mix.wav")
        print("ok", OUT, fno(END), "frames", round(total, 3), "s")


if __name__ == "__main__":
    main()
