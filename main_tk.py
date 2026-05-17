"""Point d'entrée de l'interface PyQt6."""
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from ui.window import VideoWindow


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
