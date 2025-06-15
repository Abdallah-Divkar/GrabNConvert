import os
from flask import Flask, request, render_template, flash, redirect, send_from_directory
from downloader import download_video, download_audio
from converter import video_to_audio, audio_to_wav, convert_image_format

app = Flask(__name__)
app.secret_key = 'your_secret_key'

BASE_OUTPUT_DIR = 'output'
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form_type = request.form.get("form_type")
        output_folder = request.form.get("output_folder", "").strip()
        final_output = os.path.join(BASE_OUTPUT_DIR, output_folder) if output_folder else BASE_OUTPUT_DIR
        os.makedirs(final_output, exist_ok=True)

        try:
            if form_type == "yt_download":
                url = request.form.get("url")
                option = request.form.get("yt_option")
                if option == "video":
                    download_video(url, final_output)
                elif option == "audio":
                    download_audio(url, final_output)
                flash("✅ Download complete!", "success")

            elif form_type == "convert_file":
                file = request.files.get("file")
                filename = file.filename
                save_path = os.path.join("uploads", filename)
                file.save(save_path)

                option = request.form.get("convert_option")
                custom_name = request.form.get("filename").strip() or None

                if option == "v2a":
                    video_to_audio(save_path, final_output, custom_name)
                elif option == "a2wav":
                    audio_to_wav(save_path, final_output, custom_name)
                elif option.startswith("img2"):
                    img_format = option.split("img2")[1]  # e.g., png, jpg, etc.
                    convert_image_format(save_path, final_output, img_format, custom_name)

                flash("✅ Conversion complete!", "success")
        except Exception as e:
            flash(f"❌ Error: {e}", "danger")

        return redirect("/")

    return render_template("index.html")

@app.route("/downloads")
def list_downloads():
    files = os.listdir(BASE_OUTPUT_DIR)
    return render_template("downloads.html", files=files)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(BASE_OUTPUT_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
