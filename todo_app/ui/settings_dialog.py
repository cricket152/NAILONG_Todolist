from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox,
    QCheckBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt

from ..database import DatabaseManager
from ..utils import set_autostart, get_autostart


class SettingsDialog(QDialog):
    def __init__(self, parent=None, db: DatabaseManager = None):
        super().__init__(parent)
        self._db = db
        self.setWindowTitle("设置")
        self.setMinimumWidth(320)
        self.resize(360, 160)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        group = QGroupBox("常规")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(8)

        self._autostart_check = QCheckBox("开机自启动")
        current_autostart = get_autostart()
        self._autostart_check.setChecked(current_autostart)
        group_layout.addWidget(self._autostart_check)

        self._tray_check = QCheckBox("关闭窗口时最小化到系统托盘")
        tray_setting = db.get_setting("minimize_to_tray", "1") if db else "1"
        self._tray_check.setChecked(tray_setting == "1")
        group_layout.addWidget(self._tray_check)

        layout.addWidget(group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if self._db:
            self._db.set_setting("minimize_to_tray", "1" if self._tray_check.isChecked() else "0")
        set_autostart(self._autostart_check.isChecked())
        self.accept()
