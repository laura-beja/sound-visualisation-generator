import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk
import pygame
from PIL import Image, ImageTk

from src.svg.animator import get_delay_ms, get_radius_from_chunk
from src.svg.audio_loader import load_wav_audio

#  py -3.11 -m venv .venv
# .venv\Scripts\Activate.ps1

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SoundVisualisationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        print("UI running 2")
        self.title("Sound Visualisation Generator")
        self.geometry("1100x700")

        self.audio_file = ""
        self.preview_image = None
        self.preview_tk = None

        self.is_playing = False
        self.is_animating = False

        self.audio_data = None
        self.sample_rate = 0
        self.current_chunk = 0
        self.chunk_size = 1024

        # pygame.mixer.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2)

        # Main window layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Left frame = controls
        self.left_frame = ctk.CTkFrame(self, corner_radius=12)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Right frame = preview
        self.right_frame = ctk.CTkFrame(self, corner_radius=12)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.build_left_side()
        self.build_right_side()

    def build_left_side(self):
        title_label = ctk.CTkLabel(
            self.left_frame, text="Controls", font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(15, 20))

        self.select_button = ctk.CTkButton(
            self.left_frame, text="Select Audio File", command=self.select_audio
        )
        self.select_button.pack(padx=15, pady=10, fill="x")

        self.start_button = ctk.CTkButton(self.left_frame, text="Play", command=self.play_audio)
        self.start_button.pack(padx=15, pady=10, fill="x")

        self.file_label = ctk.CTkLabel(
            self.left_frame, text="No file selected", wraplength=250, justify="left"
        )
        self.file_label.pack(padx=15, pady=(0, 15))

        self.scale_label = ctk.CTkLabel(self.left_frame, text="Scale")
        self.scale_label.pack(pady=(10, 0))

        self.scale_slider = ctk.CTkSlider(
            self.left_frame, from_=1, to=100, command=self.update_scale_value
        )
        self.scale_slider.set(1.0)
        self.scale_slider.pack(padx=15, pady=5, fill="x")

        self.scale_value_label = ctk.CTkLabel(self.left_frame, text="1.0")
        self.scale_value_label.pack(pady=(0, 10))

        self.speed_label = ctk.CTkLabel(self.left_frame, text="Speed")
        self.speed_label.pack(pady=(10, 0))

        self.speed_slider = ctk.CTkSlider(
            self.left_frame, from_=1, to=10, command=self.update_speed_value
        )
        self.speed_slider.set(1.0)
        self.speed_slider.pack(padx=15, pady=5, fill="x")

        self.speed_value_label = ctk.CTkLabel(self.left_frame, text="1.0")
        self.speed_value_label.pack(pady=(0, 10))

        self.detail_label = ctk.CTkLabel(self.left_frame, text="Detail")
        self.detail_label.pack(pady=(10, 0))

        self.detail_slider = ctk.CTkSlider(
            self.left_frame, from_=1, to=10, number_of_steps=9, command=self.update_detail_value
        )
        self.detail_slider.set(5)
        self.detail_slider.pack(padx=15, pady=5, fill="x")

        self.detail_value_label = ctk.CTkLabel(self.left_frame, text="5")
        self.detail_value_label.pack(pady=(0, 10))

        self.colour_label = ctk.CTkLabel(self.left_frame, text="Colour Mode")
        self.colour_label.pack(pady=(10, 0))

        self.colour_menu = ctk.CTkOptionMenu(
            self.left_frame, values=["Blue", "Purple", "Grayscale"]
        )
        self.colour_menu.set("Blue")
        self.colour_menu.pack(padx=15, pady=5, fill="x")

        self.generate_button = ctk.CTkButton(
            self.left_frame, text="Generate Video", command=self.generate_video
        )
        self.generate_button.pack(padx=15, pady=(25, 10), fill="x")

        self.status_label = ctk.CTkLabel(self.left_frame, text="Status: Waiting")
        self.status_label.pack(pady=(10, 5))

    def build_right_side(self):
        preview_label = ctk.CTkLabel(
            self.right_frame, text="Preview", font=ctk.CTkFont(size=22, weight="bold")
        )
        preview_label.pack(pady=(15, 20))

        self.preview_box = tk.Canvas(
            self.right_frame, width=500, height=320, bg="#1a1a1a", highlightthickness=0
        )
        self.preview_box.pack(padx=20, pady=10)

        self.output_label = ctk.CTkLabel(
            self.right_frame, text="Output file: Not generated yet", wraplength=450, justify="left"
        )
        self.output_label.pack(pady=(10, 15))

        self.progress_bar = ctk.CTkProgressBar(self.right_frame, width=450)
        self.progress_bar.pack(padx=20, pady=10, fill="x")
        self.progress_bar.set(0)

    def update_scale_value(self, value):
        self.scale_value_label.configure(text=f"{value:.1f}")

    def update_speed_value(self, value):
        self.speed_value_label.configure(text=f"{value:.1f}")

    def update_detail_value(self, value):
        self.detail_value_label.configure(text=f"{int(value)}")

    def select_audio(self):
        file_path = filedialog.askopenfilename(
            title="Select Audio File", filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )

        if file_path:
            self.audio_file = file_path
            self.file_label.configure(text=self.audio_file)
            self.status_label.configure(text="Status: Audio selected")
            print(self.audio_file)

    def play_audio(self):
        print("play_audio")
        if not self.audio_file:
            self.status_label.configure(text="Status: Please select an audio file")
            return

        if not self.buffer_audio():
            return

        pygame.mixer.music.load(self.audio_file)
        pygame.mixer.music.play()

        self.is_playing = True
        self.is_animating = True
        self.current_chunk = 0

        self.start_button.configure(text="Stop", command=self.stop_audio)
        self.status_label.configure(text="Status: Playing audio")

        self.animate_from_audio()

    def stop_audio(self):
        pygame.mixer.music.stop()

        self.is_playing = False
        self.is_animating = False

        self.start_button.configure(text="Play", command=self.play_audio)
        self.status_label.configure(text="Status: Audio stopped")

        self.clear_preview()

    def generate_video(self):
        if self.audio_file == "":
            self.status_label.configure(text="Status: Please select an audio file")
            return

        scale = self.scale_slider.get()
        speed = self.speed_slider.get()
        detail = int(self.detail_slider.get())
        colour = self.colour_menu.get()

        self.status_label.configure(text="Status: Generating...")
        self.progress_bar.set(0.25)

        self.preview_box.delete("all")
        self.preview_box.create_oval(150, 60, 350, 260, outline="cyan", width=1)

        self.progress_bar.set(0.75)

        output_path = "output/visualization.mp4"
        self.output_label.configure(text=f"Output file: {output_path}")

        self.progress_bar.set(1.0)
        self.status_label.configure(
            text=(
                f"Status: Generation complete | "
                f"Scale {scale:.1f}, Speed {speed:.1f}, "
                f"Detail {detail}, Colour {colour}"
            )
        )

    def load_preview_image(self, image_path):
        image = Image.open(image_path).resize((500, 320))
        self.preview_tk = ImageTk.PhotoImage(image)

        self.preview_box.delete("all")
        self.preview_box.create_image(0, 0, anchor="nw", image=self.preview_tk)

    def clear_preview(self):
        self.preview_box.delete("all")

    def buffer_audio(self):
        if not self.audio_file:
            self.status_label.configure(text="Status: Please select an audio file")
            return False

        try:
            audio, sample_rate = load_wav_audio(self.audio_file)

            self.audio_data = audio
            self.sample_rate = sample_rate
            self.current_chunk = 0

            print("Sample rate:", self.sample_rate)

            self.status_label.configure(text="Status: Audio buffered")
            return True

        except Exception as e:
            self.status_label.configure(text=f"Status: Buffer error: {e}")
            print("buffer_audio error:", e)
            return False

    def draw_circle(self, radius):
        self.preview_box.delete("all")

        canvas_width = 500
        canvas_height = 320

        cx = canvas_width // 2
        cy = canvas_height // 2

        self.preview_box.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius, outline="cyan", width=1
        )

    def animate_from_audio(self):
        if self.audio_data is None or not self.is_animating:
            print("animate not working, no audio data")
            return

        radius, next_chunk = get_radius_from_chunk(
            audio_data=self.audio_data,
            current_chunk=self.current_chunk,
            chunk_size=self.chunk_size,
            min_radius=30,
            max_radius=120,
            scale=400,
        )

        if radius is None:
            self.is_animating = False
            self.is_playing = False
            self.start_button.configure(text="Play", command=self.play_audio)
            self.status_label.configure(text="Status: Animation complete")
            return

        self.draw_circle(radius)
        self.current_chunk = next_chunk

        delay_ms = get_delay_ms(self.chunk_size, self.sample_rate)
        self.after(delay_ms, self.animate_from_audio)

    def start_audio_visual(self):
        self.is_animating = True
        self.current_chunk = 0
        self.status_label.configure(text="Status: Animating from audio")
        self.animate_from_audio()


if __name__ == "__main__":
    app = SoundVisualisationApp()
    app.mainloop()
