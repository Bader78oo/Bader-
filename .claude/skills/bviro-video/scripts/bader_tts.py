#!/usr/bin/env python3
"""Bader's cloned voice (Chatterbox Multilingual, MIT, CPU, free): one wav per line.

Usage: /opt/cbx/bin/python bader_tts.py out_prefix "سطر أول…" "سطر ثاني!" [--ref brand/voice/bader_ref12.wav]
Setup (once per container): python3 -m venv /opt/cbx && /opt/cbx/bin/pip install --no-cache-dir torch==2.6.0 torchaudio==2.6.0 chatterbox-tts
  (download.pytorch.org is blocked here, so torch comes from PyPI; keep it in the venv — chatterbox pins numpy<2 / transformers).
~25-45 s per line on 4 CPUs. Write lines in friendly Gulf dialect, no tanween.
"""
import os, sys
import torch, torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

args = sys.argv[1:]
ref = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "brand", "voice", "bader_ref12.wav")
if "--ref" in args:
    i = args.index("--ref"); ref = args[i + 1]; del args[i:i + 2]
prefix, lines = args[0], args[1:]
torch.set_num_threads(os.cpu_count() or 4)
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
for i, t in enumerate(lines):
    w = m.generate(t, language_id="ar", audio_prompt_path=ref, exaggeration=0.55, cfg_weight=0.4, temperature=0.7)
    ta.save(f"{prefix}{i}.wav", w, m.sr); print("saved", f"{prefix}{i}.wav", flush=True)
