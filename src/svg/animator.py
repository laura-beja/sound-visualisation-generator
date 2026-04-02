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
