"""Storyboard frame of the first-person shot: the lane plate, the hologram controllers and one tutorial arrow.

usage: python3 -I pov_mock.py PLATE_PNG OVERLAY_PNG OUT_PNG [arrow: up|right|left|none] [stick_x,stick_y] [dx,dy]
stick_x,stick_y: where the right thumbstick sits in the overlay, as fractions of width and height (default 0.71,0.645).
dx,dy: slide the overlay by these fractions of width and height (default 0,0), to keep the hands off what must be read.
The controllers are a picture of turquoise holograms on black, so they are added as light (screen blend). In the
film the same layers are animated: the plate moves, the controllers bob with the steps, the arrow follows the words.
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

plate, overlay, out = sys.argv[1:4]
arrow = sys.argv[4] if len(sys.argv) > 4 else "up"
STICK = tuple(float(v) for v in sys.argv[5].split(",")) if len(sys.argv) > 5 else (0.71, 0.645)
TURQ = np.array([0, 205, 200], np.float32)

bg = np.asarray(Image.open(plate).convert("RGB"), np.float32) / 255
H, W = bg.shape[:2]
ov = np.asarray(Image.open(overlay).convert("RGB").resize((W, H), Image.LANCZOS), np.float32) / 255
if len(sys.argv) > 6:
    dx, dy = (float(v) for v in sys.argv[6].split(","))
    ox, oy = int(dx * W), int(dy * H)
    moved = np.zeros_like(ov)
    moved[max(oy, 0):H + min(oy, 0), max(ox, 0):W + min(ox, 0)] = ov[max(-oy, 0):H - max(oy, 0), max(-ox, 0):W - max(ox, 0)]
    ov = moved
ov = np.clip((ov - 0.11) / 0.89, 0, 1)            # drop the wide haze around the holograms: only they add light
lum = ov.max(axis=2, keepdims=True)
# a hologram hides a little of what is behind it, then adds its own light
body = np.clip(lum * 1.6, 0, 1) * 0.38
comp = bg * (1 - body) + ov * 0.95
comp = 1 - (1 - comp) * (1 - ov * 0.35)

if arrow != "none":
    cx, cy = int(W * STICK[0]), int(H * STICK[1])
    layer = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(layer)
    s = int(W * 0.060)
    ax, ay = cx, cy - int(H * 0.062)
    for k in range(3):                              # three chevrons fading away from the stick
        o = k * int(s * 0.95)
        a = int(255 * (1 - 0.28 * k))
        if arrow == "up":
            pts = [(ax - s, ay - o + s * 0.6), (ax, ay - o - s * 0.4), (ax + s, ay - o + s * 0.6)]
        elif arrow == "right":
            pts = [(ax + o - s * 0.6, ay - s), (ax + o + s * 0.4, ay), (ax + o - s * 0.6, ay + s)]
        else:
            pts = [(ax - o + s * 0.6, ay - s), (ax - o - s * 0.4, ay), (ax - o + s * 0.6, ay + s)]
        d.line(pts, fill=a, width=max(6, int(W * 0.010)), joint="curve")
    glow = np.asarray(layer.filter(ImageFilter.GaussianBlur(W * 0.012)), np.float32) / 255
    core = np.asarray(layer.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    a = np.clip(core + 0.55 * glow, 0, 1)[..., None]
    comp = comp * (1 - a * 0.9) + (TURQ / 255 * 0.75 + 0.25) * a * 0.9
Image.fromarray((np.clip(comp, 0, 1) * 255).astype(np.uint8)).save(out)
print("composited", out, "| arrow", arrow)
