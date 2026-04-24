import os

import numpy as np
import pytest

import svg.video_producer as video_producer


def test_resolve_colour_known_and_fallback():
    assert video_producer.resolve_colour("Purple") == "#BB86FC"
    assert video_producer.resolve_colour("Unknown") == "#00B7FF"


def test_save_circle_frame_creates_file(tmp_path):
    frame_path = tmp_path / "frame.png"
    video_producer.save_circle_frame(
        str(frame_path), radius=30, width=64, height=64, colour="#FFFFFF"
    )
    assert frame_path.exists()
    assert frame_path.stat().st_size > 0


def test_encode_frames_to_video_builds_ffmpeg_command(monkeypatch, tmp_path):
    calls = {}

    def fake_run(cmd, check):
        calls["cmd"] = cmd
        calls["check"] = check

    monkeypatch.setattr(video_producer.subprocess, "run", fake_run)

    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    out_file = tmp_path / "out" / "video.mp4"

    result = video_producer.encode_frames_to_video(
        frames_dir=str(frames_dir),
        audio_file="audio.wav",
        output_file=str(out_file),
        frame_rate=30,
    )

    assert result == str(out_file)
    assert calls["check"] is True
    assert calls["cmd"][0] == "ffmpeg"
    assert "-framerate" in calls["cmd"]
    assert str(out_file.parent).endswith("out")


def test_create_video_file_generates_frames_and_encodes(monkeypatch, tmp_path):
    audio = np.array([0.1] * 4096, dtype=np.float32)
    monkeypatch.setattr(video_producer, "load_wav_audio", lambda _path: (audio, 44100))

    chunk_sequence = [(50, 1024), (60, 2048), (None, 2048)]

    def fake_get_radius_from_chunk(**_kwargs):
        return chunk_sequence.pop(0)

    saved_frames = []

    def fake_save_circle_frame(frame_path, radius, width=500, height=320, colour="#00B7FF"):
        saved_frames.append((frame_path, radius, colour))
        open(frame_path, "wb").close()

    encoded = {}

    def fake_encode(frames_dir, audio_file, output_file, frame_rate):
        encoded["frames_dir"] = frames_dir
        encoded["audio_file"] = audio_file
        encoded["output_file"] = output_file
        encoded["frame_rate"] = frame_rate
        return output_file

    monkeypatch.setattr(video_producer, "get_radius_from_chunk", fake_get_radius_from_chunk)
    monkeypatch.setattr(video_producer, "save_circle_frame", fake_save_circle_frame)
    monkeypatch.setattr(video_producer, "encode_frames_to_video", fake_encode)

    output_file = tmp_path / "output" / "visualization.mp4"
    result = video_producer.create_video_file("audio.wav", str(output_file), colour_mode="Purple")

    assert result == str(output_file)
    assert len(saved_frames) == 2
    assert all(colour == "#BB86FC" for _, _, colour in saved_frames)
    assert encoded["output_file"] == str(output_file)
    assert encoded["audio_file"] == "audio.wav"
    assert os.path.basename(encoded["frames_dir"]) == "frames"
    assert encoded["frame_rate"] == 44100 // 1024


def test_create_video_file_raises_when_no_frames(monkeypatch, tmp_path):
    audio = np.array([0.1] * 1024, dtype=np.float32)
    monkeypatch.setattr(video_producer, "load_wav_audio", lambda _path: (audio, 44100))
    monkeypatch.setattr(video_producer, "get_radius_from_chunk", lambda **_kwargs: (None, 0))

    output_file = tmp_path / "output" / "visualization.mp4"
    with pytest.raises(ValueError, match="No frames generated"):
        video_producer.create_video_file("audio.wav", str(output_file))
