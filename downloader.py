import yt_dlp
import os

OUTPUT_DIR = 'output'  # Default output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_video(url, output_path=OUTPUT_DIR):
    try:
        print("\n🔽 Downloading video...")
        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("✅ Video download complete!\n")
    except Exception as e:
        print(f"❌ Error downloading video: {e}")

def download_audio(url, output_path=OUTPUT_DIR):
    try:
        print("\n🎵 Downloading audio...")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("✅ Audio download complete!\n")
    except Exception as e:
        print(f"❌ Error downloading audio: {e}")
