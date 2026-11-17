# Changelog

## 0.1.2 (2026-11-17)

- Normalize every response to the declared output format (mono at the
  declared `sample_rate`, 48 kHz by default): multi-channel audio is
  down-mixed and resampled before being emitted, so emitted frames always
  match `TTS.sample_rate` / `TTS.num_channels` (MiniMax previously emitted
  32 kHz stereo frames against a 48 kHz mono declaration).
- `audio_format` other than `WAV` is now rejected with a clear `ValueError`.
- Queue polling raises `APIStatusError` immediately on permanent HTTP errors
  (e.g. 401/404) instead of polling to the budget; only 408/429/5xx retry,
  and each poll GET is bounded by `conn_options.timeout`.

## 0.1.1 (2026-11-17)

- Empty input text now completes as a clean zero-audio segment (a no-op in
  AgentSession event consumption) instead of raising an internal
  `AudioEmitter` RuntimeError.

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
