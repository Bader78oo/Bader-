#!/usr/bin/env python3
"""Word-level transcript of a voice recording -> words.json ([[start, end, word], ...]).

Usage: python3 transcribe.py voice.mp3 [script.txt] [--model medium]

Passing the written script as script.txt biases Whisper toward the right spelling
(brand names like بيفيرو). Whisper sometimes repeats earlier words after the audio
ends; those zero-length / out-of-range words are dropped.
"""
import json, re, subprocess, sys

from faster_whisper import WhisperModel

args = [a for a in sys.argv[1:] if not a.startswith("--")]
model_name = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "medium"
if "--model" in sys.argv:
    args.remove(model_name)
audio = args[0]
prompt = open(args[1], encoding="utf-8").read().strip() if len(args) > 1 else None

dur = float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio]).decode())

# Where the trailing silence starts: Whisper likes to "repeat" earlier words into it.
log = subprocess.run(["ffmpeg", "-i", audio, "-af", "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
speech_end = starts[-1] if starts and (len(ends) < len(starts) or ends[-1] >= dur - 0.1) else dur

model = WhisperModel(model_name, device="cpu", compute_type="int8")
segments, _ = model.transcribe(audio, language="ar", word_timestamps=True, initial_prompt=prompt)

words = []
for seg in segments:
    for w in seg.words:
        s, e, t = round(float(w.start), 2), round(float(w.end), 2), w.word.strip().strip("،.!؟?")
        if not t or e - s < 0.05 or s >= speech_end - 0.05:
            continue  # hallucinated tail / empty token
        words.append([s, e, t])

json.dump(words, open("words.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"{len(words)} words, audio {dur:.2f}s")
for i, w in enumerate(words):
    print(i, w)
