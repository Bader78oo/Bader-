"""«Under construction» looks for a filmed shot: wireframe, untextured clay and low-poly colour.

Every look is computed from the footage itself, so the stages line up exactly with the finished picture and can be
revealed one after another (the way a 3D scene is built: mesh, then surfaces, then colour and light).

The mesh is a Delaunay triangulation of points placed along the picture's edges, so its triangles follow the hills,
the water and the horizon. A subject (the camel) is kept out of the looks with a colour-seeded GrabCut matte.
"""
import subprocess

import cv2
import numpy as np
from scipy.spatial import Delaunay

W, H = 1080, 1920
TURQ = np.array([0, 205, 200], np.float32)


def load_frames(path, fps=None, start=0.0, dur=None):
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}" + (f",fps={fps}" if fps else "")
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}"] + (["-t", f"{dur:.3f}"] if dur else []) + ["-i", path, "-vf", vf, "-pix_fmt", "rgb24", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def fur_mask(frame):
    """Rough colour mask of a tan camel (and the white headset strap on it) against green scenery."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.int32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]  # h in 0..179
    fur = (h >= 6) & (h <= 28) & (s >= 28) & (s <= 190) & (v >= 70)
    return fur


def zoom(frames, z, cx=0.5, cy=1.0):
    """Frames enlarged by z about the point (cx, cy) given as fractions of the frame (default: bottom centre)."""
    w, h = W / z, H / z
    x0, y0 = int(round((W - w) * cx)), int(round((H - h) * cy))
    out = np.empty_like(frames)
    for k, f in enumerate(frames):
        out[k] = cv2.resize(f[y0:y0 + int(round(h)), x0:x0 + int(round(w))], (W, H), interpolation=cv2.INTER_LANCZOS4)
    return out


def subject_matte(frame, region=(0.0, 0.50, 1.0, 1.0), prev=None, headset_band=0.40, earth_below=None, shell_reach=None):
    """Soft matte (0..1) of the camel and her headset inside `region` (x0, y0, x1, y1 as fractions of the frame).

    The fur is found by colour and the white headset is added to it; GrabCut then settles the outline.
    Seen from the front (shell_reach=None) the headset lies inside the convex hull of the fur, in its upper
    `headset_band`. Seen from behind, the shell sticks out past the fur when she turns her head: shell_reach (a fraction
    of the fur's width) lets white that touches the fur count as headset that far outside the hull, and the outline
    then stays within a few pixels of those colour seeds, which keeps it steady from frame to frame.
    earth_below (a fraction of the frame height) keeps bare brown earth, darker and more saturated than the fur, out of
    the matte below that line, for shots where she stands beside a dirt path; above the line the same colours are the
    shaded fur of her ears."""
    x0, y0, x1, y1 = int(region[0] * W), int(region[1] * H), int(region[2] * W), int(region[3] * H)
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    hh, ss, vv = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    fur = np.zeros((H, W), np.uint8)
    fur[y0:y1, x0:x1] = fur_mask(frame)[y0:y1, x0:x1]
    earth = np.zeros((H, W), bool)
    if earth_below is not None:
        earth = (hh >= 10) & (hh <= 30) & (ss >= 85) & (vv >= 40) & (vv <= 165)
        earth[: int(earth_below * H)] = False
        earth = cv2.morphologyEx(earth.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0
        fur[earth] = 0
    fur = cv2.morphologyEx(fur, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(fur, 8)
    if n <= 1:
        return np.zeros((H, W), np.float32)
    big = [k for k in range(1, n) if stats[k, cv2.CC_STAT_AREA] >= 0.004 * W * H]
    if not big:
        big = [1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))]
    core = np.isin(lab, big).astype(np.uint8)
    hull = np.zeros((H, W), np.uint8)
    cv2.fillConvexPoly(hull, cv2.convexHull(cv2.findNonZero(core)), 1)
    bx, by, bw, bh = cv2.boundingRect(cv2.findNonZero(hull))
    light = (ss < 75) & (vv > 120)  # the white headset shell and strap
    band = np.zeros((H, W), bool)  # the headset sits in the upper part of the head; lower down, light pixels are water
    if shell_reach is None:
        glow = (vv > 150) & (ss > 50) & (((hh > 120) & (hh < 165)) | ((hh > 78) & (hh < 100)))  # its purple and turquoise rim
        inner = cv2.erode(hull, np.ones((25, 25), np.uint8))
        band[by:by + int(headset_band * bh)] = True
        seed = np.clip(core + ((light | glow) & (inner > 0) & band), 0, 1).astype(np.uint8)
        seed = cv2.morphologyEx(seed, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
        water = (hh > 70) & (hh < 105) & (ss > 28) & ~band  # turquoise pool beside her cheek: never part of her
        seed[water] = 0
        pad = int(0.08 * max(bw, bh))
        allowed = np.zeros((H, W), bool)
        allowed[max(by - pad, 0):min(by + bh + pad, H), max(bx - pad, 0):min(bx + bw + pad, W)] = True
    else:
        reach = int(shell_reach * bw)
        dil = cv2.distanceTransform(1 - hull, cv2.DIST_L2, 5) <= reach  # everything within `reach` of the fur's hull
        band[max(by - reach, 0):by + int(headset_band * bh)] = True
        water = (hh > 40) & (hh < 105) & (ss >= 20)  # the pool, the mist over it and the grass are greenish even when pale
        cand = cv2.morphologyEx((light & ~water & dil & band).astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n, lab = cv2.connectedComponents(np.clip(core + cand, 0, 1).astype(np.uint8), connectivity=8)
        keep = np.unique(lab[core > 0])
        seed = np.isin(lab, keep[keep > 0])  # white that touches the fur
        near = cv2.dilate(seed.astype(np.uint8), np.ones((41, 41), np.uint8)) > 0
        seed = (seed | ((vv < 75) & near & ~water)).astype(np.uint8)  # the headset's black padding and strap housing
        seed = cv2.morphologyEx(seed, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
        seed[water] = 0
        allowed = cv2.dilate(seed, np.ones((31, 31), np.uint8)) > 0
    gc = np.full((H, W), cv2.GC_BGD, np.uint8)
    gc[allowed] = cv2.GC_PR_BGD
    gc[cv2.dilate(seed, np.ones((9, 9), np.uint8)) > 0] = cv2.GC_PR_FGD
    gc[cv2.erode(seed, np.ones((15, 15), np.uint8)) > 0] = cv2.GC_FGD
    green = (hh > 32) & (hh < 105) & (ss > 60)
    gc[(green | water) & (gc != cv2.GC_FGD)] = cv2.GC_BGD  # grass and pool are background for sure
    gc[earth] = cv2.GC_BGD
    if prev is not None:  # only the deep core of the previous matte is a safe prior when the head moves
        deep = cv2.erode((prev > 0.97).astype(np.uint8), np.ones((41, 41), np.uint8)) > 0
        gc[deep & (gc != cv2.GC_BGD)] = cv2.GC_FGD
    small = cv2.resize(frame, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    gcs = cv2.resize(gc, (W // 2, H // 2), interpolation=cv2.INTER_NEAREST)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(cv2.cvtColor(small, cv2.COLOR_RGB2BGR), gcs, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
    m = ((gcs == cv2.GC_FGD) | (gcs == cv2.GC_PR_FGD)).astype(np.uint8)
    notsubj = cv2.resize((green | water | earth).astype(np.uint8), (W // 2, H // 2), interpolation=cv2.INTER_NEAREST)
    m[notsubj > 0] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))  # drops slivers of background along the outline
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        m = (lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    inv = (1 - m).astype(np.uint8)  # fill holes: background that does not touch the frame border is inside the subject
    n, lab, stats, _ = cv2.connectedComponentsWithStats(inv, 4)
    for k in range(1, n):
        x, y, w, h = stats[k, :4]
        if x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]:
            m[lab == k] = 1
    m = cv2.resize(m.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    return np.clip(cv2.GaussianBlur(m, (0, 0), 2.2) * 1.15 - 0.075, 0, 1)


def decontaminate(frame, matte):
    """Foreground colours for compositing over a new background: edge pixels take the colour of the fur just inside,
    so no green fringe from the old background is carried along."""
    solid = (matte > 0.96).astype(np.float32)
    f = frame.astype(np.float32)
    num = cv2.GaussianBlur(f * solid[..., None], (0, 0), 7)
    den = cv2.GaussianBlur(solid, (0, 0), 7)[..., None]
    est = num / np.maximum(den, 1e-4)
    k = np.clip((matte - 0.55) / 0.41, 0, 1)[..., None]  # 1 = trust the pixel itself, 0 = use the inside colour
    edge = (den > 0.02)
    return np.where(edge, f * k + est * (1 - k), f)


def build_mesh(frame, keep_out=None, cell=13, grid=62, seed=3, blur=2.0, canny=(22, 60)):
    """Mesh points along the picture's edges plus a loose grid; returns (points, triangles)."""
    rng = np.random.default_rng(seed)
    g = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY), (0, 0), blur)
    mag = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    edges = cv2.Canny(g, canny[0], canny[1])
    ys, xs = np.nonzero(edges)
    order = np.argsort(-mag[ys, xs])
    taken = np.zeros((H // cell + 2, W // cell + 2), bool)
    pts = []
    for i in order:  # strongest edges first, at most one point per cell
        cy, cx = ys[i] // cell, xs[i] // cell
        if not taken[cy, cx]:
            taken[cy, cx] = True
            pts.append((xs[i], ys[i]))
    for y in range(0, H + grid, grid):
        for x in range(0, W + grid, grid):
            px = min(max(x + rng.integers(-grid // 3, grid // 3 + 1), 0), W - 1)
            py = min(max(y + rng.integers(-grid // 3, grid // 3 + 1), 0), H - 1)
            if not taken[py // cell, px // cell]:
                pts.append((px, py))
    m = 90  # border points sit outside the frame, so a mesh that follows the camera still covers the picture
    for x in np.linspace(-m, W - 1 + m, 16):
        pts += [(x, -m), (x, H - 1 + m)]
    for y in np.linspace(-m, H - 1 + m, 26):
        pts += [(-m, y), (W - 1 + m, y)]
    pts = np.unique(np.array(pts, np.float32), axis=0)
    if keep_out is not None:  # no edge points on the subject (she is not part of the built world), only a loose grid
        inside = keep_out[np.clip(pts[:, 1].astype(int), 0, H - 1), np.clip(pts[:, 0].astype(int), 0, W - 1)] > 0.5
        border = (pts[:, 0] < 0) | (pts[:, 0] > W - 1) | (pts[:, 1] < 0) | (pts[:, 1] > H - 1)
        pts = pts[~inside | border]
        gy, gx = np.mgrid[0:H:grid, 0:W:grid]
        g = np.stack([gx.ravel() + grid // 2, gy.ravel() + grid // 2], 1).astype(np.float32)
        g = g[(g[:, 0] < W) & (g[:, 1] < H)]
        pts = np.concatenate([pts, g[keep_out[g[:, 1].astype(int), g[:, 0].astype(int)] > 0.5]])
        pts = np.unique(pts, axis=0)
    tri = Delaunay(pts).simplices.astype(np.int32)
    return pts, tri


def raster(pts, tri):
    """Triangle index for every pixel, and an anti-aliased image of the mesh lines (0..1)."""
    idx = np.zeros((H, W), np.int32)
    p = np.round(pts * 16).astype(np.int32)  # sub-pixel precision
    for k, t in enumerate(tri):
        cv2.fillConvexPoly(idx, p[t], int(k), lineType=cv2.LINE_8, shift=4)
    lines = np.zeros((H, W), np.uint8)
    e = np.unique(np.sort(np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]), axis=1), axis=0)
    cv2.polylines(lines, [p[[a, b]].reshape(-1, 1, 2) for a, b in e], False, 255, 1, cv2.LINE_AA, shift=4)
    return idx, lines.astype(np.float32) / 255.0


def tri_means(frame, idx, ntri):
    flat = idx.reshape(-1)
    cnt = np.maximum(np.bincount(flat, minlength=ntri), 1).astype(np.float32)
    f = frame.reshape(-1, 3).astype(np.float32)
    return np.stack([np.bincount(flat, weights=f[:, c], minlength=ntri) / cnt for c in range(3)], -1)


def looks(frame, idx, lines, ntri):
    """(wireframe, clay, lowpoly) RGB float images in 0..255 for one frame.

    wireframe: glowing mesh lines over faintly shaded facets on a dark viewport, so the shapes stay readable;
    clay: the same facets as an untextured grey model; lowpoly: the facets in their average colour."""
    col = tri_means(frame, idx, ntri)
    low = col[idx]
    lum = (0.299 * col[:, 0] + 0.587 * col[:, 1] + 0.114 * col[:, 2]) / 255.0
    lum = np.clip((lum - 0.12) / 0.78, 0, 1) ** 0.85
    clay_c = (72 + 150 * lum)[:, None] * np.array([0.97, 0.985, 1.03], np.float32)[None, :]
    clay = clay_c[idx]
    clay = clay * (1 - 0.55 * lines[..., None]) + np.array([245, 250, 255], np.float32) * 0.55 * lines[..., None]
    low = low * (1 - 0.22 * lines[..., None]) + 255.0 * 0.22 * lines[..., None]
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    bg = np.array([14, 10, 40], np.float32) * (1 - yy) + np.array([30, 8, 70], np.float32) * yy
    facet = (lum[:, None] ** 1.3) * np.array([46, 58, 120], np.float32)[None, :]
    glow = cv2.GaussianBlur(lines, (0, 0), 5.0)
    wire = bg + facet[idx] + TURQ * (0.95 * lines[..., None] + 0.50 * glow[..., None]) + 60.0 * (lines[..., None] ** 2)
    return np.clip(wire, 0, 255), np.clip(clay, 0, 255), np.clip(low, 0, 255)


def track(frames, bg_mask):
    """Similarity transform (2x3) of the background from frame 0 to every frame, smoothed over time."""
    g0 = cv2.cvtColor(frames[0], cv2.COLOR_RGB2GRAY)
    p0 = cv2.goodFeaturesToTrack(g0, 700, 0.01, 14, mask=bg_mask)
    guess = p0.copy()
    par = [(1.0, 0.0, 0.0, 0.0)]
    for k in range(1, len(frames)):
        g = cv2.cvtColor(frames[k], cv2.COLOR_RGB2GRAY)
        p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g, p0, guess.copy(), winSize=(31, 31), maxLevel=4, flags=cv2.OPTFLOW_USE_INITIAL_FLOW)
        ok = st.ravel() == 1
        M, _ = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=3.0)
        if M is None:
            par.append(par[-1])
            continue
        par.append((float(M[0, 0]), float(M[1, 0]), float(M[0, 2]), float(M[1, 2])))
        guess = (p0.reshape(-1, 2) @ M[:, :2].T + M[:, 2]).reshape(-1, 1, 2).astype(np.float32)
    par = np.array(par, np.float64)
    k = 7
    pad = np.pad(par, ((k // 2, k // 2), (0, 0)), mode="edge")
    sm = np.stack([np.convolve(pad[:, c], np.ones(k) / k, mode="valid") for c in range(4)], 1)
    sm[0] = par[0]
    return [np.array([[a, -b, tx], [b, a, ty]], np.float32) for a, b, tx, ty in sm]


def move(pts, M):
    return pts @ M[:, :2].T + M[:, 2]


def tri_order(pts, tri, mode, origin=None, jitter=0.07, seed=5):
    """A 0..1 ordering of the triangles (what appears first): 'radial' from a point, 'up' from the bottom, 'right'."""
    c = pts[tri].mean(1)
    if mode == "radial":
        d = np.hypot(c[:, 0] - origin[0], c[:, 1] - origin[1])
    elif mode == "up":
        d = -c[:, 1]
    elif mode == "down":
        d = c[:, 1]
    else:
        d = c[:, 0]
    d = (d - d.min()) / max(d.max() - d.min(), 1e-6)
    d = d + np.random.default_rng(seed).uniform(-jitter, jitter, len(d))
    return ((d - d.min()) / (d.max() - d.min())).astype(np.float32)


def activation(order, p, soft=0.10):
    """Per-triangle 0..1 switch for progress p (0..1): triangles turn on in their order, each over `soft`."""
    return np.clip((p * (1 + soft) - order) / soft, 0, 1).astype(np.float32)
