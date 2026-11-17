#!/usr/bin/env bash
# usage: fetch.sh OUTDIR name=url ...  -> downloads; makes <name>_s.jpg (images) or <name>_strip.jpg (videos)
set -u
OUT=$1; shift; mkdir -p "$OUT"; cd "$OUT"
for pair in "$@"; do
  name=${pair%%=*}; url=${pair#*=}; ext=${url##*.}
  curl -sS -o "$name.$ext" "$url"
  if [ "$ext" = "mp4" ]; then
    ffmpeg -v error -y -i "$name.mp4" -vf "fps=2,scale=216:-1,tile=10x1" -frames:v 1 "${name}_strip.jpg"
  else
    ffmpeg -v error -y -i "$name.$ext" -vf scale=540:-1 -q:v 3 "${name}_s.jpg"
  fi
done
