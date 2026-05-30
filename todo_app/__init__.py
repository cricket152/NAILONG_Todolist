import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .database import DatabaseManager
from .utils import resource_path
from .ui.main_window import MainWindow


def main() -> int:
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("TodoList")
    app.setOrganizationName("TodoListApp")

    # Set app icon (taskbar)
    icon_path = resource_path("resources/app_icon2.png")
    from PyQt6.QtGui import QIcon
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    # Load stylesheet
    style_path = resource_path("resources/style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    db = DatabaseManager()
    window = MainWindow(db)
    window.show()

    return app.exec()
