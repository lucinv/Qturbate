"""
Modern PyQt6 GUI for browsing and playing live streams.
"""

import sys
import io
import os
import uuid
import asyncio
import subprocess
import threading
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image
from yt_dlp import YoutubeDL
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QThread, QTimer, QObject
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QScrollArea,
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame,
    QMessageBox, QStatusBar, QToolBar, QLayout,
    QPushButton, QSizePolicy, QSplitter,
)

from services.chaturbate import fetch_rooms
from domain.video import Video


# ── Flow Layout ──────────────────────────────────────────────────────

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=8):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._items = []

    def __del__(self):
        while self._items:
            item = self._items.pop()
            if item.widget():
                item.widget().deleteLater()

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, True)

    def sizeHint(self):
        return QSize(400, 300)

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins().left() * 2
        return size + QSize(m, m)

    def _do_layout(self, rect, move_widgets):
        margin = self.contentsMargins().left()
        x = rect.x() + margin
        y = rect.y() + margin
        line_h = 0
        spacing = self.spacing()

        for item in self._items:
            w = item.widget()
            if w and not w.isVisible():
                continue
            hint = item.sizeHint()
            next_x = x + hint.width() + spacing
            if next_x - spacing > rect.right() and line_h > 0:
                x = rect.x() + margin
                y += line_h + spacing
                line_h = 0
            if move_widgets:
                item.setGeometry(QRect(x, y, hint.width(), hint.height()))
            x += hint.width() + spacing
            line_h = max(line_h, hint.height())

        return y + line_h + margin - rect.y()


# ── Helpers ──────────────────────────────────────────────────────────

def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " _-." else "_" for c in name).strip()


def format_bytes(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ── Fetch worker ─────────────────────────────────────────────────────

class FetchWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, gender, tag):
        super().__init__()
        self.gender = gender
        self.tag = tag

    def run(self):
        try:
            videos = asyncio.run(fetch_rooms(gender=self.gender, tag=self.tag))
            self.finished.emit(videos)
        except Exception as e:
            self.error.emit(str(e))


# ── Thumbnail loader ─────────────────────────────────────────────────

