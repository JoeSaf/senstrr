import os
import json
import re
import subprocess
from flask import Flask, render_template, send_file, request, jsonify, redirect, url_for, abort

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
    return render_template("index.html", files=files, current_path=path, parent=parent)


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
                # Convert MKV → MP4
                if filepath.lower().endswith(".mkv"):
                    mp4_path = filepath.rsplit(".", 1)[0] + ".mp4"
                    try:
                        subprocess.run(
                            ["ffmpeg", "-y", "-i", filepath, "-c", "copy", "-movflags", "+faststart", mp4_path],
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        os.remove(filepath)
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

    # Gather available subtitles for this video (show original files, don't convert yet)
    base = os.path.splitext(os.path.join(MEDIA_ROOT, path))[0]
    subs = []
    
    # Get the directory of the video
    video_dir = os.path.dirname(os.path.join(MEDIA_ROOT, path))
    video_basename = os.path.basename(base)
    
    if os.path.exists(video_dir):
        for file in os.listdir(video_dir):
            if file.startswith(video_basename):
                ext = os.path.splitext(file)[1].lower()
                if ext in [".srt", ".vtt"]:
                    subs.append({
                        "label": file,  # Show original filename
                        "src": os.path.relpath(os.path.join(video_dir, file), MEDIA_ROOT),
                        "ext": ext[1:]  # Store extension for client-side logic
                    })

    return render_template(
        "watch.html",
        video_path=path,
        resume_time=resume_time,
        next_ep=next_ep,
        subtitles=subs
    )


# -------------------------
# Video Streaming
# -------------------------
@app.route("/stream/<path:path>")
def stream(path):
    full = os.path.join(MEDIA_ROOT, path)
    return send_file(full, conditional=True)


# -------------------------
# New route: Convert SRT to VTT on-demand
# -------------------------
@app.route("/subs/convert/<path:path>")
def convert_subtitle(path):
    """Convert SRT to VTT on-demand and serve it"""
    full = os.path.join(MEDIA_ROOT, path)
    
    # Check if file exists
    if not os.path.exists(full):
        abort(404)
    
    # If it's already VTT, serve directly
    if full.lower().endswith('.vtt'):
        return send_file(full, mimetype="text/vtt")
    
    # If it's SRT, convert to VTT on-the-fly
    if full.lower().endswith('.srt'):
        # Create temporary VTT file path with unique identifier
        import time
        temp_id = f"{int(time.time())}_{os.getpid()}"
        vtt_file = full.rsplit('.', 1)[0] + f'_temp_{temp_id}.vtt'
        
        try:
            # Convert SRT to VTT using ffmpeg
            subprocess.run(
                ["ffmpeg", "-y", "-i", full, vtt_file],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Send the converted file
            response = send_file(vtt_file, mimetype="text/vtt")
            
            # Clean up after sending
            @response.call_on_close
            def cleanup():
                if os.path.exists(vtt_file):
                    try:
                        os.remove(vtt_file)
                    except:
                        pass  # Ignore cleanup errors
            
            return response
        except subprocess.CalledProcessError:
            # Clean up temp file if it exists
            if os.path.exists(vtt_file):
                try:
                    os.remove(vtt_file)
                except:
                    pass
            abort(500)
    
    abort(404)


# -------------------------
# Legacy subtitle route (keep for backward compatibility)
# -------------------------
@app.route("/subs/<path:path>")
def subs(path):
    full = os.path.join(MEDIA_ROOT, path)
    if os.path.exists(full):
        # If it's a VTT file, serve directly
        if full.lower().endswith('.vtt'):
            return send_file(full, mimetype="text/vtt")
        # If it's an SRT file, redirect to converter
        elif full.lower().endswith('.srt'):
            return redirect(url_for('convert_subtitle', path=path))
    abort(404)


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