"""Reel «إصبعك بيتحرك!» (one image per eye, workshop design).

Talking shots (A1..A5) are audio-driven clips made with the approved lip method (CHARACTER.md section 8); the three
explainer scenes (finger seen through the viewer's eyes, the two views merging, a view in each lens) are drawn here.

usage: python3 -I reel_finger.py WORK_DIR OUT_MP4 [--draft]
  WORK_DIR/img/    W1_hook.png W2_eye.png W3_lenses.png W4_wearing.png P1_plate.png P2_hand.png PROP_headset.png
  WORK_DIR/voice/  voice_main.wav   (the ElevenLabs take; it is the only audio in the result)
  WORK_DIR/clips/  A1.mp4 .. A5.mp4 (each made from LEAD seconds of silence + its voice segment)
  --draft          talking shots are replaced by their still pose (layout check only, never delivered as the video)
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.dirname(os.path.dirname(HERE))  # bviro/
WORK, OUT = sys.argv[1], sys.argv[2]
DRAFT = "--draft" in sys.argv[3:]
W, H, FPS = 1080, 1920, 30
PURPLE, TURQ, DARK, WHITE = (127, 2, 254), (0, 205, 200), (43, 1, 87), (255, 255, 255)
CHIP, TCHIP = "chip", "tchip"

# ---- timeline, in the voice file's own time ------------------------------------------------------------------------
PRE = 0.10  # seconds of picture before the first word
HOLD = 0.60  # seconds held after the last word
LEAD = 0.25  # silence in front of each talking clip's audio
CUTS = [0.0, 2.39, 7.52, 9.34, 12.09, 14.54, 16.10, 18.28, 19.84]  # every cut sits in the middle of a pause
SEGS = [("A1", "talk", "W1_hook"), ("B1", "pov", None), ("A2", "talk", "W2_eye"), ("B2", "merge", None),
        ("A3", "talk", "W3_lenses"), ("B3", "lens", None), ("A4", "talk", "W4_wearing"), ("A5", "talk", "W1_hook")]
TOTAL = PRE + CUTS[-1] + HOLD
NFRAMES = int(round(TOTAL * FPS))

# captions: name, lines, start, end (voice time), options
CARDS = [
    ("h1", [[("إصبعك بيتحرك..", WHITE)], [("وانت ما حركته!", CHIP)]], -PRE, 2.39, {}),
    ("p1", [[("مد إصبعك", WHITE)], [("قدام وجهك", TCHIP)]], 2.46, 3.95, {}),
    ("p2", [[("غمّض عين..", WHITE)]], 4.20, 5.06, {}),
    ("p3", [[("وبعدين الثانية", WHITE)]], 5.15, 6.12, {}),
    ("p4", [[("شفت؟", TURQ)]], 6.27, 6.80, {"size": 120}),
    ("p5", [[("تحرك!", CHIP)]], 6.90, 7.52, {"size": 120}),
    ("e1", [[("كل عين تشوفه", WHITE)], [("من مكان", TCHIP)]], 7.61, 9.34, {}),
    ("m1", [[("مخك يدمج", WHITE)], [("الصورتين", CHIP)]], 9.41, 10.85, {}),
    ("m2", [[("ويعرف", WHITE), ("المسافة", TCHIP)]], 10.90, 12.09, {}),
    ("v1", [[("نظارة الـVR", WHITE), ("نفس الحيلة", CHIP)]], 12.32, 14.54, {"size": 78, "cy": 1492}),
    ("v2", [[("تعطي كل عين", WHITE)], [("صورتها", TCHIP)]], 14.68, 16.10, {}),
    ("f1", [[("عشان كذا", WHITE)], [("تحس الشي قدامك", CHIP)]], 16.23, 18.28, {}),
    ("cta", [[("أرسله لواحد", WHITE)], [("يجرّبها", TCHIP)]], 18.40, CUTS[-1] + HOLD, {}),
]

# ---- explainer geometry (measured on the generated stills, in 1080x1920 units) ------------------------------------
DALLAH = (531.0, 705.0)  # centre of the dallah in the background plate
POV_ZOOM = 1.8  # the plate is shown this much larger
DALLAH_ON_SCREEN = (540.0, 760.0)
TIP = (497.0, 240.0)  # fingertip in the hand cut-out
HAND_ZOOM = 1.35
TIP_ON_SCREEN_Y = 560.0
SHIFT = 165.0  # how far the finger sits to each side when one eye is closed
# headset prop (2048x1360): lens centres and glass radius
LENS_L, LENS_R, LENS_RAD = (735.0, 827.0), (1308.0, 827.0), 192.0
PROP_SCALE = 0.732


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def cairo(size, weight=900):
    f = ImageFont.truetype(f"{B}/fonts/Cairo-VF.ttf", size)
    f.set_variation_by_axes([weight, 0])
    return f


def tajawal(size):
    return ImageFont.truetype(f"{B}/fonts/Tajawal-Bold.ttf", size)


def tw(d, t, font):
    return d.textlength(t, font=font, direction="rtl", language="ar")


def draw_line(img, segs, font, cy, stroke=10):
    d = ImageDraw.Draw(img)
    gap, pad = int(font.size * 0.26), int(font.size * 0.20)
    widths = [tw(d, t, font) + (2 * pad if c in (CHIP, TCHIP) else 0) for t, c in segs]
    total = sum(widths) + gap * (len(segs) - 1)
    assert total < 900, (segs, total)
    x = W / 2 + total / 2
    for (text, col), w in zip(segs, widths):
        x -= w
        if col in (CHIP, TCHIP):
            h = int(font.size * 1.18)
            d.rounded_rectangle([x, cy - h / 2 + 4, x + w, cy + h / 2 + 4], radius=int(h * 0.28), fill=PURPLE if col == CHIP else TURQ)
            d.text((x + pad, cy), text, font=font, fill=WHITE if col == CHIP else DARK, anchor="lm", direction="rtl", language="ar")
        else:
            d.text((x, cy), text, font=font, fill=col, anchor="lm", direction="rtl", language="ar", stroke_width=stroke, stroke_fill=DARK)
        x -= gap


def caption_layer(lines, size=92, cy=1465, lead=1.36):
    font = cairo(size)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    step = int(size * lead)
    y0 = cy - step * (len(lines) - 1) / 2
    for i, segs in enumerate(lines):
        draw_line(layer, segs, font, y0 + i * step)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.6))
    sh.paste((20, 0, 45, 255), (0, 10), a)
    full = Image.alpha_composite(sh, layer)
    box = full.getbbox()
    return full.crop(box), box


def handle_layer():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sym = Image.open(f"{B}/logo/bviro_sym_white.png").convert("RGBA")
    sh = 50
    sym = sym.resize((int(sym.size[0] * sh / sym.size[1]), sh), Image.LANCZOS)
    f = tajawal(44)
    txt = "@bviro.1"
    t = d.textlength(txt, font=f)
    pw, ph = int(sym.size[0] + 16 + t + 56), 80
    x, y = (W - pw) // 2, 44
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=(*DARK, 215))
    layer.alpha_composite(sym, (x + 24, y + (ph - sh) // 2))
    d.text((x + 24 + sym.size[0] + 14, y + ph / 2 + 1), txt, font=f, fill=WHITE, anchor="lm")
    return layer


# ---- eye icon ------------------------------------------------------------------------------------------------------
def eye_icon(w, openness, active):
    """Almond eye, w pixels wide. openness 1 = open, 0 = closed. active adds the turquoise ring."""
    s = 3
    cw, ch = w * s, int(w * 0.72) * s
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = cw / 2, ch / 2
    half = cw * 0.44
    lift = ch * 0.36 * max(openness, 0.0)
    n = 40
    top = [(cx - half + 2 * half * i / n, cy - lift * math.sin(math.pi * i / n)) for i in range(n + 1)]
    bot = [(cx + half - 2 * half * i / n, cy + lift * 0.85 * math.sin(math.pi * i / n)) for i in range(n + 1)]
    line = int(5 * s * w / 150)
    if openness > 0.25:
        mask = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(mask).polygon(top + bot, fill=255)
        inner = Image.new("RGBA", (cw, ch), (255, 255, 255, 255))
        di = ImageDraw.Draw(inner)
        r = ch * 0.30
        di.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(122, 74, 30, 255))
        di.ellipse([cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy + r * 0.5], fill=(25, 12, 8, 255))
        di.ellipse([cx + r * 0.15, cy - r * 0.62, cx + r * 0.55, cy - r * 0.22], fill=(255, 255, 255, 255))
        im.paste(inner, (0, 0), mask)
        d.line(top + bot + [top[0]], fill=(*DARK, 255), width=line, joint="curve")
    else:
        arc = [(cx - half + 2 * half * i / n, cy + ch * 0.10 * math.sin(math.pi * i / n)) for i in range(n + 1)]
        d.line(arc, fill=(*WHITE, 255), width=line + s, joint="curve")
        for k in (0.25, 0.5, 0.75):
            x = cx - half + 2 * half * k
            y = cy + ch * 0.10 * math.sin(math.pi * k)
            d.line([(x, y), (x + (k - 0.5) * ch * 0.25, y + ch * 0.17)], fill=(*WHITE, 255), width=line)
    im = im.resize((w, int(w * 0.72)), Image.LANCZOS)
    if active:
        glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
        a = im.getchannel("A").filter(ImageFilter.GaussianBlur(7)).point(lambda v: min(255, int(v * 1.6)))
        glow.paste((*TURQ, 255), (0, 0), a)
        im = Image.alpha_composite(glow, im)
    return im


def eyes_hud(left_open, right_open, alpha=1.0, y=206, labels=True):
    """Pill with the viewer's two eyes (the viewer's left eye is on the left of the screen)."""
    pw, ph = 520, 196 if labels else 150
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0 = (W - pw) // 2
    d.rounded_rectangle([x0, y, x0 + pw, y + ph], radius=46, fill=(*DARK, 225), outline=(*WHITE, 70), width=3)
    f = tajawal(34)
    for k, (op, name) in enumerate(((left_open, "يسار"), (right_open, "يمين"))):
        cx = x0 + pw // 4 + k * pw // 2
        ic = eye_icon(170, op, op > 0.5 and (left_open < 0.5 or right_open < 0.5))
        layer.alpha_composite(ic, (cx - ic.size[0] // 2, y + 16))
        if labels:
            d.text((cx, y + ph - 34), name, font=f, fill=WHITE if op > 0.5 else (190, 170, 220), anchor="mm", direction="rtl", language="ar")
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    return layer


# ---- assets --------------------------------------------------------------------------------------------------------
def load(name, mode="RGB"):
    return Image.open(f"{WORK}/img/{name}.png").convert(mode)


PLATE = load("P1_plate")
KP = PLATE.size[0] / W  # native pixels per 1080-unit
_hand = load("P2_hand", "RGBA")
HAND = _hand.resize((int(W * HAND_ZOOM), int(H * HAND_ZOOM)), Image.LANCZOS)
PROP = load("PROP_headset", "RGBA")


def pov(dx=0.0, rise=0.0, plate_dx=0.0, zoom=1.0, ghost=None):
    """What the viewer sees: the far shelf with the dallah, and their own finger in front of it."""
    s = POV_ZOOM * zoom
    x0 = ((0 - DALLAH_ON_SCREEN[0] - plate_dx) / s + DALLAH[0]) * KP
    x1 = ((W - DALLAH_ON_SCREEN[0] - plate_dx) / s + DALLAH[0]) * KP
    y0 = ((0 - DALLAH_ON_SCREEN[1]) / s + DALLAH[1]) * KP
    y1 = ((H - DALLAH_ON_SCREEN[1]) / s + DALLAH[1]) * KP
    fr = PLATE.resize((W, H), Image.BICUBIC, box=(x0, y0, x1, y1)).convert("RGBA")
    ox, oy = DALLAH_ON_SCREEN[0] - TIP[0] * HAND_ZOOM, TIP_ON_SCREEN_Y - TIP[1] * HAND_ZOOM
    if ghost:
        gx, ga = ghost
        g = HAND.copy()
        g.putalpha(g.getchannel("A").point(lambda v: int(v * ga)))
        paste_clip(fr, g, int(round(ox + gx)), int(round(oy)))
    paste_clip(fr, HAND, int(round(ox + dx)), int(round(oy + rise)))
    return fr.convert("RGB")


def paste_clip(dst, src, x, y):
    """alpha_composite that accepts negative offsets."""
    sx, sy = max(0, -x), max(0, -y)
    dx, dy = max(0, x), max(0, y)
    w, h = min(src.size[0] - sx, dst.size[0] - dx), min(src.size[1] - sy, dst.size[1] - dy)
    if w > 0 and h > 0:
        dst.alpha_composite(src, (dx, dy), (sx, sy, sx + w, sy + h))


def brand_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.zeros((H, W, 3), np.float32)
    t = (yy / H)[..., None]
    base += np.array([26, 2, 58], np.float32) * (1 - t) + np.array([52, 4, 108], np.float32) * t
    g1 = np.exp(-(((xx - 540) / 620) ** 2 + ((yy - 760) / 700) ** 2))[..., None]
    base += g1 * np.array([70, 8, 150], np.float32) * 0.55
    g2 = np.exp(-(((xx - 980) / 420) ** 2 + ((yy - 1750) / 420) ** 2))[..., None]
    base += g2 * np.array([0, 150, 150], np.float32) * 0.30
    rng = np.random.default_rng(7)
    base += rng.normal(0, 1.2, (H, W, 1)).astype(np.float32)
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


BG = brand_bg()


def rounded_mask(w, h, r):
    m = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], radius=r * 2, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def card(view, w, h, alpha=1.0, border=6, radius=40):
    """A rounded picture card with a white border and a soft shadow, as an RGBA tile with 40px margin."""
    m = 40
    tile = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    sh = Image.new("L", tile.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle([m, m + 12, m + w, m + h + 12], radius=radius, fill=150)
    tile.paste((10, 0, 30, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(16)))
    frame = Image.new("RGBA", (w, h), (*WHITE, 255))
    inner = view.resize((w - 2 * border, h - 2 * border), Image.LANCZOS).convert("RGBA")
    frame.paste(inner, (border, border), rounded_mask(w - 2 * border, h - 2 * border, radius - border))
    tile.paste(frame, (m, m), rounded_mask(w, h, radius))
    if alpha < 1:
        tile.putalpha(tile.getchannel("A").point(lambda v: int(v * alpha)))
    return tile


VIEW_BOX = (540 - 330, 760 - 340, 540 + 330, 760 + 558)  # the part of the POV picture shown on cards (660x900)


def eye_tag(name, openness=1.0):
    f = tajawal(40)
    ic = eye_icon(96, openness, False)
    d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    t = int(d0.textlength(name, font=f, direction="rtl", language="ar"))
    w, h = ic.size[0] + t + 60, 84
    tag = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(tag)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(*DARK, 235), outline=(*TURQ, 255), width=3)
    tag.alpha_composite(ic, (w - ic.size[0] - 18, (h - ic.size[1]) // 2))
    d.text((22, h / 2 + 2), name, font=f, fill=WHITE, anchor="lm", direction="rtl", language="ar")
    return tag


# ---- scenes --------------------------------------------------------------------------------------------------------
# finger side per eye state: left eye closed -> seen by the right eye -> the finger sits to the LEFT of the dallah
POV_EVENTS = [(4.25, -1), (5.30, +1), (6.30, -1), (6.62, +1), (6.93, -1), (7.24, +1)]  # (voice time, side)


def scene_pov(t):
    rise = (1 - ease_out((t - 2.46) / 0.55)) * 1500 if t < 3.2 else 0.0
    side, prev, since = 0, 0, 9.0
    for te, sd in POV_EVENTS:
        if t >= te:
            prev, side, since = side, sd, t - te
    k = [0.40, 0.85, 1.06, 1.0][min(int(since * FPS), 3)] if side or prev else 1.0
    dx = (prev + (side - prev) * k) * SHIFT
    ghost = (prev * SHIFT, 0.32 * (1 - since / 0.17)) if since < 0.17 and (side or prev) else None
    zoom = 1.0 + 0.035 * ease_io((t - CUTS[1]) / (CUTS[2] - CUTS[1]))
    fr = pov(dx=dx, rise=rise, plate_dx=-dx * 0.07, zoom=zoom, ghost=ghost).convert("RGBA")
    a = ease_out((t - 3.55) / 0.3)
    if a > 0:
        lo = 0.0 if side == -1 else 1.0
        ro = 0.0 if side == +1 else 1.0
        fr.alpha_composite(eyes_hud(lo, ro, alpha=a))
    return fr.convert("RGB")


def scene_merge(t):
    u = t - CUTS[3]
    fr = BG.copy().convert("RGBA")
    left_view = pov(dx=+SHIFT, plate_dx=-SHIFT * 0.07).crop(VIEW_BOX)  # what the left eye sees
    right_view = pov(dx=-SHIFT, plate_dx=+SHIFT * 0.07).crop(VIEW_BOX)
    cw, chh = 488, 664
    m0, m1 = 0.62, 1.05  # merge starts / is complete
    if u < m1:
        slide = ease_out(u / 0.30)
        mg = ease_io((u - m0) / (m1 - m0))
        sc = 1 + 0.34 * mg
        w, h = int(cw * sc), int(chh * sc)
        cy = 780 + 10 * mg
        for view, x_far, name in ((left_view, 278, "يسار"), (right_view, 802, "يمين")):
            x_in = x_far + (-640 if x_far < 540 else 640) * (1 - slide)
            cx = x_in + (540 - x_in) * mg
            tile = card(view, w, h, alpha=1.0 if x_far < 540 else 1.0 - 0.5 * mg)
            paste_clip(fr, tile, int(cx - tile.size[0] / 2), int(cy - tile.size[1] / 2))
            if mg < 0.6:
                tag = eye_tag(name)
                if mg > 0:
                    tag.putalpha(tag.getchannel("A").point(lambda v: int(v * (1 - mg / 0.6))))
                paste_clip(fr, tag, int(cx - tag.size[0] / 2), int(cy - h / 2 - 64))
    else:
        v = u - m1
        pop = 1 + 0.07 * (1 - ease_out(v / 0.22))
        sway = 30 * math.sin(2 * math.pi * 0.62 * v) * ease_out(v / 0.4)
        view = pov(dx=sway * 2.4, plate_dx=-sway * 0.5).crop(VIEW_BOX)
        w, h = int(cw * 1.34 * pop), int(chh * 1.34 * pop)
        tile = card(view, w, h)
        paste_clip(fr, tile, int(540 - tile.size[0] / 2), int(790 - tile.size[1] / 2))
        fl = 0.28 * (1 - v / 0.13)
        if fl > 0:
            fr = Image.blend(fr, Image.new("RGBA", fr.size, (*WHITE, 255)), fl)
    return fr.convert("RGB")


def lens_disc(view, rad):
    """A view shaped for a lens: round, slightly vignetted."""
    d = int(rad * 2)
    v = view.resize((d, d), Image.LANCZOS).convert("RGB")
    yy, xx = np.mgrid[0:d, 0:d].astype(np.float32)
    r = np.hypot(xx - rad, yy - rad) / rad
    vig = np.clip(1.05 - 0.55 * r ** 3, 0, 1)[..., None]
    arr = (np.asarray(v, np.float32) * vig).astype(np.uint8)
    alpha = (np.clip((1 - r) * rad / 2.5, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([arr, alpha]), "RGBA")


def scene_lens(t):
    u = t - CUTS[5]
    fr = BG.copy().convert("RGBA")
    sc = PROP_SCALE * (1.0 + 0.03 * ease_io(u / (CUTS[6] - CUTS[5])))
    pw, ph = int(PROP.size[0] * sc), int(PROP.size[1] * sc)
    mid = (LENS_L[0] + LENS_R[0]) / 2 * sc
    px = int(540 - mid)
    py = int(760 - ph / 2 + 60 * (1 - ease_out(u / 0.22)))
    prop = PROP.resize((pw, ph), Image.LANCZOS)
    a_in = ease_out(u / 0.18)
    if a_in < 1:
        prop.putalpha(prop.getchannel("A").point(lambda v: int(v * a_in)))
    paste_clip(fr, prop, px, py)
    sq = (540 - 310, 760 - 270, 540 + 310, 760 + 350)  # square part of the POV picture shown in a lens
    for (lc, dx, t_in, name) in ((LENS_L, +SHIFT, 0.14, "يسار"), (LENS_R, -SHIFT, 0.46, "يمين")):
        k = ease_out((u - t_in) / 0.22)
        if k <= 0:
            continue
        rad = LENS_RAD * sc
        cx, cy = px + lc[0] * sc, py + lc[1] * sc
        disc = lens_disc(pov(dx=dx * 0.8, plate_dx=-dx * 0.06).crop(sq), rad * (0.72 + 0.28 * k))
        disc.putalpha(disc.getchannel("A").point(lambda v: int(v * k)))
        paste_clip(fr, disc, int(cx - disc.size[0] / 2), int(cy - disc.size[1] / 2))
        # glass reflections of the prop on top (screen blend), and a turquoise ring that settles
        box = (int(lc[0] - LENS_RAD), int(lc[1] - LENS_RAD), int(lc[0] + LENS_RAD), int(lc[1] + LENS_RAD))
        d = int(rad * 2)
        gl = PROP.crop(box).convert("RGB").resize((d, d), Image.LANCZOS)
        reg = fr.crop((int(cx - rad), int(cy - rad), int(cx - rad) + d, int(cy - rad) + d)).convert("RGB")
        scr = 255 - (255 - np.asarray(reg, np.float32)) * (255 - np.asarray(gl, np.float32) * 0.75 * k) / 255
        m = Image.new("L", (d, d), 0)
        ImageDraw.Draw(m).ellipse([3, 3, d - 4, d - 4], fill=255)
        fr.paste(Image.fromarray(scr.astype(np.uint8)), (int(cx - rad), int(cy - rad)), m)
        ring = Image.new("RGBA", fr.size, (0, 0, 0, 0))
        rr = rad + 10 + 26 * (1 - k)
        ImageDraw.Draw(ring).ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(*TURQ, int(255 * (0.35 + 0.65 * k))), width=7)
        fr.alpha_composite(ring)
        tag = eye_tag(name)
        tag.putalpha(tag.getchannel("A").point(lambda v: int(v * k)))
        paste_clip(fr, tag, int(cx - tag.size[0] / 2), int(py + ph - 30 + 30 * (1 - k)))
    return fr.convert("RGB")


# ---- talking shots -------------------------------------------------------------------------------------------------
class Clip:
    """Sequential reader of a talking clip, resampled to FPS."""

    def __init__(self, path, start):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{max(start, 0):.4f}", "-i", path, "-vf",
                                   f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}",
                                   "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
        self.last = None

    def read(self):
        raw = self.p.stdout.read(W * H * 3)
        if len(raw) == W * H * 3:
            self.last = Image.frombuffer("RGB", (W, H), raw, "raw", "RGB", 0, 1).copy()
        assert self.last is not None, "talking clip gave no frames"
        return self.last

    def close(self):
        self.p.stdout.close()
        self.p.wait()


def punch(im, z, cy=560.0, cx=540.0):
    """Digital push-in around the face."""
    if z <= 1.0005:
        return im
    w, h = W / z, H / z
    x0 = min(max(cx - w / 2, 0), W - w)
    y0 = min(max(cy - h * (cy / H), 0), H - h)
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))


def talk_zoom(seg, t):
    a, b = CUTS[seg], CUTS[seg + 1] + (HOLD if seg == len(SEGS) - 1 else 0)
    x = (t - a) / (b - a)
    if seg == 0:  # hook: push, then a punch-in on «وانت ما حركته!»
        return 1.0 + 0.02 * x if t < 1.16 else 1.10 + 0.03 * (t - 1.16) / (b - 1.16)
    if seg == 7:  # CTA
        return 1.06 + 0.03 * x
    return 1.0 + 0.035 * x


# ---- render --------------------------------------------------------------------------------------------------------
def main():
    caps = []
    for name, lines, a, b, opt in CARDS:
        img, box = caption_layer(lines, **opt)
        caps.append((name, img, box, a, b))
    handle = handle_layer()
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", f"{WORK}/voice/voice_main.wav",
                            "-filter_complex", f"[1:a]adelay={int(PRE * 1000)}:all=1,loudnorm=I=-14:TP=-1.5:LRA=11,apad[a]",
                            "-map", "0:v", "-map", "[a]", "-t", f"{NFRAMES / FPS:.4f}",
                            "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                            "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    cur, clip, still = -1, None, None
    for n in range(NFRAMES):
        t = n / FPS - PRE
        seg = max(i for i in range(len(SEGS)) if t >= CUTS[i] or i == 0)
        seg = min(seg, len(SEGS) - 1)
        name, kind, pose = SEGS[seg]
        if seg != cur:
            if clip:
                clip.close()
                clip = None
            cur = seg
            if kind == "talk":
                if DRAFT:
                    still = load(pose).resize((W, H), Image.LANCZOS)
                else:
                    clip = Clip(f"{WORK}/clips/{name}.mp4", LEAD + (t - CUTS[seg]))
        if kind == "talk":
            fr = punch(still if DRAFT else clip.read(), talk_zoom(seg, t))
        elif kind == "pov":
            fr = scene_pov(t)
        elif kind == "merge":
            fr = scene_merge(t)
        else:
            fr = scene_lens(t)
        fr = fr.convert("RGBA")
        for cname, img, box, a, b in caps:
            if a <= t < b:
                k = ease_out((t - a) / 0.14) if a > -PRE else 1.0
                if k < 1:
                    s = 0.84 + 0.16 * k
                    im2 = img.resize((max(1, int(img.size[0] * s)), max(1, int(img.size[1] * s))), Image.LANCZOS)
                    im2.putalpha(im2.getchannel("A").point(lambda v: int(v * k)))
                    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                    paste_clip(fr, im2, int(cx - im2.size[0] / 2), int(cy - im2.size[1] / 2))
                else:
                    fr.alpha_composite(img, (box[0], box[1]))
        fr.alpha_composite(handle)
        if DRAFT and kind == "talk":
            d = ImageDraw.Draw(fr)
            d.rounded_rectangle([40, 150, 400, 226], radius=20, fill=(200, 30, 30, 235))
            d.text((220, 190), "مسودة: بدون كلام", font=tajawal(38), fill=WHITE, anchor="mm", direction="rtl", language="ar")
        enc.stdin.write(fr.convert("RGB").tobytes())
    if clip:
        clip.close()
    enc.stdin.close()
    assert enc.wait() == 0
    print("ok", OUT, NFRAMES, "frames", round(NFRAMES / FPS, 3), "s")


if __name__ == "__main__":
    main()