class ThumbnailLoader(QThread):
    thumbnail_data = pyqtSignal(object, bytes)
    finished_all = pyqtSignal()

    SIZE = (260, 160)

    def __init__(self, videos, parent=None):
        super().__init__(parent)
        self.videos = videos

    def run(self):
        for video in self.videos:
            try:
                resp = requests.get(str(video.thumbnail_url), timeout=10)
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content))
                img = img.convert("RGB").resize(self.SIZE, Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                self.thumbnail_data.emit(video, buf.getvalue())
            except Exception as e:
                print(f"Thumbnail fail for {video.title}: {e}")
        self.finished_all.emit()


# ── Recording manager ────────────────────────────────────────────────

class RecordingInfo:
    def __init__(self, video, output_path):
        self.uid = str(uuid.uuid4())[:8]
        self.video = video
        self.output_path = output_path
        self.start_time = datetime.now()
        self.size = 0
        self.active = True
        self.error = None


class RecordingManager(QObject):
    recording_started = pyqtSignal(str)     # uid
    recording_progress = pyqtSignal(str)    # uid
    recording_finished = pyqtSignal(str)    # uid

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recordings: dict[str, RecordingInfo] = {}
        self._download_dir = str(Path.home() / "Videos" / "streams")
        os.makedirs(self._download_dir, exist_ok=True)

    @property
    def download_dir(self):
        return self._download_dir

    def get_info(self, uid):
        return self._recordings.get(uid)

    def start_recording(self, video):
        safe_name = sanitize_filename(video.title)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self._download_dir, f"{safe_name}_{ts}.mp4")

        info = RecordingInfo(video, output_path)
        self._recordings[info.uid] = info

        def _download():
            ydl_opts = {
                "outtmpl": output_path,
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
            self.recording_progress.emit(info.uid)

    def stop_recording(self, uid):
        info = self._recordings.get(uid)
        if not info or not info.active:
            return
        info.active = False
        if os.path.exists(info.output_path):
            try:
                os.remove(info.output_path)
            except OSError:
                pass


# ── Video card ───────────────────────────────────────────────────────

class VideoCard(QFrame):
    clicked = pyqtSignal(object)
    download_clicked = pyqtSignal(object)

    def __init__(self, video, parent=None):
        super().__init__(parent)
        self.video = video
        self.setFixedSize(260, 240)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            VideoCard {
                background: #2a2a2a;
                border-radius: 8px;
                border: 1px solid #3a3a3a;
            }
            VideoCard:hover {
                border: 1px solid #5a8de0;
                background: #333;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(252, 160)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: #1e1e1e; border-radius: 4px;")
        layout.addWidget(self.image_label)

        self.title_label = QLabel(video.title, self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #ddd; font-size: 11px;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: #3a7d3a; color: #fff;
                border: none; border-radius: 4px;
                padding: 4px 10px; font-size: 10px;
            }
            QPushButton:hover { background: #4a9d4a; }
        """)
        self.play_btn.clicked.connect(lambda: self.clicked.emit(self.video))
        btn_row.addWidget(self.play_btn)

        self.dl_btn = QPushButton("⬇ Save")
        self.dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dl_btn.setStyleSheet("""
            QPushButton {
                background: #5a5a8a; color: #fff;
                border: none; border-radius: 4px;
                padding: 4px 10px; font-size: 10px;
            }
            QPushButton:hover { background: #7a7aaa; }
        """)
        self.dl_btn.clicked.connect(lambda: self.download_clicked.emit(self.video))
        btn_row.addWidget(self.dl_btn)

        layout.addLayout(btn_row)

    def set_image(self, pixmap):
        scaled = pixmap.scaled(252, 160, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled)


# ── Recording panel ─────────────────────────────────────────────────

class RecordingPanel(QFrame):
    stop_requested = pyqtSignal(str)
    open_folder_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setStyleSheet("""
            RecordingPanel { background: #222; border-left: 1px solid #3a3a3a; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("📥 Recordings")
        title.setStyleSheet("color: #eee; font-size: 14px; font-weight: bold; padding: 8px;")
        title_row.addWidget(title)

        folder_btn = QPushButton("📁")
        folder_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a; color: #ddd;
                border: 1px solid #555; border-radius: 3px;
                padding: 4px 8px; font-size: 10px;
            }
            QPushButton:hover { background: #5a8de0; }
        """)
        folder_btn.setToolTip("Open download folder")
        folder_btn.setFixedSize(30, 26)
        folder_btn.clicked.connect(self.open_folder_requested.emit)
        title_row.addWidget(folder_btn)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Active section
        active_header = QLabel("Active:")
        active_header.setStyleSheet("color: #aaa; font-size: 11px; padding: 4px 8px;")
        layout.addWidget(active_header)

        self.active_scroll = QScrollArea()
        self.active_scroll.setWidgetResizable(True)
        self.active_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.active_scroll.setMaximumHeight(300)
        self.active_scroll.setStyleSheet("QScrollArea { border: none; background: #2a2a2a; }")
        self.active_container = QWidget()
        self.active_layout = QVBoxLayout(self.active_container)
        self.active_layout.setContentsMargins(0, 0, 0, 0)
        self.active_layout.setSpacing(0)
        self.active_layout.addStretch()
        self.active_scroll.setWidget(self.active_container)
        layout.addWidget(self.active_scroll)

        # Finished section
        finished_header = QLabel("Finished:")
        finished_header.setStyleSheet("color: #aaa; font-size: 11px; padding: 4px 8px;")
        layout.addWidget(finished_header)

        self.finished_scroll = QScrollArea()
        self.finished_scroll.setWidgetResizable(True)
        self.finished_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.finished_scroll.setMaximumHeight(300)
        self.finished_scroll.setStyleSheet("QScrollArea { border: none; background: #2a2a2a; }")
        self.finished_container = QWidget()
        self.finished_layout = QVBoxLayout(self.finished_container)
        self.finished_layout.setContentsMargins(0, 0, 0, 0)
        self.finished_layout.setSpacing(0)
        self.finished_layout.addStretch()
        self.finished_scroll.setWidget(self.finished_container)
        layout.addWidget(self.finished_scroll)

        layout.addStretch()

    def add_active(self, uid, title):
        row = QWidget()
        row.setObjectName(f"active_{uid}")
        hl = QHBoxLayout(row)
        hl.setContentsMargins(6, 4, 6, 4)

        label = QLabel(f"⬇ {title}")
        label.setStyleSheet("color: #ddd; font-size: 11px;")
        hl.addWidget(label, 1)

        stop_btn = QPushButton("■ Stop")
        stop_btn.setStyleSheet("""
            QPushButton {
                background: #8a3a3a; color: #fff;
                border: none; border-radius: 3px;
                padding: 2px 8px; font-size: 10px;
            }
            QPushButton:hover { background: #aa4a4a; }
        """)
        stop_btn.clicked.connect(lambda checked, u=uid: self.stop_requested.emit(u))
        hl.addWidget(stop_btn)

        self.active_layout.insertWidget(self.active_layout.count() - 1, row)

        # Store reference so we can update/remove it
        row._uid = uid
        row._label = label

    def update_progress(self, uid, title, size):
        for i in range(self.active_layout.count()):
            w = self.active_layout.itemAt(i).widget()
            if w and hasattr(w, '_uid') and w._uid == uid:
                w._label.setText(f"⬇ {title}  ({format_bytes(size)})")
                break

    def move_to_finished(self, uid, title, error=None):
        # Remove from active
        for i in range(self.active_layout.count()):
            w = self.active_layout.itemAt(i).widget()
            if w and hasattr(w, '_uid') and w._uid == uid:
                self.active_layout.removeWidget(w)
                w.deleteLater()
                break

        # Add to finished
        prefix = "⚠" if error else "✅"
        label = QLabel(f"{prefix} {title}")
        label.setStyleSheet("color: #ddd; font-size: 11px; padding: 6px; border-bottom: 1px solid #333;")
        self.finished_layout.insertWidget(self.finished_layout.count() - 1, label)


# ── Main window ──────────────────────────────────────────────────────

class VideoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stream Browser")
        self.setMinimumSize(800, 500)
        self.resize(1200, 750)

        self.recording_manager = RecordingManager()

        self._setup_theme()
        self._setup_ui()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_recording_signals()

        self.cards = []
        self.loader = None
        self.current_gender = ""
        self.current_tag = None
        self._fetch_thread = None
        self._fetch_worker = None

        QTimer.singleShot(0, self.load_videos)

    def _setup_theme(self):
        self.setStyleSheet("""
            QMainWindow { background: #1a1a1a; }
            QToolBar {
                background: #222; border: none;
                padding: 4px; spacing: 8px;
            }
            QToolBar QPushButton {
                background: #3a3a3a; color: #eee;
                border: 1px solid #555; border-radius: 4px;
                padding: 4px 14px; font-size: 13px;
            }
            QToolBar QPushButton:hover {
                background: #5a8de0; border-color: #5a8de0;
            }
            QToolBar QPushButton:pressed { background: #4a7dd0; }
            QComboBox {
                background: #333; color: #eee;
                border: 1px solid #555; border-radius: 4px;
                padding: 4px 8px; min-width: 100px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #333; color: #eee;
                selection-background-color: #5a8de0;
            }
            QStatusBar {
                background: #222; color: #aaa;
                border-top: 1px solid #333;
            }
            QScrollArea { border: none; background: #1a1a1a; }
            QScrollBar:vertical {
                background: #222; width: 10px; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #555; border-radius: 5px; min-height: 30px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_content = QWidget()
        self.flow = FlowLayout(self.scroll_content, margin=12, spacing=10)
        scroll.setWidget(self.scroll_content)
        splitter.addWidget(scroll)

        self.recording_panel = RecordingPanel()
        self.recording_panel.stop_requested.connect(self._stop_recording)
        self.recording_panel.open_folder_requested.connect(self._open_download_folder)
        splitter.addWidget(self.recording_panel)

        splitter.setSizes([900, 300])
        main_layout.addWidget(splitter)

    def _setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        title = QLabel("🎥  Stream Browser")
        title.setStyleSheet("color: #eee; font-size: 16px; font-weight: bold; padding: 0 8px;")
        toolbar.addWidget(title)
        toolbar.addSeparator()

        lbl = QLabel("Gender:")
        lbl.setStyleSheet("color: #aaa;")
        toolbar.addWidget(lbl)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Any", "Female", "Male", "Couple"])
        self.gender_combo.setCurrentText("Female")
        self.gender_combo.currentTextChanged.connect(self._on_filter)
        toolbar.addWidget(self.gender_combo)

        lbl = QLabel("  Tag:")
        lbl.setStyleSheet("color: #aaa;")
        toolbar.addWidget(lbl)

        self.tag_combo = QComboBox()
        self.tag_combo.addItems([
            "Any", "asian", "ebony", "bigboobs", "bigass",
            "18", "new", "teen", "french", "lesbian",
        ])
        self.tag_combo.currentTextChanged.connect(self._on_filter)
        toolbar.addWidget(self.tag_combo)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        self.reload_btn = QPushButton("⟳  Reload")
        self.reload_btn.clicked.connect(self.load_videos)
        toolbar.addWidget(self.reload_btn)

    def _setup_statusbar(self):
        self.status = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status.addPermanentWidget(self.status_label)

    def _connect_recording_signals(self):
        mgr = self.recording_manager
        mgr.recording_started.connect(self._on_recording_started)
        mgr.recording_progress.connect(self._on_recording_progress)
        mgr.recording_finished.connect(self._on_recording_finished)

    def _on_recording_started(self, uid):
        info = self.recording_manager.get_info(uid)
        if info:
            self.recording_panel.add_active(uid, info.video.title)
            self.status_label.setText(f"Downloading {info.video.title}…")

    def _on_recording_progress(self, uid):
        info = self.recording_manager.get_info(uid)
        if info:
            self.recording_panel.update_progress(uid, info.video.title, info.size)

    def _on_recording_finished(self, uid):
        info = self.recording_manager.get_info(uid)
        if info:
            self.recording_panel.move_to_finished(uid, info.video.title, info.error)
            if info.error:
                self.status_label.setText(f"Download failed: {info.video.title}")
            else:
                self.status_label.setText(f"Downloaded: {info.video.title}")

    def _stop_recording(self, uid):
        info = self.recording_manager.get_info(uid)
        if info:
            self.recording_manager.stop_recording(uid)
            self.recording_panel.move_to_finished(uid, info.video.title, "Stopped")
            self.status_label.setText(f"Stopped: {info.video.title}")

    def _open_download_folder(self):
        path = self.recording_manager.download_dir
        try:
            subprocess.Popen(["xdg-open", path])
        except Exception:
            subprocess.Popen(["open", path])

    def _on_filter(self):
        gender_map = {"Any": "", "Female": "f", "Male": "m", "Couple": "c"}
        self.current_gender = gender_map.get(self.gender_combo.currentText(), "")
        raw = self.tag_combo.currentText()
        self.current_tag = raw if raw != "Any" else None
        self.load_videos()

    def load_videos(self):
        self.status_label.setText("Loading…")
        self._clear_cards()

        self._fetch_thread = QThread()
        self._fetch_worker = FetchWorker(
            self.current_gender or None,
            self.current_tag,
        )
        self._fetch_worker.moveToThread(self._fetch_thread)
        self._fetch_thread.started.connect(self._fetch_worker.run)
        self._fetch_worker.finished.connect(self._on_videos_fetched)
        self._fetch_worker.error.connect(lambda msg: print(f"Fetch error: {msg}"))
        self._fetch_worker.finished.connect(self._fetch_thread.quit)
        self._fetch_worker.finished.connect(self._fetch_worker.deleteLater)
        self._fetch_thread.finished.connect(self._fetch_thread.deleteLater)
        self._fetch_thread.start()

    def _on_videos_fetched(self, videos):
        if not videos:
            self.status_label.setText("No videos found")
            return

        for video in videos:
            card = VideoCard(video)
            card.clicked.connect(self.open_video)
            card.download_clicked.connect(self._start_download)
            self.flow.addWidget(card)
            self.cards.append(card)

        self.status_label.setText(f"Loaded {len(videos)} videos — loading thumbnails…")

        self.loader = ThumbnailLoader(videos)
        self.loader.thumbnail_data.connect(self._on_thumbnail)
        self.loader.finished_all.connect(self._on_thumbnails_done)
        self.loader.start()

    def _start_download(self, video):
        self.recording_manager.start_recording(video)

    def _on_thumbnail(self, video, jpeg_bytes):
        pixmap = QPixmap()
        if not pixmap.loadFromData(jpeg_bytes, "JPEG"):
            return
        for card in self.cards:
            if card.video is video:
                card.set_image(pixmap)
                break

    def _on_thumbnails_done(self):
        loaded = sum(1 for c in self.cards
                     if c.image_label.pixmap() and not c.image_label.pixmap().isNull())
        self.status_label.setText(f"Ready — {len(self.cards)} videos, {loaded} thumbnails")

    def _clear_cards(self):
        if self.loader:
            self.loader.quit()
            self.loader.wait()
            self.loader = None
        try:
            if self._fetch_thread and self._fetch_thread.isRunning():
                self._fetch_thread.quit()
                self._fetch_thread.wait()
        except RuntimeError:
            pass
        self._fetch_thread = None
        self._fetch_worker = None
        while self.cards:
            card = self.cards.pop()
            self.flow.removeWidget(card)
            card.deleteLater()

    def open_video(self, video):
        self.status_label.setText(f"Opening {video.title}…")
        try:
            subprocess.Popen(
                ["mpv", "--fs", str(video.stream_url)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "mpv not found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            QTimer.singleShot(1000, lambda: self.status_label.setText("Ready"))


# ── Entry point ──────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = app.palette()
    palette.setColor(app.palette().ColorRole.Window, QColor(26, 26, 26))
    palette.setColor(app.palette().ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(app.palette().ColorRole.Base, QColor(30, 30, 30))
    palette.setColor(app.palette().ColorRole.AlternateBase, QColor(40, 40, 40))
    palette.setColor(app.palette().ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(app.palette().ColorRole.Button, QColor(50, 50, 50))
    palette.setColor(app.palette().ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(app.palette().ColorRole.Link, QColor(90, 141, 224))
    palette.setColor(app.palette().ColorRole.Highlight, QColor(90, 141, 224))
    palette.setColor(app.palette().ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)

    window = VideoWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
