import os
import json
import re
import subprocess
from flask import Flask, render_template, send_file, request, jsonify, redirect, url_for

app = Flask(__name__)

MEDIA_ROOT = os.path.expanduser("~/movies")
PROGRESS_FILE = "progress.json"


# -------------------------
# Progress Handling
# -------------------------

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}


def save_progress(data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)


# -------------------------
# Sorting Episodes Properly
# -------------------------

def natural_sort(files):

    def convert(text):
        return int(text) if text.isdigit() else text.lower()

    def key(key):
        return [convert(c) for c in re.split('([0-9]+)', key)]

    return sorted(files, key=key)


# -------------------------
# File Browser
# -------------------------

def get_files(path):

    full = os.path.join(MEDIA_ROOT, path)
    items = []

    for name in os.listdir(full):
        items.append({
            "name": name,
            "is_dir": os.path.isdir(os.path.join(full, name))
        })

    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return items


# -------------------------
# Next Episode Detection
# -------------------------

def get_next_episode(current):

    folder = os.path.dirname(current)
    full = os.path.join(MEDIA_ROOT, folder)

    files = [f for f in os.listdir(full) if not os.path.isdir(os.path.join(full, f))]
    files = natural_sort(files)

    current_name = os.path.basename(current)

    for i, f in enumerate(files):
        if f == current_name and i + 1 < len(files):
            return os.path.join(folder, files[i + 1])

    return None


# -------------------------
# List All Folders
# -------------------------

def get_all_folders():

    folders = []

    for root, dirs, files in os.walk(MEDIA_ROOT):
        for d in dirs:
            folders.append(os.path.relpath(os.path.join(root, d), MEDIA_ROOT))

    folders.sort()

    return folders


# -------------------------
# Browse Media Library
# -------------------------

@app.route("/", defaults={"path": ""})
@app.route("/browse/<path:path>")
def browse(path=""):

    full = os.path.join(MEDIA_ROOT, path)

    if not os.path.exists(full):
        return "Not found"

    files = get_files(path)
    parent = os.path.dirname(path)

    return render_template(
        "index.html",
        files=files,
        current_path=path,
        parent=parent
    )


# -------------------------
# Upload Page
# -------------------------

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "POST":

        files = request.files.getlist("file")
        folder = request.form.get("folder", "")

        save_path = os.path.join(MEDIA_ROOT, folder)
        os.makedirs(save_path, exist_ok=True)

        for file in files:
            if file and file.filename:
                filepath = os.path.join(save_path, file.filename)
                file.save(filepath)

                # If the uploaded file is MKV, convert to MP4 and remove original
                if filepath.lower().endswith(".mkv"):
                    mp4_path = filepath.rsplit(".", 1)[0] + ".mp4"
                    try:
                        # Lossless conversion if possible (-c copy)
                        subprocess.run(
                            ["ffmpeg", "-y", "-i", filepath, "-c", "copy", mp4_path],
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        os.remove(filepath)  # remove original MKV
                    except subprocess.CalledProcessError:
                        print(f"Failed to convert {filepath}")

        return redirect(url_for("upload"))

    folders = get_all_folders()
    return render_template("upload.html", folders=folders)


# -------------------------
# Create Folder / Subfolder
# -------------------------

@app.route("/create_folder", methods=["POST"])
def create_folder():

    parent = request.form.get("parent", "")
    name = request.form.get("name")

    if not name:
        return redirect(url_for("upload"))

    path = os.path.join(MEDIA_ROOT, parent, name)
    os.makedirs(path, exist_ok=True)

    return redirect(url_for("upload"))


# -------------------------
# Watch Video Page
# -------------------------

@app.route("/watch/<path:path>")
def watch(path):

    progress = load_progress()
    resume_time = progress.get(path, 0)

    next_ep = get_next_episode(path)

    return render_template(
        "watch.html",
        video_path=path,
        resume_time=resume_time,
        next_ep=next_ep
    )


# -------------------------
# Video Streaming
# -------------------------

@app.route("/stream/<path:path>")
def stream(path):

    full = os.path.join(MEDIA_ROOT, path)
    return send_file(full, conditional=True)


# -------------------------
# Save Playback Progress
# -------------------------

@app.route("/save_progress", methods=["POST"])
def save():

    data = request.json
    progress = load_progress()
    progress[data["video"]] = data["time"]
    save_progress(progress)

    return jsonify({"status": "ok"})


# -------------------------
# Run Server
# -------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)