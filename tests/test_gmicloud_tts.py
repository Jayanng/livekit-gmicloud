# Copyright (c) 2026, Jayanng
#
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for livekit_gmicloud: model-family mapping and payload builders."""

import pytest

from livekit_gmicloud.tts import _TTSOptions, build_payload, model_family


def _opts(**kwargs) -> _TTSOptions:
    defaults = dict(
        api_key="test-key",
        base_url="https://console.gmicloud.ai",
        model="inworld-tts-2",
        voice=None,
        audio_format="WAV",
        speed=1.0,
        temperature=None,
        timestamp_type=None,
    )
    defaults.update(kwargs)
    return _TTSOptions(**defaults)


# --- model_family -----------------------------------------------------------


def test_model_family_inworld():
    assert model_family("inworld-tts-2") == "inworld"
    assert model_family("inworld-tts-2-flash") == "inworld"
    assert model_family("inworld-tts-1.5-mini") == "inworld"


def test_model_family_minimax():
    assert model_family("minimax-tts-speech-2.8-turbo") == "minimax"
    assert model_family("minimax-tts-speech-02-hd") == "minimax"
    assert model_family("MINIMAX-anything") == "minimax"


def test_model_family_chatterbox():
    assert model_family("Chatterbox-tts") == "chatterbox"
    assert model_family("chatterbox-tts") == "chatterbox"


def test_model_family_unknown_defaults_to_inworld():
    assert model_family("some-unknown-model") == "inworld"
    assert model_family("") == "inworld"


# --- payload builder: inworld ----------------------------------------------


def test_inworld_payload_defaults():
    payload = build_payload("hello world", _opts())
    assert payload == {
        "text": "hello world",
        "audio_encoding": "WAV",
        "speaking_rate": 1.0,
        "voice_id": "Dennis",  # family default applied when voice is None
    }


def test_inworld_payload_with_voice_and_options():
    payload = build_payload(
        "hi",
        _opts(
            voice="Ava",
            speed=1.25,
            temperature=0.7,
            timestamp_type="WORD",
        ),
    )
    assert payload["voice_id"] == "Ava"
    assert payload["speaking_rate"] == 1.25
    assert payload["temperature"] == 0.7
    assert payload["timestamp_type"] == "WORD"
    assert payload["audio_encoding"] == "WAV"


def test_inworld_payload_omits_unset_fields():
    payload = build_payload("hi", _opts(voice="Ava"))
    assert "temperature" not in payload
    assert "timestamp_type" not in payload


# --- payload builder: minimax ----------------------------------------------


def test_minimax_payload():
    payload = build_payload(
        "hi", _opts(model="minimax-tts-speech-2.8-turbo", voice="English_WiseScholar", speed=1.5)
    )
    assert payload == {
        "text": "hi",
        "speed": "1.5",  # minimax wants speed as a string
        "format": "wav",
        "voice_id": "English_WiseScholar",
    }


def test_minimax_payload_default_voice():
    payload = build_payload("hi", _opts(model="minimax-tts-speech-2.8-turbo"))
    assert payload["voice_id"] == "English_expressive_narrator"


def test_minimax_payload_lowercase_encoding():
    payload = build_payload("hi", _opts(model="minimax-tts-speech-2.8-turbo", audio_format="MP3"))
    assert payload["format"] == "mp3"


# --- payload builder: chatterbox -------------------------------------------


def test_chatterbox_payload():
    payload = build_payload(
        "hi", _opts(model="Chatterbox-tts", voice="1234-5678-abcd")
    )
    assert payload == {
        "data": "hi",
        "voice_uuid": "1234-5678-abcd",
        "output_format": "wav",
    }


def test_chatterbox_requires_voice_uuid():
    with pytest.raises(ValueError, match="voice UUID"):
        build_payload("hi", _opts(model="Chatterbox-tts"))
    with pytest.raises(ValueError, match="voice_uuid"):
        build_payload("hi", _opts(model="Chatterbox-tts", voice=""))


# --- extra_payload ----------------------------------------------------------


def test_extra_payload_merged_last():
    payload = build_payload(
        "hi",
        _opts(model="minimax-tts-speech-2.8-turbo", extra_payload={"emotion": "happy"}),
    )
    assert payload["emotion"] == "happy"


def test_extra_payload_can_override():
    payload = build_payload("hi", _opts(extra_payload={"voice_id": "Override"}))
    assert payload["voice_id"] == "Override"


# --- audio URL extraction ---------------------------------------------------

def test_extract_audio_url_direct():
    from livekit_gmicloud.tts import _extract_audio_url
    assert _extract_audio_url({"outcome": {"audio_url": "https://a/x.wav"}}) == "https://a/x.wav"


def test_extract_audio_url_media_urls_list():
    from livekit_gmicloud.tts import _extract_audio_url
    data = {"outcome": {"media_urls": [{"url": "https://a/1.wav"}]}}
    assert _extract_audio_url(data) == "https://a/1.wav"


def test_extract_audio_url_medias_and_media_keys():
    from livekit_gmicloud.tts import _extract_audio_url
    assert _extract_audio_url({"outcome": {"medias": [{"url": "https://a/2.wav"}]}}) == "https://a/2.wav"
    assert _extract_audio_url({"outcome": {"media": [{"url": "https://a/3.wav"}]}}) == "https://a/3.wav"


def test_extract_audio_url_missing():
    from livekit_gmicloud.tts import _extract_audio_url
    assert _extract_audio_url({}) is None
    assert _extract_audio_url({"outcome": {}}) is None
    assert _extract_audio_url({"outcome": "not-a-dict"}) is None


# --- WAV header parsing -----------------------------------------------------

def test_parse_wav_reads_payload_and_header():
    import io, wave
    from livekit_gmicloud.tts import _parse_wav
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(32000)
        w.writeframes(b"\x00\x00" * 32000)
    pcm, rate, channels, width = _parse_wav(buf.getvalue())
    assert (rate, channels, width) == (32000, 2, 2)
    assert len(pcm) == 32000 * 2


def test_parse_wav_garbage_returns_none():
    from livekit_gmicloud.tts import _parse_wav
    assert _parse_wav(b"not a wav at all") is None


# --- response resolution: sync vs queued ------------------------------------

class _FakeResp:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    async def json(self, content_type=None):
        return self._payload

    async def text(self):
        return "err"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeSession:
    """Records GET calls and replays canned JSON responses."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        return _FakeResp(200, self._responses.pop(0))


