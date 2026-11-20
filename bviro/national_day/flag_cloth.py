"""A waving flag rendered from the exact flag artwork.

Every frame is a geometric warp of the official design (no model redraws anything), so the emblem and the colours
are always the real ones. The cloth is a height field of travelling waves: amplitude grows from the hoist to the
fly, folds foreshorten the cloth, and the lighting comes from the surface normal.

usage as a tool: python3 -I flag_cloth.py FLAG_PNG OUT_MP4 [dusk|gold] [seconds]
"""
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS = 1080, 1920, 24
TAU = 2 * np.pi


def fbm(rng, w, h, octaves=5, base=4):
    """Soft cloud-like noise in 0..1."""
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * 2 ** o
        small = Image.fromarray((rng.random((n * h // w + 2, n + 2)) * 255).astype(np.uint8))
        out += amp * np.asarray(small.resize((w, h), Image.BICUBIC), np.float32) / 255.0
        tot += amp
        amp *= 0.5
    return out / tot


def sky(palette, seed=5, wide=1.25):
    """A sky plate wider than the frame, so that it can drift slowly."""
    rng = np.random.default_rng(seed)
    w = int(W * wide)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    stops = {"dusk": [(0.0, (22, 34, 92)), (0.45, (58, 70, 150)), (0.75, (150, 110, 170)), (1.0, (232, 160, 150))],
             "gold": [(0.0, (38, 84, 160)), (0.40, (96, 148, 214)), (0.72, (238, 196, 156)), (1.0, (255, 214, 150))]}[palette]
    grad = np.zeros((H, 1, 3), np.float32)
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        k = np.clip((yy - a) / (b - a), 0, 1)[..., None]
        m = ((yy >= a) & (yy <= b))[..., None]
        grad = np.where(m, np.array(ca, np.float32) * (1 - k) + np.array(cb, np.float32) * k, grad)
    img = np.repeat(grad, w, axis=1)
    c = fbm(rng, w, H)
    c = np.clip((c - 0.50) / 0.22, 0, 1) ** 1.4  # wisps
    c *= np.clip((yy - 0.18) / 0.5, 0, 1) * 0.9 + 0.1  # more cloud toward the horizon
    tint = np.array({"dusk": (236, 160, 176), "gold": (255, 236, 206)}[palette], np.float32)
    img = img * (1 - 0.55 * c[..., None]) + tint * 0.55 * c[..., None]
    return np.clip(img, 0, 255)


def sky_from_photo(path, box, wide=1.25):
    """A soft, out-of-focus sky plate made from the sky area of a real photograph (box = x0, y0, x1, y1)."""
    im = Image.open(path).convert("RGB").crop(box)
    w = int(W * wide)
    im = im.resize((w, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(9))
    return np.asarray(im, np.float32)


class Flag:
    def __init__(self, flag_png, x0=150, y0=330, length=900, tilt=0.13, palette="dusk", seed=5, tex_w=3000, sky_plate=None):
        tex = Image.open(flag_png).convert("RGB").resize((tex_w, tex_w // 2), Image.LANCZOS)
        self.tex = np.asarray(tex, np.float32) / 255.0
        hv, wu = self.tex.shape[:2]
        self.U, self.V = np.meshgrid((np.arange(wu) + 0.5) / wu, (np.arange(hv) + 0.5) / hv)
        self.wu, self.hv = wu, hv
        self.x0, self.y0, self.L, self.tilt = x0, y0, length, tilt
        self.Hs = length / 2.0  # the flag is 1:2
        rng = np.random.default_rng(seed)
        weave = np.asarray(Image.fromarray((rng.random((hv // 2, wu // 2)) * 255).astype(np.uint8)).resize((wu, hv), Image.BILINEAR), np.float32) / 255.0
        self.weave = 1.0 + (weave - 0.5) * 0.05
        self.sky = sky_plate if sky_plate is not None else sky(palette, seed)
        self.palette = palette
        self.light = np.array({"dusk": (-0.42, -0.30, 0.86), "gold": (-0.50, -0.34, 0.80)}[palette], np.float32)
        self.light /= np.linalg.norm(self.light)
        self.tint = np.array({"dusk": (0.97, 0.96, 1.03), "gold": (1.04, 1.00, 0.94)}[palette], np.float32)

    def cloth(self, t):
        U, V = self.U, self.V
        gust = 0.82 + 0.18 * np.sin(TAU * 0.17 * t + 0.6)
        amp = U ** 0.85
        p1 = TAU * (1.15 * U - 0.46 * t) + 2.6 * V  # the big folds run diagonally, top-hoist to bottom-fly
        p2 = TAU * (2.45 * U - 0.88 * t) - 1.4 * V + 1.3
        p3 = TAU * (4.70 * U - 1.50 * t) + 3.4 * V + 0.5
        p4 = TAU * (0.55 * U - 0.23 * t) - 0.8 * V + 2.0  # slow billow of the whole cloth
        Z = gust * amp * (np.sin(p1) + 0.50 * np.sin(p2) + 0.17 * np.sin(p3) + 0.55 * np.sin(p4))
        zs = 0.085
        dZu = np.gradient(Z, axis=1) * self.wu * zs
        dZv = np.gradient(Z, axis=0) * self.hv * zs * 2.0
        return Z, dZu, dZv, zs

    def frame(self, t, drift=0.0):
        """RGB uint8 frame: sky, pole and the flag at time t."""
        Z, dZu, dZv, zs = self.cloth(t)
        fore = 1.0 / np.sqrt(1.0 + dZu * dZu)  # a fold seen from the front is shorter
        X = np.cumsum(fore, axis=1) / self.wu * self.L * 1.22
        sway = 0.02 * np.sin(TAU * 0.11 * t)  # the whole flag rises and falls a little
        Yc = ((self.V - 0.5) * self.Hs * (1.0 - 0.04 * Z) + (0.13 + sway) * self.U ** 1.6 * self.Hs + Z * zs * self.L * 0.50)
        far = 1.0 / (1.0 + 0.30 * X / self.L)  # seen from below-left: the fly end is farther away
        sx = self.x0 + X * (0.55 + 0.45 * far)
        sy = self.y0 + self.Hs / 2 + Yc * far + self.tilt * X
        # lighting from the surface normal
        n = np.stack([-dZu, -dZv, np.ones_like(dZu)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        diff = np.clip(n @ self.light, 0, 1)
        shade = 0.30 + 0.84 * diff
        k = 90  # troughs sit in shadow: compare the height with its local average along the cloth
        cs = np.cumsum(np.pad(Z, ((0, 0), (k, k)), mode="edge"), axis=1)
        local = (cs[:, 2 * k:] - cs[:, :-2 * k]) / (2 * k)
        shade *= np.clip(1.0 + 0.55 * (Z - local), 0.62, 1.10)
        col = self.tex * (shade * self.weave)[..., None] * self.tint
        col += (diff ** 18)[..., None] * 0.09  # soft sheen on the crests
        # splat the cloth samples into the frame
        ix, iy = np.rint(sx).astype(np.int64), np.rint(sy).astype(np.int64)
        ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
        idx = (iy[ok] * W + ix[ok])
        cnt = np.bincount(idx, minlength=W * H).astype(np.float32)
        acc = np.stack([np.bincount(idx, weights=col[..., c][ok], minlength=W * H) for c in range(3)], -1).astype(np.float32)
        alpha = np.clip(cnt / 2.0, 0, 1).reshape(H, W)
        rgb = (acc / np.maximum(cnt, 1)[:, None]).reshape(H, W, 3)
        # background
        off = int((self.sky.shape[1] - W) * (0.5 + 0.5 * np.clip(drift, -1, 1)))
        out = self.sky[:, off:off + W].copy()
        out = self._pole(out)
        a = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32)[..., None] / 255.0
        out = out * (1 - a) + np.clip(rgb, 0, 1) * 255.0 * a
        return np.clip(out, 0, 255).astype(np.uint8)

    def _pole(self, img):
        """White pole seen from below: it leans and widens toward the bottom of the frame, lit from the left."""
        top = self.y0 - 40
        px = img.copy()
        base = np.array({"dusk": (226, 228, 246), "gold": (252, 246, 236)}[self.palette], np.float32)
        for y in range(max(top, 0), H):
            k = (y - top) / max(H - top, 1)
            w = 34.0 + 96.0 * k ** 1.15
            xr = self.x0 - 4 - 62.0 * k ** 1.2
            xa, xb = int(xr - w), int(xr)
            xs = np.arange(max(xa, 0), min(xb, W))
            if len(xs) == 0:
                continue
            u = (xs - xa) / max(xb - xa, 1)
            lum = 0.50 + 0.52 * np.sin(np.pi * np.clip(u * 0.85 + 0.05, 0, 1)) ** 0.9 - 0.16 * u
            edge = np.clip(np.minimum(u, 1 - u) * (xb - xa) / 1.5, 0, 1)[:, None]
            px[y, xs] = px[y, xs] * (1 - edge) + np.clip(base[None, :] * lum[:, None], 0, 255) * edge
        im = Image.fromarray(np.clip(px, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        d.ellipse([self.x0 - 44, top - 16, self.x0 + 2, top + 14], fill=tuple(int(c) for c in base))  # cap
        return np.asarray(im, np.float32)


def main():
    flag_png, out = sys.argv[1], sys.argv[2]
    palette = sys.argv[3] if len(sys.argv) > 3 else "dusk"
    secs = float(sys.argv[4]) if len(sys.argv) > 4 else 5.0
    f = Flag(flag_png, palette=palette)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = int(secs * FPS)
    for i in range(n):
        t = i / FPS
        # two sub-frames give a little motion blur on the fast ripples
        a = f.frame(t, drift=-1 + 2 * i / max(n - 1, 1)).astype(np.float32)
        b = f.frame(t + 0.5 / FPS, drift=-1 + 2 * i / max(n - 1, 1)).astype(np.float32)
        enc.stdin.write(((a + b) / 2).astype(np.uint8).tobytes())
    enc.stdin.close()
    assert enc.wait() == 0
    print("ok", out, n, "frames")


if __name__ == "__main__":
    main()
