from moviepy.editor import VideoFileClip, AudioFileClip
import os
from PIL import Image

def video_to_audio(video_path, output_dir, output_filename=None):
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        base_name = output_filename or os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.mp3")
        audio.write_audiofile(output_path)
        print(f"[✔] Audio saved to: {output_path}")
    except Exception as e:
        print(f"[✘] Error converting video: {e}")

def audio_to_wav(audio_path, output_dir, output_filename=None):
    try:
        audio = AudioFileClip(audio_path)
        base_name = output_filename or os.path.splitext(os.path.basename(audio_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.wav")
        audio.write_audiofile(output_path)
        print(f"[✔] Audio saved to: {output_path}")
    except Exception as e:
        print(f"[✘] Error converting audio: {e}")

def convert_image_format(image_path, output_dir, output_format, output_filename=None):
    try:
        image = Image.open(image_path)
        base_name = output_filename or os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.{output_format.lower()}")
        image.save(output_path, output_format.upper())
        print(f"[✔] Image converted and saved to: {output_path}")
    except Exception as e:
        print(f"[✘] Error converting image: {e}")
        raise e
