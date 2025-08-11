# Tiny TikTok Downloader (Tkinter + yt-dlp)

A minimal desktop TikTok downloader built with Python, Tkinter, and yt-dlp.  
Paste one or more TikTok video URLs, select an output folder, and click **Download**.

---

## Features
- **Minimal UI** – paste → folder → download.
- **MP4-first** – prefers MP4 video/audio streams and merges to MP4 if needed.
- **Cookies from browser** – uses your logged-in Edge (or Chrome) cookies for better reliability.
- **Windows SSL fix** – uses `certifi` to avoid certificate errors.
- **Threaded downloads** – UI stays responsive during downloads.
- **Progress bar & log** – shows current video download percentage and a running log.

---

## Requirements
- Python **3.13+**
- [**ffmpeg**](https://ffmpeg.org/) installed and on your system PATH  
  *(yt-dlp requires ffmpeg to merge separate video/audio streams into MP4)*
- [**yt-dlp**](https://github.com/yt-dlp/yt-dlp)
- [**certifi**](https://pypi.org/project/certifi/)

### Install dependencies
```bash
pip install yt-dlp certifi
