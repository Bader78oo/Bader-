"""Animatic of «رجّعنا جدي حارة العقر»: the locked timing, the recorded voices, the sound effects and the music cues,
laid over the approved stills. It is a working copy for judging timing, dialect and music before any shot is animated.
The pictures only move by camera moves made here, and the shots that have no final still yet carry a label.

usage: python3 -I animatic.py WORK_DIR OUT_MP4 [--frames 0,24,...] [--parts voice,music,ambience,effects] [--stems DIR]
                                              [--clean]
  --frames  write only these frames as JPEGs to WORK_DIR/check/ (no sound, no video)
  --parts   which stems go into the mix (default: all four)
  --stems   also write each stem as a WAV into DIR, to inspect one layer alone
  --clean   leave out the working labels (the «نسخة أولية» slug, the music tags and the «مؤقتة» marks)
  --cover   also write the reel's cover (1080x1920 JPEG) to this path
  --clips   folder of animated shots named by shot number (1.mp4, 3.mp4 ... 22.mp4): the film, not the animatic
  WORK_DIR/img/    the stills named in the shot functions below
  WORK_DIR/voice/  the recorded lines (LINES)
  WORK_DIR/sfx/    the library sound effects (see the sound map in SCREENPLAY.md)
  WORK_DIR/music/  theme_v2.mp3 (the oud theme), m3_hara.mp3 (a string drone and three strums),
                   m5_jokha.mp3 (one long low note)
"""
import math
import os
import re
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import butter, fftconvolve, sosfiltfilt

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.dirname(HERE)  # bviro/
sys.path.insert(0, os.path.join(B, "avatar", "tools"))
from reel_kit import (CHIP, DARK, PURPLE, TCHIP, TURQ, WHITE, cairo, caption_layer, ease_io, ease_out, faded, handle_layer,  # noqa: E402
                      paste_clip, pill)

WORK, OUT = sys.argv[1], sys.argv[2]


def opt(name):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


ONLY = [int(v) for v in opt("--frames").split(",")] if opt("--frames") else None
PARTS = tuple(opt("--parts").split(",")) if opt("--parts") else ("voice", "music", "ambience", "effects")
STEMS = opt("--stems")
CLEAN = "--clean" in sys.argv
COVER = opt("--cover")  # also write the cover picture to this path
CLIPS = opt("--clips")  # folder of animated shots; a shot without a clip there falls back to its still
W, H, FPS, SR = 1080, 1920, 24, 48000

# ---- the cut: every shot as (first frame, frame after its last), 24 frames a second ---------------------------------
# Shots 8 to 13 and 16 to 19 are cut on the beats of the oud theme (72 beats a minute), which is why they are not
# round numbers.
CUT = {"1": (0, 41), "2a": (41, 51), "2b": (51, 61), "2c": (61, 72), "3": (72, 110), "4": (110, 156), "5": (156, 207),
       "6": (207, 295), "7": (295, 343), "8": (343, 403), "9": (403, 445), "10": (445, 485), "11": (485, 526),
       "12": (526, 586), "13": (586, 650), "14": (650, 702), "15": (702, 729), "16": (729, 773), "17": (773, 813),
       "18": (813, 874), "19": (874, 921), "20": (921, 982), "21": (982, 1034), "22": (1034, 1111), "end": (1111, 1189)}
TOTAL_FRAMES = CUT["end"][1]
END = TOTAL_FRAMES / FPS


def at(shot):
    """Second at which a shot starts."""
    return CUT[shot][0] / FPS


T_TOUCH = 37.22  # the hands meet, on a strong pluck of the theme
T_CUT = 37.47    # ... and a quarter of a second later the music is cut off

# ---- voice: (speaker, file, cut from, cut to, starts at, level trim in dB) ------------------------------------------
KID, OLD = "kid", "old"
LINES = [(KID, "kid_hook_a.mp3", 0.00, 1.80, 0.12, 0.0),       # أول مرة أشوف دمعة جدي.. (after the opening thump)
         (KID, "kid_hook_a.mp3", 2.40, 4.64, 2.00, 0.0),       # والسبب.. نظارة VR! (half a second of its pause is cut)
         (OLD, "old_walk.mp3", 0.25, 1.50, 5.00, 0.0),         # كيف أمشي؟
         (KID, "kid_jeer_v2.mp3", 0.00, 5.39, 6.55, 0.0),      # جدي سهل.. قدّم الجير قدّام راح تمشي. وعشان تلف، حرّك الجير يمين ويسار.
         (OLD, "old_easy.mp3", 0.20, 2.75, 11.65, 0.0),        # (a small laugh) ايوه.. سهل!
         (OLD, "old_hara.mp3", 0.00, 3.04, 15.25, 0.0),        # هذي حارتنا.. مثل ما كانت!
         (OLD, "old_neighbour.mp3", 0.00, 3.52, 20.52, 0.0),   # وهذا جارنا.. مودّي الغنم للمناداة!
         (OLD, "old_home.mp3", 0.05, 1.12, 25.55, -3.0),       # بيتنا.. (near a whisper)
         (OLD, "old_jokha_a.mp3", 0.15, 1.32, 33.97, -1.0),    # يا جوخة..
         (OLD, "old_jokha_sh.mp3", 1.46, 2.88, 35.23, -1.0),   # هينِش عنّي؟ (re-recorded: the owner corrected «هينِك» to
                                                               # «هينِش»; the name is kept from the first take, where
                                                               # its jeem is clear, and the two are joined at the pause)
         (KID, "kid_rahma.mp3", 0.00, 3.20, 39.05, -2.0),      # جدتي جوخة.. الله يرحمها.
         (OLD, "old_stay_a.mp3", 0.00, 2.56, 43.45, -2.0)]     # لا.. خلّوني عندها شوية.

# ---- words on the picture: (speaker, lines, from, to, where) ---------------------------------------------------------
TOP, LOW = 470, 1500  # captions sit at the top while we look through the headset, clear of the hologram hands
SAY = [(OLD, ["كيف أمشي؟"], 5.10, 6.35, TOP),
       (KID, ["جدي سهل.."], 6.70, 7.50, LOW),
       (KID, ["قدّم الجير قدّام"], 7.62, 8.56, LOW),
       (KID, ["راح تمشي"], 8.62, 9.35, TOP),
       (KID, ["وعشان تلف.."], 9.50, 10.30, TOP),
       (KID, ["حرّك الجير يمين ويسار"], 10.38, 11.72, TOP),
       (OLD, ["ايوه.."], 12.48, 13.32, LOW),
       (OLD, ["سهل!"], 13.42, 14.26, LOW),
       (OLD, ["هذي حارتنا.."], 15.31, 16.72, LOW),
       (OLD, ["مثل ما كانت!"], 16.79, 18.30, LOW),
       (OLD, ["وهذا جارنا.."], 20.55, 21.88, TOP),
       (OLD, ["مودّي الغنم للمناداة!"], 22.03, 23.95, TOP),
       (OLD, ["بيتنا.."], 25.63, 26.85, LOW),
       (OLD, ["يا جوخة.."], 34.05, 35.23, LOW),
       (OLD, ["هينِش عنّي؟"], 35.35, 36.72, LOW),
       (KID, ["جدتي جوخة.."], 39.13, 40.90, LOW),
       (KID, ["الله يرحمها."], 41.25, 42.70, LOW),
       (OLD, ["لا.. خلّوني عندها شوية."], 43.51, 46.10, LOW)]
HOOK = [([[("أول مرة أشوف", WHITE)], [("دمعة جدي", TCHIP)]], 0.00, 1.98, {"size": 100, "cy": 1440}),
        ([[("والسبب..", WHITE)]], 2.15, 2.98, {"size": 104, "cy": 1440}),
        ([[("نظارة VR!", CHIP)]], 3.00, 4.35, {"size": 112, "cy": 1440})]
