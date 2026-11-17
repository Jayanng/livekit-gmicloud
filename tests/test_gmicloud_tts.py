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
