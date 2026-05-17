"""Panneau latéral des enregistrements (downloads en cours et terminés)."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QWidget,
)

from ui.helpers import format_bytes


class RecordingPanel(QFrame):
    """Panneau latéral affichant les téléchargements actifs et terminés."""

    stop_requested = pyqtSignal(str)  # uid

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setStyleSheet("""
            RecordingPanel { background: #222; border-left: 1px solid #3a3a3a; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Titre + bouton dossier
        title_row = QHBoxLayout()
        title = QLabel("📥 Recordings")
        title.setStyleSheet("color: #eee; font-size: 14px; font-weight: bold; padding: 8px;")
        title_row.addWidget(title)

        self.folder_btn = QPushButton("📁")
        self.folder_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a; color: #ddd;
                border: 1px solid #555; border-radius: 3px;
                padding: 4px 8px; font-size: 10px;
            }
            QPushButton:hover { background: #5a8de0; }
        """)
        self.folder_btn.setToolTip("Open download folder")
        self.folder_btn.setFixedSize(30, 26)
        title_row.addWidget(self.folder_btn)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Section active
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

        # Section terminée
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
        """Ajoute une entrée dans la section 'Active'."""
        row = QWidget()
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

        # Stocker les références pour mise à jour / suppression
        row._uid = uid
        row._label = label
        row._stop_btn = stop_btn
        row._title = title
        return row

    def remove_active(self, uid):
        """Retire une entrée de la section 'Active' par uid."""
        for i in range(self.active_layout.count()):
            w = self.active_layout.itemAt(i).widget()
            if w and hasattr(w, '_uid') and w._uid == uid:
                self.active_layout.removeWidget(w)
                w.deleteLater()
                return True
        return False

    def update_progress(self, uid, title, size):
        """Met à jour la taille affichée pour un téléchargement actif."""
        for i in range(self.active_layout.count()):
            w = self.active_layout.itemAt(i).widget()
            if w and hasattr(w, '_uid') and w._uid == uid:
                w._label.setText(f"⬇ {title}  ({format_bytes(size)})")
                return True
        return False

    def move_to_finished(self, uid, title, error=None):
        """Déplace un téléchargement des actifs vers les terminés."""
        self.remove_active(uid)
        prefix = "⚠" if error else "✅"
        label = QLabel(f"{prefix} {title}")
        label.setStyleSheet(
            "color: #ddd; font-size: 11px; padding: 6px; border-bottom: 1px solid #333;"
        )
        self.finished_layout.insertWidget(self.finished_layout.count() - 1, label)