# what plays under each stretch, shown small at the bottom of the working copy
MUSIC_TAGS = [(0.00, at("3"), "موسيقى 1 · نبضة عميقة وثلاث ضربات"),
              (at("3"), at("5"), "موسيقى 2 · نغمة وترية ثابتة"),
              (at("5"), at("8"), "موسيقى 2 · عود خفيف مرح"),
              (at("8"), at("13"), "موسيقى 3 · لحن العود يدخل مع وجه الشاب"),
              (at("13"), at("14"), "موسيقى 4 · نغمة واحدة ممسوكة"),
              (at("14"), 31.61, "بدون موسيقى · دندنة جوخة والنار"),
              (31.61, T_CUT, "موسيقى 5 · العود يرجع ويعلو"),
              (T_CUT, at("21"), "سكوت"),
              (at("21"), at("end"), "موسيقى 6 · نغمة طويلة واحدة"),
              (at("end"), END, "موسيقى 7 · اللحن يرجع ويختم")]
TEMP = {"8": "لقطة 8 مؤقتة", "17": "لقطة 17 مؤقتة", "18": "لقطة 18 مؤقتة", "19": "لقطة 19 مؤقتة"}


def seg(x, a, b):
    return min(max((x - a) / (b - a), 0.0), 1.0)


# ======================================================================================================================
# picture
# ======================================================================================================================
_stills = {}


def still(name):
    if name not in _stills:
        _stills[name] = Image.open(f"{WORK}/img/{name}.png").convert("RGB")
    return _stills[name]


def view(im, z, sx, sy, ax=0.5, ay=0.5, dx=0.0, dy=0.0):
    """A 9:16 window of a still, enlarged z times, with the source point (sx, sy) shown at the screen point (ax, ay).
    All four are fractions; dx, dy nudge the window by screen pixels. The window is kept inside the picture."""
    sw, sh = im.size
    h = sh / z
    w = h * W / H
    if w > sw:
        w, h = sw, sw * H / W
    x0 = sx * sw - ax * w - dx * w / W
    y0 = sy * sh - ay * h - dy * h / H
    x0 = min(max(x0, 0), sw - w)
    y0 = min(max(y0, 0), sh - h)
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))


def shifted(a, ox, oy):
    """Array moved by whole pixels, the uncovered edge left black."""
    if ox == 0 and oy == 0:
        return a
    out = np.zeros_like(a)
    h, w = a.shape[:2]
    out[max(oy, 0):h + min(oy, 0), max(ox, 0):w + min(ox, 0)] = a[max(-oy, 0):h - max(oy, 0), max(-ox, 0):w - max(ox, 0)]
    return out


class Holo:
    """The hologram controllers: a picture of turquoise light on black, added to the view as light (see pov_mock.py)."""

    def __init__(self, name, shift=(0.0, 0.0)):
        ov = np.asarray(Image.open(f"{WORK}/img/{name}.png").convert("RGB").resize((W, H), Image.LANCZOS), np.float32) / 255
        ov = np.clip((ov - 0.11) / 0.89, 0, 1)  # drop the haze around the holograms: only they add light
        self.ov = shifted(ov, int(shift[0] * W), int(shift[1] * H))
        self.body = np.clip(self.ov.max(axis=2, keepdims=True) * 1.6, 0, 1) * 0.38

    def over(self, bg, ox=0, oy=0):
        ov, body = shifted(self.ov, ox, oy), shifted(self.body, ox, oy)
        comp = bg * (1 - body) + ov * 0.95       # a hologram hides a little of what is behind it, then adds its light
        return 1 - (1 - comp) * (1 - ov * 0.35)


def chevrons(kind, stick=(0.71, 0.645)):
    """Three chevrons above the right thumbstick, as a 0..1 layer."""
    layer = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(layer)
    s = int(W * 0.060)
    ax, ay = int(W * stick[0]), int(H * stick[1]) - int(H * 0.062)
    for k in range(3):
        o = k * int(s * 0.95)
        a = int(255 * (1 - 0.28 * k))
        if kind == "up":
            pts = [(ax - s, ay - o + s * 0.6), (ax, ay - o - s * 0.4), (ax + s, ay - o + s * 0.6)]
        elif kind == "right":
            pts = [(ax + o - s * 0.6, ay - s), (ax + o + s * 0.4, ay), (ax + o - s * 0.6, ay + s)]
        else:
            pts = [(ax - o + s * 0.6, ay - s), (ax - o - s * 0.4, ay), (ax - o + s * 0.6, ay + s)]
        d.line(pts, fill=a, width=max(6, int(W * 0.010)), joint="curve")
    glow = np.asarray(layer.filter(ImageFilter.GaussianBlur(W * 0.012)), np.float32) / 255
    core = np.asarray(layer.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    return np.clip(core + 0.55 * glow, 0, 1)[..., None]


def brackets():
    """Thin corner marks of the headset view."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    m, n = 46, 110
    for cx, cy, sx, sy in ((m, 300, 1, 1), (W - m, 300, -1, 1), (m, 1700, 1, -1), (W - m, 1700, -1, -1)):
        d.line([(cx, cy + sy * n), (cx, cy), (cx + sx * n, cy)], fill=(*TURQ, 200), width=5)
    return layer


def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def arr(im):
    return np.asarray(im, np.float32) / 255


TURQ_F = np.array(TURQ, np.float32) / 255
_lazy = {}


def lazy(key, make):
    if key not in _lazy:
        _lazy[key] = make()
    return _lazy[key]


def walk(tau, amp=1.0):
    """Head bob of a walk, in pixels: (sideways, up and down)."""
    return 3.0 * amp * math.sin(2 * math.pi * 0.95 * tau), 7.0 * amp * math.sin(2 * math.pi * 1.9 * tau)


# ---- animated shots ---------------------------------------------------------------------------------------------------
# shot: (clip file, second of the clip at which the shot starts, playback rate). Shots not listed start their own
# clip at 0 and play it at normal speed.
CLIP_MAP = {"5": ("5", -0.55, 1.0),    # the thumb pushes the stick 0.5 s into its clip: held back to fall on «قدّم»
            "7": ("7", 0.12, 1.0),     # his mouth opens on «ايوه»
            "15": ("15", 1.55, 1.0),   # the later sweep of the palm, where the dough keeps its swirl
            "21": ("1", 2.75, 1.0),    # the tear reaching the beard is the end of the opening shot's clip
            "22": ("22", 0.10, 0.70)}  # slowed so that his lips move for as long as «لا.. خلّوني عندها شوية» lasts
_clip = {"name": None, "frames": None}


def has_clip(shot):
    return bool(CLIPS) and os.path.exists(f"{CLIPS}/{CLIP_MAP.get(shot, (shot,))[0]}.mp4")


def clip_frame(shot, t):
    """Frame of a shot's clip at t seconds into the shot, fitted to the frame. One clip is kept in memory at a time."""
    name, start, rate = CLIP_MAP.get(shot, (shot, 0.0, 1.0))
    if _clip["name"] != name:
        vf = f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{CLIPS}/{name}.mp4", "-vf", vf, "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                             capture_output=True, check=True).stdout
        _clip["name"], _clip["frames"] = name, np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    fr = _clip["frames"]
    pos = min(max((start + rate * t) * FPS, 0.0), len(fr) - 1.0)
    k = int(pos)
    w = pos - k
    if w < 0.02 or k + 1 >= len(fr) or abs(rate - 1.0) < 1e-6:
        return Image.fromarray(fr[min(int(round(pos)), len(fr) - 1)])
    # a slowed clip falls between two frames: they are blended, so the motion stays smooth
    return Image.fromarray((fr[k].astype(np.float32) * (1 - w) + fr[k + 1].astype(np.float32) * w + 0.5).astype(np.uint8))


