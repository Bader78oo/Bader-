#!/usr/bin/env python3
"""Recolour a structure in a real clip (SAM 2 ONNX, CPU) — e.g. paint the booth Bviro purple, grey the rest,
and trace its edges with neon light.

Usage: python3 sam_recolor.py in.mp4 out.mp4 --ss 0 --dur 2.5 --pts "500,560;900,500;200,800"
       [--neg "x,y;..."] [--color 7F00FF] [--glow 01CEC9] [--desat 0.85] [--scan]
  pts   positive clicks on the structure in the first frame (1080x1920 coords); tracked with optical flow
  scan  a light sweep travels top→bottom revealing the recolour (otherwise it is on from frame 1)
Models: vietanhdev/segment-anything-2-onnx-models (sam2_hiera_small) cached in ~/.cache/sam2onnx.
"""
import argparse, os, shutil, subprocess
import cv2, numpy as np, onnxruntime as ort

ap = argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("out")
ap.add_argument("--ss", type=float, default=0); ap.add_argument("--dur", type=float, default=3)
ap.add_argument("--pts", required=True); ap.add_argument("--neg", default="")
ap.add_argument("--color", default="7F00FF"); ap.add_argument("--glow", default="01CEC9")
ap.add_argument("--desat", type=float, default=0.85); ap.add_argument("--scan", action="store_true")
ap.add_argument("--every", type=int, default=2, help="run SAM every N frames, reuse mask in between")
a = ap.parse_args()

C = os.path.expanduser("~/.cache/sam2onnx"); os.makedirs(C, exist_ok=True)
for f in ("sam2_hiera_small.encoder.onnx", "sam2_hiera_small.decoder.onnx"):
    if not os.path.exists(f"{C}/{f}"):
        from huggingface_hub import hf_hub_download
        shutil.copy(hf_hub_download("vietanhdev/segment-anything-2-onnx-models", f), f"{C}/{f}")
enc = ort.InferenceSession(f"{C}/sam2_hiera_small.encoder.onnx", providers=["CPUExecutionProvider"])
dec = ort.InferenceSession(f"{C}/sam2_hiera_small.decoder.onnx", providers=["CPUExecutionProvider"])
hexc = lambda h: np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32)  # BGR
COL, GLOW = hexc(a.color), hexc(a.glow)
P = lambda s: np.array([[float(v) for v in p.split(",")] for p in s.split(";") if p.strip()], np.float32).reshape(-1, 2)
pos, neg = P(a.pts), P(a.neg)

cap = cv2.VideoCapture(a.inp); fps = cap.get(cv2.CAP_PROP_FPS) or 30
cap.set(cv2.CAP_PROP_POS_MSEC, a.ss * 1000); n = int(a.dur * fps)
frames = []
for _ in range(n):
    ok, f = cap.read()
    if not ok: break
    frames.append(f)
H, W = frames[0].shape[:2]
mean, std = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])

def segment(img, pts, labs, prev):
    x = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (1024, 1024)).astype(np.float32) / 255
    x = ((x - mean) / std).transpose(2, 0, 1)[None].astype(np.float32)
    f0, f1, emb = enc.run(None, {"image": x})
    c = pts * np.array([1024 / W, 1024 / H], np.float32)
    feeds = {"image_embed": emb, "high_res_feats_0": f0, "high_res_feats_1": f1,
             "point_coords": c[None].astype(np.float32), "point_labels": labs[None].astype(np.float32),
             "mask_input": np.zeros((1, 1, 256, 256), np.float32), "has_mask_input": np.zeros(1, np.float32)}
    masks, iou = dec.run(None, feeds)
    m = masks[0][int(np.argmax(iou[0]))]
    m = (cv2.resize(m, (W, H)) > 0).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)                    # close speckle holes
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    n_, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)      # keep the big pieces only
    keep = np.zeros_like(m)
    for j in range(1, n_):
        if stats[j, cv2.CC_STAT_AREA] > 0.01 * W * H: keep[lab == j] = 1
    cs, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)   # fill interior holes
    filled = np.zeros_like(keep); cv2.drawContours(filled, cs, -1, 1, -1)
    return filled.astype(bool)

gray_prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
allp = np.concatenate([pos, neg]) if len(neg) else pos.copy()
labs = np.concatenate([np.ones(len(pos)), np.zeros(len(neg))]).astype(np.float32)
mask = None; out = []
for i, f in enumerate(frames):
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    if i:
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(gray_prev, g, allp.reshape(-1, 1, 2), None, winSize=(41, 41), maxLevel=4)
        good = st.reshape(-1) == 1
        allp[good] = nxt.reshape(-1, 2)[good]
        allp[:, 0] = np.clip(allp[:, 0], 0, W - 1); allp[:, 1] = np.clip(allp[:, 1], 0, H - 1)
    gray_prev = g
    if mask is None or i % a.every == 0:
        m = segment(f, allp, labs, mask)
        mask = m if mask is None else m
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 2.0)
    if a.scan:   # light sweep reveals the effect from top to bottom over the first 70% of the shot
        yline = H * min(1.0, i / max(1, 0.7 * len(frames)))
        rev = np.clip((yline - np.arange(H)[:, None]) / 60.0, 0, 1)
        soft = soft * rev
    lum = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None] / 255
    tinted = np.clip(COL * (0.35 + 0.95 * lum), 0, 255)
    grey = f.astype(np.float32) * (1 - a.desat) + lum * 255 * a.desat
    grey *= 0.72
    sa = soft[..., None] * 0.88
    img = grey * (1 - sa) + (tinted * 0.8 + f.astype(np.float32) * 0.2) * sa
    edge = np.zeros((H, W), np.uint8)
    cs, _ = cv2.findContours((soft > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cs = [cv2.approxPolyDP(c, 4, True) for c in cs]
    cv2.drawContours(edge, cs, -1, 255, 4, cv2.LINE_AA)
    edge = edge.astype(np.float32) / 255
    glow = cv2.GaussianBlur(edge, (0, 0), 9) * 2.2 + edge
    img = img + GLOW * np.clip(glow, 0, 1.5)[..., None]
    if a.scan and i < 0.7 * len(frames):
        band = np.exp(-((np.arange(H) - yline) / 14.0) ** 2)[:, None, None]
        img = img + GLOW * band * 1.2
    out.append(np.clip(img, 0, 255).astype(np.uint8))
    print(f"\rframe {i + 1}/{len(frames)}", end="", flush=True)
wr = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                       "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
for o in out: wr.stdin.write(o.tobytes())
wr.stdin.close(); wr.wait(); print("\nrecolour ->", a.out)
