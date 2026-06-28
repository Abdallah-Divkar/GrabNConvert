"""
### downloader.py
"""
import yt_dlp
import os

COOKIES_FILE = os.path.abspath(os.getenv("COOKIES_FILE", "cookies.txt"))

# Make node.exe visible to yt-dlp if not already on PATH
if not os.environ.get("NODE"):
    node_path = r"C:\Program Files\nodejs\node.exe"
    if os.path.exists(node_path):
        os.environ["NODE"] = node_path

def _base_opts(output_path):
    opts = {'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s')}
    if os.path.exists(COOKIES_FILE):
        print(f"[cookies] Using: {COOKIES_FILE}")
        opts['cookiefile'] = COOKIES_FILE
    else:
        print(f"[cookies] NOT FOUND: {COOKIES_FILE}")
    return opts

def download_audio(url, output_path):
    ydl_opts = {
        **_base_opts(output_path),
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'extractor_args': {'youtube': {'player_client': ['android_vr']}},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_video(url, output_path):
    ydl_opts = {
        **_base_opts(output_path),
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'extractor_args': {'youtube': {'player_client': ['android_vr']}},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

'''def download_video(url, output_path):
    try:
        print("\n🔽 Downloading video...")
        filename = None
        
        def get_filename(d):
            if d['status'] == 'finished':
                nonlocal filename
                filename = os.path.basename(d['filename'])
                
        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'progress_hooks': [get_filename]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("✅ Video download complete!\n")
        return filename

    except Exception as e:
        print(f"❌ Error downloading video: {e}")
        raise

def download_audio(url, output_path):
    try:
        print("\n🎵 Downloading audio...")
        filename = None
        
        def get_filename(d):
            if d['status'] == 'finished':
                nonlocal filename
                # Get the final filename after conversion to mp3
                filename = os.path.splitext(os.path.basename(d['filename']))[0] + '.mp3'
                
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [get_filename]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("✅ Audio download complete!\n")
        return filename

    except Exception as e:
        print(f"❌ Error downloading audio: {e}")
        raise'''