def zoomed(im, z, cx=0.5, cy=0.5):
    """Digital push-in on a frame, keeping the point (cx, cy) in place."""
    if z <= 1.0005:
        return im
    w, h = W / z, H / z
    x0 = min(max(cx * W - w * cx, 0), W - w)
    y0 = min(max(cy * H - h * cy, 0), H - h)
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))


# ---- one function per shot: (seconds since the shot began, shot length) -> RGB image ---------------------------------
def s1(t, d):
    """Tear from under the headset. Opens on a quick settle and a breath of turquoise."""
    z = 1.0 + 0.07 * ease_io(t / d) + 0.16 * (1 - ease_out(t / 0.30))
    im = view(still("L5b_tear"), z, 0.475, 0.52, 0.475, 0.52)
    k = 0.32 * (1 - seg(t, 0.0, 0.22))
    if k > 0:
        im = Image.blend(im, Image.new("RGB", (W, H), TURQ), k)
    return im


def flash(name, sx, sy):
    def shot(t, d):
        im = view(still(name), 1.0 + 0.10 * (1 - ease_out(t / 0.30)), sx, sy)
        k = 0.55 * (1 - seg(t, 0.0, 0.125))
        return Image.blend(im, Image.new("RGB", (W, H), WHITE), k) if k > 0 else im
    return shot


def s3(t, d):
    return view(still("M3_controllers"), 1.0 + 0.06 * ease_io(t / d), 0.50, 0.42)


def pov_lane(z, pan, tau, bob, arrow=None, arrow_k=0.0):
    """The lane through the headset: the plate moves, the hologram hands stay with the head."""
    sway = walk(tau, bob)
    bg = arr(view(still("M4_pov_plate"), z, 0.53 + pan, 0.42, 0.5, 0.45, dx=sway[0], dy=sway[1]))
    holo = lazy("holo4", lambda: Holo("M4_ctrl_overlay"))
    comp = holo.over(bg, int(round(-0.6 * sway[0])), int(round(4 * math.sin(2 * math.pi * 1.9 * tau + 0.8) * bob)))
    if arrow and arrow_k > 0:
        a = lazy("chev_" + arrow, lambda: chevrons(arrow)) * 0.9 * arrow_k
        comp = comp * (1 - a) + (TURQ_F * 0.75 + 0.25) * a
    return to_img(comp)


def s4(t, d):
    return pov_lane(1.0 + 0.02 * (t / d), 0.0, t, 0.25)


def s5(t, d):
    """Thumb on the stick. The small upward nudge falls on «قدّم الجير قدّام»."""
    push = ease_io(seg(t, 1.10, 1.45)) - 0.6 * ease_io(seg(t, 1.75, 2.10))
    return view(still("M5b_thumb"), 1.0 + 0.10 * ease_io(t / d), 0.74, 0.27, 0.70, 0.32, dy=-14 * push)


T6_RIGHT, T6_LEFT = 2.38, 2.84  # seconds into shot 6: «يمين», «ويسار»


def s6(t, d):
    z = 1.0 + 0.55 * seg(t, 0.0, T6_RIGHT + 0.1) ** 0.9
    pan = 0.11 * ease_io(seg(t, T6_RIGHT, T6_RIGHT + 0.42)) - 0.22 * ease_io(seg(t, T6_LEFT, T6_LEFT + 0.62))
    if t < T6_RIGHT:
        arrow, k = "up", 0.55 + 0.45 * abs(math.sin(2 * math.pi * 1.4 * t))
    elif t < T6_LEFT:
        arrow, k = "right", 1.0
    else:
        arrow, k = "left", 1.0
    return pov_lane(z, pan, t, 1.0 if t < T6_RIGHT else 0.4, arrow, k)


def s7(t, d):
    return view(still("M7_grin"), 1.0 + 0.04 * ease_io(t / d), 0.70, 0.53, 0.70, 0.53)


def s8(t, d):
    """Match cut: the young face opens at the size and place of the grandfather's grin, then the camera pulls back."""
    u = ease_io(seg(t, 0.45, 2.0))
    z = 2.8 ** (1 - u) * (1.0 + 0.03 * (1 - seg(t, 2.0, d)))
    return view(still("L1b_young"), z, 0.40, 0.32, 0.70 + (0.40 - 0.70) * u, 0.53 + (0.32 - 0.53) * u)


def s9(t, d):
    return view(still("M9_falaj"), 1.0 + 0.08 * ease_io(t / d), 0.50, 0.62, dy=10 * (t / d))


def s10(t, d):
    jx = 5 * math.sin(2 * math.pi * 1.3 * t) + 3 * math.sin(2 * math.pi * 2.9 * t + 1.0)
    jy = 6 * math.sin(2 * math.pi * 1.7 * t + 0.5)
    return view(still("P10_kids"), 1.02 + 0.10 * ease_io(t / d), 0.60, 0.55, dx=jx, dy=jy)


def s11(t, d):
    """The pickup comes at us; the right hologram hand waves."""
    bg = arr(view(still("N11_pov_plate_lettered"), 1.0 + 0.14 * (t / d), 0.38, 0.62, 0.40, 0.60, dy=3 * math.sin(2 * math.pi * 0.5 * t)))
    holo = lazy("holo11", lambda: Holo("N11_wave_overlay", (0.03, 0.13)))
    return to_img(holo.over(bg, int(round(16 * math.sin(2 * math.pi * 2.3 * t))), int(round(5 * math.sin(2 * math.pi * 1.1 * t)))))


def s12(t, d):
    """He turns to watch it go: the old plate up close, then the truck recedes."""
    bg = arr(view(still("N12_pov_plate"), 1.12 - 0.12 * ease_io(t / d), 0.50, 0.50, dy=4 * math.sin(2 * math.pi * 0.6 * t)))
    holo = lazy("holo12", lambda: Holo("M4_ctrl_overlay", (0.0, 0.05)))
    return to_img(holo.over(bg, 0, int(round(4 * math.sin(2 * math.pi * 0.6 * t + 1.0)))))


def s13(t, d):
    """From inside the dark hallway. The light widens from the door's gap as it opens."""
    a = arr(view(still("P13_door"), 1.0 + 0.06 * ease_io(t / d), 0.55, 0.45))
    k = ease_io(seg(t, 0.05, 1.05))
    if k < 1:
        x = np.arange(W, dtype=np.float32)[None, :, None] / W
        half = 0.012 + 0.75 * k
        m = np.clip((half - np.abs(x - 0.59)) / 0.08 + 0.5, 0, 1)
        a = a * (0.16 + 0.84 * np.maximum(m, k * k))
    return to_img(a)


def s14(t, d):
    return view(still("P14_jokha"), 1.0 + 0.09 * ease_io(t / d), 0.45, 0.62)


def s15(t, d):
    return view(still("M15_dough"), 1.08 - 0.08 * ease_io(t / d), 0.55, 0.60)


def s16(t, d):
    a = arr(view(still("L7b_jokha_cu"), 1.0 + 0.06 * ease_io(t / d), 0.50, 0.42))
    return to_img(a * (0.86 + 0.14 * ease_io(seg(t, 0.2, 1.1))))  # her face lights up as she sees him


FIRE = np.array([1.06, 0.84, 0.60], np.float32)


def s17(t, d):
    """Stand-in: the approved young face, graded to firelight. The real shot is his face at the kitchen door."""
    a = arr(view(still("L1b_young"), 2.2 + 0.15 * (t / d), 0.385, 0.305, 0.5, 0.42))
    flick = 0.80 + 0.03 * math.sin(2 * math.pi * 7.0 * t) + 0.02 * math.sin(2 * math.pi * 11.3 * t + 1.0)
    return to_img(a * FIRE * flick)


