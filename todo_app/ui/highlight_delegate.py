from __future__ import annotations

from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QModelIndex, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPalette


HIGHLIGHT_BG = QColor(255, 235, 59)  # Yellow


class HighlightDelegate(QStyledItemDelegate):
    """Delegate that highlights search-text matches in cell text."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_text = ""

    def set_search_text(self, text: str) -> None:
        self._search_text = (text or "").lower()

    def paint(self, painter: QPainter, option, index: QModelIndex):
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text is None:
            text = ""
        text = str(text)

        # If nothing to highlight, use default painting
        if not self._search_text or not text:
            super().paint(painter, option, index)
            return

        painter.save()

        # --- Selection / hover background ---
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif option.state & QStyle.StateFlag.State_MouseOver:
            sel_color = option.palette.highlight().color()
            painter.fillRect(option.rect, sel_color.lighter(160))

        # --- Find all match positions (case-insensitive) ---
        text_lower = text.lower()
        search_lower = self._search_text
        matches: list[tuple[int, int]] = []
        start = 0
        while True:
            pos = text_lower.find(search_lower, start)
            if pos == -1:
                break
            matches.append((pos, pos + len(search_lower)))
            start = pos + 1

        if not matches:
            # No actual match — draw normally and bail out
            painter.setPen(option.palette.color(QPalette.ColorRole.Text))
            painter.drawText(option.rect, option.displayAlignment, text)
            painter.restore()
            return

        # --- Measure & position ---
        fm = option.fontMetrics
        alignment = option.displayAlignment
        rect = QRectF(option.rect).adjusted(4, 0, -4, 0)  # 4 px horizontal padding

        # Resolve starting X based on horizontal alignment
        total_width = fm.horizontalAdvance(text)
        if alignment & Qt.AlignmentFlag.AlignRight:
            x = rect.right() - total_width
        elif alignment & Qt.AlignmentFlag.AlignCenter:
            x = rect.center().x() - total_width / 2.0
        else:
            x = rect.x()

        y = rect.y()
        h = rect.height()

        # --- Reusable objects ---
        bold_font = QFont(option.font)
        bold_font.setBold(True)
        text_pen = option.palette.color(
            QPalette.ColorRole.HighlightedText if (option.state & QStyle.StateFlag.State_Selected)
            else QPalette.ColorRole.Text
        )
        match_text_pen = QColor(0, 0, 0)  # Dark text on yellow BG

        # --- Draw segments ---
        cursor = x
        last_end = 0
        v_flags = alignment & (Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter
                               | Qt.AlignmentFlag.AlignBottom)
        if not v_flags:
            v_flags = Qt.AlignmentFlag.AlignVCenter

        for match_start, match_end in matches:
            # Non-match segment before this match
            if last_end < match_start:
                seg = text[last_end:match_start]
                seg_w = fm.horizontalAdvance(seg)
                painter.setPen(text_pen)
                painter.setFont(option.font)
                painter.drawText(
                    QRectF(cursor, y, seg_w, h),
                    v_flags | Qt.AlignmentFlag.AlignLeft,
                    seg,
                )
                cursor += seg_w

            # Matched segment with highlight
            seg = text[match_start:match_end]
            seg_w = fm.horizontalAdvance(seg)

            # Background rect for the match
            painter.fillRect(QRectF(cursor, y, seg_w, h), HIGHLIGHT_BG)

            # Bold text on highlight
            painter.setPen(match_text_pen)
            painter.setFont(bold_font)
            painter.drawText(
                QRectF(cursor, y, seg_w, h),
                v_flags | Qt.AlignmentFlag.AlignLeft,
                seg,
            )
            cursor += seg_w
            last_end = match_end

        # Remaining non-match text after the last match
        if last_end < len(text):
            seg = text[last_end:]
            seg_w = fm.horizontalAdvance(seg)
            painter.setPen(text_pen)
            painter.setFont(option.font)
            painter.drawText(
                QRectF(cursor, y, seg_w, h),
                v_flags | Qt.AlignmentFlag.AlignLeft,
                seg,
            )

        painter.restore()

    def sizeHint(self, option, index: QModelIndex):
        return super().sizeHint(option, index)
