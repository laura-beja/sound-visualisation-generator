import os
import sys

import pytest

pytest.importorskip(
    "tkinter",
    reason="Tkinter is not available in this environment.",
    exc_type=ImportError,
)

if sys.platform.startswith("linux") and os.environ.get("DISPLAY") is None:
    pytest.skip(
        "No display available for Tkinter GUI tests on headless Linux.",
        allow_module_level=True,
    )

import svg.ui.app as app_module
from svg.ui.app import SoundVisualisationApp


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(app_module.pygame.mixer, "init", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module.pygame.mixer.music, "load", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module.pygame.mixer.music, "play", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module.pygame.mixer.music, "stop", lambda *args, **kwargs: None)

    created_app = SoundVisualisationApp()
    created_app.withdraw()
    yield created_app
    created_app.destroy()


def test_app_creation(app):
    assert app.title() == "Sound Visualisation Generator"


def test_default_audio_file(app):
    assert app.audio_file == ""


def test_slider_defaults(app):
    assert round(app.scale_slider.get(), 1) == 1.0
    assert round(app.speed_slider.get(), 1) == 1.0
    assert int(app.detail_slider.get()) == 5


def test_play_audio_preview_only_sets_mode(app, monkeypatch):
    app.audio_file = "fake.wav"
    app.record_live_var.set(False)

    monkeypatch.setattr(app, "buffer_audio", lambda: True)
    app.audio_data = [0] * 4096
    app.sample_rate = 44100
    monkeypatch.setattr(app, "animate_from_audio", lambda: None)

    app.play_audio()

    assert app.record_frames is False
    assert app.progress_mode_label.cget("text") == "Mode: Preview only"
    assert app.status_label.cget("text") == "Status: Playing audio"


def test_play_audio_recording_sets_mode(app, monkeypatch):
    app.audio_file = "fake.wav"
    app.record_live_var.set(True)

    monkeypatch.setattr(app, "buffer_audio", lambda: True)
    monkeypatch.setattr(app, "_ask_save_path", lambda *_args: "/tmp/live.mp4")
    app.audio_data = [0] * 4096
    app.sample_rate = 44100
    monkeypatch.setattr(app, "animate_from_audio", lambda: None)

    app.play_audio()

    assert app.record_frames is True
    assert app.progress_mode_label.cget("text") == "Mode: Recording while playing"
    assert app.status_label.cget("text") == "Status: Playing + recording"


def test_animate_from_audio_does_not_progress_when_not_recording(app, monkeypatch):
    app.is_animating = True
    app.audio_data = [0] * 4096
    app.sample_rate = 44100
    app.current_chunk = 0
    app.record_frames = False
    app.progress_bar.set(0)

    monkeypatch.setattr(app_module, "get_radius_from_chunk", lambda **kwargs: (50, 1024))
    monkeypatch.setattr(app, "draw_circle", lambda radius: None)
    monkeypatch.setattr(app, "after", lambda delay, callback: None)

    app.animate_from_audio()

    assert app.current_chunk == 1024
    assert app.progress_bar.get() == 0


def test_generate_video_uses_selected_colour_mode(app, monkeypatch):
    captured = {}

    def fake_create_video_file(audio_file, output_file, colour_mode):
        captured["audio_file"] = audio_file
        captured["output_file"] = output_file
        captured["colour_mode"] = colour_mode
        return output_file

    app.audio_file = "fake.wav"
    app.colour_menu.set("Purple")
    monkeypatch.setattr(app, "_ask_save_path", lambda *_args: "/tmp/output.mp4")
    monkeypatch.setattr(app_module, "create_video_file", fake_create_video_file)

    app.generate_video()

    assert captured["audio_file"] == "fake.wav"
    assert captured["colour_mode"] == "Purple"
    assert app.progress_mode_label.cget("text") == "Mode: Generation complete"


def test_stop_audio_calls_finish_live_recording_when_recording(app, monkeypatch):
    called = {"finish": False}
    app.record_frames = True

    def fake_finish_live_recording():
        called["finish"] = True

    monkeypatch.setattr(app, "finish_live_recording", fake_finish_live_recording)
    monkeypatch.setattr(app, "clear_preview", lambda: None)

    app.stop_audio()

    assert called["finish"] is True
    assert app.progress_mode_label.cget("text") == "Mode: Idle"


def test_select_audio_updates_labels(app, monkeypatch):
    monkeypatch.setattr(app_module.filedialog, "askopenfilename", lambda **kwargs: "song.wav")
    app.select_audio()
    assert app.audio_file == "song.wav"
    assert app.status_label.cget("text") == "Status: Audio selected"


def test_select_audio_no_selection_keeps_defaults(app, monkeypatch):
    monkeypatch.setattr(app_module.filedialog, "askopenfilename", lambda **kwargs: "")
    app.select_audio()
    assert app.audio_file == ""


def test_play_audio_without_file_sets_status(app):
    app.audio_file = ""
    app.play_audio()
    assert app.status_label.cget("text") == "Status: Please select an audio file"


