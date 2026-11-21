"""Check one motion clip of a story reel (CHARACTER.md section 8b) before it goes into an edit.

The character moves, so his head is found in every frame by the colours of the massar (deep purple with turquoise
embroidery) and cropped around it.

usage: python3 -I check_motion_clip.py CLIP_MP4 START_POSE_PNG OUT_PREFIX [END_POSE_PNG]
Prints: size / fps / frames, decode errors, how far the first (and last) frame is from the pose image, and how the
massar's size and colour hold along the clip. Writes OUT_PREFIX_heads.jpg (the pose head and 15 head close-ups) and
OUT_PREFIX_frames.jpg (10 whole frames, to read the body movement).
"""
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

clip, pose, out = sys.argv[1:4]
end_pose = sys.argv[4] if len(sys.argv) > 4 else None
W, H = 1080, 1920


def run(cmd):
    return subprocess.run(cmd, capture_output=True, check=True)


def fit(p):
    return np.asarray(Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS))


def massar(frame):
    """(x0, y0, x1, y1, purple share) of the massar, or None."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(int)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    purple = (h >= 128) & (h <= 160) & (s >= 90) & (v >= 40)
    turq = (h >= 82) & (h <= 104) & (s >= 90) & (v >= 90)
    m = cv2.morphologyEx((purple | turq).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        return None
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, hh = st[k, :4]
    blob = lab == k
    return int(x), int(y), int(x + w), int(y + hh), float((purple & blob).sum()) / max(int(blob.sum()), 1)


def head_crop(frame, box):
    """Square crop around the head: the massar, the headset and the beard under it."""
    x0, y0, x1, y1 = box[:4]
    w = x1 - x0
    cx, top = (x0 + x1) / 2, y0 - 0.12 * w
    side = 1.75 * w
    a, b = int(round(cx - side / 2)), int(round(top))
    pad = int(side) + 4
    big = np.pad(frame, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    return Image.fromarray(big[b + pad: b + pad + int(side), a + pad: a + pad + int(side)])


info = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
            "stream=width,height,r_frame_rate,nb_read_frames,duration", "-of", "csv=p=0", clip]).stdout.decode().strip()
errs = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-f", "null", "-"], capture_output=True).stderr.decode().strip()
print("stream:", info, "| decode errors:", len(errs.splitlines()))
raw = run(["ffmpeg", "-v", "error", "-i", clip, "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-pix_fmt", "rgb24",
           "-f", "rawvideo", "-"]).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
ref = fit(pose)
print("frames %d | mean abs diff: first frame to start pose %.1f" % (len(fr), float(np.abs(fr[0].astype(int) - ref).mean())), end="")
if end_pose:
    print(", last frame to end pose %.1f" % float(np.abs(fr[-1].astype(int) - fit(end_pose)).mean()), end="")
print()

rb = massar(ref)
assert rb, "massar not found in the pose image"
boxes = [massar(f) for f in fr]
missing = [i for i, b in enumerate(boxes) if b is None]
ok = [b for b in boxes if b]
wid = np.array([b[2] - b[0] for b in ok], float)
asp = np.array([(b[3] - b[1]) / max(b[2] - b[0], 1) for b in ok], float)
share = np.array([b[4] for b in ok], float)
ra = (rb[3] - rb[1]) / (rb[2] - rb[0])
print("massar found in %d of %d frames%s" % (len(ok), len(fr), "" if not missing else " (missing: %s)" % missing[:12]))
print("massar width px: pose %d, clip %d..%d | height/width: pose %.2f, clip %.2f..%.2f | purple share: pose %.2f, clip %.2f..%.2f" % (
    rb[2] - rb[0], wid.min(), wid.max(), ra, asp.min(), asp.max(), rb[4], share.min(), share.max()))
cx = np.array([(b[0] + b[2]) / 2 for b in ok])
cy = np.array([(b[1] + b[3]) / 2 for b in ok])
print("head travel in frame: x %d..%d, y %d..%d (px of 1080x1920)" % (cx.min(), cx.max(), cy.min(), cy.max()))

dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip]).stdout.decode().strip())
t = 300
tiles = [("POSE", head_crop(ref, rb))]
for k in np.linspace(0, len(fr) - 1, 15).round().astype(int):
    if boxes[k]:
        tiles.append((f"{k * dur / len(fr):.2f}s", head_crop(fr[k], boxes[k])))
sheet = Image.new("RGB", (t * 8, t * 2))
for i, (lab, im) in enumerate(tiles):
    im = im.resize((t, t), Image.LANCZOS)
    ImageDraw.Draw(im).text((6, 6), lab, fill=(255, 255, 0))
    sheet.paste(im, ((i % 8) * t, (i // 8) * t))
sheet.save(out + "_heads.jpg", quality=90)
strip = Image.new("RGB", (216 * 10, 384))
for i, k in enumerate(np.linspace(0, len(fr) - 1, 10).round().astype(int)):
    im = Image.fromarray(fr[k]).resize((216, 384), Image.LANCZOS)
    ImageDraw.Draw(im).text((6, 6), f"{k * dur / len(fr):.2f}s", fill=(255, 255, 0))
    strip.paste(im, (i * 216, 0))
strip.save(out + "_frames.jpg", quality=88)
print("sheets:", out + "_heads.jpg", out + "_frames.jpg")
