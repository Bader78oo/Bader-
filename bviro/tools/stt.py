"""usage: stt.py file1 [file2 ...] -> Arabic transcription with word timestamps (faster-whisper small, CPU)"""
import subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
for f in sys.argv[1:]:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32)
    segs, info = m.transcribe(audio, language="ar", word_timestamps=True, vad_filter=False)
    print("==", f, round(len(audio) / 16000, 2), "s")
    for s in segs:
        print(f"  [{s.start:5.2f}-{s.end:5.2f}] {s.text}")
        print("     ", " ".join(f"{w.word.strip()}@{w.start:.2f}" for w in s.words))
