"""Lay evenly spaced frames of a clip side by side, to inspect it frame by frame without playing it.

usage: python3 -I clip_sheet.py VIDEO OUT.jpg [N] [x0,y0,x1,y1] [HEIGHT]
N: how many frames (default 8). x0,y0,x1,y1: show only this part of the picture (fractions). HEIGHT: tile height (480).
Prints the clip's size, frame rate, length and frame count, and the time of each tile.
"""
import json
import subprocess
import sys

from PIL import Image, ImageDraw

video, out = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
box = [float(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
tile_h = int(sys.argv[5]) if len(sys.argv) > 5 else 480
info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                                  "stream=width,height,r_frame_rate,nb_read_frames:format=duration", "-of", "json", video],
                                 capture_output=True, check=True).stdout)
st = info["streams"][0]
w, h, frames = st["width"], st["height"], int(st["nb_read_frames"])
num, den = st["r_frame_rate"].split("/")
fps = float(num) / float(den)
print(f"{video.split('/')[-1]}: {w}x{h}, {fps:.2f} fps, {float(info['format']['duration']):.2f} s, {frames} frames")
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
size = w * h * 3
picks = [round(i * (frames - 1) / (n - 1)) for i in range(n)] if n > 1 else [0]
tiles = []
for k in picks:
    im = Image.frombuffer("RGB", (w, h), raw[k * size:(k + 1) * size], "raw", "RGB", 0, 1)
    if box:
        im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    im = im.resize((max(1, int(im.width * tile_h / im.height)), tile_h), Image.LANCZOS)
    ImageDraw.Draw(im).text((6, 6), f"{k / fps:.2f}s", fill=(255, 255, 0))
    tiles.append(im)
sheet = Image.new("RGB", (sum(t.width for t in tiles), tile_h))
x = 0
for t in tiles:
    sheet.paste(t, (x, 0))
    x += t.width
sheet.save(out, quality=88)
print("tiles at", " ".join(f"{k / fps:.2f}" for k in picks), "s ->", out, sheet.size)
