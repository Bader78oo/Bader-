"""A flag as simulated cloth, textured with the exact flag artwork.

The cloth is a grid of particles pinned along the hoist, pushed by a gusty wind and pulled by gravity (position-based
dynamics). Each frame is rendered by projecting the cloth with a low camera and warping the official design onto it,
so nothing redraws the emblem: it is always the real artwork, folded by the cloth.

usage: python3 -I flag_sim.py FLAG_PNG SKY_PHOTO OUT_MP4 [seconds] [seed] [scale] [origin_x origin_y]
"""
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS = 1080, 1920, 24
L, HH = 2.0, 1.0  # the flag is 1:2


def simulate(seconds, nu=96, nv=48, seed=1, warm=6.0, wind=7.5, sub=14, iters=14):
    """Particle positions (frames, nv, nu, 3); x along the fly, y up, z toward the camera."""
    rng = np.random.default_rng(seed)
    du, dv = L / (nu - 1), HH / (nv - 1)
    dd = np.hypot(du, dv)
    u = np.linspace(0, L, nu)
    v = np.linspace(0, -HH, nv)
    P = np.zeros((nv, nu, 3))
    P[..., 0], P[..., 1] = u[None, :], v[:, None]
    P[..., 2] = 0.03 * np.sin(2.2 * u)[None, :] * (u / L)[None, :]
    pin = P[:, 0].copy()
    prev = P.copy()
    dt = 1.0 / (FPS * sub)
    g = np.array([0.0, -2.6, 0.0])
    ph = rng.uniform(0, 2 * np.pi, 8)
    frames = []
    steps = int((warm + seconds) * FPS * sub)
    for step in range(steps):
        t = step * dt
        tu, tv = np.gradient(P, axis=1), np.gradient(P, axis=0)
        n = np.cross(tu, tv)
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
        vel = (P - prev) / dt
        x, y = P[..., 0], P[..., 1]
        gust = 1.0 + 0.22 * np.sin(0.7 * t + ph[0]) + 0.12 * np.sin(1.9 * t + ph[1])
        w = np.zeros_like(P)
        w[..., 0] = wind * gust
        # turbulence carried along by the wind: it is what makes the cloth ripple
        w[..., 2] = wind * (0.42 * np.sin(2 * np.pi * (0.95 * t - 0.55 * x) + 2.1 * y + ph[2])
                            + 0.24 * np.sin(2 * np.pi * (2.10 * t - 1.25 * x) - 3.0 * y + ph[3])
                            + 0.12 * np.sin(2 * np.pi * (3.70 * t - 2.30 * x) + 5.0 * y + ph[4]))
        w[..., 1] = wind * (0.10 * np.sin(1.1 * t + ph[5]) + 0.08 * np.sin(2 * np.pi * (0.6 * t - 0.4 * x) + ph[6]))
        rel = w - vel
        acc = g + 9.0 * (rel * n).sum(-1, keepdims=True) * n
        new = P + (P - prev) * 0.994 + acc * dt * dt
        new[:, 0] = pin
        for _ in range(iters):
            for off in (0, 1):  # along the fly
                a, b = new[:, off:-1:2], new[:, off + 1::2]
                d = b - a
                ln = np.linalg.norm(d, axis=-1, keepdims=True) + 1e-9
                c = d * ((ln - du) / ln * 0.5)
                a += c
                b -= c
                new[:, 0] = pin
            for off in (0, 1):  # along the hoist
                a, b = new[off:-1:2], new[off + 1::2]
                d = b - a
                ln = np.linalg.norm(d, axis=-1, keepdims=True) + 1e-9
                c = d * ((ln - dv) / ln * 0.5)
                a += c
                b -= c
                new[:, 0] = pin
            for (sa, sb) in ((new[:-1, :-1], new[1:, 1:]), (new[1:, :-1], new[:-1, 1:])):  # shear, relaxed
                d = sb - sa
                ln = np.linalg.norm(d, axis=-1, keepdims=True) + 1e-9
                c = d * ((ln - dd) / ln * 0.12)
                sa += c
                sb -= c
                new[:, 0] = pin
        prev, P = P, new
        if t >= warm and step % sub == 0:
            frames.append(P.astype(np.float32).copy())
    return np.stack(frames[: int(seconds * FPS)])


