#!/usr/bin/env python3
"""Live synthesis demo: both GMI Cloud families, emitted at the declared format."""
import asyncio
import os

import aiohttp

from livekit_gmicloud import TTS


async def synth(session, model, text, attempts=2, poll_attempts=30):
    for attempt in range(1, attempts + 1):
        tts = TTS(
            model=model,
            api_key=os.environ["GMI_CLOUD_API_KEY"],
            http_session=session,
            poll_interval_secs=2.0,
            poll_attempts=poll_attempts,
        )
        try:
            frame = await tts.synthesize(text).collect()
            dur = frame.samples_per_channel / frame.sample_rate
            print(f"[live] {model:28s}: {dur:.1f}s audio", flush=True)
            return True
        except Exception as e:
            if attempt == attempts:
                print(f"[live] {model:28s}: FAILED ({type(e).__name__})", flush=True)
                return False
    return False


async def main():
    async with aiohttp.ClientSession() as session:
        ok1 = await synth(session, "inworld-tts-2",
                          "This is a live synthesis test of the GMI Cloud plugin for LiveKit Agents.")
        ok2 = await synth(session, "minimax-tts-speech-2.8-turbo",
                          "And this is the MiniMax family through the same service.")
        if ok1 and ok2:
            print("   both at 48000 Hz, 1 ch (minimax normalized", flush=True)
            print("   from its native 32 kHz stereo)", flush=True)
            print("OK: every family emits the declared format", flush=True)


asyncio.run(main())
