#!/usr/bin/env python3
"""2.5D camera move on a still (free, CPU): Depth Anything V2 Small (ONNX) estimates depth, then
each frame warps the picture so near things move more than far things — a real dolly/crane feel
instead of a flat Ken Burns zoom.

Usage: python3 parallax.py in.png out.mp4 --dur 3.2 [--move push|pull|left|right|rise|fall] [--amount 1.0]
       [--size 1080x1920] [--fps 30]
Needs: onnxruntime, opencv-python-headless, numpy, huggingface_hub, ffmpeg. First run downloads ~100 MB.
"""
import argparse, subprocess

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--dur", type=float, default=3.0); ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--move", default="push"); ap.add_argument("--amount", type=float, default=1.0)
ap.add_argument("--size", default="1080x1920")
a = ap.parse_args()
W, H = map(int, a.size.split("x"))

# --- depth (disparity: 1 = near, 0 = far) ---------------------------------------------
def depth_map(img):
    import onnxruntime as ort
    from huggingface_hub import hf_hub_download
    model = hf_hub_download("onnx-community/depth-anything-v2-small", "onnx/model.onnx")
    sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
    h, w = img.shape[:2]; s = 518 / min(h, w)
    ih, iw = int(round(h * s / 14)) * 14, int(round(w * s / 14)) * 14
    x = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (iw, ih), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255
    x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
    d = sess.run(None, {"pixel_values": x})[0][0]
    d = (d - np.percentile(d, 2)) / (np.percentile(d, 98) - np.percentile(d, 2) + 1e-6)
    return np.clip(d, 0, 1).astype(np.float32)

img = cv2.imread(a.src)
# fill the output frame (cover) with a 12% margin so the move never shows borders
M = 1.12
s = max(W * M / img.shape[1], H * M / img.shape[0])
big = cv2.resize(img, (int(img.shape[1] * s), int(img.shape[0] * s)), interpolation=cv2.INTER_LANCZOS4)
d = cv2.resize(depth_map(img), (big.shape[1], big.shape[0]), interpolation=cv2.INTER_CUBIC)
# soften and grow the foreground a little so edges stretch the background, not the subject
k = max(3, int(min(big.shape[:2]) * 0.012) | 1)
d = cv2.GaussianBlur(cv2.dilate(d, np.ones((k, k), np.uint8)), (0, 0), k * 0.6)
BH, BW = big.shape[:2]; cx, cy = BW / 2, BH / 2
ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
X, Y = xs + (BW - W) / 2, ys + (BH - H) / 2           # output pixel -> big-image coords (centred)
dd = cv2.remap(d, X, Y, cv2.INTER_LINEAR)             # depth seen at each output pixel

n = max(1, round(a.dur * a.fps)); A = a.amount
ease = lambda u: u * u * (3 - 2 * u)                    # smoothstep: starts and lands softly
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                         "-s", f"{W}x{H}", "-r", str(a.fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                         "-crf", "14", "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
for i in range(n):
    u = ease(i / max(1, n - 1)); p = u - 0.5           # p: -0.5 .. 0.5 over the shot
    zoom, tx, ty = 1.0, 0.0, 0.0
    if a.move == "push":  zoom = 1 + 0.06 * A * u        # dolly in: near grows faster than far
    if a.move == "pull":  zoom = 1 + 0.06 * A * (1 - u)
    if a.move in ("left", "right"): tx = (1 if a.move == "right" else -1) * 0.045 * A * p * W; zoom = 1.02
    if a.move in ("rise", "fall"):  ty = (1 if a.move == "fall" else -1) * 0.045 * A * p * H; zoom = 1.02
    z = 1 + (zoom - 1) * (0.35 + 0.65 * dd)              # per-pixel zoom: parallax on push/pull
    par = 0.25 + dd                                       # per-pixel pan: near pixels travel further
    mx = cx + (X - cx) / z - tx * par
    my = cy + (Y - cy) / z - ty * par
    frame = cv2.remap(big, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    proc.stdin.write(frame.tobytes())
proc.stdin.close(); proc.wait()
print("parallax ->", a.out, f"{n} frames, move={a.move}")