def view18(t):
    return view(still("P14_jokha"), 1.9 + 0.12 * seg(t, 0, 2.54), 0.52, 0.56)


def s18(t, d):
    """Stand-in: Jokha at the hearth. The real shot is the two of them, her hand holding out the folded bread."""
    return view18(t)


_rng = np.random.default_rng(19)
P_N = 1300
P_X = W * 0.50 + _rng.normal(0, 190, P_N)
P_Y = H * 0.50 + _rng.normal(0, 260, P_N)
P_T0, P_V = _rng.uniform(0, 0.60, P_N), _rng.uniform(150, 430, P_N)
P_PH, P_R = _rng.uniform(0, 6.28, P_N), _rng.uniform(1.5, 4.8, P_N)


def s19(t, d):
    """Stand-in for the touch: she turns into points of turquoise light that rise, and the kitchen is left dim.
    The real shot is a close view of the two hands."""
    base = view(still("P14_jokha"), 2.02 + 0.30 * ease_io(seg(t, 0, 0.8)), 0.52 + 0.10 * ease_io(seg(t, 0, 0.8)), 0.56 + 0.02 * ease_io(seg(t, 0, 0.8)))
    v = t - (T_TOUCH - at("19"))
    if v <= 0:
        return base
    empty = arr(base.filter(ImageFilter.GaussianBlur(16))) * 0.42
    k = ease_io(seg(v, 0.0, 0.75))
    a = arr(base) * (1 - k) + empty * k
    a = a + TURQ_F * 0.30 * math.exp(-v / 0.16)
    layer = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(layer)
    age = v - P_T0
    for i in np.nonzero(age > 0)[0]:
        g = age[i]
        alpha = min(g / 0.10, 1.0) * max(1 - g / 1.05, 0.0)
        if alpha <= 0:
            continue
        x = P_X[i] + 24 * math.sin(P_PH[i] + 3.2 * g)
        y = P_Y[i] - P_V[i] * g - 60 * g * g
        r = P_R[i]
        dr.ellipse([x - r, y - r, x + r, y + r], fill=int(255 * alpha))
    core = np.asarray(layer, np.float32)[..., None] / 255
    glow = np.asarray(layer.filter(ImageFilter.GaussianBlur(9)), np.float32)[..., None] / 255
    a = a + (TURQ_F * 0.8 + 0.2) * core + TURQ_F * 1.4 * glow
    return to_img(a)


def s20(t, d):
    return view(still("M20_reach"), 1.0 + 0.05 * ease_io(t / d), 0.62, 0.50)


def s21(t, d):
    return view(still("L5b_tear"), 1.18 + 0.08 * ease_io(t / d), 0.475, 0.56, 0.475, 0.50)


def s22(t, d):
    return view(still("M22_chest"), 1.0 + 0.07 * ease_io(t / d), 0.48, 0.55)


