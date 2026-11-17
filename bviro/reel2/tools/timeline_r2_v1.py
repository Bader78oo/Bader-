"""Shared timeline for Reel 2 («الجو نزل درجتين»): shots, captions, voice lines and ambience per hook variant.
1080x1920, 24 fps. Imported by build_r2.py (picture) and mix_r2.py (sound)."""
S = "/tmp/claude-0/-home-user-Bader-/871f84b2-2289-5b97-9b32-a74e478b68cd/scratchpad/bviro"
R = f"{S}/reel2"
FPS = 24

# voice take A (audio/vo2_a.mp3): source windows in seconds, padded a little around the measured speech
VO = {
    "L1": (0.10, 1.66),     # الجو نزل درجتين…
    "L2": (2.22, 3.93),     # وربيعنا أعلن الشتا.
    "L2x": (2.36, 3.93),    # ربيعنا أعلن الشتا (leading «و» trimmed, hook C only)
    "L3": (4.56, 6.63),     # لبس الجاكيت… وشبّ الضو.
    "L3a": (4.56, 5.62),    # لبس الجاكيت
    "L4": (7.79, 9.76),     # والمكيّف… بعده شغّال.
    "L5": (10.40, 12.67),   # نودّيك أي مكان… وانت في مكانك.
    "L6": (13.19, 15.36),   # وكلنا نعرفه… كل سنة
}
L4_SECOND = 9.06 - 7.79     # offset of «بعده شغّال» inside L4
L5_SECOND = 11.80 - 10.40   # offset of «وانت في مكانك» inside L5

# A shot: src clip, first source frame, output frame count, speed, zoom (z0 -> z1 about cx, cy), shake px,
# captions [(layer, local first frame, local last frame)], voice [(line, local start seconds)], ambience (clip audio, gain dB)
SLED = dict(src="s1a", f0=6, speed=1.25, z=(1.10, 1.22, 0.5, 0.60), shake=7, amb=("s1a", -9))
BURST = dict(src="s2a", f0=2, speed=1.0, z=(1.00, 1.07, 0.5, 0.42), shake=0, amb=("s2a", -9))
FIRE = dict(src="s3a", f0=None, end=100, speed=1.0, z=(1.0, 1.0, 0.5, 0.5), shake=0, amb=("s3a", -8))
ARC = dict(src="s3c", f0=3, speed=1.0, z=(1.0, 1.0, 0.5, 0.5), shake=0, amb=("s3c", -8))

TAIL = [
    dict(name="reveal", src="s4a", f0=0, n=56, speed=1.0, z=(1.0, 1.045, 0.42, 0.56), shake=0,
         caps=[("c4a", 7, 54), ("c4x", 37, 54)], vo=[("L4", 0.28)], amb=None),
    # two-shot for 32 frames, then a punch-in on the friend's stare taken later in the same clip
    dict(name="stare", src="s5a", f0=10, n=57, speed=1.0, z=(1.0, 1.0, 0.5, 0.5), shake=0, punch=(34, 86, 1.7, 0.75, 0.56),
         caps=[("c5a", 2, 55), ("c5x", 35, 55)], vo=[("L5", 0.10)], amb=None),
    dict(name="loop", src="s6a", f0=2, n=53, speed=1.0, z=(1.02, 1.10, 0.5, 0.60), shake=4,
         caps=[("c6", 2, 52)], vo=[("L6", 0.08)], amb=None),
]

HEADS = {
    "A": [  # sled -> snow burst -> penguin majlis (match cut into the reveal)
        dict(name="sled", n=40, caps=[("c1", 0, 37)], vo=[("L1", 0.04)], **SLED),
        dict(name="burst", n=42, caps=[("c2", 2, 39)], vo=[("L2", 0.05)], **BURST),
        dict(name="fire", n=52, caps=[("c3", 2, 49)], vo=[("L3", 0.05)], **FIRE),
    ],
    "B": [  # snow burst first
        dict(name="burst", n=40, caps=[("c1", 0, 37)], vo=[("L1", 0.04)], **BURST),
        dict(name="sled", n=42, caps=[("c2", 2, 39)], vo=[("L2", 0.05)], **SLED),
        dict(name="fire", n=52, caps=[("c3", 2, 49)], vo=[("L3", 0.05)], **FIRE),
    ],
    "C": [  # penguin majlis (moving arc) first; no match cut
        dict(name="arc", n=40, caps=[("hC", 0, 37)], vo=[("L2x", 0.04)], **ARC),
        dict(name="sled", n=40, caps=[("c1", 2, 37)], vo=[("L1", 0.05)], **SLED),
        dict(name="burst", n=30, caps=[("cL3a", 2, 27)], vo=[("L3a", 0.05)], **BURST),
    ],
}


def shots(variant):
    out, start = [], 0
    for sh in HEADS[variant] + TAIL:
        sh = dict(sh)
        sh["start"] = start
        if sh.get("f0") is None:
            sh["f0"] = sh["end"] - sh["n"] + 1
        start += sh["n"]
        out.append(sh)
    return out, start
