# audio_loader.py
# edward tracey
# opens audio file. get the sample rate, resolution and byte depth. normalize values to -1 to +1.

import wave

import numpy as np


def load_wav_audio(file_path):
    if not file_path:
        raise ValueError("No audio file path.")
    
    with wave.open(file_path, "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        n_channels = wav_file.getnchannels()
        sampwidth = wav_file.getsampwidth()
        n_frames = wav_file.getnframes()

        raw_data = wav_file.readframes(n_frames)

    ## decode audio
    if sampwidth == 1:
        audio = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32) - 128.0
        max_value = 128.0

    elif sampwidth == 2:
        audio = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
        max_value = 32768.0

    elif sampwidth == 3:
        # 24-bit audio
        audio = np.frombuffer(raw_data, dtype=np.uint8)
        audio = audio.reshape(-1, 3)

        audio = (
            audio[:, 0].astype(np.int32)
            | (audio[:, 1].astype(np.int32) << 8)
            | (audio[:, 2].astype(np.int32) << 16)
        )

        audio = np.where(audio >= 0x800000, audio - 0x1000000, audio).astype(np.float32)
        max_value = 8388608.0

    else:
        raise ValueError(f"Unsupported sample width: {sampwidth}")

    # convert to mono. easier to process.
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels)
        audio = audio.mean(axis=1)

    # normalize audio to values from -1 to 1
    audio = audio / max_value 

    return audio, sample_rate

