"""
### app.py
"""
import io
import os
import zipfile
from flask import Flask, request, render_template, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from downloader import download_video, download_audio
from converter import video_to_audio, audio_to_wav, convert_image_format

app = Flask(__name__)
#app.secret_key = os.environ["SECRET_KEY"]
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

BASE_OUTPUT_DIR = os.path.abspath(os.getenv("BASE_OUTPUT_DIR", "output"))
UPLOAD_DIR = os.path.abspath(os.getenv("UPLOAD_FOLDER", "uploads"))
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form_type = request.form.get("form_type")
        folder = request.form.get("output_folder", "").strip()

        if not folder:
            flash("Please enter an output folder name before proceeding.", "danger")
            return redirect(url_for("index"))

        output_dir = os.path.join(BASE_OUTPUT_DIR, secure_filename(folder))
        os.makedirs(output_dir, exist_ok=True)

        try:
            if form_type == "yt_download":
                url = request.form.get("url")
                option = request.form.get("yt_option")
                if option == "video":
                    download_video(url, output_dir)
                elif option == "audio":
                    download_audio(url, output_dir)
                #flash("✅ Download complete!", "success")

            elif form_type == "convert_file":
                file = request.files.get("file")
                if not file or not file.filename:
                    raise ValueError("No file uploaded")

                filename = secure_filename(file.filename)
                saved_path = os.path.join(UPLOAD_DIR, filename)
                file.save(saved_path)

                option = request.form.get("convert_option")
                custom_name = request.form.get("filename") or None

                if option == "v2a":
                    video_to_audio(saved_path, output_dir, custom_name)
                elif option == "a2wav":
                    audio_to_wav(saved_path, output_dir, custom_name)
                elif option.startswith("img2"):
                    convert_image_format(
                        saved_path,
                        output_dir,
                        option.replace("img2", ""),
                        custom_name
                    )

            flash("Conversion complete!", "success")
            return redirect(url_for("downloads", folder=folder))

        except Exception as e:
            flash(str(e), "danger")
            return redirect(url_for("index"))

        finally:
            if form_type == "convert_file":
                try:
                    if os.path.exists(saved_path):
                        os.remove(saved_path)
                except UnboundLocalError:
                    pass

    return render_template("index.html")


@app.route("/downloads/<folder>")
def downloads(folder):
    folder_path = os.path.join(BASE_OUTPUT_DIR, secure_filename(folder))

    if not os.path.exists(folder_path):
        flash("Folder not found!", "danger")
        return redirect(url_for("index"))

    files = sorted(os.listdir(folder_path))
    return render_template("downloads.html", files=files, folder=folder)

@app.route('/download', methods=['POST'])
def download_file():
    folder = request.form.get("folder")
    filename = request.form.get("filename")

    path = os.path.join(BASE_OUTPUT_DIR, folder, filename)
    if not os.path.exists(path):
        flash("File not found.", "danger")
        return redirect(url_for("downloads", folder=folder))

    return send_file(path, as_attachment=True)

@app.route('/download_zip', methods=['POST'])
def download_zip():
    folder = secure_filename(request.form.get("folder"))
    folder_path = os.path.join(BASE_OUTPUT_DIR, folder)

    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for f in os.listdir(folder_path):
            z.write(os.path.join(folder_path, f), arcname=f)

    mem_zip.seek(0)
    return send_file(mem_zip, download_name=f"{folder}.zip", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)