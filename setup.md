# **Senstr Setup & Usage Guide**

**Project:** Senstr – Python Flask Movie Streaming & Upload Platform

**Purpose:**

* Stream movies and series from your server
* Upload videos (MKV auto-converted to MP4)
* Resume playback, next-episode autoplay
* Multi-device friendly (desktop, mobile, tablet)
* Folder/subfolder management for series/seasons

---

## **1️⃣ Prerequisites**

* **Python 3.10+** (3.11 recommended)
* **pip** (Python package manager)
* **Flask** (`pip install flask`)
* **FFmpeg** – required for MKV → MP4 conversion

**Install FFmpeg (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install ffmpeg -y
```

**Check installation:**

```bash
ffmpeg -version
```

> FFmpeg is used automatically when uploading MKV files. It **converts them to MP4** losslessly if the codecs are compatible. Original MKV files are deleted to save space.

**Optional: Create a Python virtual environment**

```bash
python3 -m venv senstr-env
source senstr-env/bin/activate
pip install flask
```

---

## **2️⃣ Project Structure**

```text
senstr/
├── app.py                  # Main Flask application
├── progress.json           # Playback progress storage (auto-created)
├── templates/
│   ├── index.html          # Library browse page
│   ├── upload.html         # Upload & folder management page
│   └── watch.html          # Video playback page
├── static/
│   └── style.css           # UI styles
└── movies/                 # Root media folder (default ~/movies)
```

* **MEDIA_ROOT** in `app.py` points to `~/movies`
* All uploaded videos are saved here
* MKV files are **automatically converted to MP4**

---

## **3️⃣ Installing Dependencies**

Inside the project directory:

```bash
pip install flask
```

Make sure **ffmpeg is installed** as described above.

---

## **4️⃣ Running the Server**

Navigate to the project folder and run:

```bash
python app.py
```

* Server runs at:

```text
http://0.0.0.0:5000
```

* Accessible on your network by IP (e.g., `http://192.168.1.110:5000`).

---

## **5️⃣ Uploading Videos**

1. Go to `http://<server-ip>:5000/upload`
2. Select the **destination folder** or create a new folder/subfolder
3. Select **one or multiple videos** (MKV supported)
4. Click **Upload**

**Behavior:**

* MKV files are automatically converted to **MP4 (lossless if compatible)**
* Original MKV files are **deleted**
* **Progress bars** show upload status in real-time

> ⚠️ Make sure FFmpeg is installed; conversion depends on it.

---

## **6️⃣ Browsing Media**

* Go to `http://<server-ip>:5000/`
* Navigate folders to find series/movies
* Click a video to watch

**Features:**

* Resume playback from last watched position
* Next episode autoplay
* Fullscreen, pause/play (space), 10s forward/backward, mute
* Mobile, tablet, and desktop friendly

---

## **7️⃣ Creating Folders/Subfolders**

1. On **Upload page**, scroll to **Create Folder** section
2. Select **Parent Folder**
3. Enter **New Folder Name**
4. Click **Create Folder**

Organize like:

```text
SeriesName/
├── Season1/
├── Season2/
```

---

## **8️⃣ Supported Video Formats**

* **MP4 (H.264 + AAC)** – fully browser compatible
* **MKV** – automatically converted to MP4 (lossless if possible)
* **Other formats** – may require manual conversion to MP4

---

## **9️⃣ Notes & Tips**

* **Storage:** Video files can be large; monitor disk space.
* **Backup progress.json** for playback history.
* **ffmpeg logs** are suppressed; check server console if conversions fail.
* **Folder structure recommendation:**

```text
~/movies/
└── BreakingBad/
    ├── Season1/
    │   ├── S01E01.mp4
    │   └── S01E02.mp4
    └── Season2/
        ├── S02E01.mp4
```

* **Security:** Designed for trusted users. For public use, add authentication.

---

## **10️⃣ Optional Improvements**

* Drag-and-drop uploads with progress feedback
* Automatic thumbnail generation
* Automatic episode detection by filename patterns
* Background conversion for large files
* Reverse proxy + HTTPS (e.g., Nginx) for secure access

---

## **11️⃣ Auto-starting Senstr on Server**

Create a **systemd service**:

```bash
sudo nano /etc/systemd/system/senstr.service
```

Add:

```ini
[Unit]
Description=Senstr Movie Streaming Server
After=network.target

[Service]
User=your_username
WorkingDirectory=/home/your_username/senstr
ExecStart=/usr/bin/python3 /home/your_username/senstr/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable & start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable senstr
sudo systemctl start senstr
```

---

✅ **With this setup, Senstr is fully functional**:

* Upload MKV → auto-convert to MP4
* Multi-file uploads with progress bars
* Resume playback & next-episode autoplay
* Cross-device friendly UI
* Folder/subfolder management

