#!/usr/bin/env bash
# Bundle the kit (scripts + brand + one storyboard) into bviro-kit.tar.gz so it can be
# uploaded once with Higgsfield media_upload and pulled into the sandbox with one curl.
# Usage: bash pack.sh storyboards/<name>.json [out.tar.gz]
set -euo pipefail
cd "$(dirname "$0")/.."
sb="$1"; out="${2:-bviro-kit.tar.gz}"
words="${sb%.json}.words.json"
tmp=$(mktemp -d)
mkdir -p "$tmp/kit"
cp -r scripts brand "$tmp/kit/"
cp "$sb" "$tmp/kit/sb.json"
[ -f "$words" ] && cp "$words" "$tmp/kit/words_final.json"
tar czf "$out" -C "$tmp" kit
rm -rf "$tmp"
echo "$out ($(du -h "$out" | cut -f1))"
