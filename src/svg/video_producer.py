import os
import subprocess

from PIL import Image, ImageDraw

from src.svg.animator import get_radius_from_chunk
from src.svg.audio_loader import load_wav_audio

def save_circle_frame(frame_path, radius, width=500, height=320):
    # create .png from single frame
    image = Image.new('RGB', (width, height), "black")
    # create a draw object to draw on the image
    draw = ImageDraw.Draw(image)
    # calculate the center of the image
    cx = width // 2
    cy = height // 2
    
    draw.ellipse((
        cx - radius, cy - radius, cx + radius, cy + radius
    ), outline="cyan", width=2)
    
    image.save(frame_path)
    
    
def create_video_file(audio_file, output_file):
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
        save_circle_frame(frame_path, int(radius))
                          
        current_chunk = next_chunk
        frame_index += 1
        
        if frame_index == 0:
            raise ValueError("No frames generated")
        
        # build ffmpeg command
        
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-framerate", str(frame_rate),
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-i", audio_file,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        output_file,
    ]
    
    # run the ffmpeg command
    subprocess.run(ffmpeg_cmd, check=True)
    
    return output_file