"""Assemble the Bviro camel Reel: 1080x1920, 24 fps, 480 frames (20.0 s).

usage: python3 -I build_reel.py OUT_SILENT.mp4
Shots are cut to exact frame counts, captions pop in over each shot, white flashes mark entering/leaving the VR world,
and the brand outro is animated from the layers rendered by overlays.py.
"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image

S = "/tmp/claude-0/-home-user-Bader-/871f84b2-2289-5b97-9b32-a74e478b68cd/scratchpad/bviro"
W, H, FPS = 1080, 1920, 24
FIT = "scale=1080:-2:flags=lanczos,crop=1080:1920,setsar=1"
GRADE = "eq=saturation=1.08:contrast=1.04"

# (source, first frame, frame count, extra filter)
SHOTS = [
    ("v1", 48, 73, FIT),                                                       # camel close-up, leans into the lens
    ("v4", 24, 70, FIT),                                                       # owner: baffled, looks at camera
    ("v11", 10, 45, FIT),                                                       # khareef, camel looks around
    ("v5", 50, 71, "scale=1674:-2:flags=lanczos,crop=1080:1920:297:0,setsar=1"),  # khareef punch-in on the waterfall
    ("v7", 0, 52, FIT),                                                        # grazing on bare sand
    ("v9", 53, 68, FIT),                                                       # role reversal
]
OUTRO = 101
CUTS = np.cumsum([n for _, _, n, _ in SHOTS])            # 73 143 188 259 311 379
TOTAL = int(CUTS[-1]) + OUTRO
assert TOTAL == 480, TOTAL

# caption: (overlay name, first frame, last frame)
CAPS = [("t1", 0, 70), ("t2", 76, 140), ("t3a", 146, 185), ("t3b", 191, 256), ("t4", 262, 308), ("t5", 314, 376)]
FLASH = {143: 1.0, 259: 1.0}                             # cut frame -> strength
VR = (143, 259)                                          # frames inside the headset world (soft vignette)


def read_shot(src, f0, n, vf):
    cmd = ["ffmpeg", "-v", "error", "-i", f"{S}/vid/{src}.mp4", "-vf",
           f"select='between(n\\,{f0}\\,{f0 + n - 1})',setpts=N/{FPS}/TB,{vf},{GRADE}", "-frames:v", str(n),
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    assert len(fr) == n, (src, len(fr), n)
    return fr


class Layer:
    """An RGBA overlay cropped to its bounding box; can be drawn scaled about its centre with a given opacity."""

    def __init__(self, name):
        im = Image.open(f"{S}/ov/{name}.png").convert("RGBA")
        self.box = im.getchannel("A").getbbox()
        self.im = im.crop(self.box)
        self.cx = (self.box[0] + self.box[2]) / 2
        self.cy = (self.box[1] + self.box[3]) / 2

    def draw(self, frame, scale=1.0, alpha=1.0, dy=0.0):
        if alpha <= 0.003:
            return
        im = self.im
        if abs(scale - 1) > 1e-3:
            im = im.resize((max(1, round(im.size[0] * scale)), max(1, round(im.size[1] * scale))), Image.BICUBIC)
        x0 = round(self.cx - im.size[0] / 2)
        y0 = round(self.cy - im.size[1] / 2 + dy)
        a = np.asarray(im, np.float32)
        xa, ya = max(0, x0), max(0, y0)
        xb, yb = min(W, x0 + im.size[0]), min(H, y0 + im.size[1])
        if xa >= xb or ya >= yb:
            return
        a = a[ya - y0:yb - y0, xa - x0:xb - x0]
        k = a[..., 3:4] / 255.0 * alpha
        reg = frame[ya:yb, xa:xb]
        reg[:] = reg * (1 - k) + a[..., :3] * k


def ease_out_back(t):
    t = min(max(t, 0.0), 1.0)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def main():
    out = sys.argv[1]
    shots = [read_shot(*s) for s in SHOTS]
    base = np.concatenate(shots)
    caps = [(Layer(n), a, b) for n, a, b in CAPS]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = np.clip((((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.60)) ** 2 - 0.62) / 0.5, 0, 1)[..., None] * 0.42

    bg = np.asarray(Image.open(f"{S}/ov/outro_bg.png").convert("RGB"), np.float32)
    sym, word, tag, srv, cta = (Layer(n) for n in ("outro_sym", "outro_word", "outro_tag", "outro_srv", "outro_cta"))

    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p", "-r", str(FPS), out],
                           stdin=subprocess.PIPE)
    last = None
    for i in range(TOTAL):
        if i < len(base):
            f = base[i].astype(np.float32)
            if VR[0] <= i < VR[1]:
                f *= (1 - vig)
            for lay, a, b in caps:
                if a <= i <= b:
                    t_in = (i - a) / 5.0
                    sc = 0.84 + 0.16 * ease_out_back(t_in) if i > 0 else 0.97   # frame 0 is already readable
                    al = min(1.0, (i - a + 1) / 2.0) if i > 0 else 1.0
                    al *= min(1.0, (b - i + 1) / 3.0)
                    lay.draw(f, scale=sc, alpha=al)
            last = f
        else:
            j = i - len(base)                                  # outro local frame
            k = smooth((j + 1) / 5.0)
            f = last * (1 - k) + bg * k if k < 1 else bg.copy()
            sym.draw(f, scale=max(0.01, ease_out_back((j - 1) / 10.0)), alpha=smooth((j - 1) / 4.0))
            word.draw(f, alpha=smooth((j - 8) / 8.0), dy=22 * (1 - smooth((j - 8) / 8.0)))
            tag.draw(f, alpha=smooth((j - 22) / 8.0), dy=26 * (1 - smooth((j - 22) / 8.0)))
            srv.draw(f, alpha=smooth((j - 44) / 8.0))
            pulse = 1 + 0.025 * math.sin((j - 66) / 24.0 * 2 * math.pi * 1.5) if j > 66 else 1
            cta.draw(f, scale=max(0.01, ease_out_back((j - 56) / 10.0)) * pulse, alpha=smooth((j - 56) / 4.0))
        for c, strength in FLASH.items():
            d = i - c
            if -2 <= d <= 3:
                w = {-2: 0.22, -1: 0.55, 0: 0.85, 1: 0.5, 2: 0.22, 3: 0.08}[d] * strength
                f = f * (1 - w) + 255.0 * w
        enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", out, TOTAL, "frames; cuts at", CUTS.tolist())


main()
