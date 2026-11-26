"""Letter the blank licence plate of the pickup still with real fonts (no generated Arabic).

usage: python3 -I plate.py IN_PNG OUT_PNG  x0,y0 x1,y1 x2,y2 x3,y3  [number] [region_ar] [region_latin]
The four points are the plate's corners in the picture: top-left, top-right, bottom-right, bottom-left.

The layout is the old Omani plate the owner sent a photo of (26 November 2026): black, heavy white pressed characters
inside white ridges, three columns. Right column: «عُمان» over OMAN. Middle column, one tall cell: the region
(«مسقط») over its Latin code (MCT). Left column: the number in Arabic-Indic digits over the same number in Latin
digits. The number here is made up for the film; the region is the one in the owner's photo, the only pairing of
Arabic name and Latin code we have seen on a real plate.

Fonts (bviro/fonts/plate, SIL Open Font License): Amiri Bold for the Arabic, a traditional hand close to the plate's
lettering, and Barlow Condensed ExtraBold for the narrow Latin letters and digits.
"""
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

assert features.check("raqm"), "Pillow has no raqm: Arabic would come out unshaped"
src, dst = sys.argv[1:3]
quad = np.float32([[float(v) for v in p.split(",")] for p in sys.argv[3:7]])
number = sys.argv[7] if len(sys.argv) > 7 else "24713"
region_ar = sys.argv[8] if len(sys.argv) > 8 else "مسقط"
region_lat = sys.argv[9] if len(sys.argv) > 9 else "MCT"
FONTS = "/home/user/Bader-/bviro/fonts/plate/"
ARABIC, LATIN = FONTS + "Amiri-Bold-arabic.woff", FONTS + "BarlowCondensed-ExtraBold-latin.woff"
INDIC = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

PW, PH = 1320, 600           # the flat plate, drawn large and warped down (2.2 : 1, as in the photo)
X1, X2 = 0.475, 0.735        # the two vertical dividers, as fractions of the width
YM = 0.515                   # the horizontal divider (left and right columns only)
M = 22                       # margin of the white frame inside the plate's own rim
LW = 15                      # weight of the pressed ridges


def fit_text(text, box, arabic, stroke, fill_w, fill_h, stretch=1.45):
    """A tile with `text` filling `box` (x0, y0, x1, y1) to the given shares of its width and height.

    Pressed plate characters are heavy and fill their cell, so the text is drawn large, thickened by `stroke`, cut to
    its ink and then scaled to the cell; the shorter side may be stretched up to `stretch` times, as plate dies are."""
    x0, y0, x1, y1 = box
    kw = dict(direction="rtl", language="ar") if arabic else {}
    size = 420
    f = ImageFont.truetype(ARABIC if arabic else LATIN, size)
    sw = max(1, int(size * stroke))
    big = Image.new("L", (size * (len(text) + 3), size * 3), 0)
    ImageDraw.Draw(big).text((size, size), text, font=f, fill=255, stroke_width=sw, stroke_fill=255, **kw)
    ys, xs = np.nonzero(np.asarray(big))
    tile = big.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    tw, th = (x1 - x0) * fill_w, (y1 - y0) * fill_h
    k = min(tw / tile.width, th / tile.height)
    kx = min(tw / tile.width, k * stretch)
    ky = min(th / tile.height, k * stretch)
    tile = tile.resize((max(4, int(tile.width * kx)), max(4, int(tile.height * ky))), Image.LANCZOS)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return tile, (int(cx - tile.width / 2), int(cy - tile.height / 2))


flat = Image.new("L", (PW, PH), 0)
d = ImageDraw.Draw(flat)
d.rounded_rectangle((M, M, PW - M, PH - M), radius=30, outline=255, width=LW)
ym, x1, x2 = int(PH * YM), int(PW * X1), int(PW * X2)
for x in (x1, x2):
    d.line([(x, M), (x, PH - M)], fill=255, width=LW)
d.line([(M, ym), (x1, ym)], fill=255, width=LW)          # the middle column is one tall cell
d.line([(x2, ym), (PW - M, ym)], fill=255, width=LW)
cells = [  # text, cell, arabic, stroke, share of cell width, share of cell height
    (number.translate(INDIC), (M, M, x1, ym), True, 0.030, 0.84, 0.70),
    (number, (M, ym, x1, PH - M), False, 0.004, 0.84, 0.70),
    (region_ar, (x1, M, x2, ym), True, 0.026, 0.80, 0.56),
    (region_lat, (x1, ym, x2, PH - M), False, 0.004, 0.76, 0.58),
    ("عُمان", (x2, M, PW - M, ym), True, 0.026, 0.80, 0.66),
    ("OMAN", (x2, ym, PW - M, PH - M), False, 0.004, 0.82, 0.58),
]
for text, box, arabic, stroke, fill_w, fill_h in cells:
    tile, pos = fit_text(text, box, arabic, stroke, fill_w, fill_h)
    flat.paste(255, pos, tile)

# pressed-metal paint is never perfect: soften the edges and wear the paint a little
rng = np.random.default_rng(7)
a = np.asarray(flat.filter(ImageFilter.GaussianBlur(1.8)), np.float32) / 255
wear = cv2.GaussianBlur(rng.random((PH, PW)).astype(np.float32), (0, 0), 11)
wear = np.clip((wear - wear.min()) / (wear.max() - wear.min()), 0, 1)
a *= 0.80 + 0.20 * wear
specks = (rng.random((PH, PW)) > 0.988).astype(np.float32)
a *= 1 - 0.5 * cv2.GaussianBlur(specks, (0, 0), 1.4)

im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
H, W = im.shape[:2]
sq = np.float32([[0, 0], [PW, 0], [PW, PH], [0, PH]])
alpha = cv2.warpPerspective(a, cv2.getPerspectiveTransform(sq, quad), (W, H), flags=cv2.INTER_AREA)[..., None]
# the paint takes the light of the scene: sample the white tailgate just above the plate
bx0, by0, bx1 = int(quad[:, 0].min()), int(quad[:, 1].min()), int(quad[:, 0].max())
around = im[max(by0 - 60, 0):max(by0 - 12, 1), bx0:bx1].reshape(-1, 3)
paint = np.clip(np.percentile(around, 97, axis=0) * 1.12, 0, 255)
out = im * (1 - alpha) + paint * alpha
grain = rng.normal(0, 2.2, (H, W, 1)).astype(np.float32) * alpha
Image.fromarray(np.clip(out + grain, 0, 255).astype(np.uint8)).save(dst)
print("plate lettered:", number, region_ar, region_lat, "| paint colour", paint.round().tolist())
