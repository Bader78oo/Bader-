"""Picture for Reel 2 («الجو نزل درجتين»). usage: python3 -I build_r2.py VARIANT(A|B|C) OUT_SILENT.mp4
Hard cuts only, captions pop in with the voice, the small @bviro.1 mark appears from the reveal, the file ends on movement (loop)."""
import math, os, subprocess, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_r2 as T

W, H, FPS = 1080, 1920, T.FPS
FIT = "scale=1080:-2:flags=lanczos,crop=1080:1920,setsar=1"
GRADE = "eq=saturation=1.06:contrast=1.03"


def read_clip(src):
    cmd = ["ffmpeg", "-v", "error", "-i", f"{T.R}/vid/{src}.mp4", "-vf", f"{FIT},{GRADE}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.uint8).reshape(-1, H, W, 3)


def zoom(frame, z, cx=0.5, cy=0.5, dx=0.0, dy=0.0):
    if z <= 1.0005 and not dx and not dy:
        return frame.astype(np.float32)
    w, h = W / z, H / z
    x0 = min(max(cx * W - w / 2 + dx, 0), W - w)
    y0 = min(max(cy * H - h / 2 + dy, 0), H - h)
    return np.asarray(Image.fromarray(frame).resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h)), np.float32)


class Layer:
    def __init__(self, name):
        im = Image.open(f"{T.R}/ov/{name}.png").convert("RGBA")
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
    variant, out = sys.argv[1], sys.argv[2]
    SWAP = dict(a.split('=') for a in sys.argv[3:])        # e.g. c6=c6send swaps a caption layer
    shots, total = T.shots(variant)
    for sh in shots:
        sh['caps'] = [(SWAP.get(n, n), a, b) for n, a, b in sh['caps']]
    clips = {s["src"]: None for s in shots}
    for src in clips:
        clips[src] = read_clip(src)
    layers = {}
    for s in shots:
        for name, _, _ in s["caps"]:
            layers.setdefault(name, Layer(name))
    handle = Layer("handle")
    reveal = next(s["start"] for s in shots if s["name"] == T.HANDLE_FROM)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p", "-r", str(FPS), out], stdin=subprocess.PIPE)
    for s in shots:
        clip, n = clips[s["src"]], s["n"]
        z0, z1, cx, cy = s["z"]
        for j in range(n):
            u = j / max(1, n - 1)
            punch = s.get("punch")
            if punch and j >= punch[0]:                       # jump later in the clip and punch in on the friend
                src_i = punch[1] + (j - punch[0])
                f = zoom(clip[min(src_i, len(clip) - 1)], punch[2] * (1 + 0.03 * (j - punch[0]) / max(1, n - punch[0])), punch[3], punch[4])
            else:
                src_i = s["f0"] + int(round(j * s["speed"]))
                assert src_i < len(clip), (s["name"], src_i, len(clip))
                dx = s["shake"] * math.sin(j * 1.9) * math.cos(j * 0.7)
                dy = s["shake"] * math.sin(j * 2.3 + 1.0)
                f = zoom(clip[src_i], z0 + (z1 - z0) * u, cx, cy, dx, dy)
            i = s["start"] + j
            for name, a, b in s["caps"]:
                if a <= j <= b:
                    # hard-in with the cut (no opacity fade): a 3-frame scale pop; frame 0 of the file is static and readable
                    sc = 1.0 if i == 0 else 0.90 + 0.10 * back((j - a + 1) / 3.0)
                    al = 1.0
                    if s["name"] != "loop" and name not in ("c4a",):
                        al = min(1.0, (b - j + 1) / 2.0)             # 2-frame fade-out before the cut
                    layers[name].draw(f, scale=sc, alpha=al)
            if i >= reveal:
                handle.draw(f, alpha=smooth((i - reveal + 1) / 4.0))
            enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    print("wrote", out, total, "frames =", round(total / FPS, 2), "s; starts", [(s["name"], s["start"]) for s in shots])


main()
