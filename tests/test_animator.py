from unittest.mock import MagicMock

import numpy as np
import pytest

from svg.animator import (
    get_delay_ms,
    get_frequency_bands,
    get_radius_from_chunk,
    update_frequency_bands,
)


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


# --- get_frequency_bands ---

def test_get_frequency_bands_empty_chunk_returns_zeros():
    result = get_frequency_bands(np.array([], dtype=np.float32), 44100, 8)
    assert len(result) == 8
    assert np.all(result == 0)


def test_get_frequency_bands_returns_correct_number_of_bands():
    chunk = np.random.rand(1024).astype(np.float32)
    result = get_frequency_bands(chunk, 44100, 16)
    assert len(result) == 16


def test_get_frequency_bands_output_normalised():
    chunk = np.random.rand(1024).astype(np.float32)
    result = get_frequency_bands(chunk, 44100, 8)
    assert np.max(result) <= 1.0
    assert np.min(result) >= 0.0


def test_get_frequency_bands_all_zeros_chunk_returns_zeros():
    chunk = np.zeros(1024, dtype=np.float32)
    result = get_frequency_bands(chunk, 44100, 8)
    assert np.all(result == 0)


def test_get_frequency_bands_single_band():
    chunk = np.random.rand(512).astype(np.float32)
    result = get_frequency_bands(chunk, 44100, 1)
    assert len(result) == 1


def test_get_frequency_bands_sine_wave_has_energy():
    t = np.linspace(0, 1, 44100, endpoint=False, dtype=np.float32)
    chunk = np.sin(2 * np.pi * 440 * t[:1024])
    result = get_frequency_bands(chunk, 44100, 8)
    assert np.max(result) > 0


# --- update_frequency_bands ---

def _make_mock_self(num_bands=4):
    mock = MagicMock()
    mock.num_bands = num_bands
    mock.thickness = 1.0
    mock.get_noise_amount.return_value = 0.0
    mock.get_visual_colour.return_value = "#00B7FF"
    mock.band_lines = [MagicMock() for _ in range(num_bands)]
    return mock


def test_update_frequency_bands_calls_coords_for_each_band():
    mock_self = _make_mock_self(num_bands=4)
    bands = np.array([0.5, 0.8, 0.3, 1.0], dtype=np.float32)
    update_frequency_bands(mock_self, bands)
    assert mock_self.preview_box.coords.call_count == 4


def test_update_frequency_bands_calls_itemconfig_for_each_band():
    mock_self = _make_mock_self(num_bands=4)
    bands = np.array([0.5, 0.8, 0.3, 1.0], dtype=np.float32)
    update_frequency_bands(mock_self, bands)
    assert mock_self.preview_box.itemconfig.call_count == 4


def test_update_frequency_bands_zero_bands_no_calls():
    mock_self = _make_mock_self(num_bands=0)
    bands = np.array([], dtype=np.float32)
    update_frequency_bands(mock_self, bands)
    mock_self.preview_box.coords.assert_not_called()


@pytest.mark.parametrize("band_value", [0.0, 0.5, 1.0])
def test_update_frequency_bands_various_amplitudes(band_value):
    mock_self = _make_mock_self(num_bands=2)
    bands = np.array([band_value, band_value], dtype=np.float32)
    update_frequency_bands(mock_self, bands)
    assert mock_self.preview_box.coords.call_count == 2

