# Copyright (c) 2026, Jayanng
#
# SPDX-License-Identifier: Apache-2.0

"""Community LiveKit Agents TTS plugin for GMI Cloud.

Synthesizes speech through GMI Cloud's multimodal inference engine
(https://www.gmicloud.ai) via its request-queue HTTP API. Three model
families are supported behind one adapter:

- Inworld Realtime TTS (``inworld-tts-2``, ...)
- MiniMax speech synthesis (``minimax-tts-speech-*``)
- Resemble AI's Chatterbox (``Chatterbox-tts``; requires a Resemble
  ``voice_uuid`` passed as ``voice``)
"""

from .tts import TTS, ChunkedStream, model_family
from .version import __version__

__all__ = ["TTS", "ChunkedStream", "model_family", "__version__"]
