import wave

import numpy as np
import pytest

from svg.audio_loader import load_wav_audio


def _write_wav(path, channels, sampwidth, framerate, data):
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(framerate)
        wav_file.writeframes(data)


def test_load_wav_audio_raises_for_missing_path():
    with pytest.raises(ValueError, match="No audio file path"):
        load_wav_audio("")


def test_load_wav_audio_decodes_8bit_mono(tmp_path):
    wav_path = tmp_path / "mono8.wav"
    raw = bytes([0, 128, 255, 128])
    _write_wav(wav_path, channels=1, sampwidth=1, framerate=22050, data=raw)

    audio, sample_rate = load_wav_audio(str(wav_path))

    assert sample_rate == 22050
    assert len(audio) == 4
    assert np.max(audio) <= 1.0
    assert np.min(audio) >= -1.0


def test_load_wav_audio_decodes_16bit_stereo_to_mono(tmp_path):
    wav_path = tmp_path / "stereo16.wav"
    samples = np.array(
        [
            [1000, -1000],
            [500, -500],
            [0, 0],
        ],
        dtype=np.int16,
    )
    _write_wav(
        wav_path,
        channels=2,
        sampwidth=2,
        framerate=44100,
        data=samples.tobytes(),
    )

    audio, sample_rate = load_wav_audio(str(wav_path))

    assert sample_rate == 44100
    assert len(audio) == 3
    assert np.all(np.abs(audio) <= 1.0)


def test_load_wav_audio_decodes_24bit(tmp_path):
    wav_path = tmp_path / "mono24.wav"
    frame_values = [0, 1, 255, 32768]
    raw = bytearray()
    for value in frame_values:
        raw.extend(int(value).to_bytes(3, byteorder="little", signed=False))

    _write_wav(wav_path, channels=1, sampwidth=3, framerate=48000, data=bytes(raw))

    audio, sample_rate = load_wav_audio(str(wav_path))

    assert sample_rate == 48000
    assert len(audio) == len(frame_values)
    assert np.all(np.abs(audio) <= 1.0)


def test_load_wav_audio_raises_for_unsupported_sample_width(monkeypatch):
    class DummyWave:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def getframerate(self):
            return 44100

        def getnchannels(self):
            return 1

        def getsampwidth(self):
            return 4

        def getnframes(self):
            return 1

        def readframes(self, _):
            return b"\x00\x00\x00\x00"

    monkeypatch.setattr("svg.audio_loader.wave.open", lambda *_args, **_kwargs: DummyWave())

    with pytest.raises(ValueError, match="Unsupported sample width"):
        load_wav_audio("dummy.wav")
