# Minimal TikTok Downloader (Tkinter + yt-dlp)
# pip install yt-dlp certifi
# Make sure ffmpeg is on PATH.
# python 3.13+

import threading
from pathlib import Path
import re
import os

# --- Tkinter ---
from tkinter import (
    Tk, Text, StringVar, DoubleVar, END, DISABLED, NORMAL,
    filedialog, messagebox, Frame, Label, Entry, Button, Scrollbar
)
from tkinter import ttk

# --- yt-dlp ---
from yt_dlp import YoutubeDL

# --- Optional: use certifi CA bundle to avoid Windows SSL issues ---
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except Exception:
    pass  # certifi not available; will proceed without overriding

URL_RE = re.compile(r'(https?://[^\s]+)', re.IGNORECASE)

class SimpleTikTokDL:
    def __init__(self, root: Tk):
        self.root = root
        root.title("TikTok Downloader (Simple)")

        self.output_dir = StringVar(value=str(Path.cwd() / "tiktoks"))
        self.progress = DoubleVar(value=0.0)

        pad = {"padx": 6, "pady": 6}

        # URLs input
        Label(root, text="TikTok URLs (one per line; any text allowed):").grid(row=0, column=0, columnspan=3, sticky="w", **pad)
        self.txt_urls = Text(root, width=90, height=10)
        self.txt_urls.grid(row=1, column=0, columnspan=3, sticky="we", **pad)
        sb = Scrollbar(root, command=self.txt_urls.yview)
        self.txt_urls.configure(yscrollcommand=sb.set)

        # Output folder
        Label(root, text="Output Folder").grid(row=2, column=0, sticky="w", **pad)
        Entry(root, textvariable=self.output_dir, width=60).grid(row=2, column=1, sticky="we", **pad)
        Button(root, text="Browse…", command=self.browse_output).grid(row=2, column=2, **pad)

        # Controls
        ctrl = Frame(root)
        ctrl.grid(row=3, column=0, columnspan=3, sticky="w", **pad)
        Button(ctrl, text="Extract URLs", command=self.extract_urls).grid(row=0, column=0, **pad)
        Button(ctrl, text="Download", command=self.start_download).grid(row=0, column=1, **pad)
        Button(ctrl, text="Clear", command=self.clear_urls).grid(row=0, column=2, **pad)

        # Progress
        Label(root, text="Progress").grid(row=4, column=0, sticky="w", **pad)
        self.pb = ttk.Progressbar(root, maximum=100.0, variable=self.progress, length=520)
        self.pb.grid(row=4, column=1, columnspan=2, sticky="we", **pad)

        # Log
        Label(root, text="Log").grid(row=5, column=0, sticky="nw", **pad)
        self.txt_log = Text(root, width=90, height=14, state=DISABLED)
        self.txt_log.grid(row=5, column=1, columnspan=2, sticky="we", **pad)

        root.grid_columnconfigure(1, weight=1)

        self.worker = None

    # ---------- UI helpers ----------
    def browse_output(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self.output_dir.set(d)

    def extract_urls(self):
        text = self.txt_urls.get("1.0", END)
        urls = URL_RE.findall(text)
        urls = [u for u in urls if "tiktok.com" in u.lower()]
        if not urls:
            messagebox.showinfo("Extract URLs", "No TikTok URLs found.")
            return
        self.txt_urls.delete("1.0", END)
        self.txt_urls.insert(END, "\n".join(urls))
        self._log("Extracted {} TikTok URL(s).".format(len(urls)))

    def clear_urls(self):
        self.txt_urls.delete("1.0", END)
        self._log("Cleared.")
        self._set_progress(0)

    # ---------- Download flow ----------
    def start_download(self):
        if self.worker and self.worker.is_alive():
            messagebox.showwarning("Busy", "A download is already running.")
            return

        urls_text = self.txt_urls.get("1.0", END).strip()
        # Accept raw text; extract URLs to be resilient
        urls = URL_RE.findall(urls_text)
        urls = [u for u in (u.strip() for u in urls) if u]

        if not urls:
            messagebox.showerror("No URLs", "Provide one or more TikTok URLs.")
            return

        outdir = Path(self.output_dir.get())
        outdir.mkdir(parents=True, exist_ok=True)

        self._set_progress(0)
        self._log(f"Downloading {len(urls)} item(s) to: {outdir}")
        self.worker = threading.Thread(target=self._download_worker, args=(urls, outdir), daemon=True)
        self.worker.start()

    def _download_worker(self, urls, outdir: Path):
        # Thread-safe progress/log hooks using .after
        def hook(d):
            if d.get('status') == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                done = d.get('downloaded_bytes') or 0
                pct = (done / total * 100) if total else 0
                self._set_progress(pct)
            elif d.get('status') == 'finished':
                self._set_progress(100.0)

        ydl_opts = {
            # MP4-oriented selection with sane fallbacks
            "format": "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b[ext=mp4]/b",
            "merge_output_format": "mp4",

            "noplaylist": True,
            "quiet": True,
            "no_warnings": False,

            "outtmpl": str(outdir / "%(title).100s.%(ext)s"),
            "windowsfilenames": True,
            "restrictfilenames": True,

            # Networking hardening
            "forceipv4": True,
            "nocheckcertificate": False,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
            },

            "progress_hooks": [hook],
            "retries": 10,
            "fragment_retries": 10,
            "retry_sleep": "2,4,8,15,30",
        }

        # If your region needs cookies, uncomment and ensure you’re logged in:
        # ydl_opts["cookiesfrombrowser"] = ("edge",)  # or ("chrome",)

        total = len(urls)
        for i, url in enumerate(urls, 1):
            self._log(f"[{i}/{total}] {url}")
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                self._log("Done.")
            except Exception as e:
                self._log(f"ERROR: {e}")
            finally:
                self._set_progress(0)

        self._log("All tasks complete.")

    # ---------- Thread-safe UI ops ----------
    def _set_progress(self, value: float):
        self.root.after(0, lambda: self.progress.set(value))

    def _log(self, msg: str):
        self.root.after(0, lambda: self._append_log(msg))

    def _append_log(self, msg: str):
        self.txt_log.config(state=NORMAL)
        self.txt_log.insert(END, msg + "\n")
        self.txt_log.see(END)
        self.txt_log.config(state=DISABLED)


if __name__ == "__main__":
    root = Tk()
    SimpleTikTokDL(root)
    root.mainloop()
