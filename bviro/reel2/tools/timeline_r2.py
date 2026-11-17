"""Shared timeline for Reel 2 («الجو نزل درجتين»), cut v4 (Bader, 17 Nov): the friend in the beige dishdasha SPEAKS.
His call «الحبيب!» is heard over the end of the snow scene, the picture cuts to him saying «تراك في الـVR.. انتبه!»
(lip-synced close-up over the shoulder of the man in the headset), then the air-conditioner beat, then the brand line with
the service named on screen. The dedication card and «وكلنا نعرفه… كل سنة» are gone. 1080x1920, 24 fps.
Earlier cuts: timeline_r2_v1.py, _v2.py, _v3.py (with build_r2_v3.py / mix_r2_v3.py)."""
S = "/tmp/claude-0/-home-user-Bader-/871f84b2-2289-5b97-9b32-a74e478b68cd/scratchpad/bviro"
R = f"{S}/reel2"
FPS = 24
NARR, FRIEND, BRAND = f"{R}/audio/vo2_a.mp3", f"{R}/audio/fr_b.mp3", f"{S}/audio/vo_b.mp3"

# voice pieces: name -> (file, start, end, level offset dB, low-pass Hz or None)
VO = {
    "L1": (NARR, 0.10, 1.66, 0, None),       # الجو نزل درجتين…
    "L2": (NARR, 2.22, 3.93, 0, None),       # وربيعنا أعلن الشتا.
    "L3b": (NARR, 5.92, 6.63, 0, None),      # وشبّ الضو.
    "L4a": (NARR, 7.79, 8.51, 0, None),      # والمكيّف…
    "L4b": (NARR, 9.01, 9.76, 0, None),      # بعده شغّال.
    "F1": (FRIEND, 0.02, 0.93, -1, 3200),    # الحبيب!  (friend, heard from outside the headset: slightly muffled)
    "F2": (FRIEND, 1.46, 2.52, 1, None),     # تراك في الـVR…
    "F3": (FRIEND, 2.65, 3.32, 1, None),     # انتبه!
    "B1": (BRAND, 15.40, 16.03, 0, None),    # بيفيرو…        (Bader's voice, from the first reel)
    "B2": (BRAND, 16.21, 17.64, 0, None),    # نودّيك أي مكان،
    "B3": (BRAND, 17.80, 18.66, 0, None),    # وانت في مكانك.
}

SLED = dict(src="s1a", f0=6, speed=1.25, z=(1.10, 1.22, 0.5, 0.60), shake=7, amb=("s1a", -9))
BURST = dict(src="s2a", f0=2, speed=1.0, z=(1.00, 1.07, 0.5, 0.42), shake=0, amb=("s2a", -9))
FIRE = dict(src="s3a", f0=None, end=100, speed=1.0, z=(1.0, 1.08, 0.42, 0.56), shake=0, amb=("s3a", -8))

SHOTS = [
    dict(name="sled", n=37, caps=[("c1", 0, 35)], vo=[("L1", 0.04)], **SLED),
    dict(name="burst", n=41, caps=[("c2", 0, 39)], vo=[("L2", 0.06)], **BURST),
    # the friend's call starts before the snow scene ends
    dict(name="fire", n=42, caps=[("c3b", 0, 19), ("f1", 21, 41)], vo=[("L3b", 0.12), ("F1", 0.88)], **FIRE),
    # lip-synced close-up; clip time 1.208 s = first frame here («تراك…» starts at 1.34 s of the clip, «انتبه!» at 2.55 s)
    dict(name="friend", src="s7ls", f0=29, n=53, speed=1.0, z=(1.0, 1.05, 0.62, 0.45), shake=0,
         caps=[("f2", 2, 52), ("f3", 32, 52)], vo=[("F2", 0.132), ("F3", 1.342)], amb=None),
    dict(name="reveal", src="s4a", f0=0, n=56, speed=1.2, z=(1.0, 1.05, 0.42, 0.56), shake=0,
         caps=[("c4a", 4, 55), ("c4x", 29, 55)], vo=[("L4a", 0.20), ("L4b", 1.18)], amb=None),
    dict(name="loop", src="s6a", f0=2, n=78, speed=1.0, z=(1.06, 1.14, 0.5, 0.60), shake=4,
         caps=[("e2", 18, 77), ("e3", 55, 77)], vo=[("B1", 0.08), ("B2", 0.78), ("B3", 2.28)], amb=None),
]
END_LAYERS = ["brandpill", "handle_low"]     # drawn from the first frame of the last shot
MUSIC_UNTIL = "friend"                        # the snow-world music and ambience stop when the picture leaves the headset
BEEP_AT = "reveal"                            # the remote beep sits on the air-conditioner shot


def shots(variant="A"):
    out, start = [], 0
    for sh in SHOTS:
        sh = dict(sh)
        sh["start"] = start
        if sh.get("f0") is None:
            sh["f0"] = sh["end"] - int(round((sh["n"] - 1) * sh["speed"]))
        start += sh["n"]
        out.append(sh)
    return out, start
