#!/usr/bin/env python3
"""Put a matted speaker (transparent video) into a new background with matched light — free, CPU.

Usage: python3 composite.py fg.mov bg.png out.mp4 [--blur 7] [--wrap 0.35] [--match 0.35] [--shadow 0.35]
                            [--push 0.04] [--key 1.06] [--fps 30]
  fg.mov   RGBA video from `hyperframes remove-background src.mp4 -o fg.mov` (ProRes 4444 with alpha)
  bg.png   background plate (e.g. a GPT-Image office), cover-fitted to the fg size
--blur    background defocus (px sigma) — sells depth like a real lens
--wrap    light wrap: background light bleeding over the subject's edges (0 = off)
--match   pull the subject's colour balance toward the background's (Lab a/b + a little L), 0..1
--shadow  soft contact shadow behind the subject on the background
--push    slow background zoom over the clip (parallax-ish camera life)
--key     brightness gain on the subject (1.0 = unchanged) — a gentle "key light" lift
"""
import argparse, subprocess

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("fg"); ap.add_argument("bg"); ap.add_argument("out")
ap.add_argument("--blur", type=float, default=7); ap.add_argument("--wrap", type=float, default=0.35)
ap.add_argument("--match", type=float, default=0.35); ap.add_argument("--shadow", type=float, default=0.35)
ap.add_argument("--push", type=float, default=0.04); ap.add_argument("--key", type=float, default=1.06)
ap.add_argument("--fps", type=int, default=30)
a = ap.parse_args()

W, H = map(int, subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                         "stream=width,height", "-of", "csv=p=0", a.fg]).decode().strip().split(",")[:2])
N = int(float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                       "csv=p=0", a.fg]).decode()) * a.fps + 0.5)

bg0 = cv2.imread(a.bg)
s = max(W * (1 + a.push) / bg0.shape[1], H * (1 + a.push) / bg0.shape[0])
bgL = cv2.resize(bg0, (int(bg0.shape[1] * s) + 1, int(bg0.shape[0] * s) + 1), interpolation=cv2.INTER_LANCZOS4)
if a.blur > 0:
    bgL = cv2.GaussianBlur(bgL, (0, 0), a.blur)

def bg_at(i):
    z = 1 + a.push * i / max(1, N - 1)                      # slow push-in
    cw, ch = int(bgL.shape[1] / z), int(bgL.shape[0] / z)
    x0, y0 = (bgL.shape[1] - cw) // 2, (bgL.shape[0] - ch) // 2
    return cv2.resize(bgL[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)

bg_lab = cv2.cvtColor(bg_at(0).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
shift = None  # colour-match offset, computed on the first frame and kept constant (no flicker)

rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.fg, "-r", str(a.fps), "-f", "rawvideo", "-pix_fmt", "bgra", "-"],
                      stdout=subprocess.PIPE)
wr = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(a.fps),
                       "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", a.out],
                      stdin=subprocess.PIPE)
size, i = W * H * 4, 0
while True:
    buf = rd.stdout.read(size)
    if len(buf) < size: break
    f = np.frombuffer(buf, np.uint8).reshape(H, W, 4)
    fg = f[..., :3].astype(np.float32); al = f[..., 3].astype(np.float32) / 255
    al = cv2.GaussianBlur(al, (0, 0), 0.8)                   # soften the matte edge a hair
    bg = bg_at(i)

    if shift is None:                                       # subject vs background colour statistics
        lab = cv2.cvtColor(fg.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
        m = al > 0.9
        shift = (bg_lab[..., 1:].reshape(-1, 2).mean(0) - lab[m][:, 1:].mean(0)) * a.match
        lshift = (bg_lab[..., 0].mean() - lab[m][:, 0].mean()) * a.match * 0.25
    lab = cv2.cvtColor(np.clip(fg * a.key, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 1:] += shift; lab[..., 0] += lshift
    fg = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)

    if a.wrap > 0:                                          # background light wrapping around the edges
        inner = cv2.GaussianBlur(al, (0, 0), 9)
        rim = np.clip(al - inner, 0, 1) * 2.5
        glow = cv2.GaussianBlur(bg, (0, 0), 18)
        k = (np.clip(rim, 0, 1) * a.wrap)[..., None]
        fg = fg * (1 - k) + np.maximum(fg, glow) * k

    if a.shadow > 0:                                        # soft shadow cast back onto the set
        sh = cv2.GaussianBlur(al, (0, 0), 40)
        sh = np.roll(sh, (int(H * 0.01), int(W * 0.015)), (0, 1))
        bg = bg * (1 - (sh * a.shadow)[..., None])

    out = fg * al[..., None] + bg * (1 - al[..., None])
    wr.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes()); i += 1
wr.stdin.close(); wr.wait(); rd.wait()
print("composite ->", a.out, f"{i} frames")