def end_card(t, d):
    """Closing card in the brand's colours: the line, the mark, the call."""
    def make_bg():
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        x = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
        top, bot = np.array(DARK, np.float32) / 255, np.array((16, 0, 36), np.float32) / 255
        a = top * (1 - y) + bot * y
        glow = np.exp(-(((x - 0.5) / 0.55) ** 2 + ((y - 0.30) / 0.22) ** 2))
        return to_img(a + np.array(PURPLE, np.float32) / 255 * 0.16 * glow).convert("RGBA")
    img = lazy("end_bg", make_bg).copy()
    rows = [(0.20, [[("بعض الأماكن ما ترجع..", WHITE)]], {"size": 80, "cy": 610}),
            (0.95, [[("بس نقدر نخليك", WHITE)], [("تمشي فيها.", TCHIP)]], {"size": 84, "cy": 810})]
    for a0, lines, o in rows:
        if t >= a0:
            im, box = lazy(("end", a0), lambda: caption_layer(lines, **o))
            k = ease_out((t - a0) / 0.22)
            paste_clip(img, faded(im, k), box[0], int(box[1] + 16 * (1 - k)))
    if t >= 1.55:
        def make_logo():
            lg = Image.open(f"{B}/logo/bviro_ara_white.png").convert("RGBA")
            hh = 170
            return lg.resize((int(lg.size[0] * hh / lg.size[1]), hh), Image.LANCZOS)
        lg = lazy("logo", make_logo)
        paste_clip(img, faded(lg, ease_out((t - 1.55) / 0.25)), (W - lg.size[0]) // 2, 1010)
    if t >= 1.85:
        q = lazy("end_q", lambda: say_layer(["عندك مكان أو مشروع في عُمان", "تريد الناس تعيشه؟"], size=46, cy=1330, stroke=0))
        paste_clip(img, faded(q[0], ease_out((t - 1.85) / 0.25)), q[1][0], q[1][1])
    if t >= 2.10:
        big = lazy("end_cta", lambda: pill("أرسل VR في الخاص", size=66, fill=PURPLE, outline=WHITE, icon="send"))
        k = ease_out((t - 2.10) / 0.2)
        pulse = 1.0 + 0.03 * math.sin(2 * math.pi * 1.6 * (t - 2.10))
        b2 = faded(big.resize((int(big.size[0] * pulse), int(big.size[1] * pulse)), Image.LANCZOS), k)
        paste_clip(img, b2, (W - b2.size[0]) // 2, int(1540 - b2.size[1] / 2))
    return img.convert("RGB")


# ---- the same shots from animated clips (used when --clips has the shot) ------------------------------------------------
def c1(t, d):
    im = zoomed(clip_frame("1", t), 1.0 + 0.16 * (1 - ease_out(t / 0.30)), 0.475, 0.52)
    k = 0.32 * (1 - seg(t, 0.0, 0.22))
    return Image.blend(im, Image.new("RGB", (W, H), TURQ), k) if k > 0 else im


def plain(shot, z0=1.0, z1=1.0, cx=0.5, cy=0.5):
    """A clip as it is, with an optional slow push-in from z0 to z1."""
    def fn(t, d):
        return zoomed(clip_frame(shot, t), z0 + (z1 - z0) * ease_io(t / d), cx, cy)
    return fn


def c4(t, d):
    bg = arr(clip_frame("4", t))
    holo = lazy("holo4", lambda: Holo("M4_ctrl_overlay"))
    return to_img(holo.over(bg, 0, int(round(3 * math.sin(2 * math.pi * 0.35 * t)))))


def c6(t, d):
    """The walk is the clip; the looks to the right and to the left are slides of a slightly enlarged frame."""
    pan = 0.075 * ease_io(seg(t, T6_RIGHT, T6_RIGHT + 0.40)) - 0.15 * ease_io(seg(t, T6_LEFT, T6_LEFT + 0.60))
    z = 1.0 + 0.19 * ease_io(seg(t, T6_RIGHT - 0.5, T6_RIGHT))
    im = clip_frame("6", t)
    if z > 1.0005:
        w, h = W / z, H / z
        x0 = min(max((W - w) / 2 + pan * W, 0), W - w)
        im = im.resize((W, H), Image.BICUBIC, box=(x0, (H - h) * 0.45, x0 + w, (H - h) * 0.45 + h))
    holo = lazy("holo4", lambda: Holo("M4_ctrl_overlay"))
    bob = 1.0 if t < T6_RIGHT else 0.4
    comp = holo.over(arr(im), int(round(-2 * math.sin(2 * math.pi * 0.95 * t) * bob)), int(round(4 * math.sin(2 * math.pi * 1.9 * t + 0.8) * bob)))
    if t < T6_RIGHT:
        arrow, k = "up", 0.55 + 0.45 * abs(math.sin(2 * math.pi * 1.4 * t))
    elif t < T6_LEFT:
        arrow, k = "right", 1.0
    else:
        arrow, k = "left", 1.0
    a_ = lazy("chev_" + arrow, lambda: chevrons(arrow)) * 0.9 * k
    return to_img(comp * (1 - a_) + (TURQ_F * 0.75 + 0.25) * a_)


def c11(t, d):
    bg = arr(clip_frame("11", t))
    holo = lazy("holo11", lambda: Holo("N11_wave_overlay", (0.03, 0.13)))
    return to_img(holo.over(bg, int(round(16 * math.sin(2 * math.pi * 2.3 * t))), int(round(5 * math.sin(2 * math.pi * 1.1 * t)))))


def c12(t, d):
    # enlarged 4% from the right edge: late in the clip a passer-by's arm comes in at the left edge
    bg = arr(zoomed(clip_frame("12", t), 1.045, 1.0, 0.5))
    holo = lazy("holo12", lambda: Holo("M4_ctrl_overlay", (0.0, 0.05)))
    return to_img(holo.over(bg, 0, int(round(4 * math.sin(2 * math.pi * 0.6 * t + 1.0)))))


def c13(t, d):
    a = arr(clip_frame("13", t))
    k = ease_io(seg(t, 0.05, 0.95))
    if k < 1:
        x = np.arange(W, dtype=np.float32)[None, :, None] / W
        m = np.clip((0.012 + 0.75 * k - np.abs(x - 0.59)) / 0.08 + 0.5, 0, 1)
        a = a * (0.16 + 0.84 * np.maximum(m, k * k))
    return to_img(a)


_rng19 = np.random.default_rng(19)
Q_N = 1100
Q_X, Q_Y = _rng19.uniform(0.02 * W, 0.56 * W, Q_N), H * 0.475 + _rng19.normal(0, 0.035 * H, Q_N)
Q_T0, Q_V = _rng19.uniform(0, 0.45, Q_N), _rng19.uniform(150, 430, Q_N)
Q_PH, Q_R = _rng19.uniform(0, 6.28, Q_N), _rng19.uniform(1.5, 4.6, Q_N)


def c19(t, d):
    """The hands come together; at the touch her hand and the bread turn into points of turquoise light that rise,
    and what is left is his hand reaching into the empty air (the twin still, Q19b_empty)."""
    t_touch = T_TOUCH - at("19")
    if t <= t_touch:
        return slowed("19", t * C19_RATE)
    v = t - t_touch
    last = arr(slowed("19", t_touch * C19_RATE))
    empty = lazy("q19b", lambda: arr(view(still("Q19b_empty"), 1.0, 0.5, 0.5)))
    k = ease_io(seg(v, 0.0, 0.55))
    a = last * (1 - k) + empty * k
    layer = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(layer)
    age = v - Q_T0
    for i in np.nonzero(age > 0)[0]:
        g = age[i]
        alpha = min(g / 0.10, 1.0) * max(1 - g / 1.0, 0.0)
        if alpha > 0:
            x, y, r = Q_X[i] + 22 * math.sin(Q_PH[i] + 3.2 * g), Q_Y[i] - Q_V[i] * g - 60 * g * g, Q_R[i]
            dr.ellipse([x - r, y - r, x + r, y + r], fill=int(255 * alpha))
    core = np.asarray(layer, np.float32)[..., None] / 255
    glow = np.asarray(layer.filter(ImageFilter.GaussianBlur(9)), np.float32)[..., None] / 255
    a = a + TURQ_F * 0.22 * math.exp(-v / 0.14) * (np.arange(W, dtype=np.float32)[None, :, None] < 0.62 * W)
    return to_img(a + (TURQ_F * 0.8 + 0.2) * core + TURQ_F * 1.4 * glow)


C19_RATE = 0.62  # the bread reaches his fingertips half a second into the clip, and the touch is 0.8 s into the shot


def slowed(shot, clip_t):
    """Frame of a clip at a time in the clip itself, blended between its two nearest frames."""
    clip_frame(shot, 0.0)
    fr = _clip["frames"]
    pos = min(max(clip_t * FPS, 0.0), len(fr) - 1.0)
    k = int(pos)
    w = pos - k
    if w < 0.02 or k + 1 >= len(fr):
        return Image.fromarray(fr[k])
    return Image.fromarray((fr[k].astype(np.float32) * (1 - w) + fr[k + 1].astype(np.float32) * w + 0.5).astype(np.uint8))


CLIP_FN = {"1": c1, "3": plain("3"), "4": c4, "5": plain("5"), "6": c6, "7": plain("7"), "8": plain("8", 1.0, 1.03, 0.6, 0.45),
           "9": plain("9"), "10": plain("10"), "11": c11, "12": c12, "13": c13, "14": plain("14"), "15": plain("15"),
           "16": plain("16"), "17": plain("17"), "18": plain("18"), "19": c19, "20": plain("20"),
           "21": plain("21", 1.10, 1.16, 0.475, 0.50), "22": plain("22")}

SHOT_FN = {"1": s1, "2a": flash("L2_hara", 0.5, 0.45), "2b": flash("L4_pickup_plate", 0.5, 0.5), "2c": flash("P13_door", 0.55, 0.45),
           "3": s3, "4": s4, "5": s5, "6": s6, "7": s7, "8": s8, "9": s9, "10": s10, "11": s11, "12": s12, "13": s13,
           "14": s14, "15": s15, "16": s16, "17": s17, "18": s18, "19": s19, "20": s20, "21": s21, "22": s22, "end": end_card}
IN_HEADSET = ("4", "6", "11", "12")


# ---- words -----------------------------------------------------------------------------------------------------------
def say_layer(lines, size=66, cy=LOW, stroke=9):
    """Spoken line in Tajawal, as (cropped RGBA image, its box on the frame)."""
    font = ImageFont.truetype(f"{B}/fonts/Tajawal-ExtraBold.ttf", size)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    step = int(size * 1.45)
    y0 = cy - step * (len(lines) - 1) / 2
    for i, text in enumerate(lines):
        assert d.textlength(text, font=font, direction="rtl", language="ar") < 960, text
        d.text((W / 2, y0 + i * step), text, font=font, fill=WHITE, anchor="mm", direction="rtl", language="ar",
               stroke_width=stroke, stroke_fill=(20, 0, 45))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.65))
    sh.paste((12, 0, 30, 255), (0, 8), a)
    full = Image.alpha_composite(sh, layer)
    box = full.getbbox()
    return full.crop(box), box


def small_pill(text, outline=TURQ, size=34):
    return pill(text, size=size, fill=(14, 4, 34), outline=outline)


def overlays():
    says = [(who, *say_layer(lines, cy=cy), a, b) for who, lines, a, b, cy in SAY]
    hooks = [(*caption_layer(lines, **o), a, b) for lines, a, b, o in HOOK]
    tags = {KID: pill("الحفيد", size=38, outline=PURPLE), OLD: pill("الجد", size=38, outline=TURQ)}
    extra = {"title": caption_layer([[("حارة العقر", WHITE)], [("نزوى 1980", TCHIP)]], size=76, cy=930),
             "road": pill("طريق سوق نزوى", size=40, fill=(14, 4, 34), outline=WHITE),
             "slug": small_pill("نسخة أولية للتوقيت والصوت · الصور ثابتة", outline=WHITE, size=30),
             "music": [(a, b, small_pill(text)) for a, b, text in MUSIC_TAGS],
             "temp": {k: small_pill(v, outline=(255, 190, 60)) for k, v in TEMP.items()},
             "brackets": brackets(), "handle": handle_layer()}
    return says, hooks, tags, extra


def shot_at(n):
    for name, (a, b) in CUT.items():
        if a <= n < b:
            return name
    return "end"


