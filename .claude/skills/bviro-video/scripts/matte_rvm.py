#!/usr/bin/env python3
"""Video matting with RobustVideoMatting (GPL-3.0 model, used as a tool; free, CPU, temporally stable).

Usage: python3 matte_rvm.py src.mp4 fg.mov [--model resnet50|mobilenetv3] [--ratio 0.25]

Much steadier than per-frame segmenters (u2net): recurrent states carry the matte across frames, so
edges don't flicker and hair / cap edges come out soft. The model also predicts a clean foreground
colour (fgr) — the old wall's spill is removed at the edges. Output: ProRes 4444 with alpha, ready for
scripts/composite.py (use --erode 0 --decontam 0 there, RVM already did both jobs).
Model: https://github.com/PeterL1n/RobustVideoMatting/releases (cached in ~/.cache/rvm).
"""
import argparse, os, subprocess, urllib.request

import numpy as np
import onnxruntime as ort

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--model", default="resnet50"); ap.add_argument("--ratio", type=float, default=0.25,
                help="internal downsample (0.25 for 1080p portrait, 0.4 for 720p)")
a = ap.parse_args()

name = f"rvm_{a.model}_fp32.onnx"
path = os.path.join(os.path.expanduser("~/.cache/rvm"), name)
if not os.path.exists(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    urllib.request.urlretrieve(f"https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/{name}", path)
so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count()
sess = ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])

probe = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                 "stream=width,height,r_frame_rate", "-of", "csv=p=0", a.src]).decode().strip().split(",")
W, H, fps = int(probe[0]), int(probe[1]), probe[2]
rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
wr = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", fps,
                       "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", a.out],
                      stdin=subprocess.PIPE)
rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
ratio = np.array([a.ratio], np.float32)
n = 0
while True:
    buf = rd.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    src = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32).transpose(2, 0, 1)[None] / 255
    fgr, pha, *rec = sess.run(None, {"src": src, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                     "downsample_ratio": ratio})
    rgba = np.concatenate([fgr[0], pha[0]], 0).transpose(1, 2, 0)
    wr.stdin.write((np.clip(rgba, 0, 1) * 255).astype(np.uint8).tobytes()); n += 1
wr.stdin.close(); wr.wait(); rd.wait()
print("rvm matte ->", a.out, f"{n} frames")
