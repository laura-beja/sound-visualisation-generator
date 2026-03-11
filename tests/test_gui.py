from svg.ui.app import SoundVisualisationApp

# basic test for GUI creation and default values, more tests can be added later for functionality and edge cases
def create_app():
    app = SoundVisualisationApp()
    app.withdraw()  # hide GUI during tests
    return app


def test_app_creation():
    app = create_app()
    assert app.title() == "Sound Visualisation Generator"
    app.destroy()


def test_default_audio_file():
    app = create_app()
    assert app.audio_file == ""
    app.destroy()


def test_slider_defaults():
    app = create_app()

    assert round(app.scale_slider.get(), 1) == 1.0
    assert round(app.speed_slider.get(), 1) == 1.0

    app.destroy()