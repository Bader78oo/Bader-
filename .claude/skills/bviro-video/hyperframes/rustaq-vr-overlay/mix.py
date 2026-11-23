#!/usr/bin/env python3
"""mix.py vo.wav music.(mp3|wav) [music_offset] -> mix.wav : VO + ducked music + SFX placed from hf/words.js"""
import json, os, re, subprocess, sys
js = open("hf/words.js").read()
W = json.loads(re.search(r"W=(\[.*?\]),E", js).group(1)); E = json.loads(re.search(r"E=(\[.*?\]),CUT", js).group(1)); C = json.loads(re.search(r"CUT=(\{.*?\}),DUR", js).group(1)); D = float(re.search(r"DUR=([\d.]+)", js).group(1))
X = os.path.expanduser("~/.claude/skills/media-use/audio/assets/sfx")
ev = [("impact-bass-1", 0.0, -12, None), ("whoosh-short", C["hook2"] - 0.05, -16, None), ("whoosh", C["uni"] - 0.12, -17, None), ("pop", W[7], -19, None),
      ("whoosh-short", C["last"] - 0.05, -19, None)]
ev += [("click-soft", W[13] + 0.1 + k * 0.22, -17, None) for k in range(3)]
ev += [("impact-bass-2", W[18] + 0.22, -16, None), ("pop", W[19], -20, None),
       ("riser", C["in"] - 1.1, -17, (8.9, 1.1)), ("impact-bass-1", C["in"], -10, None),
       ("whoosh-short", C["door"] - 0.05, -18, None), ("whoosh-short", C["cls"] - 0.05, -19, None), ("pop", W[25], -19, None),
       ("whoosh-short", C["stu"] - 0.05, -19, None), ("pop", W[26], -19, None), ("whoosh-short", C["lab"] - 0.05, -19, None), ("pop", W[27], -19, None),
       ("sparkle", W[31], -18, None), ("whoosh", C["dig"] - 0.12, -17, None), ("pop", C["dig"] + 0.15, -20, None), ("pop", C["dig"] + 0.35, -20, None),
       ("pop", W[39] - 0.05, -18, None)]
ev += [("click-soft", W[42] + k * 0.12, -18, None) for k in range(4)]
ev += [("whoosh-short", C["tryit"] - 0.05, -18, None), ("click", C["freeze"], -10, None), ("impact-bass-2", C["freeze"] + 0.02, -15, None),
       ("whoosh", C["end"] - 0.12, -16, None)]
ev += [("pop", W[51] + 0.25 + k * 0.13, -19, None) for k in range(4)] + [("chime", W[52], -17, None)]
vo, mus = sys.argv[1], sys.argv[2]; off = sys.argv[3] if len(sys.argv) > 3 else "0"
inp = ["-i", vo, "-ss", off, "-i", mus]; fc = []; labs = []
for i, (n, t, g, cut) in enumerate(ev):
    inp += (["-ss", str(cut[0]), "-t", str(cut[1])] if cut else []) + ["-i", f"{X}/{n}.mp3"]
    d = int(max(t, 0) * 1000); f = ",afade=t=in:d=0.5,afade=t=out:st=%.2f:d=0.2" % (cut[1] - 0.2) if cut else ""
    fc.append(f"[{i+2}:a]aresample=48000,aformat=channel_layouts=stereo{f},volume={g}dB,adelay={d}|{d}[s{i}]"); labs.append(f"[s{i}]")
fc.append(f"[0:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={D},asplit=2[vo][sc]")
# extra dips under key words (name of the place, «العُماني», the closing question); (start, end, depth)
dips = [(W[11] - 0.15, E[11] + 0.12, 0.6), (W[36] - 0.15, E[37] + 0.12, 0.6), (W[47] - 0.1, E[53] + 0.1, 0.55)]
dv = "*".join(f"(1-{k}*clip((t-{a:.3f})/0.15,0,1)*clip(({b:.3f}-t)/0.15,0,1))" for a, b, k in dips)
fc.append(f"[1:a]aresample=48000,aformat=channel_layouts=stereo,dynaudnorm=f=500:g=31:m=5,equalizer=f=2600:t=q:w=0.9:g=-6,loudnorm=I=-17:TP=-2,atrim=0:{D},afade=t=in:d=0.25,afade=t=out:st={D-1.3}:d=1.3[m0];[m0][sc]sidechaincompress=threshold=0.035:ratio=3:attack=20:release=450,volume='{dv}':eval=frame[mu]")
fc.append("[vo][mu]" + "".join(labs) + f"amix=inputs={len(labs)+2}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{D}[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(fc), "-map", "[a]", "-ar", "48000", "mix.wav"], check=True)
print("mix.wav", D, len(ev), "sfx")
