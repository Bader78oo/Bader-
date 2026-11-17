#!/usr/bin/env bash
# usage: mux_r2.sh SILENT.mp4 MIX.wav OUT.mp4  -> static gain to -14 LUFS (no dynamic pumping), true-peak limit, H.264 crf 18 + AAC 256k
set -euo pipefail
V=$1; A=$2; O=$3
I=$(ffmpeg -hide_banner -nostats -i "$A" -af ebur128=peak=true -f null - 2>&1 | awk '/Integrated loudness:/{f=1} f&&/I:/{print $2; exit}')
G=$(python3 -I -c "print(round(-14.0 - float('$I'), 2))")
ffmpeg -v error -y -i "$V" -i "$A" -af "volume=${G}dB,alimiter=limit=0.84:attack=2:release=40:level=false" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest "$O"
echo "measured I=$I LUFS gain=${G} dB -> $O"
ffmpeg -hide_banner -nostats -i "$O" -af ebur128=peak=true -f null - 2>&1 | awk '/Integrated loudness:/{f=1} f&&/I:/{print "final I:", $2} f&&/Peak:/{getline; print "final", $0}' | head -2
ffprobe -v error -show_entries format=duration,size -of csv=p=0 "$O"