def _stream(**opts):
    from livekit.agents import DEFAULT_API_CONNECT_OPTIONS
    from livekit_gmicloud.tts import ChunkedStream, TTS
    tts = TTS(api_key="test-key", poll_interval_secs=0.001, poll_attempts=3, **opts)
    return ChunkedStream(tts=tts, input_text="hello", conn_options=DEFAULT_API_CONNECT_OPTIONS)


@pytest.mark.asyncio
async def test_resolve_result_sync_success_no_polling():
    cs = _stream()
    session = _FakeSession([])
    data = {"status": "success", "outcome": {"audio_url": "https://a/x.wav"}}
    out, url = await cs._resolve_result(session, data)
    assert url == "https://a/x.wav"
    assert session.calls == 0  # synchronous: nothing polled


@pytest.mark.asyncio
async def test_resolve_result_queued_is_polled_to_success():
    cs = _stream()
    session = _FakeSession([
        {"status": "processing", "request_id": "r1"},
        {"status": "success", "request_id": "r1", "outcome": {"audio_url": "https://a/x.wav"}},
    ])
    data = {"status": "dispatched", "request_id": "r1"}
    out, url = await cs._resolve_result(session, data)
    assert url == "https://a/x.wav"
    assert out.get("status") == "success"
    assert session.calls == 2


