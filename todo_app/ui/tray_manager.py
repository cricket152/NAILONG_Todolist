import os

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from ..utils import resource_path


class TrayManager(QObject):
    show_requested = pyqtSignal()
    add_task_requested = pyqtSignal()
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon = self._load_tray_icon()
        self._tray = QSystemTrayIcon(self._icon, parent)

        menu = QMenu()
        show_action = menu.addAction("显示窗口")
        show_action.triggered.connect(self.show_requested.emit)
        add_action = menu.addAction("添加任务...")
        add_action.triggered.connect(self.add_task_requested.emit)
        menu.addSeparator()
        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self.exit_requested.emit)

        self._tray.setContextMenu(menu)
        self._tray.setToolTip("Todo-List")
        self._tray.activated.connect(self._on_activated)

        if self._tray.isSystemTrayAvailable():
            self._tray.show()

    def _load_tray_icon(self) -> QIcon:
        p = resource_path("resources/app_icon2.png")
        if os.path.exists(p):
            return QIcon(p)
        return self._create_fallback_icon()

    def _create_fallback_icon(self) -> QIcon:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#8D6E63"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(4, 4, 24, 24, 6, 6)
        painter.setPen(QColor("#ffffff"))
        font = painter.font()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "✓")
        painter.end()
        return QIcon(pixmap)

    def _on_activated(self, reason):
        try:
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                self.show_requested.emit()
        except TypeError:
            # PyQt6 on some Windows versions cannot convert the C++
            # ActivationReason enum to a Python object for comparison.
            # DoubleClick has the integer value 2.
            try:
                if int(reason) == 2:
                    self.show_requested.emit()
            except (TypeError, ValueError):
                pass

    def is_available(self) -> bool:
        return self._tray.isSystemTrayAvailable()

    def show_notification(self, title: str, message: str) -> None:
        """Show a system tray notification balloon."""
        if self._tray is None:
            return
        try:
            self._tray.showMessage(
                title, message, QSystemTrayIcon.MessageIcon.Information, 5000
            )
        except Exception:
            pass

    def hide(self):
        if self._tray.isSystemTrayAvailable():
            self._tray.hide()
