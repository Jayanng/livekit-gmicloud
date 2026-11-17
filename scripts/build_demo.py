#!/usr/bin/env python3
"""livekit-gmicloud demo build: 4 segments (tests, synth start, synth results,
cancel), reframe identical to the proven pipecat pipeline, captions + VO + bed."""
import os, subprocess, sys

FF = "/home/ubuntu/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin/ffmpeg"
FP = "/home/ubuntu/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin/ffprobe"
RAW = "/tmp/terminal_raw.mp4"
OUT = "/tmp/build2"
os.makedirs(OUT, exist_ok=True)

# beat map: 33 passed @~7-10.2, synth cmd @12-20.5 (inworld @20), minimax+OK @33-37.5,
# cancel steps+OK @42-48. cuts stop BEFORE each terminal clear (no tpad needed)
SEGS = [("seg1", 0.5, 9.8), ("seg2", 15.2, 22.5), ("seg3", 30.8, 34.2), ("seg4", 36.8, 45.5)]

CROP = "crop=1320:455:0:45"
SCALE = "scale=1795:619:flags=lanczos"
PAD = "pad=1920:1080:62:230:color=0x0d1117"
ZOOM = "zoompan=z='min(1.0+0.0012*on,1.040)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1200:])
        sys.exit(1)
    return r


def dur(path):
    return float(run([FP, "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=noprint_wrappers=1:nokey=1", path]).stdout.strip())


# 1) segments
for name, ss, end in SEGS:
    out = f"{OUT}/{name}.mp4"
    chain = f"[0:v]trim=start={ss}:end={end},setpts=PTS-STARTPTS,{CROP},{SCALE},{PAD},{ZOOM},format=yuv420p[v]"
    cmd = ["systemd-run", "--user", "--scope", "-p", "MemoryMax=1400M", "-p", "MemorySwapMax=0",
           FF, "-y", "-i", RAW, "-filter_complex", chain, "-map", "[v]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-threads", "2", "-an", out]
    run(cmd)
    print(f"{name}: {dur(out):.2f}s", flush=True)

# 2) concat + vignette + fades -> base
lst = f"{OUT}/list.txt"
with open(lst, "w") as f:
    for name, _, _ in SEGS:
        f.write(f"file '{OUT}/{name}.mp4'\n")
base = f"{OUT}/base.mp4"
run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-vf",
     "vignette=PI/5,fade=t=in:st=0:d=0.5,fade=t=out:st=28.5:d=1.2",
     "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-threads", "2", "-an", base])
print(f"base: {dur(base):.2f}s", flush=True)

# 3) captions (absolute timeline offsets)
caps = [
    (0.8, 3.2, "livekit-gmicloud  ·  a GMI Cloud TTS plugin for LiveKit Agents"),
    (6.8, 9.4, "33 unit tests  ·  all passing"),
    (16.9, 19.5, "Live synthesis  ·  normalized to 48 kHz mono"),
    (20.6, 23.2, "Clean cancellation mid-synthesis"),
]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
filters = []
for s, e, text in caps:
    filters.append(
        f"drawtext=fontfile={FONT}:text='{text}':fontsize=38:fontcolor=#c9d1d9:"
        f"box=1:boxcolor=0x0d1117@0.62:boxborderw=12:x=(w-text_w)/2:y=920:"
        f"enable='between(t,{s},{e})'"
    )
titled = f"{OUT}/titled.mp4"
run([FF, "-y", "-i", base, "-vf", ",".join(filters), "-c:v", "libx264",
     "-preset", "veryfast", "-crf", "20", "-threads", "2", "-an", titled])
print(f"titled: {dur(titled):.2f}s", flush=True)

# 4) audio: VO (atempo 1.038, delayed) + music bed + loudnorm
total = dur(titled)
amix = (
    "[1:a]atempo=1.038,adelay=300|300[a1];"
    "[2:a]atempo=1.038,adelay=5200|5200[a2];"
    "[3:a]atempo=1.038,adelay=10600|10600[a3];"
    "[4:a]atempo=1.038,adelay=23400|23400[a4];"
    f"[0:a]atrim=0:{total},volume=0.13[bed];"
    "[bed][a1][a2][a3][a4]amix=inputs=5:normalize=0,"
    "loudnorm=I=-16:TP=-1.5:LRA=11[out]"
)
final = "/home/ubuntu/livekit-gmicloud-demo.mp4"
run([FF, "-y", "-i", "/tmp/audio/music.wav",
     "-i", "/tmp/vo2/intro.wav", "-i", "/tmp/vo2/beat1.wav",
     "-i", "/tmp/vo2/beat2.wav", "-i", "/tmp/vo2/beat3.wav",
     "-i", titled,
     "-filter_complex", amix, "-map", "5:v", "-map", "[out]",
     "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final])
print(f"FINAL: {final} {dur(final):.2f}s {os.path.getsize(final)} bytes")
