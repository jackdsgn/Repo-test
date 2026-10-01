#!/usr/bin/env bash
# frames/master.mkv + audio/mix.wav → out/*.mp4 (H.264/AAC) and out/*.webm (VP9/Opus), 1080×1920 @ 60 fps.
# RGB → YUV uses BT.709 explicitly so lime and ink keep their values.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p out
NAME=out/fin-jack-novo-lancamento-9x16
VF="scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
TAGS=(-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv)

ffmpeg -y -v error -i frames/master.mkv -i audio/mix.wav -map 0:v -map 1:a \
  -vf "$VF" -c:v libx264 -preset slow -crf 16 -profile:v high -tune animation "${TAGS[@]}" \
  -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest "$NAME.mp4"

ffmpeg -y -v error -i frames/master.mkv -i audio/mix.wav -map 0:v -map 1:a \
  -vf "$VF" -c:v libvpx-vp9 -crf 26 -b:v 0 -row-mt 1 -deadline good -cpu-used 2 "${TAGS[@]}" \
  -c:a libopus -b:a 160k -shortest "$NAME.webm"

ls -la out/
