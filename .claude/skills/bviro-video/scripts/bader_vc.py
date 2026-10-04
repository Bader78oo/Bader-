#!/usr/bin/env python3
"""Bader's voice with a Gulf accent: convert Gulf-accented TTS (Higgsfield text2speech_v2 / elevenlabs,
preset Arthur) into Bader's timbre with Chatterbox VC (MIT, local, free). Keeps the source accent and
pronunciation, swaps only the voice colour.

Usage: /opt/cbx/bin/python bader_vc.py src1.wav out1.wav [src2.wav out2.wav ...] [--ref brand/voice/bader_ref12.wav]
"""
import os, sys
import torch, torchaudio as ta
from chatterbox.vc import ChatterboxVC

args = sys.argv[1:]
ref = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "brand", "voice", "bader_ref12.wav")
if "--ref" in args:
    i = args.index("--ref"); ref = args[i + 1]; del args[i:i + 2]
torch.set_num_threads(os.cpu_count() or 4)
vc = ChatterboxVC.from_pretrained(device="cpu")
for src, out in zip(args[0::2], args[1::2]):
    ta.save(out, vc.generate(src, target_voice_path=ref), vc.sr); print("saved", out, flush=True)
