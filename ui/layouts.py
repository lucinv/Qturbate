"""Disposition personnalisée en flux (FlowLayout) pour PyQt6."""
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtWidgets import QLayout, QSizePolicy


class FlowLayout(QLayout):
    """Layout qui dispose les widgets en lignes, passant à la ligne suivante
    lorsque la largeur disponible est insuffisante."""

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
