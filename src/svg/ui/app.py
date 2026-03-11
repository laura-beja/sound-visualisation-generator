import customtkinter as ctk
from tkinter import filedialog
from PIL import Image


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SoundVisualisationApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sound Visualisation Generator")
        self.geometry("1100x700")
        

        self.audio_file = ""
        self.preview_image = None

        # Main window layout
        self.grid_columnconfigure(0, weight=1)   # left side
        self.grid_columnconfigure(1, weight=2)   # right side
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
            self.left_frame,
            text="Controls",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(15, 20))

        self.select_button = ctk.CTkButton(
            self.left_frame,
            text="Select Audio File",
            command=self.select_audio
        )
        self.select_button.pack(padx=15, pady=10, fill="x")

        self.file_label = ctk.CTkLabel(
            self.left_frame,
            text="No file selected",
            wraplength=250,
            justify="left"
        )
        self.file_label.pack(padx=15, pady=(0, 15))

        self.scale_label = ctk.CTkLabel(self.left_frame, text="Scale")
        self.scale_label.pack(pady=(10, 0))

        self.scale_slider = ctk.CTkSlider(
            self.left_frame,
            from_=1,
            to=100,
            command=self.update_scale_value
        )
        self.scale_slider.set(1.0)
        self.scale_slider.pack(padx=15, pady=5, fill="x")

        self.scale_value_label = ctk.CTkLabel(self.left_frame, text="1.0")
        self.scale_value_label.pack(pady=(0, 10))

        self.speed_label = ctk.CTkLabel(self.left_frame, text="Speed")
        self.speed_label.pack(pady=(10, 0))

        self.speed_slider = ctk.CTkSlider(
            self.left_frame,
            from_=1,
            to=10,
            command=self.update_speed_value
        )
        self.speed_slider.set(1.0)
        self.speed_slider.pack(padx=15, pady=5, fill="x")

        self.speed_value_label = ctk.CTkLabel(self.left_frame, text="1.0")
        self.speed_value_label.pack(pady=(0, 10))

        self.detail_label = ctk.CTkLabel(self.left_frame, text="Detail")
        self.detail_label.pack(pady=(10, 0))

        self.detail_slider = ctk.CTkSlider(
            self.left_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            command=self.update_detail_value
        )
        self.detail_slider.set(5)
        self.detail_slider.pack(padx=15, pady=5, fill="x")

        self.detail_value_label = ctk.CTkLabel(self.left_frame, text="5")
        self.detail_value_label.pack(pady=(0, 10))

        self.colour_label = ctk.CTkLabel(self.left_frame, text="Colour Mode")
        self.colour_label.pack(pady=(10, 0))

        self.colour_menu = ctk.CTkOptionMenu(
            self.left_frame,
            values=["Blue", "Purple", "Grayscale"]
        )
        self.colour_menu.set("Blue")
        self.colour_menu.pack(padx=15, pady=5, fill="x")

        self.generate_button = ctk.CTkButton(
            self.left_frame,
            text="Generate Video",
            command=self.generate_video
        )
        self.generate_button.pack(padx=15, pady=(25, 10), fill="x")

        self.status_label = ctk.CTkLabel(
            self.left_frame,
            text="Status: Waiting"
        )
        self.status_label.pack(pady=(10, 5))

    def build_right_side(self):
        preview_label = ctk.CTkLabel(
            self.right_frame,
            text="Preview",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        preview_label.pack(pady=(15, 20))

        # Placeholder preview area
        self.preview_box = ctk.CTkLabel(
            self.right_frame,
            text="Preview image will appear here",
            width=500,
            height=320,
            corner_radius=10
        )
        self.preview_box.pack(padx=20, pady=10)

        self.output_label = ctk.CTkLabel(
            self.right_frame,
            text="Output file: Not generated yet",
            wraplength=450,
            justify="left"
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
            title="Select Audio File",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )

        if file_path:
            self.audio_file = file_path
            self.file_label.configure(text=file_path)
            self.status_label.configure(text="Status: Audio selected")

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

        # Placeholder preview text for now
        preview_text = (
            "Preview image will appear here\n\n"
            f"Audio file selected\n"
            f"Scale: {scale:.1f}\n"
            f"Speed: {speed:.1f}\n"
            f"Detail: {detail}\n"
            f"Colour: {colour}"
        )
        self.preview_box.configure(text=preview_text)

        self.progress_bar.set(0.75)

        output_path = "output/visualization.mp4"
        self.output_label.configure(text=f"Output file: {output_path}")

        self.progress_bar.set(1.0)
        self.status_label.configure(text="Status: Generation complete")

    def load_preview_image(self, image_path):
        image = Image.open(image_path)
        self.preview_image = ctk.CTkImage(light_image=image, dark_image=image, size=(500, 320))
        self.preview_box.configure(text="", image=self.preview_image)