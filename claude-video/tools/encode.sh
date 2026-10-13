#!/usr/bin/env bash
# frames/master.mkv → out/<nome>.mp4 (H.264, BT.709, 1080×1920 @ 30 fps).
# Sem locução gravada: a prévia leva uma faixa AAC silenciosa (compatibilidade com players e redes).
#   tools/encode.sh <nome>
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p out
NAME="out/${1:?nome do arquivo}"
ffmpeg -y -v error -i frames/master.mkv -f lavfi -i anullsrc=r=48000:cl=stereo -map 0:v -map 1:a \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" \
  -c:v libx264 -preset slow -crf 16 -profile:v high -tune animation \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a aac -b:a 128k -movflags +faststart -shortest "$NAME.mp4"
ls -la "$NAME.mp4"
