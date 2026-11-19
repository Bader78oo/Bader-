"""Reel «جولة 360 ولا تجربة VR؟» (Oman-targeted buyer question, workshop design).

Talking shots A1..A4 are audio-driven clips made with the approved lip method (CHARACTER.md section 8). The 360 scene
(a real-looking room you turn around in) and the VR scene (a built 3D room you walk into, touch and change) are drawn
here from stills.

usage: python3 -I reel_360.py WORK_DIR OUT_MP4 [--draft] [--cover COVER_JPG]
  WORK_DIR/img/    S1_cam.png S2_choice.png W1_hook.png S4_majlis.png S5a_vr.png S5b_vr.png
  WORK_DIR/voice/  voice_main.wav
  WORK_DIR/clips/  A1.mp4 .. A4.mp4 (each made from LEAD seconds of silence + its voice segment)
  --draft          talking shots are replaced by their still pose (layout check only)
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reel_kit import (CHIP, DARK, FPS, H, PURPLE, TCHIP, TURQ, W, WHITE, Clip, cairo, caption_layer, draw_line, ease_io,  # noqa: E402
                      ease_out, faded, handle_layer, paste_clip, pill, punch, tajawal)

WORK, OUT = sys.argv[1], sys.argv[2]
DRAFT = "--draft" in sys.argv[3:]
COVER = sys.argv[sys.argv.index("--cover") + 1] if "--cover" in sys.argv else None

# ---- timeline, in the voice file's own time ------------------------------------------------------------------------
PRE, HOLD, LEAD = 0.10, 0.60, 0.25
CUTS = [0.0, 2.79, 6.75, 12.13, 17.19, 21.15, 22.96]  # every cut sits inside a pause
SEGS = [("A1", "talk", "S1_cam"), ("A2", "talk", "S2_choice"), ("B1", "pano", None), ("B2", "vr", None),
        ("A3", "talk", "S2_choice"), ("A4", "talk", "W1_hook")]
AUDIO_T0 = {0: 0.0, 1: 2.79, 4: 17.19, 5: 21.15}  # voice time at which each talking clip's audio segment starts
END = CUTS[-1] + HOLD
NFRAMES = int(round((PRE + END) * FPS))

L_A2 = [[("قدامك طريقين", WHITE)], [("جولة 360", TCHIP), ("أو", WHITE), ("تجربة VR", CHIP)]]
L_B2 = [[("تتمشى", WHITE), ("تلمس", WHITE), ("تغيّر", TCHIP)]]
L_A3 = [[("المكان موجود؟", WHITE), ("جولة 360", TCHIP)], [("ما انبنى بعد؟", WHITE), ("تجربة VR", CHIP)]]
# captions: lines, start, end, options. "hidden" keeps a piece in the layout without drawing it yet; "fade" makes a
# card appear without the pop (used when it only adds a piece to the card before it).
CARDS = [
    ([[("عندك مشروع", WHITE), ("في عُمان", TCHIP)], [("وتريد الناس تشوفه؟", WHITE)]], -PRE, 2.79, {"size": 82}),
    (L_A2, 2.94, 4.25, {"size": 84, "hidden": {(1, 0), (1, 1), (1, 2)}}),
    (L_A2, 4.13, 5.51, {"size": 84, "hidden": {(1, 1), (1, 2)}, "fade": True}),
    (L_A2, 5.39, 6.75, {"size": 84, "fade": True}),
    ([[("الـ360", TCHIP), ("تصوير حقيقي", WHITE)]], 6.98, 9.25, {}),
    ([[("تلف وتشوف كل شي", WHITE)]], 9.51, 10.82, {}),
    ([[("بس", WHITE), ("واقف مكانك", CHIP)]], 11.04, 12.13, {}),
    ([[("الـVR", CHIP), ("عالم مبني", WHITE)]], 12.32, 14.52, {}),
    (L_B2, 14.71, 15.66, {"hidden": {(0, 1), (0, 2)}}),
    (L_B2, 15.54, 16.42, {"hidden": {(0, 2)}, "fade": True}),
    (L_B2, 16.30, 17.19, {"fade": True}),
    (L_A3, 17.40, 18.56, {"size": 72, "hidden": {(0, 1), (1, 0), (1, 1)}}),
    (L_A3, 18.44, 19.62, {"size": 72, "hidden": {(1, 0), (1, 1)}, "fade": True}),
    (L_A3, 19.50, 20.56, {"size": 72, "hidden": {(1, 1)}, "fade": True}),
    (L_A3, 20.44, 21.15, {"size": 72, "fade": True}),
    ([[("أرسله لصاحب مشروع", WHITE)], [("يحتاجه", TCHIP)]], 21.29, END, {}),
]
MID_CTA = (12.45, 17.05)  # the written call to action, while about 40% of viewers are still watching


def load(name, mode="RGB"):
    return Image.open(f"{WORK}/img/{name}.png").convert(mode)


# ---- 360 scene -----------------------------------------------------------------------------------------------------
PANO = load("S4_majlis")
PSC = H / PANO.size[1]  # panorama pixels -> screen pixels
PAN_MAX = PANO.size[0] * PSC - W


def pan_x(t):
    a, b = CUTS[2], CUTS[3]
    if t < 9.30:
        return 250 + 420 * (t - a) / (9.30 - a)
    if t < 10.95:
        return 670 + (PAN_MAX - 190 - 670) * ease_io((t - 9.30) / (10.95 - 9.30))
    return PAN_MAX - 190 + 110 * (t - 10.95) / (b - 10.95)


def gauge(frac, alpha):
    """Top bar showing where you are looking in the full turn."""
    wd, ht = 470, 70
    im = Image.new("RGBA", (wd, ht), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, wd - 1, ht - 1], radius=ht // 2, fill=(*DARK, 225), outline=(*WHITE, 80), width=3)
    d.text((wd - 30, ht / 2 + 2), "360°", font=tajawal(38), fill=WHITE, anchor="rm")
    x0, x1 = 34, wd - 150
    for k in range(13):
        x = x0 + (x1 - x0) * k / 12
        d.line([(x, ht / 2 - (11 if k % 3 == 0 else 6)), (x, ht / 2 + (11 if k % 3 == 0 else 6))], fill=(*WHITE, 150), width=3)
    x = x0 + (x1 - x0) * frac
    d.ellipse([x - 13, ht / 2 - 13, x + 13, ht / 2 + 13], fill=(*TURQ, 255), outline=(*WHITE, 255), width=3)
    return faded(im, alpha)


def pin(k, pulse):
    """'You stay here' marker on the floor: a location pin with a flat ring under it."""
    s = 3
    wd, ht = 300, 300
    im = Image.new("RGBA", (wd * s, ht * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, base = wd * s / 2, 230 * s
    rr = (70 + 55 * pulse) * s
    d.ellipse([cx - rr, base - rr * 0.32, cx + rr, base + rr * 0.32], outline=(*TURQ, int(255 * (1 - pulse))), width=7 * s)
    d.ellipse([cx - 46 * s, base - 15 * s, cx + 46 * s, base + 15 * s], fill=(*DARK, 150))
    r, top = 52 * s, 60 * s
    d.polygon([(cx - r * 0.82, top + r * 1.45), (cx + r * 0.82, top + r * 1.45), (cx, base)], fill=(*TURQ, 255))
    d.ellipse([cx - r, top, cx + r, top + 2 * r], fill=(*TURQ, 255))
    d.ellipse([cx - r * 0.42, top + r * 0.58, cx + r * 0.42, top + r * 1.42], fill=(*DARK, 255))
    im = im.resize((wd, ht), Image.LANCZOS)
    sc = 0.6 + 0.4 * k
    im = im.resize((int(wd * sc), int(ht * sc)), Image.LANCZOS)
    return faded(im, k)


def scene_pano(t):
    x = pan_x(t)
    # a step forward that goes nowhere: you can look, you cannot walk
    u = (t - 11.10) / 0.50
    z = 1.0 + (0.055 * math.sin(math.pi * u) if 0 < u < 1 else 0.0)
    bw, bh = W / PSC / z, PANO.size[1] / z
    cx, cy = (x + W / 2) / PSC, PANO.size[1] * 0.52
    x0 = min(max(cx - bw / 2, 0), PANO.size[0] - bw)
    y0 = min(max(cy - bh * 0.52, 0), PANO.size[1] - bh)
    fr = PANO.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + bw, y0 + bh)).convert("RGBA")
    a = ease_out((t - CUTS[2] - 0.15) / 0.3)
    g = gauge(x / PAN_MAX, a)
    paste_clip(fr, g, (W - g.size[0]) // 2, 154)
    k = ease_out((t - 10.98) / 0.25)
    if k > 0:
        p = pin(k, ((t - 10.98) * 1.6) % 1.0)
        paste_clip(fr, p, int(540 - p.size[0] / 2), int(1250 - p.size[1]))
    return fr.convert("RGB")


# ---- VR scene ------------------------------------------------------------------------------------------------------
VR_A = load("S5a_vr").resize((W, H), Image.LANCZOS)
VR_B = load("S5b_vr").resize((W, H), Image.LANCZOS)
ANCHOR = (757.0, 938.0)  # pushing VR_A in around this point brings the sofa to where it sits in VR_B
Z_WALK = 1.37
TOUCH = (730.0, 1206.0)  # fingertip on the sofa in VR_B


def grey_sofa(img):
    """VR_B with its turquoise sofa turned back to grey, and the mask of what changed."""
    a = np.asarray(img, np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.zeros_like(mx)
    d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == g, 60 * ((b - r) / d) + 120, hue)
    hue = np.where(mx == b, 60 * ((r - g) / d) + 240, hue)
    m = ((hue > 160) & (hue < 190) & (sat > 0.48) & (mx > 0.25)).astype(np.float32)
    yy = np.arange(H)[:, None]
    m *= ((yy > 880) & (yy < 1330)).astype(np.float32)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2.5)), np.float32) / 255.0
    lum = (0.299 * r + 0.587 * g + 0.114 * b)
    grey = np.stack([lum * 1.10 + 0.05, lum * 1.10 + 0.05, lum * 1.08 + 0.05], -1)
    out = a * (1 - m[..., None]) + np.clip(grey, 0, 1) * m[..., None]
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)), m


VR_B_GREY, SOFA_MASK = grey_sofa(VR_B)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
DIST = np.hypot(_xx - TOUCH[0], _yy - TOUCH[1])
VR_B_ARR, VR_B_GREY_ARR = np.asarray(VR_B, np.float32), np.asarray(VR_B_GREY, np.float32)
T_WALK, T_TOUCH, T_CHANGE = 14.62, 15.54, 16.30


def scene_vr(t):
    if t < T_TOUCH - 0.08:
        z = 1.0 + 0.07 * (t - CUTS[3]) / (T_WALK - CUTS[3]) if t < T_WALK else 1.07 + (Z_WALK - 1.07) * ease_io((t - T_WALK) / (T_TOUCH - 0.08 - T_WALK))
        bob = 9 * math.sin(2 * math.pi * 2.2 * (t - T_WALK)) * ease_io((t - T_WALK) / 0.2) if t > T_WALK else 0.0
        fr = punch(VR_A, z, cy=ANCHOR[1] + bob, cx=ANCHOR[0])
    else:
        k = min(max((t - T_CHANGE) / 0.42, 0.0), 1.0)
        rad = 40 + 1250 * ease_out(k)
        m = np.clip((rad - DIST) / 60.0, 0, 1)[..., None] if k > 0 else 0.0
        arr = VR_B_GREY_ARR * (1 - m) + VR_B_ARR * m
        fr = Image.fromarray(arr.astype(np.uint8))
        fr = punch(fr, 1.0 + 0.035 * (t - T_TOUCH) / (CUTS[4] - T_TOUCH), cy=TOUCH[1], cx=TOUCH[0])
        x = (t - (T_TOUCH - 0.08)) / 0.07
        if x < 1:  # two-frame blend from the walk into the touch (longer blends show doubled window frames)
            fr = Image.blend(punch(VR_A, Z_WALK, cy=ANCHOR[1], cx=ANCHOR[0]), fr, ease_io(x))
        # ripple rings at the fingertip: one on the touch, one on the change
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for t0, col in ((T_TOUCH, WHITE), (T_CHANGE, TURQ)):
            u = (t - t0) / 0.5
            if 0 <= u < 1:
                rr = 30 + 190 * ease_out(u)
                d.ellipse([TOUCH[0] - rr, TOUCH[1] - rr * 0.8, TOUCH[0] + rr, TOUCH[1] + rr * 0.8], outline=(*col, int(230 * (1 - u))), width=9)
        fr = Image.alpha_composite(fr.convert("RGBA"), ov).convert("RGB")
    return fr


# ---- talking shots -------------------------------------------------------------------------------------------------
def talk_zoom(seg, t):
    a, b = CUTS[seg], CUTS[seg + 1] + (HOLD if seg == len(SEGS) - 1 else 0)
    x = (t - a) / (b - a)
    if seg == 0:  # hook: gentle push, then a punch-in on «وتريد الناس تشوفه؟»
        return 1.0 + 0.02 * x if t < 1.42 else 1.09 + 0.03 * (t - 1.42) / (b - 1.42)
    if seg == 5:
        return 1.06 + 0.03 * x
    return 1.0 + 0.04 * x


# ---- cover ---------------------------------------------------------------------------------------------------------
def make_cover(path):
    im = load("S2_choice").resize((W, H), Image.LANCZOS).convert("RGBA")
    yy = np.arange(H, dtype=np.float32)[:, None]
    shade = np.clip((yy - 1050) / 520, 0, 1) ** 1.3 * 190
    ov = np.zeros((H, W, 4), np.uint8)
    ov[..., :3] = DARK
    ov[..., 3] = np.broadcast_to(shade, (H, W)).astype(np.uint8)
    im = Image.alpha_composite(im, Image.fromarray(ov, "RGBA"))
    for lines, size, cy in (([[("عندك مشروع في عُمان؟", WHITE)]], 62, 1205), ([[("جولة 360", TCHIP)]], 122, 1340), ([[("ولا", WHITE), ("تجربة VR؟", CHIP)]], 122, 1498)):
        layer, box = caption_layer(lines, size=size, cy=cy)
        im.alpha_composite(layer, (box[0], box[1]))
    im.alpha_composite(handle_layer())
    im.convert("RGB").save(path, quality=93)


# ---- render --------------------------------------------------------------------------------------------------------
def main():
    if COVER:
        make_cover(COVER)
    caps = []
    for lines, a, b, opt in CARDS:
        o = dict(opt)
        fade = o.pop("fade", False)
        img, box = caption_layer(lines, **o)
        caps.append((img, box, a, b, fade))
    handle = handle_layer()
    cta = pill("أرسله لصاحب مشروع", size=46, icon="send")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", f"{WORK}/voice/voice_main.wav",
                            "-filter_complex", f"[1:a]adelay={int(PRE * 1000)}:all=1,loudnorm=I=-14:TP=-1.5:LRA=11,apad[a]",
                            "-map", "0:v", "-map", "[a]", "-t", f"{NFRAMES / FPS:.4f}",
                            "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                            "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    cur, clip, still = -1, None, None
    for n in range(NFRAMES):
        t = n / FPS - PRE
        seg = min(max([i for i in range(len(SEGS)) if t >= CUTS[i]] or [0]), len(SEGS) - 1)
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
                    clip = Clip(f"{WORK}/clips/{name}.mp4", LEAD + (t - AUDIO_T0[seg]))
        if kind == "talk":
            fr = punch(still if DRAFT else clip.read(), talk_zoom(seg, t))
        elif kind == "pano":
            fr = scene_pano(t)
        else:
            fr = scene_vr(t)
        fr = fr.convert("RGBA")
        for img, box, a, b, fade in caps:
            if a <= t < b:
                k = ease_out((t - a) / 0.14) if a > -PRE else 1.0
                if k < 1 and not fade:
                    s = 0.84 + 0.16 * k
                    im2 = faded(img.resize((max(1, int(img.size[0] * s)), max(1, int(img.size[1] * s))), Image.LANCZOS), k)
                    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                    paste_clip(fr, im2, int(cx - im2.size[0] / 2), int(cy - im2.size[1] / 2))
                else:
                    fr.alpha_composite(faded(img, k) if k < 1 else img, (box[0], box[1]))
        if MID_CTA[0] <= t < MID_CTA[1]:
            k = min(ease_out((t - MID_CTA[0]) / 0.25), ease_out((MID_CTA[1] - t) / 0.2))
            c = faded(cta, k)
            paste_clip(fr, c, (W - c.size[0]) // 2, int(150 - 24 * (1 - k)))
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
