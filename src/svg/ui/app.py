import math
import os
import shutil
import tempfile
import threading
import time
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk
import pygame
from PIL import Image, ImageTk

from svg.animator import (
    get_delay_ms,
    get_frequency_bands,
    get_radius_from_chunk,
    update_frequency_bands,
)
from svg.audio_loader import load_wav_audio
from svg.video_producer import create_video_file, encode_frames_to_video, save_circle_frame

#  py -3.11 -m venv .venv
# .venv\Scripts\Activate.ps1

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None

        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tooltip:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20

        self.tooltip = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(tw, text=self.text)
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class SoundVisualisationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        print("UI running 2")
        self.title("Sound Visualisation Generator")
        # self.geometry("1100x700")

        self.audio_file = ""
        self.preview_image = None
        self.preview_tk = None

        self.is_playing = False
        self.is_animating = False
        self.controls_visible = True

        self.audio_data = None
        self.sample_rate = 0
        self.current_chunk = 0

        self.chunk_size = 512
        self.thickness = 0.9
        self.visual_mode = "circle"
        self.volume = 1.0
        self.modulation = 5

        self.frame_rate = 1

        self.record_frames = False
        self.frames_dir = ""
        self.frame_index = 0
        self.live_output_path = ""
        self.is_encoding = False
        self._generate_thread = None
        self._generate_done_event = None

        # pygame.mixer.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2)

        # Main window layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # Left frame = controls
        self.left_frame = ctk.CTkFrame(self, corner_radius=12)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Right frame = preview
        self.right_frame = ctk.CTkFrame(self, corner_radius=12)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.build_left_side()
        self.build_right_side()
        self.update_idletasks()

        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()

        self.geometry(f"{width}x{height}")
        self.minsize(width, height)

        self.previous_bands = None

    def build_left_side(self):
        title_label = ctk.CTkLabel(
            self.left_frame, text="Controls", font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(15, 20))

        self.select_button = ctk.CTkButton(
            self.left_frame, text="Select Audio File", command=self.select_audio
        )
        self.select_button.pack(padx=15, pady=10, fill="x")
        ToolTip(self.select_button, "Select a WAV audio file to generate visualisation")

        # self.start_button = ctk.CTkButton(self.left_frame, text="Play", command=self.play_audio)
        # self.start_button.pack(padx=15, pady=10, fill="x")

        self.file_label = ctk.CTkLabel(
            self.left_frame, text="No file selected", wraplength=250, justify="left"
        )
        self.file_label.pack(padx=15, pady=(0, 15))

        self.thickness_label = ctk.CTkLabel(self.left_frame, text="Thickness")
        self.thickness_label.pack(pady=(10, 0))

        self.thickness_slider = ctk.CTkSlider(
            self.left_frame, from_=0.1, to=1.5, command=self.update_thickness_value
        )

        self.thickness_slider.set(0.9)
        self.thickness_slider.pack(padx=15, pady=5, fill="x")

        self.thickness_value_label = ctk.CTkLabel(self.left_frame, text="1.0")
        self.thickness_value_label.pack(pady=(0, 10))

        self.volume_label = ctk.CTkLabel(self.left_frame, text="Volume")

        self.volume_label.pack(pady=(10, 0))

        self.volume_slider = ctk.CTkSlider(
            self.left_frame, from_=0.0, to=1.0, command=self.update_volume_value
        )

        self.volume_slider.set(1.0)
        self.volume_slider.pack(padx=15, pady=5, fill="x")

        self.volume_value_label = ctk.CTkLabel(self.left_frame, text="1.00")
        self.volume_value_label.pack(pady=(0, 10))

        self.modulation_label = ctk.CTkLabel(self.left_frame, text="Modulation")
        self.modulation_label.pack(pady=(10, 0))

        self.modulation_slider = ctk.CTkSlider(
            self.left_frame, from_=1, to=10, number_of_steps=9, command=self.update_modulation_value
        )

        self.modulation_slider.set(5)
        self.modulation_slider.pack(padx=15, pady=5, fill="x")

        self.modulation_value_label = ctk.CTkLabel(self.left_frame, text="5")
        self.modulation_value_label.pack(pady=(0, 10))

        self.colour_label = ctk.CTkLabel(self.left_frame, text="Colour Mode")
        self.colour_label.pack(pady=(10, 0))

        self.colour_menu = ctk.CTkOptionMenu(
            self.left_frame, values=["Red", "Green", "Cyan", "White"]
        )
        self.colour_menu.set("Red")
        self.colour_menu.pack(padx=15, pady=5, fill="x")
        ToolTip(self.colour_menu, "Choose colour scheme for the visualisation")

        self.visual_mode_label = ctk.CTkLabel(self.left_frame, text="Visualisation")
        self.visual_mode_label.pack(pady=(10, 0))

        self.visual_mode_menu = ctk.CTkOptionMenu(
            self.left_frame, values=["Spectrum", "Circle"], command=self.update_visual_mode
        )

        self.visual_mode_menu.set("Circle")
        self.visual_mode_menu.pack(padx=15, pady=5, fill="x")

        # (Generate button removed — video generation now triggered automatically by play)

        # Output file entry + browse button (used for both live recording and export)
        self.output_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.output_frame.pack(padx=15, pady=(10, 0), fill="x")

        self.output_entry = ctk.CTkEntry(
            self.output_frame, placeholder_text="Save video as...", width=200
        )
        self.output_entry.grid(row=0, column=0, sticky="ew")

        self.output_browse = ctk.CTkButton(
            self.output_frame, text="Browse", width=80, command=self.choose_output_path
        )
        self.output_browse.grid(row=0, column=1, padx=(8, 0))
        self.output_frame.grid_columnconfigure(0, weight=1)
        ToolTip(self.output_entry, "Specify output file path for generated video / live recording")

        self.record_live_var = tk.BooleanVar(value=True)
        self.record_live_switch = ctk.CTkSwitch(
            self.left_frame, text="Record while playing", variable=self.record_live_var
        )
        ToolTip(self.record_live_switch, "Toggle whether to record frames while playing audio")
        self.record_live_switch.pack(padx=15, pady=(5, 10), fill="x")

        self.status_label = ctk.CTkLabel(self.left_frame, text="Status: Waiting")
        self.status_label.pack(pady=(10, 5))

    def build_right_side(self):
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        preview_label = ctk.CTkLabel(
            self.right_frame, text="Preview", font=ctk.CTkFont(size=22, weight="bold")
        )
        preview_label.pack(pady=(15, 20))

        self.preview_box = tk.Canvas(self.right_frame, bg="#1a1a1a", highlightthickness=0)
        self.preview_box.pack(padx=20, pady=10, fill="both", expand=True)

        self.preview_box.configure(width=500, height=320)

        self.preview_controls_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.preview_controls_frame.pack(padx=20, pady=(0, 10), fill="x")

        self.preview_controls_frame.grid_columnconfigure(0, weight=1)
        self.preview_controls_frame.grid_columnconfigure(1, weight=1)

        self.start_button = ctk.CTkButton(
            self.preview_controls_frame, text="Play", command=self.play_audio
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.toggle_controls_button = ctk.CTkButton(
            self.preview_controls_frame,
            text="Hide Controls",
            command=self.toggle_controls,
        )
        self.toggle_controls_button.grid(row=0, column=1, padx=(10, 0), sticky="ew")

        # (Generate button removed — video generation now triggered automatically by play)

        self.output_label = ctk.CTkLabel(
            self.right_frame,
            text="Output file: Not generated yet",
            wraplength=450,
            justify="left",
        )
        self.output_label.pack(pady=(10, 15))

        self.progress_bar = ctk.CTkProgressBar(self.right_frame, width=450)
        self.progress_bar.pack(padx=20, pady=10, fill="x")
        self.progress_bar.set(0)

        self.num_bands = 32
        self.band_lines = []
        self.init_spectrum()

        self.progress_mode_label = ctk.CTkLabel(self.right_frame, text="Mode: Idle")
        self.progress_mode_label.pack(pady=(0, 10))

    def update_thickness_value(self, value):
        self.thickness = float(value)
        self.thickness_value_label.configure(text=f"{value:.2f}")

    def update_volume_value(self, value):
        self.volume = float(value)
        self.volume_value_label.configure(text=f"{value:.2f}")

        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.volume)

    def update_modulation_value(self, value):
        self.modulation = int(value)
        self.modulation_value_label.configure(text=f"{self.modulation}")

    def on_colour_change(self, _value):
        if self.is_animating and self.audio_data is not None:
            preview_chunk = max(0, self.current_chunk - self.chunk_size)
            radius, _ = get_radius_from_chunk(
                audio_data=self.audio_data,
                current_chunk=preview_chunk,
                chunk_size=self.chunk_size,
                min_radius=30,
                max_radius=120,
                scale=400,
            )
            if radius is not None:
                self.draw_circle(radius)

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

        # If user requested recording (generate video) but has not provided an
        # output path, do not start playback — force the user to set the path
        # or turn off the 'Record while playing' toggle.
        out_path = None
        try:
            out_path = self.output_entry.get().strip()
            if not out_path:
                out_path = self.live_output_path
        except Exception:
            out_path = self.live_output_path

        if self.record_live_var.get() and not out_path:
            self.status_label.configure(
                text="Status: Set output file or turn off recording to play"
            )
            self.progress_mode_label.configure(text="Mode: Preview disabled")
            return

        if not self.buffer_audio():
            return

        try:
            pygame.mixer.music.load(self.audio_file)
        except Exception:
            pass

        try:
            pygame.mixer.music.set_volume(self.volume)
        except Exception:
            pass

        try:
            pygame.mixer.music.play()
        except Exception:
            pass
        self.is_playing = True
        self.is_animating = True
        self.current_chunk = 0
        self.frame_rate = max(1, self.sample_rate // self.chunk_size)

        if self.record_live_var.get():
            self.start_live_recording()
        else:
            self.stop_live_recording(clear_only=True)

        # decide whether to animate preview: if recording is requested but not enabled
        # (e.g. no save path provided), suppress animation until user provides a path
        should_animate = True
        if self.record_live_var.get() and not self.record_frames:
            should_animate = False

        self.start_button.configure(text="Stop", command=self.stop_audio)
        if self.record_frames:
            self.status_label.configure(text="Status: Playing + recording")
            self.progress_mode_label.configure(text="Mode: Recording while playing")
        else:
            if not should_animate and self.record_live_var.get():
                self.status_label.configure(text="Status: Save path required — preview disabled")
                self.progress_mode_label.configure(text="Mode: Preview disabled")
            else:
                self.status_label.configure(text="Status: Playing audio")
                self.progress_mode_label.configure(text="Mode: Preview only")

        if should_animate:
            self.is_animating = True
            self.animate_from_audio()
        else:
            self.is_animating = False

        # start watching playback to detect natural end and trigger generation
        try:
            self.after(200, self.watch_playback)
        except Exception:
            pass

        # If user has specified an output path and is NOT recording live,
        # automatically generate the full video in a background thread.
        out_path = None
        try:
            out_path = self.output_entry.get().strip()
        except Exception:
            out_path = self.live_output_path

        if out_path and not self.record_live_var.get():
            # prepare generation tracking
            self._generate_done_event = threading.Event()

            def _generate():
                self.progress_mode_label.configure(text="Mode: Generating video")
                try:
                    create_video_file(
                        audio_file=self.audio_file,
                        output_file=out_path,
                        colour_mode=self.colour_menu.get(),
                        thickness=self.thickness,
                        modulation=self.modulation,
                    )

                    def _done():
                        self.output_label.configure(text=f"Output file: {out_path}")
                        self.progress_bar.set(1.0)
                        self.status_label.configure(text="Status: Generation complete")
                        self.progress_mode_label.configure(text="Mode: Generation complete")

                    self.after(0, _done)
                except Exception as e:

                    def _fail(_e=e):
                        self.progress_bar.set(0)
                        self.status_label.configure(text=f"Status: Generation failed: {_e}")
                        self.progress_mode_label.configure(text="Mode: Generation failed")

                    self.after(0, _fail)
                finally:
                    # signal generation finished
                    try:
                        self._generate_done_event.set()
                    except Exception:
                        pass

            thread = threading.Thread(target=_generate, daemon=True)
            self._generate_thread = thread
            thread.start()
        # delay audio to in sync with graphics
        # audio_delay_ms = 100
        # self.after(audio_delay_ms, pygame.mixer.music.play)

    def stop_audio(self):
        pygame.mixer.music.stop()

        self.is_playing = False
        self.is_animating = False

        self.start_button.configure(text="Play", command=self.play_audio)
        self.status_label.configure(text="Status: Audio stopped")
        self.progress_mode_label.configure(text="Mode: Idle")

        if self.record_frames:
            self.finish_live_recording()

        # If video generation is running in background, wait for it in a watcher
        if getattr(self, "_generate_thread", None) and self._generate_thread.is_alive():
            # inform user we're waiting for generation to finish
            self.status_label.configure(
                text="Status: Audio finished — waiting for video generation"
            )
            self.progress_mode_label.configure(text="Mode: Waiting for generation")

            def _watch():
                try:
                    # wait for the event if available, otherwise join thread
                    if getattr(self, "_generate_done_event", None) is not None:
                        self._generate_done_event.wait()
                    else:
                        self._generate_thread.join()
                except Exception:
                    pass

                def _on_done():
                    self.progress_bar.set(1.0)
                    self.output_label.configure(
                        text=f"Output file: {getattr(self, 'live_output_path', '') or ''}"
                    )
                    self.status_label.configure(text="Status: Generation complete")
                    self.progress_mode_label.configure(text="Mode: Generation complete")

                try:
                    self.after(0, _on_done)
                except Exception:
                    pass

            t = threading.Thread(target=_watch, daemon=True)
            t.start()

    def _start_background_generation(self, out_path):
        """Start background generation thread and track its completion."""
        # do not start twice
        if getattr(self, "_generate_thread", None) and self._generate_thread.is_alive():
            return

        self._generate_done_event = threading.Event()

        def _generate():
            self.progress_mode_label.configure(text="Mode: Generating video")
            try:
                create_video_file(
                    audio_file=self.audio_file,
                    output_file=out_path,
                    colour_mode=self.colour_menu.get(),
                    thickness=self.thickness,
                    modulation=self.modulation,
                )

                def _done():
                    self.output_label.configure(text=f"Output file: {out_path}")
                    self.progress_bar.set(1.0)
                    self.status_label.configure(text="Status: Generation complete")
                    self.progress_mode_label.configure(text="Mode: Generation complete")

                self.after(0, _done)
            except Exception as e:

                def _fail(_e=e):
                    self.progress_bar.set(0)
                    self.status_label.configure(text=f"Status: Generation failed: {_e}")
                    self.progress_mode_label.configure(text="Mode: Generation failed")

                self.after(0, _fail)
            finally:
                try:
                    self._generate_done_event.set()
                except Exception:
                    pass

        thread = threading.Thread(target=_generate, daemon=True)
        self._generate_thread = thread
        thread.start()

    def watch_playback(self):
        """Poll pygame mixer to detect natural end of playback and finalize generation."""
        if not getattr(self, "is_playing", False):
            return
        try:
            busy = pygame.mixer.music.get_busy()
        except Exception:
            busy = False

        if busy:
            # check again shortly
            try:
                self.after(200, self.watch_playback)
            except Exception:
                pass
            return

        # playback finished naturally — ensure generation started (if needed)
        out_path = None
        try:
            out_path = self.output_entry.get().strip()
            if not out_path:
                out_path = self.live_output_path
        except Exception:
            out_path = self.live_output_path

        if out_path and not self.record_live_var.get():
            # start generation if not already running
            self._start_background_generation(out_path)

        # then stop audio (updates UI and starts watcher for generation)
        try:
            self.stop_audio()
        except Exception:
            pass
        # self.clear_preview()

    def _ask_save_path(self, default_name="visualization.mp4"):
        """Open a Save As dialog and return the chosen path, or empty string if cancelled."""
        return filedialog.asksaveasfilename(
            title="Save Video As",
            initialfile=default_name,
            defaultextension=".mp4",
            filetypes=[("MP4 video", "*.mp4"), ("All files", "*.*")],
        )

    def choose_output_path(self):
        """Handler for the browse button next to the output entry."""
        save_path = self._ask_save_path("visualization.mp4")
        if not save_path:
            return
        self.live_output_path = save_path
        try:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, save_path)
        except Exception:
            pass
        self.status_label.configure(text=f"Status: Output path set: {os.path.basename(save_path)}")

    def generate_video(self):
        if self.audio_file == "":
            self.status_label.configure(text="Status: Please select an audio file")
            return

        scale = self.thickness_slider.get()
        speed = 1.0
        modulation = int(self.modulation_slider.get())
        colour = self.colour_menu.get()

        output_path = self._ask_save_path("visualization.mp4")
        if not output_path:
            self.status_label.configure(text="Status: Save cancelled")
            return

        self.status_label.configure(text="Status: Generating video...")
        self.progress_bar.set(0.2)
        self.progress_mode_label.configure(text="Mode: Generating video")

        self.preview_box.delete("all")
        self.preview_box.create_oval(
            150, 60, 350, 260, outline="cyan", width=int(5 * self.thickness)
        )

        self.progress_bar.set(0.75)

        output_path = "output/visualization.mp4"
        self.output_label.configure(text=f"Output file: {output_path}")

        self.progress_bar.set(1.0)
        self.status_label.configure(
            text=(
                f"Status: Generation complete | "
                f"Scale {scale:.1f}, Speed {speed:.1f}, "
                f"Modulation {modulation}, Colour {colour}"
            )
        )

        try:
            # Call the export function from video_producer.py
            try:
                create_video_file(
                    audio_file=self.audio_file,
                    output_file=output_path,
                    colour_mode=self.colour_menu.get(),
                    thickness=self.thickness,
                    modulation=self.modulation,
                )
            except TypeError:
                # Fall back for older/stubbed implementations that don't accept new kwargs
                create_video_file(self.audio_file, output_path, self.colour_menu.get())

            # If successful, update the GUI
            self.progress_bar.set(1.0)
            self.output_label.configure(text=f"Output file: {output_path}")
            self.status_label.configure(text="Status: Generation complete")
            self.progress_mode_label.configure(text="Mode: Generation complete")

        except Exception as e:
            # If something fails, show the error in the GUI and terminal
            self.progress_bar.set(0)
            self.status_label.configure(text=f"Status: Generation failed: {e}")
            self.progress_mode_label.configure(text="Mode: Generation failed")
            print("generate_video error:", e)

    def toggle_controls(self):
        if self.controls_visible:
            self.left_frame.grid_remove()
            self.grid_columnconfigure(0, weight=0)
            self.grid_columnconfigure(1, weight=1)
            self.toggle_controls_button.configure(text="Show Controls")
            self.controls_visible = False
        else:
            self.left_frame.grid()
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=3)
            self.toggle_controls_button.configure(text="Hide Controls")
            self.controls_visible = True

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

        self.preview_box.update_idletasks()

        canvas_width = self.preview_box.winfo_width()
        canvas_height = self.preview_box.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 500
            canvas_height = 320

        cx = canvas_width // 2
        cy = canvas_height // 2

        noise_amount = self.get_noise_amount()
        t = time.perf_counter()

        radius_wobble = math.sin(t * 4.0) * noise_amount * 10
        radius = radius + radius_wobble

        base_width = 10 * self.thickness
        width_wobble = math.sin(t * 8.0) * noise_amount * 4
        line_width = max(1, int(base_width + width_wobble))

        self.preview_box.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            outline=self.get_visual_colour(),
            width=line_width,
        )

    def get_selected_colour_hex(self):
        colour_map = {
            "Blue": "#00B7FF",
            "Purple": "#BB86FC",
            "Grayscale": "#D0D0D0",
        }
        return colour_map.get(self.colour_menu.get(), "#00B7FF")

    def start_live_recording(self):
        # Use pre-set output path if available, otherwise prompt the user
        save_path = self.live_output_path or self._ask_save_path("live_visualization.mp4")
        if not save_path:
            # user cancelled or no path set; do not record
            self.record_frames = False
            self.status_label.configure(text="Status: Save cancelled — playing preview only")
            self.progress_mode_label.configure(text="Mode: Preview only")
            return

        self.live_output_path = save_path
        # ensure entry reflects chosen path
        try:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, save_path)
        except Exception:
            pass

        self.frames_dir = tempfile.mkdtemp(prefix="live_frames_")
        self.frame_index = 0
        self.record_frames = True
        self.progress_bar.set(0)
        self.progress_mode_label.configure(text="Mode: Recording while playing")

    def stop_live_recording(self, clear_only=False):
        self.record_frames = False
        self.frame_index = 0
        if clear_only and self.frames_dir:
            shutil.rmtree(self.frames_dir, ignore_errors=True)
            self.frames_dir = ""

    def finish_live_recording(self):
        if not self.frames_dir:
            self.stop_live_recording(clear_only=True)
            return

        if self.frame_index == 0:
            self.stop_live_recording(clear_only=True)
            self.status_label.configure(text="Status: No live frames captured")
            return

        frames_dir = self.frames_dir
        frame_rate = self.frame_rate

        self.record_frames = False
        self.frames_dir = ""
        self.frame_index = 0
        self.is_encoding = True
        self.status_label.configure(text="Status: Encoding live video...")
        self.progress_mode_label.configure(text="Mode: Encoding live recording")

        thread = threading.Thread(
            target=self._encode_live_video,
            args=(frames_dir, frame_rate),
            daemon=True,
        )
        thread.start()

    def _encode_live_video(self, frames_dir, frame_rate):
        try:
            encode_frames_to_video(
                frames_dir=frames_dir,
                audio_file=self.audio_file,
                output_file=self.live_output_path,
                frame_rate=frame_rate,
            )

            def on_success():
                self.is_encoding = False
                self.progress_bar.set(1.0)
                self.output_label.configure(text=f"Output file: {self.live_output_path}")
                self.status_label.configure(text="Status: Live recording complete")
                self.progress_mode_label.configure(text="Mode: Live export complete")

            self.after(0, on_success)
        except Exception as e:
            error_message = str(e)

            def on_failure():
                self.is_encoding = False
                self.progress_bar.set(0)
                self.status_label.configure(text=f"Status: Live export failed: {error_message}")
                self.progress_mode_label.configure(text="Mode: Live export failed")

            self.after(0, on_failure)
        finally:
            shutil.rmtree(frames_dir, ignore_errors=True)

    def animate_from_audio(self):

        if self.audio_data is None or not self.is_animating:
            print("animate not working, no audio data")
            return

        if self.visual_mode == "circle":
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
            # record frame if requested
            if self.record_frames and self.frames_dir:
                frame_path = os.path.join(self.frames_dir, f"frame_{self.frame_index:05d}.png")
                save_circle_frame(
                    frame_path=frame_path,
                    radius=int(radius),
                    colour=self.get_selected_colour_hex(),
                )
                self.frame_index += 1

            self.current_chunk = next_chunk

            if self.record_frames and self.audio_data is not None and len(self.audio_data) > 0:
                progress = min(1.0, self.current_chunk / len(self.audio_data))
                self.progress_bar.set(progress)

            delay_ms = get_delay_ms(self.chunk_size, self.sample_rate)
            self.after(delay_ms, self.animate_from_audio)

        if self.visual_mode == "spectrum":
            # print(self.chunk_size)
            start = self.current_chunk
            end = start + self.chunk_size

            if start >= len(self.audio_data):
                self.is_animating = False
                self.is_playing = False
                self.start_button.configure(text="Play", command=self.play_audio)
                self.status_label.configure(text="Status: Animation complete")
                return

            chunk = self.audio_data[start:end]

            if len(chunk) == 0:
                self.is_animating = False
                self.is_playing = False
                self.start_button.configure(text="Play", command=self.play_audio)
                return

            bands = get_frequency_bands(
                chunk=chunk, sample_rate=self.sample_rate, num_bands=self.num_bands
            )

            if self.previous_bands is None:
                smoothed = bands
            else:
                # smoothed = bands
                smoothed = 0.5 * self.previous_bands + 0.5 * bands

            self.previous_bands = smoothed

            update_frequency_bands(self, smoothed)

            self.current_chunk += self.chunk_size

            delay_ms = max(1, int((self.chunk_size / self.sample_rate) * 1000))
            # delay_ms = 22 # optimization test
            self.after(delay_ms, self.animate_from_audio)

    def get_visual_colour(self):
        colour = self.colour_menu.get()

        if colour == "Red":
            return "red"
        elif colour == "Green":
            return "lime"
        elif colour == "Cyan":
            return "cyan"
        elif colour == "White":
            return "white"

        return "cyan"

    def update_visual_mode(self, value):
        self.visual_mode = value.lower()
        self.preview_box.delete("all")

        if self.visual_mode == "spectrum":
            self.init_spectrum()

    def init_spectrum(self):
        self.band_lines = []

        canvas_width = 500
        canvas_height = 320
        baseline_y = canvas_height // 2
        band_width = canvas_width / self.num_bands

        for i in range(self.num_bands):
            x = i * band_width + band_width / 2

            line = self.preview_box.create_line(
                x,
                baseline_y,
                x,
                baseline_y,
                fill=self.get_visual_colour(),
                width=int(band_width * self.thickness),
            )

            self.band_lines.append(line)

    def get_noise_amount(self):
        return (self.modulation - 1) / 9.0

    def start_audio_visual(self):
        self.is_animating = True
        self.current_chunk = 0
        self.status_label.configure(text="Status: Animating from audio")
        self.animate_from_audio()


if __name__ == "__main__":
    app = SoundVisualisationApp()
    app.mainloop()
