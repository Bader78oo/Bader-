#!/usr/bin/env python3
"""Tighten a voice-over: shorten pauses, optionally speed up, normalize loudness,
remap word timings, and cut the clips that talking-head shots will lip-sync to.

Usage:
  python3 tighten_vo.py voice.mp3 words.json [--tempo 1.05] [--gap 0.08] [--lead 0.25]
                        [--talk A:15-21 --talk B:33-37]

--talk NAME:FIRST-LAST   word-index range spoken on camera; writes talk_NAME.mp3 and
                         prints its start time in the final timeline (use that as the
                         shot's position so the lip-sync lines up).
Outputs: vo.mp3, words_final.json, talk_*.mp3
"""
import argparse, json, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("audio"); ap.add_argument("words")
ap.add_argument("--tempo", type=float, default=1.05)
ap.add_argument("--gap", type=float, default=0.08, help="silence kept on each side of speech")
ap.add_argument("--lead", type=float, default=0.25, help="silence before the first word")
ap.add_argument("--noise", default="-35dB"); ap.add_argument("--min-silence", type=float, default=0.3)
ap.add_argument("--talk", action="append", default=[])
a = ap.parse_args()

dur = float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.audio]).decode())
log = subprocess.run(["ffmpeg", "-i", a.audio, "-af", f"silencedetect=noise={a.noise}:d={a.min_silence}",
                      "-f", "null", "-"], capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]

# speech intervals = complement of silences
speech, cur = [], 0.0
for s, e in zip(starts, ends + [dur] * (len(starts) - len(ends))):
    if s > cur: speech.append((cur, s))
    cur = e
if cur < dur: speech.append((cur, dur))
keep = [(max(0, s - a.gap), min(dur, e + a.gap)) for s, e in speech if e - s > 0.05]

offs, pos = [], a.lead
for s, e in keep:
    offs.append((s, e, pos)); pos += e - s
total = pos / a.tempo

def remap(t):
    for s, e, o in offs:
        if t <= e: return (o + max(0.0, t - s)) / a.tempo
    s, e, o = offs[-1]; return (o + e - s) / a.tempo

parts = "".join(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS[s{i}];" for i, (s, e) in enumerate(keep))
fc = (f"anullsrc=r=44100:cl=mono,atrim=0:{a.lead}[ld];" + parts + "[ld]" +
      "".join(f"[s{i}]" for i in range(len(keep))) +
      f"concat=n={len(keep) + 1}:v=0:a=1,atempo={a.tempo},loudnorm=I=-14:TP=-1.5:LRA=9[o]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.audio, "-filter_complex", fc, "-map", "[o]",
                "-ar", "44100", "-ac", "1", "-b:a", "192k", "vo.mp3"], check=True)

words = json.load(open(a.words, encoding="utf-8"))
final = [[round(remap(s), 2), round(remap(e), 2), w] for s, e, w in words]
json.dump(final, open("words_final.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"vo.mp3: {total:.2f}s (was {dur:.2f}s)")

for spec in a.talk:
    name, rng = spec.split(":"); i, j = map(int, rng.split("-"))
    s, e = max(0.0, final[i][0] - 0.12), final[j][1] + 0.12
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "vo.mp3", "-ss", f"{s:.2f}", "-to", f"{e:.2f}",
                    "-b:a", "192k", f"talk_{name}.mp3"], check=True)
    print(f"talk_{name}.mp3: starts at {s:.2f}s, {e - s:.2f}s long  ({' '.join(w[2] for w in final[i:j + 1])})")
for k, w in enumerate(final):
    print(k, w)
