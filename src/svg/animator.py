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

    window = np.hanning(len(chunk))
    chunk = chunk * window

    fft_result = np.fft.rfft(chunk)
    magnitudes = np.abs(fft_result)

    if len(magnitudes) > 0:
        magnitudes[0] = 0

    # log
    min_bin = 1
    max_bin = len(magnitudes) - 1

    log_edges = np.logspace(
        np.log10(min_bin),
        np.log10(max_bin),
        num_bands + 1
    ).astype(int)

    bands = np.zeros(num_bands, dtype=np.float32)

    for i in range(num_bands):
        start = log_edges[i]
        end = log_edges[i + 1]

        if end > start:
            bands[i] = np.mean(magnitudes[start:end])

    # normalize
    max_val = np.max(bands)
    if max_val > 0:
        bands = bands / max_val

    return bands

def update_frequency_bands(self, bands):
    canvas_height = 320
    baseline_y = canvas_height // 2
    max_height = 120

    for i, band in enumerate(bands):
        line = self.band_lines[i]

        height = band * max_height

        self.preview_box.coords(
            line,
            self.preview_box.coords(line)[0], baseline_y,
            self.preview_box.coords(line)[0], baseline_y - height
        )