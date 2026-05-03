import numpy as np

from svg.animator import get_delay_ms, get_radius_from_chunk


def test_get_radius_from_chunk_returns_none_when_start_out_of_bounds():
    radius, next_chunk = get_radius_from_chunk(np.array([0.1, 0.2], dtype=np.float32), 10, 4)
    assert radius is None
    assert next_chunk == 10


def test_get_radius_from_chunk_maps_volume_and_advances_chunk():
    audio = np.array([0.0, 0.5, 0.5, 0.0], dtype=np.float32)
    radius, next_chunk = get_radius_from_chunk(audio, 0, 4, min_radius=10, max_radius=100, scale=80)
    assert radius is not None
    assert 10 <= radius <= 100
    assert next_chunk == 4


def test_get_radius_from_chunk_respects_clamp_to_max_radius():
    audio = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
    radius, _ = get_radius_from_chunk(audio, 0, 4, min_radius=10, max_radius=25, scale=100)
    assert radius == 25


def test_get_delay_ms_defaults_when_sample_rate_invalid():
    assert get_delay_ms(1024, 0) == 30
    assert get_delay_ms(1024, -1) == 30


def test_get_delay_ms_computes_positive_delay():
    assert get_delay_ms(1024, 44100) >= 1
