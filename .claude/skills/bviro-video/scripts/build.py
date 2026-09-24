#!/usr/bin/env python3
"""Render a Bviro reel from a storyboard (sb.json): cut + grade shots, overlay captions/
stickers/name card/checklist/end card, and mix voice + ambient pad + whooshes.

Usage (work dir holds sb.json, the shot clips, vo.mp3, words_final.json, and the kit):
  python3 build.py sb.json [--reuse-overlay] [--qa]

--reuse-overlay  skip re-rendering ov/*.png (only shots/audio changed)
--qa             also write qa_sheet.jpg: one small frame per shot, for a cheap visual check
Needs ffmpeg, node + playwright (for the overlay), internet on first run (Cairo font, icons).
"""
import json, os, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sb = json.load(open(sys.argv[1], encoding="utf-8"))
W, H, FPS, DUR = sb["width"], sb["height"], sb["fps"], sb["duration"]

def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)

# 0. fetch any input that has a URL in the storyboard but isn't on disk yet --------
for item in sb["shots"] + [sb.get("assets", {})]:
    for name, url in ([(item["src"], item.get("url"))] if "src" in item else item.items()):
        if url and not os.path.exists(name):
            urllib.request.urlretrieve(url, name)

# 1. icons (Lucide, MIT) ----------------------------------------------------------
icons = {"circle-check"} | {c["icon"] for c in sb.get("captions", []) if c.get("icon")}
icons |= {c["icon"] for c in sb.get("checklist", {}).get("items", [])}
os.makedirs("icons", exist_ok=True)
for n in icons:
    if not os.path.exists(f"icons/{n}.svg"):
        urllib.request.urlretrieve(f"https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{n}.svg", f"icons/{n}.svg")

# 2. overlay frames ---------------------------------------------------------------
for f in ("overlay.html", "frames.js"):
    if not os.path.exists(f):
        os.symlink(os.path.join(HERE, f), f)
if not os.path.exists("brand"):
    os.symlink(os.path.join(HERE, "..", "brand"), "brand")
if "--reuse-overlay" not in sys.argv or not os.path.isdir("ov"):
    npm_root = subprocess.check_output(["npm", "root", "-g"]).decode().strip()
    subprocess.run(["node", "frames.js", sys.argv[1]], check=True, env={**os.environ, "NODE_PATH": npm_root})

# 3. shots: cut, fill 9:16, grade -------------------------------------------------
g = sb.get("grade", {})
vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1,"
      f"eq=contrast={g.get('contrast', 1.06)}:saturation={g.get('saturation', 1.10)}:brightness={g.get('brightness', 0.005)},"
      "unsharp=5:5:0.4")
if g.get("lut"):
    vf += f",lut3d=file={g['lut']}"
cuts, t = [], 0.0
with open("list.txt", "w") as lst:
    for i, s in enumerate(sb["shots"]):
        ff("-ss", s["in"], "-i", s["src"], "-t", s["dur"], "-an",
           "-vf", f"{vf},tpad=stop_mode=clone:stop_duration=3,trim=duration={s['dur']},setpts=PTS-STARTPTS",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", 14, "-pix_fmt", "yuv420p", f"seg{i}.mp4")
        lst.write(f"file 'seg{i}.mp4'\n")
        t += s["dur"]; cuts.append(round(t, 3))
cuts = cuts[:-1]
ff("-f", "concat", "-safe", 0, "-i", "list.txt", "-c", "copy", "base.mp4")
print(f"shots total {t:.2f}s (storyboard duration {DUR}s); cuts at {cuts}")

# 4. sound: voice + ambient pad + whoosh per cut + impact on end card + optional music
au = sb.get("audio", {})
inputs, chains, labels = ["-i", sb["voiceover"]], ["[0:a]volume=1.0[vo]"], ["[vo]"]
k = 1  # next ffmpeg input index
if au.get("pad", True):
    pad_labels = []
    for f, v in [(110, .5), (164.81, .35), (220, .25), (329.63, .15)]:  # soft A-minor-ish drone
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={f}:duration={DUR}"]
        chains.append(f"[{k}:a]volume={v},afade=t=in:d=2,afade=t=out:st={DUR - 2}:d=2[p{k}]"); pad_labels.append(f"[p{k}]"); k += 1
    chains.append("".join(pad_labels) + f"amix=inputs={len(pad_labels)}:normalize=0,aecho=0.8:0.6:120|240:0.35|0.2,volume={au.get('pad_gain', 0.035)}[pad]")
    labels.append("[pad]")
if au.get("whoosh_on_cuts", True):
    for c in cuts:
        d = max(0, int((c - 0.2) * 1000))
        inputs += ["-f", "lavfi", "-i", "anoisesrc=color=pink:duration=0.45:amplitude=0.5"]
        chains.append(f"[{k}:a]bandpass=f=1500:w=2500,afade=t=in:d=0.2,afade=t=out:st=0.2:d=0.25,volume=0.18,adelay={d}|{d}[w{k}]")
        labels.append(f"[w{k}]"); k += 1
if au.get("impact_at_end", True) and sb.get("end_card"):
    d = int(sb["end_card"]["s"] * 1000)
    inputs += ["-f", "lavfi", "-i", "sine=frequency=55:duration=1.2"]
    chains.append(f"[{k}:a]afade=t=out:st=0.05:d=1.1,volume=0.5,adelay={d}|{d}[imp]"); labels.append("[imp]"); k += 1
if au.get("music"):
    inputs += ["-stream_loop", "-1", "-i", au["music"]]
    chains.append(f"[{k}:a]volume={au.get('music_gain_db', -20)}dB,afade=t=out:st={DUR - 1.5}:d=1.5[mus]"); labels.append("[mus]"); k += 1
fc = ";".join(chains) + ";" + "".join(labels) + \
     f"amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.95,apad=whole_dur={DUR},atrim=0:{DUR}[a]"
ff(*inputs, "-filter_complex", fc, "-map", "[a]", "-ar", 48000, "-ac", 2, "mix.wav")

# 5. composite + mux ----------------------------------------------------------------
vig = "vignette=PI/5," if g.get("vignette", True) else ""
ff("-i", "base.mp4", "-framerate", FPS, "-i", "ov/%04d.png", "-i", "mix.wav",
   "-filter_complex", f"[0:v]{vig}null[b];[b][1:v]overlay=0:0:format=auto,format=yuv420p[v]",
   "-map", "[v]", "-map", "2:a", "-t", DUR, "-c:v", "libx264", "-preset", "slow", "-crf", 17,
   "-profile:v", "high", "-r", FPS, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", sb.get("output", "final.mp4"))
subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "compact", sb.get("output", "final.mp4")])

# 6. optional QA sheet: one 180px-wide frame from the middle of every shot ----------
if "--qa" in sys.argv:
    t, tiles = 0.0, []
    for i, s in enumerate(sb["shots"]):
        ff("-ss", round(t + s["dur"] / 2, 2), "-i", sb.get("output", "final.mp4"), "-frames:v", 1, "-vf", "scale=180:-2", f"qa{i}.jpg")
        tiles.append(f"qa{i}.jpg"); t += s["dur"]
    ff(*sum((["-i", x] for x in tiles), []), "-filter_complex", "".join(f"[{i}:v]" for i in range(len(tiles))) + f"hstack=inputs={len(tiles)}",
       "-q:v", 6, "qa_sheet.jpg")
    print("qa_sheet.jpg written")
