#!/usr/bin/env python3
"""Cancellation demo: interrupt mid-synthesis, then synthesize again cleanly."""
import asyncio
import os

import aiohttp

from livekit_gmicloud import TTS


async def main():
    async with aiohttp.ClientSession() as session:
        tts = TTS(
            model="inworld-tts-2",
            api_key=os.environ["GMI_CLOUD_API_KEY"],
            http_session=session,
        )
        print("1) bot starts speaking a long turn (live GMI)...", flush=True)

        async def consume():
            return await tts.synthesize(
                "This is a long turn of speech that will be interrupted in the middle of synthesis."
            ).collect()

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.35)
        print("2) user interrupts -> cancelling the TTS task", flush=True)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("   -> CancelledError handled cleanly", flush=True)

        print("3) next turn right after the interruption:", flush=True)
        frame = await tts.synthesize("Back to normal on the next turn.").collect()
        print(f"   -> synthesized {frame.samples_per_channel} samples on the next turn", flush=True)
        print("OK: cancellation handled cleanly, healthy after.", flush=True)


asyncio.run(main())
