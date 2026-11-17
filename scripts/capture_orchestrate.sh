#!/usr/bin/env bash
# Records the livekit-gmicloud demo terminal via Xvfb + xterm + ffmpeg x11grab.
set -u
export DISPLAY=:99
OUT=/tmp/terminal_raw.mp4

ffmpeg -y -video_size 1920x1080 -framerate 30 -f x11grab -i :99.0+0,0 \
  -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -threads 2 "$OUT" &
REC=$!
sleep 1.2

xterm -bg '#0d1117' -fg '#c9d1d9' -fa 'DejaVu Sans Mono' -fs 26 \
      -cr '#58a6ff' -b 10 -geometry 120x34+0+0 \
      -e 'bash /home/ubuntu/livekit-gmicloud/scripts/capture_runner.sh'

sleep 1.5
kill -INT $REC
wait $REC 2>/dev/null
echo "RECORDING_DONE"
