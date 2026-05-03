import numpy as np
import math
import time


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

    volume = np.sqrt(np.max(chunk**2))

    radius = int(min_radius + volume * scale)
    radius = max(min_radius, min(radius, max_radius))

    next_chunk = current_chunk + chunk_size
    return radius, next_chunk


def get_delay_ms(chunk_size, sample_rate):
    if sample_rate <= 0:
        return 30
    return max(1, int((chunk_size / sample_rate) * 1000))


def get_frequency_bands(chunk, sample_rate, num_bands):
    if len(chunk) == 0:
        return np.zeros(num_bands, dtype=np.float32)

    window = np.hanning(len(chunk))
    # window = chunk
    chunk = chunk * window

    fft_result = np.fft.rfft(chunk)
    magnitudes = np.abs(fft_result)

    if len(magnitudes) > 0:
        magnitudes[0] = 0

    # log
    min_bin = 1
    max_bin = len(magnitudes) - 1

    # log_edges = np.logspace(
    #     np.log10(min_bin),
    #     np.log10(max_bin),
    #     num_bands + 1
    # ).astype(int)
    log_edges = np.logspace(np.log10(min_bin), np.log10(max_bin), num_bands + 1)
    log_edges = np.round(log_edges).astype(int)

    for i in range(1, len(log_edges)):
        if log_edges[i] <= log_edges[i - 1]:
            log_edges[i] = log_edges[i - 1] + 1

    bands = np.zeros(num_bands, dtype=np.float32)

    for i in range(num_bands):
        start = log_edges[i]
        end = log_edges[i + 1]

        if end > start:
            bands[i] = np.max(magnitudes[start:end])

    # normalize
    max_val = np.max(bands)
    if max_val > 0:
        bands = bands / max_val

    return bands


def update_frequency_bands(self, bands):
    canvas_width = 500
    canvas_height = 320
    baseline_y = canvas_height // 2
    max_height = 120
    noise_amount = self.get_noise_amount()
    t = time.perf_counter()

    band_width = canvas_width / self.num_bands
    base_width = band_width * self.thickness
    colour = self.get_visual_colour()

    for i, band in enumerate(bands):
        line = self.band_lines[i]

        height = band * max_height
        width_wobble = math.sin(t * 8.0 + i * 0.9) * noise_amount * 8
        line_width = max(1, int(base_width + width_wobble))

        x = i * band_width + band_width / 2

        self.preview_box.coords(line, x, baseline_y, x, baseline_y - height)

        self.preview_box.itemconfig(line, width=line_width, fill=colour)
