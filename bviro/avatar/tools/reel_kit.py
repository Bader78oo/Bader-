"""Shared pieces for the presenter reels: brand constants, Arabic captions with chips, the @bviro.1 handle,
talking-clip reader and small drawing helpers. Imported by the per-episode scripts (reel_360.py, ...)."""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.dirname(os.path.dirname(HERE))  # bviro/
W, H, FPS = 1080, 1920, 30
PURPLE, TURQ, DARK, WHITE = (127, 2, 254), (0, 205, 200), (43, 1, 87), (255, 255, 255)
CHIP, TCHIP = "chip", "tchip"


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


def draw_line(img, segs, font, cy, hidden=(), stroke=10, max_w=900):
    """One right-to-left caption line. segs: (text, colour or CHIP/TCHIP). Segments whose index is in `hidden` keep
    their place but are not drawn, so a line can be revealed piece by piece without anything moving."""
    d = ImageDraw.Draw(img)
    gap, pad = int(font.size * 0.26), int(font.size * 0.20)
    widths = [tw(d, t, font) + (2 * pad if c in (CHIP, TCHIP) else 0) for t, c in segs]
    total = sum(widths) + gap * (len(segs) - 1)
    assert total < max_w, (segs, total)
    x = W / 2 + total / 2
    for k, ((text, col), w) in enumerate(zip(segs, widths)):
        x -= w
        if k not in hidden:
            if col in (CHIP, TCHIP):
                h = int(font.size * 1.18)
                d.rounded_rectangle([x, cy - h / 2 + 4, x + w, cy + h / 2 + 4], radius=int(h * 0.28), fill=PURPLE if col == CHIP else TURQ)
                d.text((x + pad, cy), text, font=font, fill=WHITE if col == CHIP else DARK, anchor="lm", direction="rtl", language="ar")
            else:
                d.text((x, cy), text, font=font, fill=col, anchor="lm", direction="rtl", language="ar", stroke_width=stroke, stroke_fill=DARK)
        x -= gap


def caption_layer(lines, size=92, cy=1465, lead=1.36, hidden=()):
    """Caption as (cropped RGBA image, its box on the frame). hidden: set of (line index, segment index)."""
    font = cairo(size)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    step = int(size * lead)
    y0 = cy - step * (len(lines) - 1) / 2
    for i, segs in enumerate(lines):
        draw_line(layer, segs, font, y0 + i * step, hidden={s for (l, s) in hidden if l == i})
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


def paste_clip(dst, src, x, y):
    """alpha_composite that accepts offsets outside the frame."""
    sx, sy = max(0, -x), max(0, -y)
    dx, dy = max(0, x), max(0, y)
    w, h = min(src.size[0] - sx, dst.size[0] - dx), min(src.size[1] - sy, dst.size[1] - dy)
    if w > 0 and h > 0:
        dst.alpha_composite(src, (dx, dy), (sx, sy, sx + w, sy + h))


def faded(img, k):
    if k >= 1:
        return img
    out = img.copy()
    out.putalpha(out.getchannel("A").point(lambda v: int(v * max(k, 0.0))))
    return out


def send_icon(size, colour):
    """Paper-plane 'send' glyph."""
    s = 4
    im = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    n = size * s
    pts = [(0.06 * n, 0.44 * n), (0.94 * n, 0.08 * n), (0.60 * n, 0.92 * n), (0.46 * n, 0.58 * n)]
    d.polygon(pts, fill=(*colour, 255))
    d.line([(0.46 * n, 0.58 * n), (0.94 * n, 0.08 * n)], fill=(*DARK, 255), width=int(0.05 * n))
    return im.resize((size, size), Image.LANCZOS)


def pill(text, size=44, fill=DARK, outline=TURQ, colour=WHITE, icon=None):
    """Small rounded label with optional icon on its right (RTL)."""
    f = tajawal(size)
    d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    t = int(tw(d0, text, f))
    ic = send_icon(int(size * 1.05), TURQ) if icon == "send" else None
    h = int(size * 1.9)
    w = t + (ic.size[0] + 16 if ic else 0) + int(size * 1.3)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(*fill, 232), outline=(*outline, 255), width=3)
    x = w - int(size * 0.65)
    if ic:
        im.alpha_composite(ic, (x - ic.size[0], (h - ic.size[1]) // 2))
        x -= ic.size[0] + 16
    d.text((x, h / 2 + 2), text, font=f, fill=colour, anchor="rm", direction="rtl", language="ar")
    return im


class Clip:
    """Sequential reader of a talking clip, resampled to FPS and fitted to the frame."""

    def __init__(self, path, start):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{max(start, 0):.4f}", "-i", path, "-vf",
                                   f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}",
                                   "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.last = None

    def read(self):
        raw = self.p.stdout.read(W * H * 3)
        if len(raw) == W * H * 3:
            self.last = Image.frombuffer("RGB", (W, H), raw, "raw", "RGB", 0, 1).copy()
        assert self.last is not None, "clip gave no frames"
        return self.last

    def close(self):
        self.p.kill()
        self.p.stdout.close()
        self.p.wait()


def punch(im, z, cy=560.0, cx=540.0):
    """Digital push-in that keeps the point (cx, cy) in place."""
    if z <= 1.0005:
        return im
    w, h = W / z, H / z
    x0 = min(max(cx - w * (cx / W), 0), W - w)
    y0 = min(max(cy - h * (cy / H), 0), H - h)
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
