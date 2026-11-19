"""Check one talking clip made with the approved lip method (CHARACTER.md section 8) before it goes into an edit.

usage: python3 -I check_talk_clip.py CLIP_MP4 POSE_PNG SEGMENT_AUDIO OUT_SHEET_JPG [face box] [eyes box | none]
       (boxes are x0,y0,x1,y1 in 1080x1920; "none" skips the blink check for shots where a headset covers the eyes)
Prints: size / fps / frames, decode errors, audio match against the voice segment, how far the last frame is from
the pose, the length of every blink, and writes a sheet of 15 face close-ups next to the approved pose.
"""
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

clip, pose, seg, out = sys.argv[1:5]
box = tuple(int(v) for v in sys.argv[5].split(",")) if len(sys.argv) > 5 else (235, 90, 845, 830)
eyes = None if (len(sys.argv) > 6 and sys.argv[6] == "none") else (tuple(int(v) for v in sys.argv[6].split(",")) if len(sys.argv) > 6 else (360, 415, 730, 525))
W, H = 1080, 1920


def run(cmd):
    return subprocess.run(cmd, capture_output=True, check=True)


info = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
            "stream=width,height,r_frame_rate,nb_read_frames,duration", "-of", "csv=p=0", clip]).stdout.decode().strip()
errs = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-f", "null", "-"], capture_output=True).stderr.decode().strip()
print("stream:", info, "| decode errors:", len(errs.splitlines()))


def env(p):
    raw = run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", "8000", "-f", "f32le", "-"]).stdout
    x = np.frombuffer(raw, np.float32)
    n = len(x) // 80
    return np.sqrt((x[: n * 80].reshape(n, 80) ** 2).mean(1))


a, b = env(clip), env(seg)
n = min(len(a), len(b))
best = max((float(np.corrcoef(a[max(l, 0): n + min(l, 0)], b[max(-l, 0): n - max(l, 0)])[0, 1]), l) for l in range(-30, 31))
print("audio vs voice segment: corr %.4f at lag %d ms" % (best[0], best[1] * 10))

raw = run(["ffmpeg", "-v", "error", "-i", clip, "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"]).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
ref = np.asarray(Image.open(pose).convert("RGB").resize((W, H), Image.LANCZOS))
d0 = float(np.abs(fr[0].astype(int) - ref).mean())
d1 = float(np.abs(fr[-1].astype(int) - ref).mean())
mid = max(float(np.abs(f.astype(int) - ref).mean()) for f in fr[:: max(1, len(fr) // 30)])
print("frames %d | mean abs diff to pose: first %.1f, last %.1f, max along clip %.1f" % (len(fr), d0, d1, mid))

if eyes:
    def white(f):  # visible eye-white: bright, unsaturated pixels inside the eyes box
        r = f[eyes[1]:eyes[3], eyes[0]:eyes[2]].astype(int)
        return int(((r.max(2) > 205) & (r.max(2) - r.min(2) < 38)).sum())
    sc = np.array([white(f) for f in fr], float)
    sc /= max(sc[0], 1.0)
    runs = []
    for i in np.where(sc < 0.45)[0]:
        if runs and i == runs[-1][1] + 1:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    blinks = [(int(a), int(b - a + 1)) for a, b in runs]
    worst = max([n for _, n in blinks] or [0])
    print("blinks (start frame, length in frames):", blinks, "| longest", worst, "frames ->", "OK" if worst <= 6 else "TOO LONG (limit 6)")

dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip]).stdout.decode().strip())
tw, th = 244, int(244 * (box[3] - box[1]) / (box[2] - box[0]))
tiles = [("APPROVED", Image.fromarray(ref).crop(box))]
for k in np.linspace(0, len(fr) - 1, 15).round().astype(int):
    tiles.append((f"{k * dur / len(fr):.2f}s", Image.fromarray(fr[k]).crop(box)))
sheet = Image.new("RGB", (tw * 8, th * 2))
for i, (lab, im) in enumerate(tiles):
    t = im.resize((tw, th), Image.LANCZOS)
    ImageDraw.Draw(t).text((6, 6), lab, fill=(255, 255, 0))
    sheet.paste(t, ((i % 8) * tw, (i // 8) * th))
sheet.save(out, quality=90)
print("sheet:", out)
