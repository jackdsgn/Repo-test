#!/usr/bin/env bash
# frames/master.mkv [+ áudio] → out/<nome>.mp4 (H.264, BT.709, 1080×1920 @ 30 fps; AAC 48 kHz).
# Sem arquivo de áudio, leva uma faixa AAC silenciosa (compatibilidade com players e redes).
#   tools/encode.sh <nome> [audio.wav]
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p out
NAME="out/${1:?nome do arquivo}"
if [ -n "${2:-}" ]; then AUDIO=(-i "$2"); else AUDIO=(-f lavfi -i anullsrc=r=48000:cl=stereo); fi
ffmpeg -y -v error -i frames/master.mkv "${AUDIO[@]}" -map 0:v -map 1:a \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" \
  -c:v libx264 -preset slow -crf 16 -profile:v high -tune animation \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart -shortest "$NAME.mp4"
ls -la "$NAME.mp4"
