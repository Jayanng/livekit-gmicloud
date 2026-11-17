# livekit-gmicloud

A community [LiveKit Agents](https://github.com/livekit/agents) text-to-speech
plugin for [GMI Cloud](https://www.gmicloud.ai)'s multimodal inference engine.

GMI Cloud serves several TTS model families behind one request-queue HTTP API;
this plugin maps each family's request shape and resolves both synchronous and
queued/dispatched responses to WAV audio:

- **Inworld Realtime TTS** (`inworld-tts-2`, ...)
- **MiniMax speech synthesis** (`minimax-tts-speech-*`)
- **Resemble AI's Chatterbox** (`Chatterbox-tts`, requires a Resemble
  `voice_uuid`)

## Installation

```bash
uv add livekit-gmicloud
```

## Prerequisites

- Python 3.10+
- A GMI Cloud API key from <https://console.gmicloud.ai/>

## Configuration

```python
from livekit_gmicloud import TTS

tts = TTS(
    model="inworld-tts-2",       # GMI Cloud model id
    voice=None,                  # family default voice, or a voice id /
                                 # Resemble voice_uuid (Chatterbox)
    speed=1.0,                   # speaking rate / speed multiplier
    temperature=None,            # Inworld family only
    timestamp_type=None,         # Inworld family only (e.g. "WORD")
    extra_payload=None,          # provider-specific fields, passed through
    audio_format="WAV",          # output container requested from GMI Cloud
    sample_rate=48000,           # nominal; emitted audio uses the rate of the
                                 # WAV returned by the model (read at runtime)
    api_key=None,                # or GMI_CLOUD_API_KEY / GMI_API_KEY env var
    base_url="https://console.gmicloud.ai",
    poll_interval_secs=2.0,      # polling interval for queued responses
    poll_attempts=90,            # max polls before giving up (90 x 2s = 3 min)
    http_session=None,           # optional shared aiohttp session; required
                                 # outside an agent worker (see Usage)
)
```

## Usage

In an `AgentSession`:

```python
from livekit.agents import AgentSession
from livekit_gmicloud import TTS

session = AgentSession(
    tts=TTS(model="inworld-tts-2", voice="Dennis"),
    # ... llm, stt, turn_detection ...
)
```

Standalone (outside an agent worker, pass your own `aiohttp` session):

```python
import asyncio

import aiohttp
from livekit.agents import APIConnectOptions
from livekit_gmicloud import TTS


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        tts = TTS(
            model="inworld-tts-2",
            voice="Dennis",
            http_session=session,
        )
        stream = tts.synthesize(
            "Hello from GMI Cloud!", conn_options=APIConnectOptions(timeout=60)
        )
        audio = await stream.collect()          # rtc.AudioFrame
        with open("out.wav", "wb") as f:
            f.write(audio.to_wav_bytes())


asyncio.run(main())
```

## Models

Any GMI Cloud audio model id can be passed via `model`; the plugin picks the
request shape from the id prefix. `extra_payload` passes provider-specific
fields through unchanged. Ids that match none of the three prefixes fall back
to the Inworld request shape.

| Model id | Family | Notes |
| --- | --- | --- |
| `inworld-tts-2` | Inworld | `voice_id`, `audio_encoding`, `speaking_rate`, `temperature`, `timestamp_type` |
| `minimax-tts-speech-2.8-turbo` | MiniMax | `voice_id`, `speed`, `format`, plus `extra_payload`; may return queued/dispatched (polled) |
| `Chatterbox-tts` | Chatterbox | requires a Resemble `voice_uuid` as `voice` |

## Measured results

Measured 2026-11-17 against the live GMI Cloud API through
`scripts/verify_live.py`, with the input text
"Hello from LiveKit Agents! This is a live test of the GMI Cloud text to
speech plugin." Bytes is the size of the output WAV written by the script
(PCM audio plus WAV header); duration is computed from the emitted audio
frames. GMI Cloud synthesis is non-deterministic, so the same text produces
slightly different audio on each call (independently reproduced runs of
`inworld-tts-2` ranged 493,484-518,444 bytes); the counts below are one
measured sample, not fixed values.

| Model | Family | Output WAV bytes | Sample rate | Channels | Duration |
| --- | --- | --- | --- | --- | --- |
| `inworld-tts-2` | Inworld | 493,484 | 48000 Hz | 1 (mono) | 5.14 s |
| `minimax-tts-speech-2.8-turbo` | MiniMax | 742,684 | 32000 Hz | 2 (stereo) | 5.80 s |

Observed while measuring:

- `minimax-tts-speech-2.8-turbo` returns `dispatched`/`processing` and is
  resolved through the queued-request polling path. This path is
  intermittent on GMI Cloud: in our live calls most MiniMax requests returned
  audio (typically within a minute), while an occasional request stays
  `processing` past the 3-minute default poll budget, in which case
  `synthesize()` raises a clear error. Queued MiniMax generation is slow on GMI Cloud, so raise
  `poll_attempts` / `poll_interval_secs` for slow generations, or prefer the
  Inworld family for latency-sensitive voice agents.
- `Chatterbox-tts` without a `voice_uuid` is rejected with a clear
  `ValueError` before any audio is requested (verified live).
- GMI Cloud returns WAV at the model's native rate/channels (Inworld 48 kHz
  mono; MiniMax 32 kHz stereo in every successful MiniMax run); the
  plugin reads the real sample rate and channel count from each WAV header
  and emits audio frames at that format.

## Compatibility

- `livekit-agents[codecs]` 1.8.12 or newer (tested with 1.8.12)
- Python 3.10+ (tested with 3.14.7)
- The HTTP transport is ported from the proven `pipecat-gmicloud` plugin
  (same GMI Cloud request-queue endpoint and response resolution).
- Synthesis is chunked (non-streaming): each `synthesize()` call returns one
  completed WAV. Streaming (`TTS.stream()`) is not implemented.
- Empty input text completes as a clean zero-audio segment (a no-op in an
  `AgentSession`).

## Attribution

Community-maintained by Jayanng (GMI Cloud Ambassador); not an official GMI
Cloud or LiveKit project.

## License

Apache-2.0
