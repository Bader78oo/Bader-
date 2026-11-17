# bviro

Editing scripts and notes for the @bviro.1 Instagram work (reels, voice replacement, captions).

- `tools/` reel 1 (camel) builders, speech checks (`stt.py`, `stt_large.py`, `closure.py`), `webtext.py` page reader.
- `reel2/tools/` reel 2 («الجو نزل درجتين»): `overlays_r2.py`, `timeline_r2.py`, `build_r2.py`, `mix_r2.py`, `mux_r2.sh`.
- `screens/tools/` voice replacement for the screens video (`bed.py`, `fit_voice.py`, `mix_screens.py`, `prosody.py`).
- `fonts/`, `logo/` brand assets used by the overlay scripts.
- `skill/bviro-instagram/SKILL.md` the updated house skill (upload it to replace the account's copy).

The scripts were written against a session scratchpad: the `S = "/tmp/.../scratchpad/bviro"` path at the top of each
one must be pointed at this folder, and the source clips, keyframes and audio are NOT in the repo (they are large and
were generated per job). Videos themselves are not stored here.