@pytest.mark.asyncio
async def test_resolve_result_poll_timeout_returns_no_url():
    cs = _stream()
    session = _FakeSession([
        {"status": "processing", "request_id": "r1"},
        {"status": "processing", "request_id": "r1"},
        {"status": "processing", "request_id": "r1"},
    ])
    data = {"status": "dispatched", "request_id": "r1"}
    out, url = await cs._resolve_result(session, data)
    assert url is None
    assert session.calls == 3  # poll_attempts exhausted


@pytest.mark.asyncio
async def test_resolve_result_failed_status_never_polls():
    cs = _stream()
    session = _FakeSession([])
    data = {"status": "failed", "request_id": "r1"}
    out, url = await cs._resolve_result(session, data)
    assert url is None
    assert session.calls == 0


# --- session fallback error path --------------------------------------------

def test_missing_session_outside_job_context_raises_clear_error():
    import pytest
    from livekit.agents import APIConnectionError
    from livekit_gmicloud.tts import TTS
    tts = TTS(api_key="test-key")  # no http_session, no job context in pytest
    with pytest.raises(APIConnectionError, match="http_session"):
        tts._ensure_session()


# --- output normalization (declared-format contract) -------------------------

def test_to_mono_s16_downmixes_by_averaging():
    import struct
    from livekit_gmicloud.tts import _to_mono_s16
    stereo = struct.pack("<4h", 1000, 3000, 2000, 4000)
    assert struct.unpack("<2h", _to_mono_s16(stereo, 2)) == (2000, 3000)


def test_to_mono_s16_passthrough_mono():
    from livekit_gmicloud.tts import _to_mono_s16
    mono = b"\x01\x00" * 100
    assert _to_mono_s16(mono, 1) == mono


def test_resample_s16_32k_to_48k():
    from livekit_gmicloud.tts import _resample_s16
    pcm = b"\x01\x00" * 32000
    out = _resample_s16(pcm, 32000, 48000)
    assert 47900 <= len(out) // 2 <= 48100


def test_wrap_wav_s16_roundtrip():
    from livekit_gmicloud.tts import _parse_wav, _wrap_wav_s16
    pcm = b"\x01\x00" * 500
    parsed = _parse_wav(_wrap_wav_s16(pcm, 48000))
    assert parsed == (pcm, 48000, 1, 2)


def test_non_wav_audio_format_rejected():
    import pytest
    from livekit_gmicloud.tts import TTS
    with pytest.raises(ValueError, match="WAV"):
        TTS(model="inworld-tts-2", api_key="k", audio_format="MP3")


# --- queue polling error handling -------------------------------------------

class _PollResp:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    async def json(self, content_type=None):
        return self._payload

    async def text(self):
        return "err"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _PollSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        status, payload = self._responses.pop(0)
        return _PollResp(status, payload)


async def test_poll_permanent_error_raises_immediately():
    import pytest
    from livekit.agents import APIStatusError
    cs = _stream()
    session = _PollSession([(401, {})])
    with pytest.raises(APIStatusError) as exc:
        await cs._resolve_result(session, {"status": "dispatched", "request_id": "r"})
    assert exc.value.status_code == 401
    assert session.calls == 1


async def test_poll_transient_retries_to_budget():
    cs = _stream()
    session = _PollSession([(503, {}), (503, {}), (503, {})])
    _, url = await cs._resolve_result(session, {"status": "dispatched", "request_id": "r"})
    assert url is None
    assert session.calls == 3


async def test_poll_rate_limit_then_success():
    cs = _stream()
    session = _PollSession([
        (429, {}),
        (200, {"status": "success", "request_id": "r", "outcome": {"audio_url": "https://a/x.wav"}}),
    ])
    _, url = await cs._resolve_result(session, {"status": "dispatched", "request_id": "r"})
    assert url == "https://a/x.wav"
