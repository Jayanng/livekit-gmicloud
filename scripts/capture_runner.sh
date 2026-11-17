#!/bin/bash
# Real demo beats with streaming output and tight pacing, for screen capture.
cd /home/ubuntu/livekit-gmicloud
export GMI_CLOUD_API_KEY=$(grep -oP 'GMI_API_KEY=\K[^\s"]+' /home/ubuntu/.hermes/.env)

GREEN='\033[1;32m'; DIM='\033[2m'; NC='\033[0m'

clear
echo ""
echo -e "  ${DIM}livekit-gmicloud  ·  GMI Cloud TTS for LiveKit${NC}"
echo ""
sleep 1.2
echo -e "  ${GREEN}\$${NC} python -m pytest tests/ -q"
sleep 1.0
stdbuf -oL -eL .venv/bin/python -m pytest tests/ -q -W "ignore::DeprecationWarning" -p no:cacheprovider 2>&1 | stdbuf -oL grep -vE "INFO|DEBUG|__init__|linking|registry|worker|pipeline|frame_processor|tts_service"
sleep 2.2

clear
echo ""
echo -e "  ${DIM}live synthesis through the GMI Cloud API${NC}"
echo ""
sleep 1.2
echo -e "  ${GREEN}\$${NC} python scripts/demo_synth.py"
sleep 1.0
stdbuf -oL -eL .venv/bin/python scripts/demo_synth.py 2>&1 | stdbuf -oL grep -vE "INFO|DEBUG|retrying|failed to synthesize"
sleep 2.4

clear
echo ""
echo -e "  ${DIM}cancellation handling${NC}"
echo ""
sleep 1.2
echo -e "  ${GREEN}\$${NC} python scripts/demo_cancel.py"
sleep 1.0
stdbuf -oL -eL .venv/bin/python scripts/demo_cancel.py 2>&1 | stdbuf -oL grep -vE "INFO|DEBUG|retrying|failed to synthesize"
sleep 3.0
