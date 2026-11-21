"""Reel «كيف وصّلنا الناقة صلالة؟»: how a VR scene is designed, told with the camel of the first reel.

The camel is an imaginary client. The design stages (plan, mesh, untextured model, colour, light) are computed from
the footage itself (mesh_look.py), so every stage lines up with the finished picture. Three shots are new; the rest
is footage of the first camel reel.

usage: python3 -I reel_camel2.py WORK_DIR OUT_MP4 [--frames 0,24,...] [--cover COVER_JPG]
  WORK_DIR/clips/  H.mp4 C.mp4 I.mp4 (new)  v1.mp4 v2.mp4 v10.mp4 v11.mp4 v12.mp4 (first reel)
  WORK_DIR/voice/  voice_main.wav music.mp3 ;  WORK_DIR/sfx/  sfx_v1.wav sfx_v6.wav sfx_v8.wav (first reel ambience)
  --frames         write only these output frames to WORK_DIR/check/dbg_NNNN.jpg (no video, no audio)
"""
import math
import os
import subprocess
import sys
import wave

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "avatar", "tools"))
import mesh_look as ml  # noqa: E402
from reel_kit import (CHIP, DARK, PURPLE, TCHIP, TURQ, WHITE, cairo, caption_layer, ease_io, ease_out, faded, handle_layer,  # noqa: E402
                      paste_clip, pill, tajawal)

WORK, OUT = sys.argv[1], sys.argv[2]
ONLY = [int(v) for v in sys.argv[sys.argv.index("--frames") + 1].split(",")] if "--frames" in sys.argv else None
COVER = sys.argv[sys.argv.index("--cover") + 1] if "--cover" in sys.argv else None
W, H, FPS = 1080, 1920, 24
SR = 48000
PRE = 0.15  # picture before the first word
VOICE_END = 22.47
END = VOICE_END + 1.45  # the written call to action stays for a second and a half after the last word
T_PLAN, T_BUILD, T_COLOUR = 7.20, 8.22, 10.48  # voice times: blueprint appears, mesh starts, colour starts
MUSIC_DROP = 9.64  # where the music's full groove enters, in seconds of the music file
os.makedirs(f"{WORK}/cache", exist_ok=True)
os.makedirs(f"{WORK}/check", exist_ok=True)


def fno(t):
    return int(round((t + PRE) * FPS))


def seg(x, a, b):
    return min(max((x - a) / (b - a), 0.0), 1.0)


def up(m_half):
    return cv2.resize(m_half.astype(np.float32) / 255.0, (W, H), interpolation=cv2.INTER_LINEAR)


