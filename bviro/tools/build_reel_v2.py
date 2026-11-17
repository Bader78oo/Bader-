"""Bviro camel Reel v2 (after the virality test): motion from frame 1, Salalah reveal at 4.75 s, snap-zoom on the sand gag,
brand ending over live footage. 1080x1920, 24 fps, 450 frames (18.75 s).
usage: python3 -I build_reel_v2.py OUT_SILENT.mp4"""
import math, subprocess, sys
import numpy as np
from PIL import Image

S = "/tmp/claude-0/-home-user-Bader-/871f84b2-2289-5b97-9b32-a74e478b68cd/scratchpad/bviro"
W, H, FPS = 1080, 1920, 24
FIT = "scale=1080:-2:flags=lanczos,crop=1080:1920,setsar=1"
GRADE = "eq=saturation=1.08:contrast=1.04"
SHOTS = [
    ("v1", 55, 66, FIT),     # 0     camel close-up (hook)
    ("v4", 38, 48, FIT),     # 66    owner baffled
    ("v11", 10, 48, FIT),    # 114   Salalah, camel from behind
    ("v5", 50, 68, "scale=1674:-2:flags=lanczos,crop=1080:1920:297:0,setsar=1"),  # 162 waterfall
    ("v7", 0, 62, FIT),      # 230   grazing on sand (snap-zoom at local frame 22)
    ("v9", 57, 64, FIT),     # 292   role reversal
    ("v2", 0, 94, FIT),      # 356   camel close-up under the brand ending
]
CUTS = np.cumsum([n for _, _, n, _ in SHOTS]).tolist()      # 66 114 162 230 292 356 450
TOTAL = CUTS[-1]
assert TOTAL == 450, TOTAL
CAPS = [("t1", 0, 63), ("t2", 69, 111), ("t3a", 117, 159), ("t3b", 165, 227), ("t4", 233, 289), ("t5", 295, 353)]
FLASH = (114, 230)
VR = (114, 230)


def read_shot(src, f0, n, vf):
    cmd = ["ffmpeg", "-v", "error", "-i", f"{S}/vid/{src}.mp4", "-vf",
           f"select='between(n\\,{f0}\\,{f0 + n - 1})',setpts=N/{FPS}/TB,{vf},{GRADE}", "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    fr = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.uint8).reshape(-1, H, W, 3)
    assert len(fr) == n, (src, len(fr), n)
    return fr


def zoom(frame, z, cx=0.5, cy=0.5):
    if z <= 1.0005:
        return frame.astype(np.float32)
    w, h = W / z, H / z
    x0 = min(max(cx * W - w / 2, 0), W - w); y0 = min(max(cy * H - h / 2, 0), H - h)
    im = Image.fromarray(frame).resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
    return np.asarray(im, np.float32)


class Layer:
    def __init__(self, name):
        im = Image.open(f"{S}/ov2/{name}.png").convert("RGBA")
        self.box = im.getchannel("A").getbbox(); self.im = im.crop(self.box)
        self.cx = (self.box[0] + self.box[2]) / 2; self.cy = (self.box[1] + self.box[3]) / 2

    def draw(self, frame, scale=1.0, alpha=1.0):
        if alpha <= 0.003:
            return
        im = self.im
        if abs(scale - 1) > 1e-3:
            im = im.resize((max(1, round(im.size[0] * scale)), max(1, round(im.size[1] * scale))), Image.BICUBIC)
        x0 = round(self.cx - im.size[0] / 2); y0 = round(self.cy - im.size[1] / 2)
        a = np.asarray(im, np.float32)
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + im.size[0]), min(H, y0 + im.size[1])
        a = a[ya - y0:yb - y0, xa - x0:xb - x0]
        k = a[..., 3:4] / 255.0 * alpha
        frame[ya:yb, xa:xb] = frame[ya:yb, xa:xb] * (1 - k) + a[..., :3] * k


def back(t):
    t = min(max(t, 0.0), 1.0); c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def main():
    out = sys.argv[1]
    shots = [read_shot(*s) for s in SHOTS]
    caps = [(Layer(n), a, b) for n, a, b in CAPS]
    grad, top, srv, cta = (Layer(n) for n in ("end_grad", "end_top", "end_srv", "end_cta"))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = np.clip((((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.60)) ** 2 - 0.62) / 0.5, 0, 1)[..., None] * 0.42
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p", "-r", str(FPS), out], stdin=subprocess.PIPE)
    starts = [0] + CUTS[:-1]
    for i in range(TOTAL):
        s = max(k for k, st in enumerate(starts) if st <= i); j = i - starts[s]; n = SHOTS[s][2]
        raw = shots[s][j]
        if s == 0:      # hook: visible push-in from the very first frame (fast at first, then easing)
            f = zoom(raw, 1 + 0.11 * (1 - (1 - j / (n - 1)) ** 2.2), 0.5, 0.50)
        elif s == 4:    # sand gag: wide for 22 frames, then snap-zoom onto the camel's head and hold
            f = zoom(raw, 1 + 0.48 * smooth((j - 21) / 4.0), 0.64, 0.44)
        elif s == 6:    # ending: gentle push on the camel under the brand
            f = zoom(raw, 1 + 0.05 * j / (n - 1), 0.5, 0.42)
        else:
            f = raw.astype(np.float32)
        if VR[0] <= i < VR[1]:
            f *= (1 - vig)
        for lay, a, b in caps:
            if a <= i <= b:
                sc = 0.84 + 0.16 * back((i - a) / 5.0) if i > 0 else 0.97
                al = (min(1.0, (i - a + 1) / 2.0) if i > 0 else 1.0) * min(1.0, (b - i + 1) / 3.0)
                lay.draw(f, scale=sc, alpha=al)
        if s == 6:      # brand visible from the first frame of the ending
            a = smooth((j + 1) / 5.0)
            grad.draw(f, alpha=a); top.draw(f, alpha=a); srv.draw(f, alpha=a)
            cta.draw(f, scale=(0.9 + 0.1 * back(j / 6.0)) * (1 + 0.03 * math.sin(max(0, j - 10) / 24.0 * 2 * math.pi * 1.4)), alpha=a)
        for c in FLASH:
            d = i - c
            if -2 <= d <= 3:
                w = {-2: 0.22, -1: 0.55, 0: 0.85, 1: 0.5, 2: 0.22, 3: 0.08}[d]
                f = f * (1 - w) + 255.0 * w
        enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    print("wrote", out, TOTAL, "frames; cuts", CUTS)


main()
