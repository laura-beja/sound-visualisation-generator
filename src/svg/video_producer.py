import math
import os
import subprocess

from PIL import Image, ImageDraw

from svg.animator import get_frequency_bands, get_radius_from_chunk
from svg.audio_loader import load_wav_audio
from svg.colours import resolve_colour


def save_circle_frame(frame_path, radius, width=500, height=320, colour="#00B7FF", thickness=0.9):
    # create .png from single frame
    image = Image.new("RGB", (width, height), "black")
    # create a draw object to draw on the image
    draw = ImageDraw.Draw(image)
    # calculate the center of the image
    cx = width // 2
    cy = height // 2

    line_width = max(1, int(round(8 * float(thickness))))
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        outline=colour,
        width=line_width,
    )

    image.save(frame_path)


def save_spectrum_frame(
    frame_path,
    bands,
    width=500,
    height=320,
    colour="#00B7FF",
    thickness=1,
    modulation=5,
    frame_index=0,
):
    """Render a simple spectrum-style frame using vertical bars for `bands`.

    `bands` is an iterable of floats in [0..1].
    """
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)

    num = len(bands)
    if num == 0:
        image.save(frame_path)
        return

    band_width = width / num
    baseline = height // 2
    noise_amount = (modulation - 1) / 9.0

    for i, v in enumerate(bands):
        x = int(i * band_width)
        bar_height = int(v * (height // 2 - 10))
        # apply modulation wobble to band height based on frame and band index
        wobble = math.sin(frame_index * 4.0 + i * 0.9) * noise_amount * 8
        adj_bar_height = int(max(0, bar_height + wobble))
        # draw a vertical line centered vertically
        draw.line(
            (
                x + band_width / 2,
                baseline,
                x + band_width / 2,
                baseline - adj_bar_height,
            ),
            fill=colour,
            width=max(1, int(band_width * thickness)),
        )

    image.save(frame_path)


def encode_frames_to_video(frames_dir, audio_file, output_file, frame_rate):
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        f"{float(frame_rate):.8f}",
        "-i",
        os.path.join(frames_dir, "frame_%05d.png"),
        "-i",
        audio_file,
        "-r",
        f"{float(frame_rate):.8f}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "320k",
        "-shortest",
        output_file,
    ]

    subprocess.run(ffmpeg_cmd, check=True)
    return output_file


def create_video_file(
    audio_file,
    output_file,
    colour_mode="Blue",
    *,
    chunk_size=735,
    thickness=0.9,
    modulation=5,
    style_callback=None,
    num_bands=32,
):
    # get the folder that will contain the final .mp4 file
    output_dir = os.path.dirname(output_file)

    # create output folder if it does not exist
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # create frames folder inside output folder
    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    # clear old frames from previous runs
    for name in os.listdir(frames_dir):
        file_name = os.path.join(frames_dir, name)
        if os.path.isfile(file_name):
            os.remove(file_name)

    # load the wav audio
    audio_data, sample_rate = load_wav_audio(audio_file)

    current_chunk = 0
    frame_index = 0
    frame_rate = sample_rate / float(chunk_size)
    frame_colour = resolve_colour(colour_mode)
    base_scale = 400
    scale = int(base_scale * thickness)

    while True:
        # allow caller to provide dynamic per-frame style via callback
        frame_thickness = thickness
        frame_modulation = modulation
        frame_colour_mode = colour_mode
        frame_min_radius = 30
        frame_max_radius = 120
        frame_scale = scale

        if callable(style_callback):
            try:
                style = style_callback(frame_index, current_chunk)
                if isinstance(style, dict):
                    frame_thickness = float(style.get("thickness", frame_thickness))
                    frame_modulation = int(style.get("modulation", frame_modulation))
                    frame_colour_mode = style.get("colour_mode", frame_colour_mode)
                    frame_min_radius = int(style.get("min_radius", frame_min_radius))
                    frame_max_radius = int(style.get("max_radius", frame_max_radius))
                    # scale can be provided directly or derived from thickness
                    if "scale" in style:
                        frame_scale = int(style.get("scale", frame_scale))
                    else:
                        frame_scale = int(base_scale * frame_thickness)
            except Exception:
                # ignore style callback errors and use defaults
                pass

        radius, next_chunk = get_radius_from_chunk(
            audio_data=audio_data,
            current_chunk=current_chunk,
            chunk_size=chunk_size,
            min_radius=frame_min_radius,
            max_radius=frame_max_radius,
            scale=frame_scale,
        )

        if radius is None:
            break

        # apply a small wobble based on modulation for visual interest
        # recompute noise amount from frame_modulation
        frame_noise = (frame_modulation - 1) / 9.0
        wobble = math.sin(frame_index * 4.0) * frame_noise * 10
        adj_radius = int(max(1, min(radius + wobble, 10000)))

        frame_path = os.path.join(frames_dir, f"frame_{frame_index:05d}.png")
        # resolve colour for this frame
        frame_colour = resolve_colour(frame_colour_mode)

        # select visual mode: circle (default) or spectrum
        visual_mode = None
        if callable(style_callback):
            try:
                style = style_callback(frame_index, current_chunk)
                if isinstance(style, dict):
                    visual_mode = style.get("visual_mode") or style.get("mode")
            except Exception:
                pass

        if visual_mode is None:
            visual_mode = "circle"

        if str(visual_mode).lower().startswith("spec"):
            # compute frequency bands for this chunk and draw spectrum frame
            chunk = audio_data[current_chunk : current_chunk + chunk_size]
            bands = get_frequency_bands(chunk=chunk, sample_rate=sample_rate, num_bands=num_bands)
            save_spectrum_frame(
                frame_path,
                bands,
                colour=frame_colour,
                thickness=frame_thickness,
                modulation=frame_modulation,
                frame_index=frame_index,
            )
        else:
            # circle visual
            save_circle_frame(
                frame_path,
                int(adj_radius),
                colour=frame_colour,
                thickness=frame_thickness,
            )

        current_chunk = next_chunk
        frame_index += 1

    if frame_index == 0:
        raise ValueError("No frames generated")

    return encode_frames_to_video(
        frames_dir=frames_dir,
        audio_file=audio_file,
        output_file=output_file,
        frame_rate=frame_rate,
    )
