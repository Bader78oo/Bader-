"""Shared timeline for Reel 2 («الجو نزل درجتين»), cut v2 (after the independent review):
reveal at ~4.4 s instead of 5.6 s (the spoken «لبس الجاكيت…» is dropped; the jacket line now lives only on the end card),
the punchline pill «بعده شغّال» and the brand pill «وانت في مكانك» each stay on screen ~1.2-1.4 s, the stare is longer,
the @bviro.1 mark starts with the brand line, and the end card is a dedication. 1080x1920, 24 fps.
Imported by build_r2.py (picture) and mix_r2.py (sound). The first cut is kept in timeline_r2_v1.py."""
S = "/tmp/claude-0/-home-user-Bader-/871f84b2-2289-5b97-9b32-a74e478b68cd/scratchpad/bviro"
R = f"{S}/reel2"
FPS = 24

# voice take A (audio/vo2_a.mp3): source windows in seconds, cut in the silences around the measured speech
VO = {
    "L1": (0.10, 1.66),      # الجو نزل درجتين…
    "L2": (2.22, 3.93),      # وربيعنا أعلن الشتا.
    "L2x": (2.36, 3.93),     # ربيعنا أعلن الشتا (leading «و» trimmed, hook C only)
    "L3b": (5.92, 6.63),     # وشبّ الضو.
    "L4a": (7.79, 8.51),     # والمكيّف…
    "L4b": (9.01, 9.76),     # بعده شغّال.
    "L5a": (10.40, 11.48),   # نودّيك أي مكان…
    "L5b": (11.75, 12.67),   # وانت في مكانك.
    "L6a": (13.19, 14.23),   # وكلنا نعرفه…
    "L6b": (14.53, 15.36),   # كل سنة
}

# A shot: src clip, first source frame, output frame count, speed, zoom (z0 -> z1 about cx, cy), shake px,
# captions [(layer, local first frame, local last frame)], voice [(line, local start seconds)], ambience (clip audio, gain dB)
SLED = dict(src="s1a", f0=6, speed=1.25, z=(1.10, 1.22, 0.5, 0.60), shake=7, amb=("s1a", -9))
BURST = dict(src="s2a", f0=2, speed=1.0, z=(1.00, 1.07, 0.5, 0.42), shake=0, amb=("s2a", -9))
FIRE = dict(src="s3a", f0=None, end=100, speed=1.0, z=(1.0, 1.08, 0.42, 0.56), shake=0, amb=("s3a", -8))
ARC = dict(src="s3c", f0=3, speed=1.0, z=(1.0, 1.0, 0.5, 0.5), shake=0, amb=("s3c", -8))

TAIL = [
    # match cut: same zoom and anchor as the last fire frame, the push continues
    dict(name="reveal", src="s4a", f0=0, n=58, speed=1.2, z=(1.08, 1.13, 0.42, 0.56), shake=0,
         caps=[("c4a", 4, 57), ("c4x", 29, 57)], vo=[("L4a", 0.20), ("L4b", 1.18)], amb=None),
    # v3: the dedication sits on the friend's stare (the laugh peak) and the brand line moves to the last shot,
    # because three fresh blind viewers named the brand line at 7.0 s as the moment the joke turned into an ad
    dict(name="stare", src="s5a", f0=10, n=62, speed=1.0, z=(1.0, 1.03, 0.5, 0.55), shake=0, punch=(27, 86, 1.7, 0.75, 0.56),
         caps=[("c7", 1, 26), ("c6", 28, 61)], vo=[("L6a", 0.10), ("L6b", 1.17)], amb=None),
    dict(name="loop", src="s6a", f0=2, n=54, speed=1.0, z=(1.02, 1.10, 0.5, 0.60), shake=4,
         caps=[("c5a", 1, 53), ("c5x", 31, 53)], vo=[("L5a", 0.06), ("L5b", 1.22)], amb=None),
]

HEADS = {
    "A": [  # sled -> snow burst -> penguin majlis (match cut into the reveal)
        dict(name="sled", n=37, caps=[("c1", 0, 35)], vo=[("L1", 0.04)], **SLED),
        dict(name="burst", n=41, caps=[("c2", 0, 39)], vo=[("L2", 0.06)], **BURST),
        dict(name="fire", n=28, caps=[("c3b", 0, 25)], vo=[("L3b", 0.12)], **FIRE),
    ],
    "B": [  # snow burst first
        dict(name="burst", n=37, caps=[("c1", 0, 35)], vo=[("L1", 0.04)], **BURST),
        dict(name="sled", n=41, caps=[("c2", 0, 39)], vo=[("L2", 0.06)], **SLED),
        dict(name="fire", n=28, caps=[("c3b", 0, 25)], vo=[("L3b", 0.12)], **FIRE),
    ],
    "C": [  # penguin majlis (moving arc) first; no match cut
        dict(name="arc", n=38, caps=[("hC", 0, 36)], vo=[("L2x", 0.04)], **ARC),
        dict(name="sled", n=37, caps=[("c1", 0, 35)], vo=[("L1", 0.04)], **SLED),
        dict(name="burst", n=22, caps=[], vo=[], **BURST),
    ],
}
HANDLE_FROM = "loop"       # the small @bviro.1 mark starts with the brand line


def shots(variant):
    out, start = [], 0
    for sh in HEADS[variant] + TAIL:
        sh = dict(sh)
        sh["start"] = start
        if sh.get("f0") is None:
            sh["f0"] = sh["end"] - int(round((sh["n"] - 1) * sh["speed"]))
        start += sh["n"]
        out.append(sh)
    return out, start
