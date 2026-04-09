import numpy as np


def get_radius_from_chunk(
    audio_data,
    current_chunk,
    chunk_size,
    min_radius=30,
    max_radius=120,
    scale=400,
):
    start = current_chunk
    end = start + chunk_size

    if start >= len(audio_data):
        return None, current_chunk

    chunk = audio_data[start:end]

    if len(chunk) == 0:
        return None, current_chunk

    volume = np.sqrt(np.mean(chunk**2))

    radius = int(min_radius + volume * scale)
    radius = max(min_radius, min(radius, max_radius))

    next_chunk = current_chunk + chunk_size
    return radius, next_chunk


def get_delay_ms(chunk_size, sample_rate):
    if sample_rate <= 0:
        return 30
    return max(1, int((chunk_size / sample_rate) * 1000))

def get_frequency_bands(chunk, sample_rate, num_bands=32):
    if len(chunk) == 0:
        return np.zeros(num_bands, dtype=np.float32)

    # optional windowing to reduce FFT leakage
    window = np.hanning(len(chunk))
    windowed_chunk = chunk * window

    # real FFT
    fft_result = np.fft.rfft(windowed_chunk)
    magnitudes = np.abs(fft_result)

    # avoid DC dominance
    if len(magnitudes) > 0:
        magnitudes[0] = 0

    # split spectrum into bands
    band_edges = np.linspace(0, len(magnitudes), num_bands + 1, dtype=int)
    bands = np.zeros(num_bands, dtype=np.float32)

    for i in range(num_bands):
        start = band_edges[i]
        end = band_edges[i + 1]

        if end > start:
            bands[i] = np.mean(magnitudes[start:end])

    # normalize
    max_val = np.max(bands)
    if max_val > 0:
        bands = bands / max_val

    return bands

def draw_frequency_bands(preview_box, bands):
    preview_box.delete("all")

    canvas_width = 500
    canvas_height = 320

    baseline_y = canvas_height // 2
    num_bands = len(bands)
    band_width = canvas_width / num_bands
    max_bar_height = 120

    preview_box.create_line(
        0, baseline_y,
        canvas_width, baseline_y,
        fill="gray"
    )

    for i, band_value in enumerate(bands):
        x = i * band_width + band_width / 2
        bar_height = band_value * max_bar_height

        preview_box.create_line(
            x, baseline_y,
            x, baseline_y - bar_height,
            fill="cyan",
            width=2
        )