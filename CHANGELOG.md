# Changelog

## 0.1.0 (2026-11-17)

Initial release.

- `livekit_gmicloud.TTS`: community LiveKit Agents TTS plugin for GMI Cloud.
- One adapter for three GMI Cloud model families: Inworld Realtime TTS
  (`inworld-tts-*`), MiniMax speech synthesis (`minimax-tts-speech-*`), and
  Resemble AI's Chatterbox (`Chatterbox-tts`).
- Handles both documented GMI Cloud response shapes: synchronous inline
  `outcome` responses and queued/dispatched responses resolved by polling
  `GET /api/v1/ie/requestqueue/apikey/requests/{request_id}`.
- Chunked (non-streaming) synthesis via `tts.ChunkedStream` / `AudioEmitter`.
