import io
import os
import zipfile
from dotenv import load_dotenv

from flask import Flask, request, render_template, flash, redirect, send_file
from downloader import download_video, download_audio
from converter import video_to_audio, audio_to_wav, convert_image_format

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

BASE_OUTPUT_DIR = os.environ.get('BASE_OUTPUT_DIR', 'output')
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

for directory in ['uploads', 'output']:
    os.makedirs(directory, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form_type = request.form.get("form_type")
        output_folder = request.form.get("output_folder", "default").strip()  # Set default folder if none provided

        # Create a timestamped folder name if none provided
        if not output_folder or output_folder == "default":
            from datetime import datetime
            output_folder = datetime.now().strftime("%Y%m%d_%H%M%S")

        final_output = os.path.join(BASE_OUTPUT_DIR, output_folder)
        os.makedirs(final_output, exist_ok=True)

        try:
            if form_type == "yt_download":
                url = request.form.get("url")
                option = request.form.get("yt_option")
                if option == "video":
                    filename = download_video(url, final_output)
                elif option == "audio":
                    filename = download_audio(url, final_output)
                flash(f"✅ Download complete! Your file is ready: {filename}", "success")
                return redirect(f"/downloads/{output_folder}")  # Redirect to downloads page

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
                    img_format = option.split("img2")[1]
                    convert_image_format(save_path, final_output, img_format, custom_name)

                flash("✅ Conversion complete!", "success")
        except Exception as e:
            flash(f"❌ Error: {e}", "danger")

        return redirect("/")

    return render_template("index.html")


@app.route("/downloads/<folder>")
def list_downloads(folder):
    folder_path = os.path.join(BASE_OUTPUT_DIR, folder)

    if not os.path.exists(folder_path):
        flash("❌ Folder not found!", "danger")
        return redirect("/")

    files = os.listdir(folder_path)
    return render_template("downloads.html", files=files, folder=folder)


@app.route('/download', methods=['POST'])
def download_file():
    folder = request.form.get("folder")
    filename = request.form.get("filename")

    if not folder or not filename:
        flash("❌ Missing folder or filename.", "danger")
        return redirect("/")

    filepath = os.path.join(BASE_OUTPUT_DIR, folder, filename)

    if not os.path.exists(filepath):
        flash("❌ File not found.", "danger")
        return redirect(f"/downloads/{folder}")

    try:
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename  # Ensure proper filename
        )
    except Exception as e:
        flash(f"❌ Download failed: {str(e)}", "danger")
        return redirect(f"/downloads/{folder}")

@app.route('/download_zip', methods=['POST'])
def download_zip():
    folder = request.form.get("folder")
    if not folder:
        flash("❌ Folder name missing.", "danger")
        return redirect("/")

    folder_path = os.path.join(BASE_OUTPUT_DIR, folder)
    if not os.path.exists(folder_path):
        flash("❌ Folder not found.", "danger")
        return redirect("/")

    # Create in-memory zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            zip_file.write(file_path, arcname=filename)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        download_name=f"{folder}.zip",
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(debug=True)