def decorate(img, n, ov):
    says, hooks, tags, extra = ov
    t = n / FPS
    name = shot_at(n)
    if name in IN_HEADSET:
        img.alpha_composite(extra["brackets"])
    if name == "4":  # where and when, once we are inside
        im, box = extra["title"]
        k = min(ease_out((t - at("4") - 0.10) / 0.25), ease_out((at("5") - 0.05 - t) / 0.2))
        if k > 0:
            paste_clip(img, faded(im, k), box[0], box[1])
    if name == "12":
        k = min(ease_out((t - at("12") - 0.3) / 0.25), ease_out((at("13") - 0.1 - t) / 0.2))
        if k > 0:
            p = faded(extra["road"], k)
            paste_clip(img, p, (W - p.size[0]) // 2, 150 if CLEAN else 204)
    if name != "end":
        for im, box, a, b in hooks:
            if a <= t < b:
                k = ease_out((t - a) / 0.12) if a > 0.1 else 1.0
                s = 0.86 + 0.14 * k
                im2 = faded(im.resize((max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s))), Image.LANCZOS), k) if k < 1 else im
                paste_clip(img, im2, int((box[0] + box[2]) / 2 - im2.size[0] / 2), int((box[1] + box[3]) / 2 - im2.size[1] / 2))
                tag = faded(tags[KID], k)
                paste_clip(img, tag, (W - tag.size[0]) // 2, box[1] - tag.size[1] - 16)
        for who, im, box, a, b in says:
            if a <= t < b:
                k = min(ease_out((t - a) / 0.12), ease_out((b - t) / 0.10))
                paste_clip(img, faded(im, k), box[0], int(box[1] + 10 * (1 - k)))
                tag = faded(tags[who], k)
                paste_clip(img, tag, (W - tag.size[0]) // 2, box[1] - tag.size[1] - 12)
    img.alpha_composite(extra["handle"])
    if not CLEAN:
        s = extra["slug"]
        paste_clip(img, s, (W - s.size[0]) // 2, 136)
        if name in extra["temp"] and not has_clip(name):
            p = extra["temp"][name]
            paste_clip(img, p, W - p.size[0] - 40, 214)
        for a, b, p in extra["music"]:
            if a <= t < b:
                paste_clip(img, p, (W - p.size[0]) // 2, 1790)
    return img


_grain = None


def grain(img, n):
    """A little film grain, so the stills sit together and do not look frozen."""
    global _grain
    if _grain is None:
        r = np.random.default_rng(5)
        _grain = [r.normal(0, 2.6, (H, W, 1)).astype(np.float32) for _ in range(7)]
    a = np.asarray(img, np.float32) + _grain[n % 7]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def frame(n, ov):
    name = shot_at(n)
    f0, f1 = CUT[name]

    def shot_image(which, t, d):
        if which in CLIP_FN and has_clip(which):
            return CLIP_FN[which](t, d)
        return SHOT_FN[which](t, d)

    base = shot_image(name, (n - f0) / FPS, (f1 - f0) / FPS)
    if name == "end":  # the last shot dissolves into the card
        k = ease_io(seg(n - f0, 0, 9))
        if k < 1:
            p0, p1 = CUT["22"]
            base = Image.blend(shot_image("22", (n - p0) / FPS, (p1 - p0) / FPS), base, k)
    elif not (name in CLIP_FN and has_clip(name)):
        base = grain(base, n)   # the stills get a little grain; the clips have their own
    return decorate(base.convert("RGBA"), n, ov).convert("RGB")


# ======================================================================================================================
# sound
# ======================================================================================================================
def db(v):
    return 10 ** (v / 20)


def load(path, start=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}"] + (["-t", f"{dur:.3f}"] if dur else []) + ["-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)


def rms(x):
    return float(np.sqrt((x ** 2).mean()) + 1e-12)


def fade(x, a=0.02, b=0.02):
    x = x.copy()
    na, nb = min(max(int(a * SR), 1), len(x)), min(max(int(b * SR), 1), len(x))
    x[:na] *= np.linspace(0, 1, na)[:, None]
    x[-nb:] *= np.linspace(1, 0, nb)[:, None]
    return x


def filt(x, lo=None, hi=None):
    """Zero-phase band limit: lo = high-pass corner, hi = low-pass corner (Hz)."""
    if lo and hi:
        sos = butter(2, [lo, hi], btype="band", fs=SR, output="sos")
    elif hi:
        sos = butter(2, hi, btype="low", fs=SR, output="sos")
    else:
        sos = butter(2, lo, btype="high", fs=SR, output="sos")
    return sosfiltfilt(sos, x, axis=0)


def limit(x, thr=0.7, win=0.040):
    """Look-ahead peak limiter: the gain dips smoothly around a peak. The window is several pitch periods of the
    grandfather's low voice: with 10 ms the gain followed each period, and a check then heard «الغنب» for «الغنم»."""
    k = int(win * SR) | 1
    g = np.minimum(1.0, thr / np.maximum(np.abs(x).max(axis=1), 1e-9))
    g = uniform_filter1d(minimum_filter1d(g, size=k, mode="nearest"), size=k, mode="nearest")
    return x * g[:, None]


def active_level(x):
    """RMS over the 20 ms frames that carry speech (within 25 dB of the loudest frame)."""
    m = x.mean(1)
    fr = m[: len(m) // 960 * 960].reshape(-1, 960)
    e = np.sqrt((fr ** 2).mean(1)) + 1e-12
    return float(np.sqrt((e[e > e.max() * db(-25)] ** 2).mean()))


def ring(x, length=2.4, decay=0.55, seed=1):
    """What a hall would hold of a sound after it stops: `x` smeared by a decaying burst of noise."""
    r = np.random.default_rng(seed)
    n = int(length * SR)
    t = np.arange(n) / SR
    out = []
    for ch in range(2):
        ir = filt((r.standard_normal(n) * np.exp(-t / decay))[:, None], 180, 3200)[:, 0]
        out.append(fftconvolve(x[:, ch], ir)[: len(x) + n])
    y = np.stack(out, 1)
    return y / (np.abs(y).max() + 1e-9)


def envelope(n, spans, ramp=0.05):
    """1 inside the (from, to) spans, 0 outside, with short linear ramps."""
    t = np.arange(n) / SR
    g = np.zeros(n)
    for a, b in spans:
        g = np.maximum(g, np.clip((t - a) / ramp, 0, 1) * np.clip((b - t) / ramp, 0, 1))
    return g[:, None]


SPEECH = db(-18.5)  # every line is brought to this level on its spoken parts


def mix_audio(path, total):
    n = int(round(total * SR))

    def place(buf, x, t):
        i = int(round(t * SR))
        if i < 0:
            x, i = x[-i:], 0
        m = min(len(x), n - i)
        if m > 0:
            buf[i:i + m] += x[:m]

    def new():
        return np.zeros((n, 2))

    # ---- voice: one gain per recording, so two cuts of one take stay matched
    gains = {}
    voice = new()
    for who, src, a, b, t0, trim in LINES:
        if src not in gains:
            gains[src] = SPEECH / active_level(load(f"{WORK}/voice/{src}"))
        voice_part = fade(load(f"{WORK}/voice/{src}", a, b - a) * gains[src] * db(trim), 0.015, 0.05)
        place(voice, limit(voice_part), t0)

    # ---- music ------------------------------------------------------------------------------------------------------
    music = new()
    theme = load(f"{WORK}/music/theme_v2.mp3")
    theme = theme / rms(theme)                       # unit RMS: its levels below are relative to the speech level
    drone_src = load(f"{WORK}/music/m3_hara.mp3")
    low = load(f"{WORK}/music/m5_jokha.mp3", 0.0, 5.2)
    low = fade(low / np.abs(low).max(), 0.004, 1.2)   # one long low D, peak 1.0

    def pad(length):
        """The string drone, made as long as needed by folding its steady part over itself."""
        first = drone_src[int(0.55 * SR): int(6.0 * SR)]
        loop = drone_src[int(2.0 * SR): int(6.0 * SR)]
        x, c = first.copy(), int(1.0 * SR)
        while len(x) < length * SR:
            a_, b_ = np.sqrt(np.linspace(1, 0, c))[:, None], np.sqrt(np.linspace(0, 1, c))[:, None]
            x = np.concatenate([x[:-c], x[-c:] * a_ + loop[:c] * b_, loop[c:]])
        x = x[: int(length * SR)]
        return x / rms(x)

    # 1. the hook: one deep note under the tear, then a strum on each of the three flashes
    place(music, low * db(-9), 0.0)
    for (a, b), f0 in zip(((6.20, 6.76), (6.74, 7.27), (7.25, 7.95)), (CUT["2a"][0], CUT["2b"][0], CUT["2c"][0])):
        hit = fade(drone_src[int(a * SR): int(b * SR)], 0.012, 0.18)
        place(music, hit / np.abs(hit).max() * db(-11), f0 / FPS - 0.06)
    # 2. headset and the «جير»: a still string drone while he looks around, then a light plucked oud once the
    # grandson starts teaching. Its first note (0.31 s into the file) falls on the cut to the thumb, its eighth on
    # the cut into the headset, and it stops before «سهل!» so that the word lands in the clear.
    t2 = at("3")
    jeer_path = f"{WORK}/music/jeer_v2.mp3"
    if os.path.exists(jeer_path):
        place(music, fade(pad(at("5") - t2 + 0.3), 1.3, 0.9) * SPEECH * db(-16), t2)
        jeer = load(jeer_path)
        jeer = jeer / rms(jeer)
        j0, j1 = at("5") - 0.31, 13.36
        part = fade(jeer[: int((j1 - j0) * SR)], 0.004, 0.10) * SPEECH * db(-13.0)
        place(music, part, j0)
        place(music, fade(ring(part[-int(0.5 * SR):], 1.2, 0.30), 0.2, 0.7) * SPEECH * db(-9), j1 - 0.5)
    else:  # the animatic's stand-in: the drone alone
        place(music, fade(pad(at("8") - t2 - 0.15), 1.3, 0.5) * SPEECH * db(-16), t2)
    # 3. the hara: the oud theme enters with the young face. Its first note sits 0.03 s into the file.
    t3 = at("8") - 0.03
    cut3 = at("13") - t3 - 0.01                       # the door cut falls just before the theme's 13th beat
    part = fade(theme[: int(cut3 * SR)], 0.004, 0.22) * SPEECH * db(-6.5)
    place(music, part, t3)
    hold = ring(part[-int(0.7 * SR):], 2.6, 0.6)      # ... and its last chord hangs in the dark hallway
    place(music, fade(hold, 0.3, 1.6) * SPEECH * db(-4), t3 + cut3 - 0.7)
    # 4. the house: one long low note as the door opens
    place(music, low * db(-13), at("13") + 0.02)
    # 5. Jokha: the theme comes back when her humming stops, and climbs until the hands meet
    # The strong pluck at 15.20 s of the file is the touch; the beats before it fall on the cuts to shots 17 and 18.
    t5 = 31.61
    a5 = 15.20 - (T_TOUCH - t5)
    t5_len = T_CUT - t5
    part = theme[int(a5 * SR): int((a5 + t5_len) * SR)].copy()
    climb = np.interp(np.arange(len(part)) / SR, [0.0, 2.6, t5_len - 1.1, t5_len], [-16.0, -11.0, -5.5, -4.0])
    part = fade(part * db(climb)[:, None] * SPEECH, 0.20, 0.004)  # no fade at its end: it is cut
    place(music, part, t5)
    # 6. the present: the low note again on the tear, and the drone under the last words
    t6 = at("21")
    place(music, low * db(-11), t6)
    place(music, fade(pad(at("end") - t6 - 0.2), 1.8, 0.8) * SPEECH * db(-17), t6 + 0.5)
    # 7. the end card: the theme's first phrase comes back; with the closing cue present, its third beat is
    # answered by a full final chord on D that rings to the last frame
    t7 = at("end") - 0.03
    end_path = f"{WORK}/music/ending_v2.mp3"
    if os.path.exists(end_path):
        t_chord = t7 + 1.70                               # the theme's third beat
        part = fade(theme[: int((t_chord - t7 + 0.12) * SR)], 0.004, 0.30) * SPEECH * db(-5.5)
        place(music, part, t7)
        chord = load(end_path, 7.33, 4.6)                 # its final chord starts 7.38 s into the file
        chord = fade(chord / np.abs(chord).max(), 0.004, 0.5)
        chord = chord[: int((END - (t_chord - 0.05)) * SR)]
        place(music, fade(chord, 0.004, 0.55) * db(-8.5), t_chord - 0.05)
    else:
        part = fade(theme[: int((END - t7) * SR)], 0.004, 1.0) * SPEECH * db(-5.5)
        place(music, part, t7)

    # ---- ambience ---------------------------------------------------------------------------------------------------
    amb = new()
    a0, a1 = at("4"), at("14")
    bed = new()
    for src, start, level in (("dawn", 150.0, -31.0), ("falaj", 20.0, -35.0), ("palms", 62.0, -37.0)):
        x = load(f"{WORK}/sfx/{src}.mp3", start, a1 - a0)
        place(bed, x / rms(x) * db(level), a0)
    inside = [(at("4"), at("5")), (at("6"), at("7")), (at("8"), at("13"))]      # the hara as he hears it
    leak = [(at("5"), at("6")), (at("7"), at("8"))]                              # thin, from the headset's speakers
    amb += bed * envelope(n, inside, 0.04)
    amb += filt(bed, 700, 3200) * db(-9) * envelope(n, leak, 0.04)
    amb += filt(bed, hi=800) * db(-5) * envelope(n, [(at("13"), at("13") + 1.2)], 0.04) * \
        np.interp(np.arange(n) / SR, [at("13"), at("13") + 1.2], [1, 0])[:, None]   # the street closes behind him
    x = load(f"{WORK}/sfx/falaj.mp3", 50.0, at("10") - at("9") + 0.3)                 # the falaj close by
    place(amb, fade(x / rms(x) * db(-26), 0.12, 0.3), at("9") - 0.05)
    # the kitchen fire: far from the hallway, close in the kitchen, then a memory that fades
    f0, f1 = at("13") + 1.9, 39.5
    x = load(f"{WORK}/sfx/fire.mp3", 12.0, f1 - f0)
    fire = new()
    place(fire, limit(x / rms(x), thr=4.0), f0)      # the loudest pops are held 12 dB over the crackle
    amb += filt(fire, hi=1100) * db(-41) * envelope(n, [(f0, at("14"))], 0.25)
    amb += fire * db(-30) * envelope(n, [(at("14"), T_CUT)], 0.06)
    amb += filt(fire, hi=900) * db(-36) * envelope(n, [(T_CUT, f1)], 0.05) * \
        np.interp(np.arange(n) / SR, [T_CUT, f1], [1, 0])[:, None]
    # Jokha humming: muffled from the hallway, clear in the kitchen, and it stops when she sees him
    h0 = at("13") + 2.03
    x = load(f"{WORK}/sfx/humming.mp3", 0.10, 31.50 - h0)
    hum = new()
    place(hum, fade(x / rms(x), 0.08, 0.28), h0)
    amb += filt(hum, hi=1400) * db(-36) * envelope(n, [(h0, at("14"))], 0.05)
    amb += hum * db(-27) * envelope(n, [(at("14"), 31.6)], 0.05)

    # ---- effects ----------------------------------------------------------------------------------------------------
    fx = new()

    def hit(src, a, b, t0, peak, fi=0.01, fo=0.12, lo=None, hi=None):
        x = load(f"{WORK}/sfx/{src}.mp3", a, b - a)
        if lo or hi:
            x = filt(x, lo, hi)
        place(fx, fade(x / (np.abs(x).max() + 1e-9) * db(peak), fi, fo), t0)

    hit("thump", 0.0, 1.6, 0.0, -13, 0.002, 0.8)                         # with the first frame
    hit("vr_chime", 0.0, 1.3, 4.15, -24, 0.01, 0.3)                      # the headset wakes, then we are inside
    tick = np.random.default_rng(3).standard_normal(int(0.012 * SR)) * np.exp(-np.arange(int(0.012 * SR)) / (0.003 * SR))
    place(fx, np.stack([tick, tick], 1) * db(-27), at("5") + 1.12)       # the stick clicks forward on «قدّم»
    hit("ui_beep", 0.0, 0.5, at("6") + 0.02, -31, 0.005, 0.12)           # one soft tone as the first arrow lights:
    # the right and left arrows have none, because a tone on «ويسار» made a check hear «ويصار»
    hit("footsteps", 0.0, 2.3, at("6") + 0.08, -27, 0.05, 0.3)           # he "walks" inside the headset
    hit("footsteps", 10.0, 11.75, at("9"), -22, 0.03, 0.2)               # sandals beside the falaj
    hit("children", 0.10, 2.05, at("10") - 0.20, -19, 0.2, 0.45)
    hit("chicken", 0.15, 0.95, at("10") + 0.22, -24)
    hit("goats", 4.15, 5.05, at("11") - 0.45, -28, 0.03, 0.15)           # heard before the pickup is seen
    x = load(f"{WORK}/sfx/pickup_rattle.mp3", 10.4, 5.6)                 # its own rise and fall is the pass-by
    place(fx, fade(x / np.abs(x).max() * db(-20), 0.9, 1.3), at("12") - 2.6)
    hit("horn", 0.0, 0.36, at("11") + 0.07, -21, 0.004, 0.08)
    hit("goats", 1.95, 2.95, 23.86, -22, 0.03, 0.15)                     # a goat answers after his line
    hit("door", 0.10, 1.65, at("13") + 0.01, -17, 0.01, 0.4)
    hit("bangles", 6.30, 7.40, at("13") + 2.10, -31, 0.01, 0.2, hi=2500)  # her bangles, from the next room
    hit("bangles", 0.00, 0.85, 28.30, -26, 0.01, 0.2)
    hit("sizzle", 2.20, 3.45, at("15") - 0.02, -22, 0.02, 0.25)
    hit("bangles", 6.30, 7.40, at("16") + 0.05, -24, 0.01, 0.2)          # she turns
    hit("shimmer", 0.10, 3.10, T_TOUCH - 0.02, -21, 0.01, 1.2)           # she turns to light

    # ---- the words stay 15 dB above everything else ---------------------------------------------------------------
    bg = music + amb + fx
    m = np.abs(voice).max(axis=1)
    hop = SR // 100
    lev = np.sqrt((voice[: n // hop * hop].mean(1).reshape(-1, hop) ** 2).mean(1))
    on = lev > db(-45)
    spans, start = [], None
    for i, v in enumerate(np.append(on, False)):
        if v and start is None:
            start = i
        if not v and start is not None:
            if spans and start - spans[-1][1] < 14:      # pauses under 0.14 s are part of the phrase
                spans[-1][1] = i
            else:
                spans.append([start, i])
            start = None
    g = np.ones(n)
    t = np.arange(n) / SR
    report = []
    for a, b in spans:
        ta, tb = a * hop / SR, b * hop / SR
        if tb - ta < 0.12:
            continue
        ia, ib = int(ta * SR), int(tb * SR)
        sp = rms(voice[ia:ib][m[ia:ib] > db(-45)]) if (m[ia:ib] > db(-45)).any() else 1e-9
        under = rms(bg[ia:ib])
        need = 20 * np.log10(under / sp) + 15.0
        dip = db(-min(max(need, 0.0), 18.0))
        pre = 0.0 if ta < 0.5 else 0.16                  # the opening thump is let through before the first word
        g = np.minimum(g, 1 - (1 - dip) * np.clip((t - (ta - pre)) / 0.12, 0, 1) * np.clip(((tb + 0.20) - t) / 0.16, 0, 1))
        report.append((ta, tb, 20 * np.log10(sp), 20 * np.log10(under), max(need, 0.0)))
    for buf in (music, amb, fx):
        buf *= g[:, None]
    print("speech spans: from-to s | speech dBFS | everything else before ducking | ducked by dB")
    for ta, tb, sp, under, need in report:
        print(f"  {ta:6.2f}-{tb:6.2f} | {sp:6.1f} | {under:6.1f} | {need:4.1f}")

    stems = {"voice": voice, "music": music, "ambience": amb, "effects": fx}
    for k, v in stems.items():
        print(f"stem {k:9s} mean {20 * np.log10(rms(v)):6.1f} dBFS, peak {20 * np.log10(np.abs(v).max() + 1e-9):6.1f}")
    out = np.clip(sum(stems[k] for k in PARTS), -1, 1)
    write_wav(path, out)
    if STEMS:
        os.makedirs(STEMS, exist_ok=True)
        for k, v in stems.items():
            write_wav(f"{STEMS}/{k}.wav", np.clip(v, -1, 1))


def write_wav(path, x):
    w = wave.open(path, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((x * 32767).astype("<i2").tobytes())
    w.close()


def master(path, target=-14.2, ceiling=0.84):
    """Bring the finished mix to the target loudness with one fixed gain and a peak ceiling of -1.5 dBFS."""
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True).stderr.decode()
    before = float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", log)[-1])
    w = wave.open(path, "rb")
    x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32).reshape(-1, 2) / 32767.0
    w.close()
    y = limit(x * 10 ** ((target - before) / 20), thr=ceiling)
    write_wav(path, np.clip(y, -1, 1))
    print("master: mix was %.1f LUFS, gain %+.1f dB, peak now %.2f" % (before, target - before, float(np.abs(y).max())), flush=True)


def make_cover(path, handle):
    """Cover: the tear under the headset, and the name of the place. The words sit inside the middle 4:5 of the
    picture, which is what the profile grid shows."""
    a = arr(view(still("L5b_tear"), 1.0, 0.5, 0.5))
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    a = a * (1 - 0.45 * np.clip((y - 0.52) / 0.33, 0, 1))        # darker toward the bottom, behind the words
    img = to_img(a).convert("RGBA")
    cap, box = caption_layer([[("رجّعنا جدي", WHITE)], [("حارة العقر", TCHIP)]], size=124, cy=1290)
    img.alpha_composite(cap, (box[0], box[1]))
    tag = pill("نزوى 1980", size=50, fill=(14, 4, 34), outline=WHITE)
    paste_clip(img, tag, (W - tag.size[0]) // 2, box[3] + 34)
    img.alpha_composite(handle)
    img.convert("RGB").save(path, quality=93)
    print("cover written:", path)


def main():
    ov = overlays()
    if COVER:
        make_cover(COVER, ov[3]["handle"])
    if ONLY is not None:
        os.makedirs(f"{WORK}/check", exist_ok=True)
        for n in ONLY:
            frame(n, ov).save(f"{WORK}/check/an_{n:04d}.jpg", quality=88)
        print("frames written:", ONLY)
        return
    mixp = OUT + ".mix.wav"
    mix_audio(mixp, END)
    master(mixp)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", mixp, "-map", "0:v", "-map", "1:a", "-t", f"{END:.4f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                            "-maxrate", "10M", "-bufsize", "20M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                            "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    for n in range(TOTAL_FRAMES):
        enc.stdin.write(frame(n, ov).tobytes())
    enc.stdin.close()
    assert enc.wait() == 0
    print("ok", OUT, TOTAL_FRAMES, "frames", round(END, 3), "s")


if __name__ == "__main__":
    main()
