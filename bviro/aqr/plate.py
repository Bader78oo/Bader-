"""Letter the blank licence plate of the pickup still with real fonts (no generated Arabic).

usage: python3 -I plate.py IN_PNG OUT_PNG  x0,y0 x1,y1 x2,y2 x3,y3  [digits] [word]
The four points are the plate's corners in the picture: top-left, top-right, bottom-right, bottom-left.
The plate is a prop of the film: black, white Arabic-Indic numerals and the word «عُمان», a made-up number.
"""
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

assert features.check("raqm"), "Pillow has no raqm: Arabic would come out unshaped"
src, dst = sys.argv[1:3]
quad = np.float32([[float(v) for v in p.split(",")] for p in sys.argv[3:7]])
digits = sys.argv[7] if len(sys.argv) > 7 else "٤٧١٣"
word = sys.argv[8] if len(sys.argv) > 8 else "عُمان"
FONT = "/home/user/Bader-/bviro/fonts/Cairo-VF.ttf"

PW, PH = 880, 420  # the flat plate, drawn large and warped down


def font(size, weight):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([weight])
    return f


flat = Image.new("L", (PW, PH), 0)
d = ImageDraw.Draw(flat)
fw, fd = font(104, 800), font(300, 900)
d.text((PW / 2, 74), word, font=fw, fill=255, anchor="mm", direction="rtl", language="ar")
d.text((PW / 2, 268), digits, font=fd, fill=255, anchor="mm", direction="rtl", language="ar")
d.line([(60, 134), (PW - 60, 134)], fill=170, width=6)
# pressed-metal paint is never perfect: soften the edges and wear the paint a little
rng = np.random.default_rng(7)
a = np.asarray(flat.filter(ImageFilter.GaussianBlur(1.6)), np.float32) / 255
wear = cv2.GaussianBlur(rng.random((PH, PW)).astype(np.float32), (0, 0), 9)
wear = np.clip((wear - wear.min()) / (wear.max() - wear.min()), 0, 1)
a *= 0.80 + 0.20 * wear
specks = (rng.random((PH, PW)) > 0.985).astype(np.float32)
a *= 1 - 0.55 * cv2.GaussianBlur(specks, (0, 0), 1.2)

im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
H, W = im.shape[:2]
inset = 0.03  # keep the lettering inside the plate's raised rim
sq = np.float32([[-inset * PW, -inset * PH * 1.4], [PW * (1 + inset), -inset * PH * 1.4],
                 [PW * (1 + inset), PH * (1 + inset * 1.4)], [-inset * PW, PH * (1 + inset * 1.4)]])
M = cv2.getPerspectiveTransform(sq, quad)
alpha = cv2.warpPerspective(a, M, (W, H), flags=cv2.INTER_AREA)[..., None]
# the paint takes the light of the plate it sits on: sample the plate's own brightness and tint
x0, y0, x1, y1 = int(quad[:, 0].min()), int(quad[:, 1].min()), int(quad[:, 0].max()), int(quad[:, 1].max())
around = im[max(y0 - 60, 0):y0 - 12, x0:x1].reshape(-1, 3)   # the white tailgate just above the plate
paint = np.percentile(around, 97, axis=0) * 1.12            # the plate's white is cleaner than the dusty tailgate
out = im * (1 - alpha) + paint * alpha
grain = rng.normal(0, 2.2, (H, W, 1)).astype(np.float32) * alpha
Image.fromarray(np.clip(out + grain, 0, 255).astype(np.uint8)).save(dst)
print("plate lettered:", digits, word, "| paint colour", paint.round().tolist())
