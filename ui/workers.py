"""Workers pour les opérations asynchrones / en arrière-plan (PyQt6)."""
import os
import threading
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QThread
from yt_dlp import YoutubeDL

from services.chaturbate import fetch_rooms
from ui.helpers import sanitize_filename


class FetchWorker(QObject):
    """Worker qui récupère la liste des rooms dans un thread séparé."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, gender, tag):
        super().__init__()
        self.gender = gender
        self.tag = tag

    def run(self):
        try:
            videos = fetch_rooms(gender=self.gender, tag=self.tag)
            self.finished.emit(videos)
        except Exception as e:
            self.error.emit(str(e))


class RecordingInfo:
    """État d'un téléchargement en cours."""
    def __init__(self, video):
        self.uid = video.id
        self.title = video.title
        self.stream_url = video.stream_url
        self.active = True
        self.size = 0
        self.error = None
        self.output_path = None


class RecordingManager(QObject):
    """Gère les téléchargements de streams via yt-dlp."""
    recording_started = pyqtSignal(str)
    recording_finished = pyqtSignal(str)
    recording_progress = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.download_dir = Path.home() / "Videos" / "vods"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self._recordings: dict[str, RecordingInfo] = {}

    def start_recording(self, video):
        """Lance le téléchargement d'un stream."""
        info = RecordingInfo(video)
        self._recordings[info.uid] = info

        safe = sanitize_filename(video.title)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.download_dir / f"{safe}_{ts}.mp4"
        info.output_path = output_path

        def _download():
            ydl_opts = {
                "outtmpl": str(output_path),
                "format": "best",
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [lambda d: self._on_ytdlp_progress(info, d)],
            }
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([str(video.stream_url)])
                info.active = False
                self.recording_finished.emit(info.uid)
            except Exception as e:
                info.active = False
                info.error = str(e)
                self.recording_finished.emit(info.uid)

        self.recording_started.emit(info.uid)
        t = threading.Thread(target=_download, daemon=True)
        t.start()

    def _on_ytdlp_progress(self, info, d):
        if d.get("status") == "downloading":
            info.size = d.get("downloaded_bytes", 0)
            self.recording_progress.emit(info)
