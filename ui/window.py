"""Fenêtre principale de l'interface PyQt6."""
import subprocess

from PyQt6.QtCore import Qt, QThread, QTimer
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QScrollArea, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QMessageBox, QStatusBar, QToolBar, QPushButton,
    QSizePolicy, QSplitter,
)

from ui.favorites import FavoritesStore
from ui.layouts import FlowLayout
from ui.widgets import VideoCard, ThumbnailLoader
from ui.workers import FetchWorker, RecordingManager
from ui.recording_panel import RecordingPanel
from services.chaturbate import fetch_rooms


class VideoWindow(QMainWindow):
    """Fenêtre principale de navigation des streams."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vids")
        self.resize(1500, 900)
        self.setMinimumSize(1000, 600)

        self.current_gender = "f"
        self.current_tag = None
        self.cards = []
        self.loader = None
        self._fetch_thread = None
        self._fetch_worker = None
        self._favorites_mode = False

        self.recording_manager = RecordingManager(self)

        self._setup_ui()
        self.load_videos()

    # ── UI Setup ──────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        vlayout = QVBoxLayout(central)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet(
            "QToolBar { background: #1a1a1a; border: none; padding: 4px; spacing: 8px; }"
        )

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Any", "Female", "Male", "Couple"])
        self.gender_combo.setCurrentText("Female")
        self.gender_combo.currentTextChanged.connect(lambda _: self._on_filter())
        toolbar.addWidget(QLabel("  Gender:"))
        toolbar.addWidget(self.gender_combo)

        self.tag_combo = QComboBox()
        self.tag_combo.addItems(
            ["Any", "asian", "ebony", "bigboobs", "bigass",
             "18", "new", "teen", "french", "lesbian"]
        )
        self.tag_combo.currentTextChanged.connect(lambda _: self._on_filter())
        toolbar.addWidget(QLabel("  Tag:"))
        toolbar.addWidget(self.tag_combo)

        self.fav_btn = QPushButton("☆ Favorites")
        self.fav_btn.setCheckable(True)
        self.fav_btn.setStyleSheet("""
            QPushButton { background: #333; color: #aaa;
                          border: 1px solid #555; border-radius: 4px;
                          padding: 6px 12px; font-size: 12px; }
            QPushButton:hover { background: #444; color: #FFD700; }
            QPushButton:checked { background: #5a3e00; color: #FFD700;
                                  border: 1px solid #FFD700; font-weight: bold; }
        """)
        self.fav_btn.toggled.connect(self._on_favorites_toggled)
        toolbar.addWidget(self.fav_btn)
        toolbar.addSeparator()

        self.refresh_btn = QPushButton("⟳ Refresh")
        self.refresh_btn.clicked.connect(self.load_videos)
        self.refresh_btn.setStyleSheet("""
            QPushButton { background: #5a8de0; color: white;
                          border: none; border-radius: 4px;
                          padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background: #4a7dcf; }
        """)
        toolbar.addWidget(self.refresh_btn)

        vlayout.addWidget(toolbar)

        # Splitter horizontal: galerie (gauche) / panel downloads (droite)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Zone de défilement avec FlowLayout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: #1a1a1a; border: none; }")

        scroll_content = QWidget()
        self.flow = FlowLayout(scroll_content, margin=8, spacing=8)
        scroll_content.setLayout(self.flow)
        scroll.setWidget(scroll_content)
        splitter.addWidget(scroll)

        # Panneau latéral des enregistrements
        self.recording_panel = RecordingPanel()
        self.recording_panel.folder_btn.clicked.connect(self._open_download_folder)
        self.recording_panel.stop_requested.connect(self._stop_recording)
        splitter.addWidget(self.recording_panel)

        splitter.setSizes([1000, 300])
        vlayout.addWidget(splitter)

        # Status bar
        status_bar = QStatusBar()
        status_bar.setStyleSheet("QStatusBar { background: #1a1a1a; color: #aaa; }")
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)
        self.setStatusBar(status_bar)

        # Connexion des signaux du recording manager
        self.recording_manager.recording_started.connect(self._on_recording_started)
        self.recording_manager.recording_finished.connect(self._on_recording_finished)
        self.recording_manager.recording_progress.connect(self._on_recording_progress)

    # ── Ouverture dossier ─────────────────────────────────────────────

    def _open_download_folder(self):
        try:
            subprocess.Popen(["xdg-open", str(self.recording_manager.download_dir)])
        except Exception:
            pass

    # ── Filtres ───────────────────────────────────────────────────────

    def _on_filter(self):
        gender_map = {"Any": "", "Female": "f", "Male": "m", "Couple": "c"}
        self.current_gender = gender_map.get(self.gender_combo.currentText(), "")
        raw = self.tag_combo.currentText()
        self.current_tag = raw if raw != "Any" else None
        self.load_videos()

    # ── Chargement des vidéos ─────────────────────────────────────────

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
            card.favorite_toggled.connect(self._on_card_favorite_toggled)
            self.flow.addWidget(card)
            self.cards.append(card)

        if self._favorites_mode:
            self._apply_favorites_filter()

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
        if self._favorites_mode:
            visible = sum(1 for c in self.cards if c.isVisible())
            self.status_label.setText(f"Favorites ({visible})")
            return
        loaded = sum(
            1 for c in self.cards
            if c.image_label.pixmap() and not c.image_label.pixmap().isNull()
        )
        self.status_label.setText(
            f"Ready — {len(self.cards)} videos, {loaded} thumbnails"
        )

    # ── Favorites ─────────────────────────────────────────────────────

    def _on_favorites_toggled(self, checked: bool):
        self._favorites_mode = checked
        self.fav_btn.setText("★ Favorites" if checked else "☆ Favorites")
        self._apply_favorites_filter()

    def _apply_favorites_filter(self):
        if not self.cards:
            return
        visible = 0
        for card in self.cards:
            is_fav = FavoritesStore.is_favorite(card.video.id)
            show = is_fav if self._favorites_mode else True
            card.setVisible(show)
            if show:
                visible += 1
        if self._favorites_mode:
            self.status_label.setText(f"Favorites ({visible})")
        else:
            total = len(self.cards)
            loaded = sum(1 for c in self.cards if c.image_label.pixmap() and not c.image_label.pixmap().isNull())
            self.status_label.setText(f"Ready — {total} videos, {loaded} thumbnails")

    def _on_card_favorite_toggled(self, video, is_favorite: bool):
        if self._favorites_mode and not is_favorite:
            for card in self.cards:
                if card.video is video:
                    card.setVisible(False)
                    break
            visible = sum(1 for c in self.cards if c.isVisible())
            self.status_label.setText(f"Favorites ({visible})")

    # ── Clear ─────────────────────────────────────────────────────────

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

    # ── Recording events ──────────────────────────────────────────────

    def _on_recording_started(self, uid):
        info = self.recording_manager.get_info(uid)
        if info:
            self.recording_panel.add_active(uid, info.title)
            self.status_label.setText(f"Downloading {info.title}…")

    def _on_recording_finished(self, uid):
        info = self.recording_manager.get_info(uid)
        if info:
            self.recording_panel.move_to_finished(uid, info.title, info.error)
            if info.error:
                self.status_label.setText(f"Download failed: {info.title}")
            else:
                self.status_label.setText(f"Downloaded: {info.title}")
            # Mettre à jour la taille sur la carte
            for card in self.cards:
                if card.video.id == uid:
                    card.update_size(info.size)
                    break

    def _on_recording_progress(self, info):
        # Mettre à jour le panel latéral
        self.recording_panel.update_progress(info.uid, info.title, info.size)
        # Mettre à jour la taille sur la carte
        for card in self.cards:
            if card.video.id == info.uid:
                card.update_size(info.size)
                break

    def _stop_recording(self, uid):
        """Arrête un téléchargement et le déplace dans 'Finished'."""
        info = self.recording_manager.get_info(uid)
        if info:
            self.recording_manager.stop_recording(uid)
            self.recording_panel.move_to_finished(uid, info.title, "Stopped")
            self.status_label.setText(f"Stopped: {info.title}")