def sky_from_photo(path, box, wide=1.2):
    """A soft, out-of-focus sky plate made from the sky area of a real photograph."""
    im = Image.open(path).convert("RGB").crop(box)
    im = im.resize((int(W * wide) // 8, H // 8), Image.LANCZOS)  # drop the photo's fine detail and compression blocks first
    im = im.resize((int(W * wide), H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(14))
    return np.asarray(im, np.float32)


class Renderer:
    def __init__(self, flag_png, sky_plate, tex_w=2600, yaw=24.0, pitch=17.0, dist=5.2, scale=1050.0, origin=(210, 470)):
        tex = Image.open(flag_png).convert("RGB").resize((tex_w, tex_w // 2), Image.LANCZOS)
        self.tex = (np.asarray(tex, np.float32) / 255.0).reshape(-1, 3)
        self.wu, self.hv = tex_w, tex_w // 2
        rng = np.random.default_rng(4)
        wv = np.asarray(Image.fromarray((rng.random((self.hv // 2, self.wu // 2)) * 255).astype(np.uint8)).resize((self.wu, self.hv), Image.BILINEAR), np.float32) / 255.0
        self.weave = (1.0 + (wv - 0.5) * 0.06).reshape(-1)
        self.sky = sky_plate
        cy, sy_ = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
        cp, sp = np.cos(np.radians(pitch)), np.sin(np.radians(pitch))
        ry = np.array([[cy, 0, -sy_], [0, 1, 0], [sy_, 0, cy]], np.float32)  # the fly end swings away from the camera
        rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], np.float32)  # the camera looks up at the flag
        self.R = rx @ ry
        self.dist, self.scale, self.origin = dist, scale, origin
        self.light = np.array([-0.45, 0.50, 0.74], np.float32)
        self.light /= np.linalg.norm(self.light)

    def project(self, P):
        q = P @ self.R.T
        k = self.dist / (self.dist - q[..., 2])
        return self.origin[0] + q[..., 0] * k * self.scale / 2.0, self.origin[1] - q[..., 1] * k * self.scale / 2.0, q[..., 2]

    def frame(self, P, drift=0.0):
        nv, nu = P.shape[:2]
        up = np.stack([np.asarray(Image.fromarray(P[..., c]).resize((self.wu, self.hv), Image.BICUBIC)) for c in range(3)], -1)
        tu, tv = np.gradient(up, axis=1), np.gradient(up, axis=0)
        n = np.cross(tu, tv)
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
        n = n @ self.R.T
        ndl = n @ self.light
        facing = np.sign(n[..., 2] + 1e-6)  # the side of the cloth turned to the camera
        lit = np.clip(ndl * facing, 0, 1)  # light falling on the visible side
        through = np.clip(-ndl * facing, 0, 1)  # light coming through the cloth from behind
        shade = 0.30 + 0.80 * lit + 0.42 * through
        sx, sy, depth = self.project(up)
        col = self.tex * (shade.reshape(-1) * self.weave)[:, None]
        col += (lit.reshape(-1) ** 20)[:, None] * 0.08
        ix, iy = np.rint(sx).astype(np.int64).reshape(-1), np.rint(sy).astype(np.int64).reshape(-1)
        ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
        idx = iy[ok] * W + ix[ok]
        order = np.argsort(depth.reshape(-1)[ok], kind="stable")  # far first, so the nearest sample is written last
        canvas = np.zeros((W * H, 3), np.float32)
        canvas[idx[order]] = col[ok][order]
        cnt = np.bincount(idx, minlength=W * H).astype(np.float32)
        alpha = np.clip(cnt / 1.5, 0, 1).reshape(H, W)
        off = int((self.sky.shape[1] - W) * (0.5 + 0.5 * np.clip(drift, -1, 1)))
        out = self._pole(self.sky[:, off:off + W].copy(), P)
        a_img = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.9))
        a = np.asarray(a_img, np.float32)[..., None] / 255.0
        # blur the colours together with their coverage and divide, so that the empty pixels around the cloth do not
        # darken its edge; the same step fills pin-holes inside the cloth from their neighbours
        have = (cnt > 0).reshape(H, W)
        pre = (np.clip(canvas.reshape(H, W, 3), 0, 1) * 255 * have[..., None]).astype(np.uint8)
        cb = np.asarray(Image.fromarray(pre).filter(ImageFilter.GaussianBlur(1.2)), np.float32)
        mb = np.asarray(Image.fromarray((have * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None]
        spread = cb * 255.0 / np.maximum(mb, 1.0)
        sharp = np.asarray(Image.fromarray(pre).filter(ImageFilter.GaussianBlur(0.6)), np.float32)
        ms = np.asarray(Image.fromarray((have * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)), np.float32)[..., None]
        rgb = np.where(ms > 250, sharp, spread)
        return np.clip(out * (1 - a) + rgb * a, 0, 255).astype(np.uint8)

    def _pole(self, img, P):
        """White pole along the hoist, widening toward the bottom of the frame (seen from below)."""
        xt, yt, _ = self.project(P[0, 0][None, :])
        xb, yb, _ = self.project(P[-1, 0][None, :])
        xt, yt, xb, yb = float(xt[0]), float(yt[0]), float(xb[0]), float(yb[0])
        dx = (xb - xt) / max(yb - yt, 1e-6)
        top = int(yt - 0.10 * (yb - yt))
        base = np.array((228, 230, 246), np.float32)
        for y in range(max(top, 0), H):
            k = (y - top) / max(H - top, 1)
            wd = 30.0 + 80.0 * k ** 1.2
            xr = xt + dx * (y - yt) - 3
            xa = xr - wd
            xs = np.arange(max(int(xa), 0), min(int(xr) + 1, W))
            if len(xs) == 0:
                continue
            uu = (xs - xa) / wd
            lum = 0.46 + 0.58 * np.sin(np.pi * np.clip(uu * 0.85 + 0.04, 0, 1)) ** 0.9 - 0.14 * uu
            edge = np.clip(np.minimum(uu, 1 - uu) * wd / 1.5, 0, 1)[:, None]
            img[y, xs] = img[y, xs] * (1 - edge) + np.clip(base[None, :] * lum[:, None], 0, 255) * edge
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        cx = xt + dx * (top - yt) - 18
        d.ellipse([cx - 21, top - 18, cx + 21, top + 16], fill=(232, 234, 248))
        return np.asarray(im, np.float32)


def render_clip(flag_png, sky_photo, sky_box, out, seconds=5.0, seed=1, **cam):
    """sky_box must be a part of the photo that shows only sky (no flag, no buildings)."""
    sim = simulate(seconds, seed=seed)
    r = Renderer(flag_png, sky_from_photo(sky_photo, sky_box), **cam)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-crf", "13", "-preset", "medium", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i, P in enumerate(sim):
        enc.stdin.write(r.frame(P, drift=-1 + 2 * i / max(len(sim) - 1, 1)).tobytes())
    enc.stdin.close()
    assert enc.wait() == 0
    return len(sim)


if __name__ == "__main__":
    secs = float(sys.argv[4]) if len(sys.argv) > 4 else 5.0
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    scale = float(sys.argv[6]) if len(sys.argv) > 6 else 800.0
    ox, oy = (int(sys.argv[7]), int(sys.argv[8])) if len(sys.argv) > 8 else (150, 520)
    print("ok", sys.argv[3], render_clip(sys.argv[1], sys.argv[2], (800, 20, 1195, 380), sys.argv[3], secs, seed, scale=scale, origin=(ox, oy)), "frames")