def mattes(name, frames, region, band, **kw):
    """Camel mattes for a clip, half size uint8, cached; a 3-frame median steadies the outline."""
    path = f"{WORK}/cache/matte_{name}_{len(frames)}.npy"
    if os.path.exists(path):
        return np.load(path)
    out = np.zeros((len(frames), H // 2, W // 2), np.uint8)
    prev = None
    for k, f in enumerate(frames):
        prev = ml.subject_matte(f, region=region, prev=prev, headset_band=band, **kw)
        out[k] = (cv2.resize(prev, (W // 2, H // 2), interpolation=cv2.INTER_AREA) * 255).astype(np.uint8)
    med = out.copy()
    med[1:-1] = np.median(np.stack([out[:-2], out[1:-1], out[2:]]), axis=0).astype(np.uint8)
    np.save(path, med)
    return med


def over(bg, fg, a):
    return fg * a[..., None] + bg * (1 - a[..., None])


def blend_frames(fr, pos):
    i = int(math.floor(pos))
    j = min(i + 1, len(fr) - 1)
    k = pos - i
    if k < 0.02 or i == j:
        return fr[min(i, len(fr) - 1)].astype(np.float32)
    return fr[i].astype(np.float32) * (1 - k) + fr[j].astype(np.float32) * k


# ---- small drawn pieces --------------------------------------------------------------------------------------------
def cursor_icon(scale=1.5):
    pts = [(0, 0), (0, 58), (14, 45), (24, 68), (34, 64), (24, 41), (42, 41)]
    s = 4
    im = Image.new("RGBA", (int(52 * scale * s), int(76 * scale * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    p = [(4 * s + x * scale * s, 4 * s + y * scale * s) for x, y in pts]
    d.polygon(p, fill=(255, 255, 255, 255))
    d.line(p + [p[0]], fill=(*DARK, 255), width=int(4 * s), joint="curve")
    im = im.resize((im.size[0] // s, im.size[1] // s), Image.LANCZOS)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 130), (3, 5), im.getchannel("A").filter(ImageFilter.GaussianBlur(4)))
    return Image.alpha_composite(sh, im)


CURSOR = cursor_icon()


def slider_handle():
    s = 4
    r = 46
    im = Image.new("RGBA", (2 * (r + 10) * s, 2 * (r + 10) * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (r + 10) * s
    d.ellipse([c - r * s, c - r * s, c + r * s, c + r * s], fill=(255, 255, 255, 255), outline=(*DARK, 255), width=5 * s)
    for sign in (-1, 1):
        x0 = c + sign * 10 * s
        d.polygon([(x0, c - 15 * s), (x0, c + 15 * s), (x0 + sign * 20 * s, c)], fill=(*PURPLE, 255))
    im = im.resize((im.size[0] // s, im.size[1] // s), Image.LANCZOS)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 120), (0, 6), im.getchannel("A").filter(ImageFilter.GaussianBlur(6)))
    return Image.alpha_composite(sh, im)


HANDLE = slider_handle()
TAG_BEFORE, TAG_AFTER = pill("قبل", size=42), pill("بعد", size=42, fill=PURPLE, outline=WHITE)


def bubble(k):
    """The client's note. k = 0..1 pop-in."""
    w, h = 800, 300
    s = 2
    im = Image.new("RGBA", (w * s, (h + 90) * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(470 * s, (h - 6) * s), (590 * s, (h - 6) * s), (560 * s, (h + 84) * s)], fill=(255, 255, 255, 255), outline=(*DARK, 255))
    d.rounded_rectangle([4 * s, 4 * s, (w - 4) * s, (h - 4) * s], radius=70 * s, fill=(255, 255, 255, 255), outline=(*DARK, 255), width=7 * s)
    d.polygon([(476 * s, (h - 12) * s), (584 * s, (h - 12) * s), (560 * s, (h + 70) * s)], fill=(255, 255, 255, 255))
    f1, f2 = tajawal(46 * s), cairo(92 * s)
    d.text((w * s / 2, 78 * s), "الزبونة تقول:", font=f1, fill=(*PURPLE, 255), anchor="mm", direction="rtl", language="ar")
    d.text((w * s / 2, 184 * s), "كبّروا الشلال!", font=f2, fill=(*DARK, 255), anchor="mm", direction="rtl", language="ar")
    im = im.resize((w, h + 90), Image.LANCZOS)
    sc = 0.6 + 0.4 * ease_out(k) + 0.06 * math.sin(math.pi * min(k, 1.0)) * (1 - k)
    im = im.resize((max(2, int(w * sc)), max(2, int((h + 90) * sc))), Image.LANCZOS)
    return faded(im, min(k * 2.5, 1.0))


def stamp(k):
    """«معتمد» stamp. k = 0..1 slam-in."""
    w, h = 640, 250
    s = 2
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    green = (0, 190, 150)
    d.rounded_rectangle([8 * s, 8 * s, (w - 8) * s, (h - 8) * s], radius=36 * s, fill=(255, 255, 255, 235), outline=(*green, 255), width=13 * s)
    d.rounded_rectangle([30 * s, 30 * s, (w - 30) * s, (h - 30) * s], radius=22 * s, outline=(*green, 255), width=4 * s)
    d.text(((w - 110) * s / 2 + 110 * s, h * s / 2 - 8 * s), "معتمد", font=cairo(124 * s), fill=(*green, 255), anchor="mm", direction="rtl", language="ar")
    d.line([(62 * s, 128 * s), (98 * s, 168 * s), (160 * s, 86 * s)], fill=(*green, 255), width=20 * s, joint="curve")
    im = im.resize((w, h), Image.LANCZOS).rotate(8, expand=True, resample=Image.BICUBIC)
    sc = 1.0 + 0.9 * (1 - ease_out(k))
    im = im.resize((int(im.size[0] * sc), int(im.size[1] * sc)), Image.LANCZOS)
    return faded(im, min(k * 3.0, 1.0))


def select_box(x0, y0, x1, y1, alpha, label=None):
    """Editor selection box with eight handles (and a size label)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([x0, y0, x1, y1], outline=(*TURQ, 255), width=5)
    for hx in (x0, (x0 + x1) / 2, x1):
        for hy in (y0, (y0 + y1) / 2, y1):
            if hx == (x0 + x1) / 2 and hy == (y0 + y1) / 2:
                continue
            d.rectangle([hx - 13, hy - 13, hx + 13, hy + 13], fill=(255, 255, 255, 255), outline=(*TURQ, 255), width=4)
    if label:
        p = pill(label, size=44)
        layer.alpha_composite(p, (int(min(max(x1 - p.size[0], 10), W - p.size[0] - 10)), int(max(y0 - p.size[1] - 16, 130))))
    return faded(layer, alpha)


def step_pill(n, text):
    return pill(f"الخطوة {n} · {text}", size=44)


# ---- beats ---------------------------------------------------------------------------------------------------------
class Beat:
    def __init__(self, t0, t1):
        self.t0, self.t1, self.n0, self.n1 = t0, t1, fno(t0), fno(t1)

    def prepare(self):
        pass

    def release(self):
        self.__dict__ = {k: v for k, v in self.__dict__.items() if k in ("t0", "t1", "n0", "n1")}


class Hook(Beat):
    """The camel in a half-built Salalah: a before/after slider is dragged across the world behind her."""
    KEYS = [(0.0, 0.50), (0.45, 0.50), (1.35, 0.86), (1.80, 0.86), (3.12, -0.04), (9.0, -0.04)]
    cover = False

    def prepare(self):
        n = self.n1 - self.n0
        self.fr = ml.load_frames(f"{WORK}/clips/H.mp4")[: n + 1]
        self.mt = mattes("H", self.fr, (0.0, 0.10, 1.0, 1.0), 0.40)
        m0 = up(self.mt[0])
        keep = cv2.dilate((m0 > 0.3).astype(np.uint8), np.ones((25, 25), np.uint8)).astype(np.float32)
        self.pts, self.tri = ml.build_mesh(self.fr[0], keep_out=keep, cell=17, grid=74)
        self.idx, self.lines = ml.raster(self.pts, self.tri)
        ys = np.nonzero((m0 > 0.5).any(1))[0]
        self.hy = int(min(max(ys.min() - 190, 330), 520))

    def slider(self, u):
        for (a, xa), (b, xb) in zip(self.KEYS[:-1], self.KEYS[1:]):
            if a <= u < b:
                return xa + (xb - xa) * ease_io((u - a) / (b - a)) + (0.006 * math.sin(2 * math.pi * 1.4 * u) if xa == xb else 0.0)
        return self.KEYS[-1][1]

    def frame(self, k, t):
        u = t - self.t0
        k = min(k, len(self.fr) - 1)
        f = self.fr[k].astype(np.float32)
        a = up(self.mt[k])
        wire, _, _ = ml.looks(self.fr[k], self.idx, self.lines, len(self.tri))
        x = self.slider(u) * W
        X = np.arange(W, dtype=np.float32)[None, :, None]
        side = np.clip((x - X) / 3.0 + 0.5, 0, 1)  # 1 = left of the line (before), 0 = right (after)
        bg = wire * side + f * (1 - side)
        core = np.exp(-((X - x) / 3.0) ** 2)
        glow = np.exp(-((X - x) / 16.0) ** 2) * 0.55
        bg = bg * (1 - core) + 255.0 * core + np.array(TURQ, np.float32) * glow
        out = over(bg, ml.decontaminate(self.fr[k], a), a)
        img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")
        ui = seg(x, 40.0, 190.0)  # the handle, the cursor and the tags fade as the line leaves the frame
        if ui > 0:
            paste_clip(img, faded(HANDLE, ui), int(x - HANDLE.size[0] / 2), int(self.hy - HANDLE.size[1] / 2))
            if not self.cover:
                grab = 6 * math.sin(2 * math.pi * 0.8 * u)
                paste_clip(img, faded(CURSOR, ui), int(x + 14), int(self.hy + 12 + grab))
                paste_clip(img, faded(TAG_BEFORE, ui), int(x - 30 - TAG_BEFORE.size[0]), self.hy - 150)
                paste_clip(img, faded(TAG_AFTER, ui), int(x + 30), self.hy - 150)
        return img


class Place(Beat):
    """Step 1: the real place, captured in 360."""

    def prepare(self):
        self.fr = ml.load_frames(f"{WORK}/clips/C.mp4")

    def frame(self, k, t):
        n = self.n1 - self.n0
        return Image.fromarray(np.clip(blend_frames(self.fr, k * (len(self.fr) - 1) / max(n - 1, 1)), 0, 255).astype(np.uint8)).convert("RGBA")


class Build(Beat):
    """Plan, then the scene is built in front of the camel: mesh, untextured model, colour, light."""
    ZOOM = 1.18

    def prepare(self):
        self.kplan = fno(T_BUILD) - self.n0
        n = self.n1 - self.n0
        self.fr = ml.zoom(ml.load_frames(f"{WORK}/clips/v11.mp4"), self.ZOOM)  # her head clears the caption
        last = len(self.fr) - 1  # the clip is a few frames shorter than the beat: spread it, repeating a frame now and then
        self.src = [min(int(round(k * last / (n - 1))), last) for k in range(n)]
        self.mt = mattes("v11z", self.fr, (0.0, 0.45, 1.0, 1.0), 0.75, earth_below=0.78, shell_reach=0.30)
        m0 = up(self.mt[0])
        tp = f"{WORK}/cache/track_v11z_{len(self.fr)}.npy"
        if os.path.exists(tp):
            self.Ms = list(np.load(tp))
        else:
            self.Ms = ml.track(self.fr, ((m0 < 0.05) * 255).astype(np.uint8))
            np.save(tp, np.stack(self.Ms))
        keep = cv2.dilate((m0 > 0.3).astype(np.uint8), np.ones((25, 25), np.uint8)).astype(np.float32)
        self.pts, self.tri = ml.build_mesh(self.fr[0], keep_out=keep, cell=17, grid=74)
        hsv = cv2.cvtColor(self.fr[0], cv2.COLOR_RGB2HSV)
        wf = ((hsv[..., 1] < 55) & (hsv[..., 2] > 190)).astype(np.uint8)
        wf[:780] = 0
        wf[1250:] = 0
        n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.morphologyEx(wf, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)), 8)
        j = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        self.wf = (float(cen[j][0]), float(cen[j][1]))
        self.o_grow = ml.tri_order(self.pts, self.tri, "radial", origin=(540, 1560), seed=5)
        self.o_clay = ml.tri_order(self.pts, self.tri, "radial", origin=(540, 1560), seed=7)
        self.o_col = ml.tri_order(self.pts, self.tri, "down", seed=9)
        self.o_real = ml.tri_order(self.pts, self.tri, "radial", origin=self.wf, seed=11)
        # blueprint of the first frame
        g = cv2.GaussianBlur(cv2.cvtColor(self.fr[0], cv2.COLOR_RGB2GRAY), (0, 0), 3.0)  # the big shapes only
        e = cv2.dilate(cv2.Canny(g, 14, 36), np.ones((3, 3), np.uint8))
        self.bp_lines = np.clip(cv2.GaussianBlur(e.astype(np.float32) / 255.0, (0, 0), 1.0) * 1.6, 0, 1)
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        bg = np.array([18, 62, 146], np.float32) * (1 - yy) + np.array([10, 38, 102], np.float32) * yy
        bg = np.repeat(bg, W, axis=1)
        grid = np.zeros((H, W), np.float32)
        grid[::54, :] = 0.10
        grid[:, ::54] = 0.10
        grid[::270, :] = 0.26
        grid[:, ::270] = 0.26
        self.bp_bg = bg * (1 - grid[..., None]) + 255.0 * grid[..., None]
        rng = np.random.default_rng(2)
        wob = cv2.GaussianBlur(rng.random((H, 1)).astype(np.float32), (0, 0), 40)
        self.bp_wob = ((wob - wob.min()) / max(float(wob.max() - wob.min()), 1e-6) * 240.0)[:, :, None] if wob.ndim == 2 else None
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        self.dark = np.repeat(np.array([14, 10, 40], np.float32) * (1 - yy) + np.array([30, 8, 70], np.float32) * yy, W, axis=1)

    def plan_image(self, reveal):
        X = np.arange(W, dtype=np.float32)[None, :, None]
        r = np.clip((reveal * (W + 420) - X - self.bp_wob) / 130.0, 0, 1)[..., 0]
        return self.bp_bg + (255.0 - self.bp_bg) * (self.bp_lines * r)[..., None] * 0.95

    def frame(self, k, t):
        kk = self.src[min(k, len(self.src) - 1)]
        f = self.fr[kk]
        a = up(self.mt[kk])
        if k < self.kplan:  # the plan is drawn
            u = t - self.t0
            out = over(self.plan_image(ease_io(u / 0.92)), ml.decontaminate(f, a), a)
            return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")
        v = t - T_BUILD
        idx, lines = ml.raster(ml.move(self.pts, self.Ms[kk]), self.tri)
        wire, clay, low = ml.looks(f, idx, lines, len(self.tri))
        c0 = T_COLOUR - T_BUILD
        stages = [(self.o_grow, seg(v, 0.00, 1.05), wire, np.array(TURQ, np.float32), 0.55),
                  (self.o_clay, seg(v, 1.00, c0 - 0.12), clay, np.array([255, 255, 255], np.float32), 0.30),
                  (self.o_col, seg(v, c0 + 0.10, c0 + 1.05), low, np.array([255, 255, 255], np.float32), 0.22),
                  (self.o_real, seg(v, c0 + 1.12, c0 + 1.72), f.astype(np.float32), np.array([255, 250, 235], np.float32), 0.50)]
        x = ease_io(v / 0.7)
        out = self.plan_image(1.0) * (1 - x) + self.dark * x
        for order, p, look, tint, amount in stages:
            if p <= 0:
                continue
            al = ml.activation(order, p)[idx][..., None]
            out = out * (1 - al) + look * al
            if p < 1:
                out = out + tint * (4 * al * (1 - al)) * amount  # a glowing front where the stage is arriving
        out = over(out, ml.decontaminate(f, a), a)
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")


class Touch(Beat):
    """Step 3, second half: the world answers a touch."""
    POINT = (552, 1236)

    def prepare(self):
        self.fr = ml.load_frames(f"{WORK}/clips/I.mp4")

    def frame(self, k, t):
        u = t - self.t0
        img = Image.fromarray(self.fr[min(4 + k, len(self.fr) - 1)]).convert("RGBA")
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for t0 in (0.05, 0.40, 0.75):
            x = (u - t0) / 0.75
            if 0 <= x < 1:
                rx = 60 + 330 * ease_out(x)
                d.ellipse([self.POINT[0] - rx, self.POINT[1] - rx * 0.30, self.POINT[0] + rx, self.POINT[1] + rx * 0.30],
                          outline=(*TURQ, int(245 * (1 - x) ** 0.7)), width=11)
        img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(9)))  # glow under the rings
        img.alpha_composite(ov)
        return img


class Review(Beat):
    """Step 4: the client tries it and asks for a change."""
    T_NOTE = 15.45
    START = 6  # v2 at its own speed from this frame: her smirk grows through «ويطلب تعديل» and ends on bared teeth

    def prepare(self):
        self.fr = ml.load_frames(f"{WORK}/clips/v2.mp4")[self.START:]

    def frame(self, k, t):
        img = Image.fromarray(self.fr[min(k, len(self.fr) - 1)]).convert("RGBA")
        if t >= self.T_NOTE:
            b = bubble(seg(t, self.T_NOTE, self.T_NOTE + 0.28))
            paste_clip(img, b, int(540 - b.size[0] / 2), int(450 - b.size[1] / 2))
        return img


class Fix(Beat):
    """The waterfall is selected and scaled up, the way an object is resized in a 3D editor."""
    START = 58

    def prepare(self):
        n = self.n1 - self.n0
        self.fr = ml.load_frames(f"{WORK}/clips/v12.mp4")[self.START: self.START + n + 1]
        hsv = cv2.cvtColor(self.fr[0], cv2.COLOR_RGB2HSV)
        wf = ((hsv[..., 1] < 55) & (hsv[..., 2] > 190)).astype(np.uint8)
        wf[:780] = 0
        wf[1250:] = 0
        n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.morphologyEx(wf, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)), 8)
        j = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        x, y, w, h = st[j, :4]
        cx = x + 0.62 * w  # the fall itself sits right of the spray
        self.box = (int(cx - 235), int(y - 0.22 * h), int(cx + 235), int(y + 1.08 * h))
        print("waterfall in v12:", (x, y, w, h), "box", self.box, flush=True)

    def frame(self, k, t):
        u = t - self.t0
        f = self.fr[min(k, len(self.fr) - 1)].astype(np.float32)
        x0, y0, x1, y1 = self.box
        s = 1.0 + 1.0 * ease_out(seg(u, 0.30, 0.92)) + 0.06 * math.sin(math.pi * seg(u, 0.70, 1.04))
        w, h = x1 - x0, y1 - y0
        dw, dh = int(w * s), int(h * s)
        cx = (x0 + x1) / 2
        dx0, dy0 = int(min(max(cx - dw / 2, 14), max(W - 14 - dw, 14))), int(y1 - dh)
        out = f
        if s > 1.003:
            patch = cv2.resize(f[y0:y1, x0:x1], (dw, dh), interpolation=cv2.INTER_CUBIC)
            m = np.zeros((dh, dw), np.float32)
            fe = int(26 * s)
            m[fe:-fe, fe:-fe] = 1.0
            m = cv2.GaussianBlur(m, (0, 0), fe * 0.55)
            sx0, sy0 = max(0, -dx0), max(0, -dy0)
            ex, ey = min(dw, W - dx0), min(dh, H - dy0)
            out = f.copy()
            reg = out[dy0 + sy0: dy0 + ey, dx0 + sx0: dx0 + ex]
            mm = m[sy0:ey, sx0:ex, None]
            out[dy0 + sy0: dy0 + ey, dx0 + sx0: dx0 + ex] = reg * (1 - mm) + patch[sy0:ey, sx0:ex] * mm
        img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")
        al = min(ease_out(u / 0.18), 1.0 - seg(u, 1.12, 1.32))
        if al > 0:
            img.alpha_composite(select_box(dx0, dy0, dx0 + dw, dy0 + dh, al, f"{int(round(s * 100))}%"))
            cur = (x1 + 60 + (dx0 + dw + 6 - (x1 + 60)) * ease_out(seg(u, 0.05, 0.28)), y0 - 60 + (dy0 - 4 - (y0 - 60)) * ease_out(seg(u, 0.05, 0.28)))
            paste_clip(img, faded(CURSOR, al), int(cur[0]), int(cur[1]))
        return img


class Approved(Beat):
    T_STAMP = 18.24

    def prepare(self):
        self.fr = ml.load_frames(f"{WORK}/clips/v1.mp4")[: self.n1 - self.n0 + 2]

    def frame(self, k, t):
        img = Image.fromarray(self.fr[min(k, len(self.fr) - 1)]).convert("RGBA")
        if t >= self.T_STAMP:
            s = stamp(seg(t, self.T_STAMP, self.T_STAMP + 0.20))
            paste_clip(img, s, int(540 - s.size[0] / 2), int(400 - s.size[1] / 2))
        return img


class Close(Beat):
    def prepare(self):
        self.fr = ml.load_frames(f"{WORK}/clips/v10.mp4")

    def frame(self, k, t):
        return Image.fromarray(self.fr[min(k, len(self.fr) - 1)]).convert("RGBA")


BEATS = [Hook(-PRE, 3.62), Place(3.62, T_PLAN), Build(T_PLAN, 12.47), Touch(12.47, 13.84), Review(13.84, 16.76), Fix(16.76, 18.17),
         Approved(18.17, 19.09), Close(19.09, END)]

L_S0 = [[("أول شي:", WHITE)], [("نبدأ من", WHITE), ("المكان", TCHIP)]]
L_S1 = [[("صور 360", TCHIP), ("أو", WHITE), ("مخطط", CHIP)]]
L_S2 = [[("نبنيه مجسّم", WHITE)], [("حبّة حبّة", CHIP)]]
L_S3 = [[("نلبّسه", WHITE), ("ألوان", TCHIP), ("وإضاءة", CHIP)]]
CARDS = [
    ([[("كيف وصّلنا الناقة", WHITE)], [("صلالة؟", TCHIP)]], -PRE, 3.62, {"size": 96, "cy": 1500}),
    (L_S0, 3.83, 5.36, {"hidden": {(1, 0), (1, 1)}}),
    (L_S0, 5.24, 6.08, {"fade": True}),
    (L_S1, 6.17, 7.32, {"hidden": {(0, 1), (0, 2)}}),
    (L_S1, 7.20, 8.22, {"fade": True}),
    (L_S2, 8.42, 9.58, {"hidden": {(1, 0)}}),
    (L_S2, 9.46, 10.48, {"fade": True}),
    (L_S3, 10.63, 11.74, {"size": 86, "hidden": {(0, 2)}}),
    (L_S3, 11.62, 12.47, {"size": 86, "fade": True}),
    ([[("ونخليه", WHITE), ("يتفاعل معك", TCHIP)]], 12.54, 13.84, {}),
    ([[("الزبون يجرّب..", WHITE)]], 13.94, 15.42, {}),
    ([[("ويطلب تعديل!", CHIP)]], 15.48, 16.76, {"size": 104}),
    ([[("كبّرنا الشلال..", WHITE)]], 16.85, 18.17, {}),
    ([[("مشروعك", WHITE), ("في عُمان؟", TCHIP)]], 19.35, 20.58, {}),
    ([[("نصممه لك", WHITE)], [("بنفس الخطوات", CHIP)]], 20.63, 22.34, {}),
    ([[("أرسل", WHITE), ("VR", CHIP), ("في الخاص", WHITE)]], 22.34, END, {"size": 98}),
]
STEPS = [(3.62, T_BUILD, step_pill(1, "المكان")), (T_BUILD, T_COLOUR, step_pill(2, "المجسّم")),
         (T_COLOUR, 13.84, step_pill(3, "الألوان والتفاعل")), (13.84, 19.09, step_pill(4, "التجربة والتعديل"))]
CTA = pill("أرسل VR في الخاص", size=46, icon="send")
CTA_TIMES = [(10.70, 13.70, 250), (19.30, 22.34, 150)]  # start, end, y (the last caption card then says it in large type)


def overlays():
    caps = []
    for lines, a, b, opt in CARDS:
        o = dict(opt)
        fade = o.pop("fade", False)
        img, box = caption_layer(lines, **o)
        caps.append((img, box, a, b, fade))
    return caps, handle_layer()


def decorate(img, t, caps, handle):
    for im, box, a, b, fade in caps:
        if a <= t < b:
            k = ease_out((t - a) / 0.14) if a > -PRE else 1.0
            if k < 1 and not fade:
                s = 0.84 + 0.16 * k
                im2 = faded(im.resize((max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s))), Image.LANCZOS), k)
                cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                paste_clip(img, im2, int(cx - im2.size[0] / 2), int(cy - im2.size[1] / 2))
            else:
                img.alpha_composite(faded(im, k) if k < 1 else im, (box[0], box[1]))
    for a, b, p in STEPS:
        if a <= t < b:
            k = min(ease_out((t - a) / 0.2), ease_out((b - t) / 0.15))
            q = faded(p, k)
            paste_clip(img, q, (W - q.size[0]) // 2, int(150 - 20 * (1 - k)))
    for a, b, y in CTA_TIMES:
        if a <= t < b:
            k = min(ease_out((t - a) / 0.25), ease_out((b - t) / 0.2))
            q = faded(CTA, k)
            paste_clip(img, q, (W - q.size[0]) // 2, int(y - 20 * (1 - k)))
    img.alpha_composite(handle)
    return img


# ---- sound ---------------------------------------------------------------------------------------------------------
def mix_audio(path, total, parts=("voice", "music", "ambience", "effects")):
    """Voice, music bed, ambience and effects mixed to `path`. `parts` keeps only some of them, for checking the mix."""
    n = int(total * SR)

    def load(p, start=0.0, dur=None):
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}"] + (["-t", f"{dur:.3f}"] if dur else []) + ["-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
        return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()

    def place(buf, x, t):
        i = max(int((t + PRE) * SR), 0)
        m = min(len(x), n - i)
        if m > 0:
            buf[i:i + m] += x[:m]

    def rms(x):
        return float(np.sqrt((x ** 2).mean()) + 1e-9)

    def fade(x, a=0.05, b=0.10):
        x = x.copy()
        na, nb = int(a * SR), int(b * SR)
        x[:na] *= np.linspace(0, 1, na)[:, None]
        x[-nb:] *= np.linspace(1, 0, nb)[:, None]
        return x

    db = lambda v: 10 ** (v / 20)
    v = load(f"{WORK}/voice/voice_main.wav")
    v = v / max(np.abs(v).max(), 1e-6) * 0.89
    voice = np.zeros((n, 2), np.float32)
    place(voice, v, 0.0)
    speech = rms(v[np.abs(v[:, 0]) > 0.02])
    # The track opens with sparse single hits and its full groove enters at MUSIC_DROP. The groove is placed on the cut
    # to the build; left where it was, one of the opening hits fell on the end of «مجسّم» and blurred the word.
    m = load(f"{WORK}/voice/music.mp3", MUSIC_DROP - (T_BUILD + PRE))
    m = m / max(np.abs(m).max(), 1e-6)
    music = np.zeros((n, 2), np.float32)
    music[: min(n, len(m))] = m[:n]
    t = np.arange(n) / SR - PRE
    i0 = int((T_BUILD + PRE + 0.5) * SR)
    g_groove = speech * db(-15.5) / rms(music[i0: i0 + 12 * SR])  # the groove sits 15.5 dB under the speech
    opening = np.clip((T_BUILD - 0.02 - t) / 0.12, 0, 1)  # 1 before the groove: the sparse opening may sit a little higher
    rise = np.clip((t - (VOICE_END - 0.2)) / 0.6, 0, 1)  # and the bed comes up once he has finished
    g = g_groove * (1 + (db(4) - 1) * opening) * (1 + 1.2 * rise)
    end = min(total, len(m) / SR) - PRE - 0.02
    g = g * np.minimum(np.clip((end - t) / 1.1, 0, 1), np.clip((t + PRE) / 0.25, 0, 1))
    amb = np.zeros((n, 2), np.float32)
    # Ambience changes only on cuts that fall in a pause. In the build the waterfall comes in slowly, after «مجسّم»: the
    # word ends on a soft m and any water noise under it made it unclear. (source, offset, dB, from, to, fade in, fade out)
    for src, s0, lvl, t0, t1, fi, fo in [("v6", 0.6, -38, -PRE, 3.62, 0.06, 0.12), ("v6", 1.2, -37, 3.62, T_PLAN, 0.06, 0.12),
                                         ("v6", 0.2, -38, 9.40, 12.00, 1.0, 0.3), ("v6", 1.3, -38, 11.70, 13.84, 0.3, 0.12),
                                         ("v1", 1.0, -36, 13.84, 16.76, 0.06, 0.12), ("v8", 1.6, -40, 13.84, 16.76, 0.06, 0.12),
                                         ("v6", 2.2, -37, 16.76, 18.17, 0.06, 0.12), ("v1", 0.2, -37, 18.17, 19.09, 0.06, 0.12),
                                         ("v8", 0.05, -39, 19.09, total - PRE, 0.06, 0.12)]:
        need = int((t1 - t0 + 0.12) * SR)
        s = load(f"{WORK}/sfx/sfx_{src}.wav", s0)
        assert len(s) >= need, (src, s0, len(s) / SR, need / SR)  # the ambience clips are 5 s long
        s = s[:need]
        place(amb, fade(s * db(lvl) / rms(s), fi, fo), t0 - 0.03)
    rng = np.random.default_rng(3)

    def whoosh(dur=0.5, lvl=-26):
        m_ = int(dur * SR)
        spec = np.fft.rfft(rng.standard_normal(m_))
        f = np.fft.rfftfreq(m_, 1 / SR)
        spec *= np.exp(-((np.log2(np.maximum(f, 1)) - np.log2(1400)) ** 2) / 1.2)
        w = np.fft.irfft(spec, m_)
        tt = np.linspace(0, 1, m_)
        w *= np.sin(np.pi * tt) ** 2 * (0.6 + 0.4 * tt)
        w = w / (np.abs(w).max() + 1e-9) * db(lvl)
        return np.stack([w * (1 - 0.3 * tt), w * (0.7 + 0.3 * tt)], 1).astype(np.float32)

    def thud(lvl=-20):
        tt = np.arange(int(0.16 * SR)) / SR
        w = np.sin(2 * np.pi * 105 * tt) * np.exp(-tt / 0.045) * db(lvl)
        w[: int(0.004 * SR)] += rng.standard_normal(int(0.004 * SR)) * db(lvl - 8)
        return np.stack([w, w], 1).astype(np.float32)

    fx = np.zeros((n, 2), np.float32)
    for tw, dur in ((8.02, 0.40), (10.33, 0.30), (3.42, 0.40), (13.73, 0.22), (18.84, 0.45)):  # the pauses between phrases
        place(fx, whoosh(dur), tw)
    place(fx, thud(), Approved.T_STAMP + 0.12)  # the stamp lands; the client's note pops in silently, he is mid-phrase there
    bed = music * g[:, None]
    said = np.abs(voice[:, 0]) > 0.02
    before = said & (t < T_BUILD)
    print("levels dBFS  speech %.1f  music under speech: opening %.1f, groove %.1f  ambience %.1f  effects peak %.1f" % (
        20 * np.log10(speech), 20 * np.log10(rms(bed[before])), 20 * np.log10(rms(bed[said & ~before])), 20 * np.log10(rms(amb[said])),
        20 * np.log10(np.abs(fx).max() + 1e-9)), flush=True)
    stems = {"voice": voice, "music": bed, "ambience": amb, "effects": fx}
    out = np.clip(sum(stems[k] for k in parts), -1, 1)
    w = wave.open(path, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((out * 32767).astype("<i2").tobytes())
    w.close()


def make_cover(path, handle):
    """Cover: the opening frame with the slider at rest, a larger title and the subject of the reel above it."""
    hook = Hook(-PRE, 3.62)
    hook.cover = True
    hook.prepare()
    img = hook.frame(8, -PRE + 0.30)
    im, box = caption_layer([[("كيف وصّلنا الناقة", WHITE)], [("صلالة؟", TCHIP)]], size=106, cy=1500)
    img.alpha_composite(im, (box[0], box[1]))
    tag = pill("كيف نصمم الـVR؟", size=54, fill=PURPLE, outline=WHITE)
    paste_clip(img, tag, (W - tag.size[0]) // 2, 262)
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
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-i", mixp, "-filter_complex", "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]", "-map", "0:v", "-map", "[a]",
                                "-t", f"{total:.4f}", "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-maxrate", "12M", "-bufsize", "24M",
                                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    for beat in BEATS:
        want = [n for n in range(beat.n0, beat.n1) if ONLY is None or n in ONLY]
        if not want:
            continue
        beat.prepare()
        for n in want:
            t = n / FPS - PRE
            img = decorate(beat.frame(n - beat.n0, t), t, caps, handle).convert("RGB")
            if enc:
                enc.stdin.write(img.tobytes())
            else:
                img.save(f"{WORK}/check/dbg_{n:04d}.jpg", quality=90)
        beat.release()
    if enc:
        enc.stdin.close()
        assert enc.wait() == 0
        os.remove(OUT + ".mix.wav")
        print("ok", OUT, fno(END), "frames", round(total, 3), "s")


if __name__ == "__main__":
    main()
