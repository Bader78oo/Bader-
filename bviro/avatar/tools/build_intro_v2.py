"""Avatar intro reel v2: opens inside VR (headset on, hands working), cuts on «لا!» to the talking shot with the
headset in his hand. Caption PNGs come from build_intro.py (same cards, same timing).
usage: python3 -I build_intro_v2.py CLIP_A SYNCED_B VOICE_MP3 OV_DIR OUT_MP4
  CLIP_A   silent opening shot (headset on); A_IN..A_IN+HOOK seconds of it are used
  SYNCED_B lip-synced talking shot, already cut to the voice from «لا!» to the end
"""
import subprocess
import sys

CLIP_A, SYNC_B, VO, OV, OUT = sys.argv[1:6]
W, H = 1080, 1920
SEGS = [(7.62, 15.34), (1.20, 7.56), (15.38, 23.10)]  # voice-track cuts, hook first (as in build_intro.py)
HOOK = 3.46  # «لا!» starts here on the new timeline
A_IN = 0.72  # where the used part of CLIP_A starts
CARDS = [("c1", 7.62, 10.95), ("c2", 11.08, 12.75), ("c3", 12.90, 15.34), ("c4", 1.25, 3.80), ("c5", 3.90, 7.56),
         ("c6", 15.40, 18.60), ("c7", 18.80, 20.45), ("c8", 20.62, 23.10)]


def new_t(src_t):
    off = 0.0
    for a, b in SEGS:
        if a <= src_t <= b:
            return off + src_t - a
        off += b - a
    raise ValueError(src_t)


total = sum(b - a for a, b in SEGS)
up = f"scale={W}:{H}:flags=lanczos,unsharp=5:5:0.6,setsar=1,fps=24"
fc = [f"[0:v]trim={A_IN}:{A_IN + HOOK},setpts=PTS-STARTPTS,{up}[va]",
      f"[1:v]trim=0:{total - HOOK:.3f},setpts=PTS-STARTPTS,{up}[vb]",
      "[va][vb]concat=n=2:v=1:a=0[vc]"]
alab = []
for i, (a, b) in enumerate(SEGS):
    d = b - a
    fc.append(f"[2:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03[a{i}]")
    alab.append(f"[a{i}]")
fc.append(f"{''.join(alab)}concat=n={len(SEGS)}:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11[ao]")
inputs = ["-i", CLIP_A, "-i", SYNC_B, "-i", VO]
last = "vc"
for k, (name, a, b) in enumerate(CARDS):
    inputs += ["-loop", "1", "-i", f"{OV}/{name}.png"]
    fc.append(f"[{last}][{k + 3}:v]overlay=0:0:enable='between(t,{new_t(a):.2f},{new_t(b):.2f})'[o{k}]")
    last = f"o{k}"
inputs += ["-loop", "1", "-i", f"{OV}/handle.png"]
fc.append(f"[{last}][{len(CARDS) + 3}:v]overlay=0:0:enable='gte(t,{HOOK:.2f})'[vo]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vo]", "-map", "[ao]", "-t", f"{total:.2f}",
                "-r", "24", "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                "-ar", "48000", "-movflags", "+faststart", OUT], check=True)
print("ok", OUT, round(total, 2), "s")
