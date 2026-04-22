import os
import subprocess

from PIL import Image, ImageDraw

from svg.animator import get_radius_from_chunk
from svg.audio_loader import load_wav_audio

COLOUR_MODE_MAP = {
    "Blue": "#00B7FF",
    "Purple": "#BB86FC",
    "Grayscale": "#D0D0D0",
}


def resolve_colour(colour_mode):
    return COLOUR_MODE_MAP.get(colour_mode, COLOUR_MODE_MAP["Blue"])


def save_circle_frame(frame_path, radius, width=500, height=320, colour="#00B7FF"):
    # create .png from single frame
    image = Image.new('RGB', (width, height), "black")
    # create a draw object to draw on the image
    draw = ImageDraw.Draw(image)
    # calculate the center of the image
    cx = width // 2
    cy = height // 2
    
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=colour, width=2)
    
    image.save(frame_path)


def encode_frames_to_video(frames_dir, audio_file, output_file, frame_rate):
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(frame_rate),
        "-i",
        os.path.join(frames_dir, "frame_%05d.png"),
        "-i",
        audio_file,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        output_file,
    ]

    subprocess.run(ffmpeg_cmd, check=True)
    return output_file
    
    
def create_video_file(audio_file, output_file, colour_mode="Blue"):
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
    chunk_size = 1024
    frame_index = 0
    frame_rate = sample_rate // chunk_size
    frame_colour = resolve_colour(colour_mode)
    
    while True:
        radius, next_chunk = get_radius_from_chunk(
            audio_data=audio_data,
            current_chunk=current_chunk,
            chunk_size=chunk_size,
            min_radius=30,
            max_radius=120,
            scale=400,
        )
         
        if radius is None:
            break
        
        frame_path = os.path.join(frames_dir, f"frame_{frame_index:05d}.png")
        # save the frame as a .png file with the radius of the circle based on the audio volume
        save_circle_frame(frame_path, int(radius), colour=frame_colour)
                          
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