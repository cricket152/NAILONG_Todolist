from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QFont


class CheckBoxDelegate(QStyledItemDelegate):
    """Delegate that renders a centered checkbox in a table cell."""

    def paint(self, painter: QPainter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        checked = index.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked

        # Checkbox dimensions
        size = 18
        rect = option.rect
        x = rect.center().x() - size // 2
        y = rect.center().y() - size // 2
        box = QRectF(x, y, size, size)

        # Background
        if option.state & QStyle.StateFlag.State_MouseOver:
            bg = QColor("#E5DEC9")
        else:
            bg = QColor("#FDFBF7")
        painter.setPen(QPen(QColor("#A1887F"), 1.5))
        painter.setBrush(bg)
        painter.drawRoundedRect(box, 3, 3)

        # Check mark
        if checked:
            painter.setPen(QPen(QColor("#8D6E63"), 2.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            # Draw ✓ using a simple polyline
            from PyQt6.QtGui import QPainterPath
            path = QPainterPath()
            # 起点：原为 x+3, 现改为 x+5
            path.moveTo(x + 5, y + size * 0.5)
            # 折返点（最下方）：原为 x+size*0.4, y+size-3，现改为 x+size*0.45, y+size-5
            path.lineTo(x + size * 0.45, y + size - 5)
            # 终点（右上角）：原为 x+size-2, y+3，现改为 x+size-5, y+5
            path.lineTo(x + size - 5, y + 5)
            painter.drawPath(path)

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == event.Type.MouseButtonRelease:
            current = index.data(Qt.ItemDataRole.CheckStateRole)
            new_val = Qt.CheckState.Unchecked if current == Qt.CheckState.Checked else Qt.CheckState.Checked
            return model.setData(index, new_val, Qt.ItemDataRole.CheckStateRole)
        return False