def test_generate_video_without_file_sets_status(app):
    app.audio_file = ""
    app.generate_video()
    assert app.status_label.cget("text") == "Status: Please select an audio file"


def test_generate_video_failure_sets_failure_mode(app, monkeypatch):
    app.audio_file = "fake.wav"
    monkeypatch.setattr(app, "_ask_save_path", lambda *_args: "/tmp/output.mp4")

    def fake_create_video_file(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module, "create_video_file", fake_create_video_file)
    app.generate_video()

    assert "Generation failed" in app.status_label.cget("text")
    assert app.progress_mode_label.cget("text") == "Mode: Generation failed"


def test_buffer_audio_success(app, monkeypatch):
    monkeypatch.setattr(app_module, "load_wav_audio", lambda _path: ([0.1, 0.2], 22050))
    app.audio_file = "ok.wav"
    assert app.buffer_audio() is True
    assert app.sample_rate == 22050
    assert app.current_chunk == 0
    assert app.status_label.cget("text") == "Status: Audio buffered"


def test_buffer_audio_failure(app, monkeypatch):
    def fake_load(_path):
        raise ValueError("bad")

    monkeypatch.setattr(app_module, "load_wav_audio", fake_load)
    app.audio_file = "bad.wav"
    assert app.buffer_audio() is False
    assert "Buffer error" in app.status_label.cget("text")


def test_on_colour_change_draws_preview_when_animating(app, monkeypatch):
    app.is_animating = True
    app.audio_data = [0.1] * 2048
    app.current_chunk = 1024
    app.chunk_size = 1024
    called = {"drawn": False}

    monkeypatch.setattr(app_module, "get_radius_from_chunk", lambda **kwargs: (42, 2048))
    monkeypatch.setattr(app, "draw_circle", lambda _radius: called.__setitem__("drawn", True))

    app.on_colour_change("Purple")
    assert called["drawn"] is True


def test_start_and_stop_live_recording_clear_temp_dir(app, monkeypatch):
    monkeypatch.setattr(app, "_ask_save_path", lambda *_args: "/tmp/live.mp4")
    app.start_live_recording()
    assert app.record_frames is True
    assert app.frames_dir

    frames_dir = app.frames_dir
    app.stop_live_recording(clear_only=True)

    assert app.record_frames is False
    assert app.frames_dir == ""
    assert not os.path.exists(frames_dir)


def test_finish_live_recording_with_no_frames_sets_status(app, monkeypatch):
    monkeypatch.setattr(app, "_ask_save_path", lambda *_args: "/tmp/live.mp4")
    app.start_live_recording()
    app.frame_index = 0
    app.finish_live_recording()
    assert app.status_label.cget("text") == "Status: No live frames captured"


def test_encode_live_video_success_updates_ui(app, monkeypatch, tmp_path):
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    app.audio_file = "audio.wav"
    app.live_output_path = str(tmp_path / "live.mp4")

    monkeypatch.setattr(app_module, "encode_frames_to_video", lambda **kwargs: app.live_output_path)
    monkeypatch.setattr(app, "after", lambda _delay, callback: callback())

    app._encode_live_video(str(frames_dir), 30)

    assert app.progress_mode_label.cget("text") == "Mode: Live export complete"
    assert app.status_label.cget("text") == "Status: Live recording complete"


def test_encode_live_video_failure_updates_ui(app, monkeypatch, tmp_path):
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()

    def fail_encode(**kwargs):
        raise RuntimeError("encode failed")

    monkeypatch.setattr(app_module, "encode_frames_to_video", fail_encode)
    monkeypatch.setattr(app, "after", lambda _delay, callback: callback())

    app._encode_live_video(str(frames_dir), 30)

    assert app.progress_mode_label.cget("text") == "Mode: Live export failed"
    assert "Live export failed" in app.status_label.cget("text")


def test_animate_from_audio_handles_end_of_audio_without_recording(app, monkeypatch):
    app.is_animating = True
    app.is_playing = True
    app.record_frames = False
    app.audio_data = [0.1] * 1024

    monkeypatch.setattr(app_module, "get_radius_from_chunk", lambda **kwargs: (None, 0))

    app.animate_from_audio()
    assert app.is_animating is False
    assert app.is_playing is False
    assert app.status_label.cget("text") == "Status: Animation complete"


def test_animate_from_audio_records_frame_and_progress(app, monkeypatch, tmp_path):
    app.is_animating = True
    app.audio_data = [0.1] * 4096
    app.sample_rate = 44100
    app.current_chunk = 0
    app.record_frames = True
    app.frames_dir = str(tmp_path)
    app.frame_index = 0

    monkeypatch.setattr(app_module, "get_radius_from_chunk", lambda **kwargs: (55, 1024))
    monkeypatch.setattr(app, "draw_circle", lambda _radius: None)
    monkeypatch.setattr(app_module, "save_circle_frame", lambda **kwargs: None)
    monkeypatch.setattr(app, "after", lambda _delay, _callback: None)

    app.animate_from_audio()

    assert app.frame_index == 1
    assert app.current_chunk == 1024
    assert app.progress_bar.get() > 0
