# Copyright (c) 2026, Jayanng
#
# SPDX-License-Identifier: Apache-2.0

"""Live verification of livekit-gmicloud against the live GMI Cloud API.

Loads the GMI Cloud API key from /home/ubuntu/.hermes/.env (GMI_API_KEY= or
GMI_CLOUD_API_KEY=), synthesizes speech with at least two models through the
LiveKit ChunkedStream interface, writes real WAV output, prints measured
numbers (bytes, sample rate, channels, duration), and verifies that a
Chatterbox request without a voice_uuid is rejected with a clear error.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import aiohttp

ENV_PATH = Path("/home/ubuntu/.hermes/.env")
OUT_DIR = Path(__file__).resolve().parent / "out"
TEXT = "Hello from LiveKit Agents! This is a live test of the GMI Cloud text to speech plugin."
MODELS = ["inworld-tts-2", "minimax-tts-speech-2.8-turbo"]


def load_key() -> str:
    key = os.environ.get("GMI_CLOUD_API_KEY") or os.environ.get("GMI_API_KEY")
    if key:
        return key.strip()
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line.startswith("GMI_API_KEY=") or line.startswith("GMI_CLOUD_API_KEY="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                return value
    raise SystemExit(f"no GMI Cloud API key found in {ENV_PATH} or environment")


async def run_model(session: aiohttp.ClientSession, api_key: str, model: str) -> dict:
    from livekit.agents import APIConnectOptions
    from livekit_gmicloud import TTS

    tts = TTS(model=model, api_key=api_key, http_session=session)
    stream = tts.synthesize(TEXT, conn_options=APIConnectOptions(timeout=60, max_retry=1))
    frame = await stream.collect()

    wav_bytes = frame.to_wav_bytes()
    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / f"{model}.wav"
    out_path.write_bytes(wav_bytes)

    duration_s = frame.samples_per_channel / frame.sample_rate
    result = {
        "model": model,
        "status": "ok",
        "bytes": len(wav_bytes),
        "sample_rate": frame.sample_rate,
        "channels": frame.num_channels,
        "duration_s": round(duration_s, 3),
    }
    print(
        f"[live] {model}: bytes={result['bytes']} sample_rate={result['sample_rate']} "
        f"channels={result['channels']} duration_s={result['duration_s']} -> {out_path}"
    )
    return result


async def check_chatterbox_rejection(session: aiohttp.ClientSession, api_key: str) -> bool:
    from livekit.agents import APIConnectOptions
    from livekit_gmicloud import TTS

    tts = TTS(model="Chatterbox-tts", api_key=api_key, http_session=session)
    stream = tts.synthesize("test", conn_options=APIConnectOptions(timeout=30, max_retry=0))
    try:
        await stream.collect()
    except ValueError as e:
        print(f"[live] Chatterbox without voice_uuid rejected with ValueError: {e}")
        return True
    except Exception as e:
        print(f"[live] FAIL: Chatterbox raised unexpected {type(e).__name__}: {e}")
        return False
    print("[live] FAIL: Chatterbox without voice_uuid was NOT rejected")
    return False


async def main() -> int:
    api_key = load_key()
    results: list[dict] = []

    async with aiohttp.ClientSession() as session:
        for model in MODELS:
            try:
                results.append(await run_model(session, api_key, model))
            except Exception as e:
                print(f"[live] FAIL: {model}: {type(e).__name__}: {e}")
                results.append({"model": model, "status": f"error: {e}"})

        chatterbox_ok = await check_chatterbox_rejection(session, api_key)

    print("RESULTS_JSON=" + json.dumps({"live_results": results, "chatterbox_rejected": chatterbox_ok}))

    ok = all(r.get("status") == "ok" for r in results) and chatterbox_ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
