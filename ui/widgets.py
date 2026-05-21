"""Widgets personnalisés pour l'interface de la galerie vidéo (PyQt6)."""
import io

import requests
from PIL import Image
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy,
)

from ui.helpers import format_bytes


class ThumbnailLoader(QThread):
    """Charge les vignettes en arrière-plan."""
    thumbnail_data = pyqtSignal(object, bytes)
    finished_all = pyqtSignal()

    SIZE = (260, 146)

    def __init__(self, videos, parent=None):
        super().__init__(parent)
        self.videos = videos

    def run(self):
        for video in self.videos:
            try:
                resp = requests.get(str(video.thumbnail_url), timeout=10)
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content))
                img = img.convert("RGB")
                img.thumbnail(self.SIZE, Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                self.thumbnail_data.emit(video, buf.getvalue())
            except Exception:
                pass
        self.finished_all.emit()


class VideoCard(QFrame):
    """Carte individuelle représentant une vidéo dans la galerie."""
    clicked = pyqtSignal(object)
    download_clicked = pyqtSignal(object)

    CARD_WIDTH = 268

    def __init__(self, video, parent=None):
        super().__init__(parent)
        self.video = video

        self.setFixedWidth(self.CARD_WIDTH)
        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("""
            VideoCard {
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 4px;
            }
            VideoCard:hover {
                border: 1px solid #5a8de0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Vignette
        self.image_label = QLabel()
        self.image_label.setFixedSize(260, 146)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #2a2a2a; border-radius: 4px;")
        placeholder = QPixmap(260, 146)
        placeholder.fill(Qt.GlobalColor.darkGray)
        self.image_label.setPixmap(placeholder)
        layout.addWidget(self.image_label)

        # Titre
        title_label = QLabel(video.title)
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(40)
        title_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        play_btn = QPushButton("▶ Play")
        play_btn.setFixedHeight(28)
        play_btn.setStyleSheet("""
            QPushButton {
                background-color: #5a8de0; color: white;
                border: none; border-radius: 4px; padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #4a7dcf; }
        """)
        play_btn.clicked.connect(lambda: self.clicked.emit(self.video))
        btn_layout.addWidget(play_btn)

        dl_btn = QPushButton("⬇ DL")
        dl_btn.setFixedHeight(28)
        dl_btn.setStyleSheet("""
            QPushButton {
                background-color: #444; color: white;
                border: none; border-radius: 4px; padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #555; }
        """)
        dl_btn.clicked.connect(lambda: self.download_clicked.emit(self.video))
        btn_layout.addWidget(dl_btn)

        layout.addLayout(btn_layout)

        # Taille (affiché pendant le download)
        self.size_label = QLabel("")
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.size_label)

        self.setLayout(layout)

    def set_image(self, pixmap: QPixmap):
        """Définit l'image de la vignette."""
        self.image_label.setPixmap(pixmap.scaled(
            260, 146,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))

    def update_size(self, bytes_: int):
        """Met à jour l'affichage de la taille téléchargée."""
        self.size_label.setText(format_bytes(bytes_))
