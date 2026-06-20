from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QFont


class DeleteButtonDelegate(QStyledItemDelegate):
    delete_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option, index):
        if hasattr(index.model(), "get_task") and index.model().get_task(index.row()) is None:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = option.rect
        btn_w = 28
        btn_h = 22
        x = rect.center().x() - btn_w // 2
        y = rect.center().y() - btn_h // 2
        btn_rect = QRectF(x, y, btn_w, btn_h)

        # Hover or pressed state (approximate via State_MouseOver)
        if option.state & QStyle.StateFlag.State_MouseOver:
            bg = QColor("#C0392B")  # red
            fg = QColor("#ffffff")
        else:
            bg = QColor("#E8E0D8")  # warm gray
            fg = QColor("#8D6E63")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(btn_rect, 4, 4)

        painter.setPen(fg)
        font = QFont()
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "✕")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if model.get_task(index.row()) is None:
            return False
        if event.type() == event.Type.MouseButtonRelease:
            rect = option.rect
            btn_w = 28
            btn_h = 22
            x = rect.center().x() - btn_w // 2
            y = rect.center().y() - btn_h // 2
            btn_rect = QRectF(x, y, btn_w, btn_h)
            if btn_rect.contains(QPointF(event.pos())):
                task = model.get_task(index.row())
                if task and task.id is not None:
                    self.delete_clicked.emit(task.id)
                return True
        return super().editorEvent(event, model, option, index)
