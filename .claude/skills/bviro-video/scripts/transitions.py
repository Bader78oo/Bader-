#!/usr/bin/env python3
"""Animated cut transitions on the concatenated base video (free, CPU).

Usage: python3 transitions.py base.mp4 out.mp4 --fps 30 --cuts '[[3.6,"zoom"],[6.9,"whip"],[21.8,"flash"]]'

Styles (applied over ~4 frames either side of the cut):
  zoom   punch-in blur out of shot A, settle from 112% into shot B
  whip   fast horizontal pan with motion blur (direction alternates)
  flash  brand-violet light flash / light leak — use on section changes and open loops
  cut    nothing (hard cut)
"""
import argparse, json, subprocess

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--fps", type=int, default=30); ap.add_argument("--cuts", required=True)
a = ap.parse_args()

W, H = map(int, subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                         "stream=width,height", "-of", "csv=p=0", a.src]).decode().strip().split(","))
fx = {}  # frame index -> (style, r) with r in [-1, 1): negative before the cut, >= 0 from the cut on
whip_dir = 1
for t, style in json.loads(a.cuts):
    k = round(t * a.fps)
    if style == "whip": whip_dir = -whip_dir
    span = 5 if style == "flash" else 4
    for j in range(-span, span + 1):
        if j < 0 and style == "flash": continue          # a flash only blooms after the cut
        fx[k + j] = (style, j / span, whip_dir)

def zoom(img, f):
    if f <= 1.001: return img
    h, w = img.shape[:2]; ch, cw = int(h / f), int(w / f)
    y0, x0 = (h - ch) // 2, (w - cw) // 2
    return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_LINEAR)

def zoom_blur(img, f):
    # average a few progressively zoomed copies: cheap radial motion blur
    steps = [zoom(img, 1 + (f - 1) * q) for q in (1.0, 0.8, 0.6, 0.4)]
    return np.mean(np.stack(steps).astype(np.float32), 0).astype(np.uint8)

def whip(img, shift, blur):
    m = np.float32([[1, 0, shift], [0, 1, 0]])
    out = cv2.warpAffine(img, m, (W, H), borderMode=cv2.BORDER_REFLECT)
    if blur > 1:
        kx = np.ones((1, int(blur)), np.float32) / int(blur)
        out = cv2.filter2D(out, -1, kx)
    return out

VIOLET = np.array([255, 80, 170], np.float32)  # BGR, brand #AA50FF-ish glow
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
leak = np.clip(1.2 - np.hypot((xx - W * 0.85) / W, (yy - H * 0.2) / H) * 1.6, 0, 1)[..., None]  # corner light leak

rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.src, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
wr = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(a.fps),
                       "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", a.out],
                      stdin=subprocess.PIPE)
i, size = 0, W * H * 3
while True:
    buf = rd.stdout.read(size)
    if len(buf) < size: break
    img = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    if i in fx:
        style, r, d = fx[i]
        e = 1 - abs(r) if r < 0 else 1 - r              # strength: peaks at the cut
        e = e * e
        if style == "zoom":
            img = zoom_blur(img, 1 + 0.18 * e) if r < 0 else zoom_blur(zoom(img, 1 + 0.12 * e), 1 + 0.10 * e)
        elif style == "whip":
            s = (0.35 * e * W) * (d if r < 0 else -d)
            img = whip(img, s, 2 + 90 * e)
        elif style == "flash":
            k = 0.85 * e
            f = img.astype(np.float32)
            f = f * (1 - k * 0.55) + (255 * k * 0.55) + VIOLET * leak * k * 0.6
            img = np.clip(f, 0, 255).astype(np.uint8)
    wr.stdin.write(np.ascontiguousarray(img).tobytes()); i += 1
wr.stdin.close(); wr.wait(); rd.wait()
print("transitions ->", a.out, f"{i} frames, {len(json.loads(a.cuts))} cuts")
