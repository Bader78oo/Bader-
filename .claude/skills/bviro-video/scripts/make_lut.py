#!/usr/bin/env python3
"""Generate the Bviro look as a 33-point .cube LUT (for ffmpeg lut3d / Resolve / Premiere).

Look: gentle filmic S-curve, shadows tinted toward Bviro deep purple (#2B0157),
highlights kept clean with a faint teal (#01CEC9) sheen, skin-safe mid-tones,
slightly richer saturation. Strength is baked at `--mix` (default 0.6) so it layers
on top of the per-shot eq in build.py without looking heavy.

Usage: python3 make_lut.py [out.cube] [--mix 0.6]
"""
import sys
import numpy as np

out = next((a for a in sys.argv[1:] if a.endswith(".cube")), "bviro_look.cube")
mix = float(sys.argv[sys.argv.index("--mix") + 1]) if "--mix" in sys.argv else 0.6
N = 33

g = np.linspace(0, 1, N)
b, gg, r = np.meshgrid(g, g, g, indexing="ij")  # .cube order: red varies fastest
rgb = np.stack([r, gg, b], -1)

def s_curve(x, k=0.35):  # soft contrast: blend toward smoothstep, pivots at mid-grey
    return x + k * (x * x * (3 - 2 * x) - x)

luma = rgb @ np.array([0.2126, 0.7152, 0.0722])
graded = s_curve(rgb)

shadow = np.clip(1 - luma / 0.45, 0, 1)[..., None] ** 1.5        # 1 in deep shadows -> 0 by 45% luma
high = np.clip((luma - 0.6) / 0.4, 0, 1)[..., None] ** 1.5         # 0 below 60% -> 1 at white
purple, teal = np.array([43, 1, 87]) / 255, np.array([1, 206, 201]) / 255
graded = graded + shadow * 0.10 * (purple - 0.5 * graded)            # lift/tint shadows
graded = graded + high * 0.035 * (teal - graded)                     # faint teal sheen

lum2 = (graded @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
graded = lum2 + (graded - lum2) * 1.08                               # +8% saturation

graded = np.clip(rgb + (graded - rgb) * mix, 0, 1)

with open(out, "w") as f:
    f.write(f'TITLE "Bviro look (mix {mix})"\nLUT_3D_SIZE {N}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
    for v in graded.reshape(-1, 3):
        f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
print(out, f"{N}^3, mix {mix}")
