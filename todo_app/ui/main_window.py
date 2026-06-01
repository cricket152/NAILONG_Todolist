from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QHeaderView, QMenuBar, QMenu,
    QStatusBar, QLabel, QLineEdit, QComboBox, QPushButton,
    QTabBar, QMessageBox
)
from PyQt6.QtCore import Qt, QByteArray, QPoint, QTimer
from PyQt6.QtGui import QAction, QIcon

from ..models import FilterParams
from ..database import DatabaseManager
from ..utils import resource_path
import os
from .task_table_model import TaskTableModel
from .task_dialog import TaskDialog
from .settings_dialog import SettingsDialog
from .tray_manager import TrayManager
from .delete_delegate import DeleteButtonDelegate
from .today_task_dialog import TodayTaskDialog
from .checkbox_delegate import CheckBoxDelegate

TAB_LABELS = ["DDL任务", "每日任务", "每周任务"]
TAB_TYPES = ["ddl", "daily", "weekly"]


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self._db = db
        self._tray: TrayManager | None = None

        self.setWindowTitle("Todo-List")
        self.resize(860, 580)
        self.setMinimumSize(640, 400)

        icon_path = self._get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        self._init_model()
        self._init_ui()
        self._init_menu_bar()
        self._init_status_bar()
        self._init_tray()
        self._connect_signals()
        self._init_overdue_timer()
        self._load_settings()
        self._refresh_view()

    def _init_model(self):
        self._model = TaskTableModel(self._db, self)
        self._current_filter = FilterParams(task_type="ddl")

    def _get_icon_path(self):
        p = resource_path("resources/app_icon2.png")
        return p if os.path.exists(p) else None

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)

        # --- Navigation tab bar ---
        self._tab_bar = QTabBar()
        self._tab_bar.setExpanding(False)
        self._tab_bar.setDrawBase(False)
        for label in TAB_LABELS:
            self._tab_bar.addTab(label)
        self._tab_bar.setCurrentIndex(0)
        layout.addWidget(self._tab_bar)

        # --- Filter bar ---
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("搜索:"))
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("搜索任务...")
        self._search_box.setClearButtonEnabled(True)
        filter_layout.addWidget(self._search_box)

        filter_layout.addWidget(QLabel("优先级:"))
        self._priority_combo = QComboBox()
        self._priority_combo.addItem("全部", "All")
        self._priority_combo.addItem("高", "High")
        self._priority_combo.addItem("中", "Medium")
        self._priority_combo.addItem("低", "Low")
        filter_layout.addWidget(self._priority_combo)

        self._status_label_widget = QLabel("状态:")
        self._status_combo = QComboBox()
        self._status_combo.addItem("全部", "All")
        self._status_combo.addItem("待完成", "Pending")
        self._status_combo.addItem("已完成", "Completed")
        self._status_label_widget.setVisible(True)
        self._status_combo.setVisible(True)

        filter_layout.addWidget(self._status_label_widget)
        filter_layout.addWidget(self._status_combo)

        self._clear_filter_btn = QPushButton("清除")
        self._clear_filter_btn.setFixedWidth(60)
        filter_layout.addWidget(self._clear_filter_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_widget)

        # --- Table ---
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        v_header = self._table.verticalHeader()
        v_header.setVisible(False)

        layout.addWidget(self._table)

        # Delete button delegate
        self._delete_delegate = DeleteButtonDelegate(self._table)
        self._delete_delegate.delete_clicked.connect(self._on_delete_by_id)

        # Checkbox delegate
        self._check_delegate = CheckBoxDelegate(self._table)

        self._apply_column_layout("ddl")

    def _apply_column_layout(self, task_type: str):
        h_header = self._table.horizontalHeader()
        action_col = 5 if task_type == "ddl" else 3
        check_col = 4 if task_type == "ddl" else 2
        if task_type == "ddl":
            h_header.setStretchLastSection(False)
            h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)   # 标题
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            h_header.resizeSection(1, 64)                                       # 优先级
            h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)   # 截止日期
            h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            h_header.resizeSection(3, 72)                                       # 状态
        else:
            h_header.setStretchLastSection(False)
            h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)   # 标题
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            h_header.resizeSection(1, 72)                                       # 优先级
        h_header.setSectionResizeMode(check_col, QHeaderView.ResizeMode.Fixed)
        h_header.resizeSection(check_col, 48)                                   # 完成
        h_header.setSectionResizeMode(action_col, QHeaderView.ResizeMode.Fixed)
        h_header.resizeSection(action_col, 44)                                  # 删除

        # Clear delegates from all columns, then set checkbox and action delegates
        for c in range(self._model.columnCount() + 2):
            self._table.setItemDelegateForColumn(c, None)
        self._table.setItemDelegateForColumn(check_col, self._check_delegate)
        self._table.setItemDelegateForColumn(action_col, self._delete_delegate)

    def _init_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("文件(&F)")
        add_action = QAction("添加任务(&A)", self)
        add_action.setShortcut("Ctrl+N")
        file_menu.addAction(add_action)

        edit_action = QAction("编辑任务(&E)", self)
        edit_action.setShortcut("Ctrl+E")
        file_menu.addAction(edit_action)

        file_menu.addSeparator()
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Alt+F4")
        file_menu.addAction(exit_action)

        remind_menu = menu_bar.addMenu("提醒(&R)")
        today_action = QAction("今日任务(&T)", self)
        today_action.setShortcut("Ctrl+T")
        remind_menu.addAction(today_action)
        all_action = QAction("全部任务(&A)", self)
        all_action.setShortcut("Ctrl+Shift+A")
        remind_menu.addAction(all_action)

        view_menu = menu_bar.addMenu("视图(&V)")
        settings_action = QAction("设置(&S)...", self)
        view_menu.addAction(settings_action)

        help_menu = menu_bar.addMenu("帮助(&H)")
        about_action = QAction("关于(&A)", self)
        help_menu.addAction(about_action)

        self._act_add = add_action
        self._act_edit = edit_action
        self._act_exit = exit_action
        self._act_today = today_action
        self._act_all = all_action
        self._act_settings = settings_action
        self._act_about = about_action

    def _init_status_bar(self):
        self._status_label = QLabel("就绪")
        self.statusBar().addWidget(self._status_label)

    def _init_tray(self):
        self._tray = TrayManager(self)
        self._tray.show_requested.connect(self._show_from_tray)
        self._tray.add_task_requested.connect(self._on_add_task)
        self._tray.exit_requested.connect(self._quit_app)

    def _connect_signals(self):
        # Tab bar
        self._tab_bar.currentChanged.connect(self._on_tab_changed)

        # Filter
        self._search_box.textChanged.connect(self._apply_filters)
        self._priority_combo.currentTextChanged.connect(self._apply_filters)
        self._status_combo.currentTextChanged.connect(self._apply_filters)
        self._clear_filter_btn.clicked.connect(self._clear_filters)

        # Table
        self._table.doubleClicked.connect(self._on_edit_current_task)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.horizontalHeader().sortIndicatorChanged.connect(self._on_sort_changed)

        # Menu
        self._act_add.triggered.connect(self._on_add_task)
        self._act_edit.triggered.connect(self._on_edit_current_task)
        self._act_exit.triggered.connect(self._quit_app)
        self._act_settings.triggered.connect(self._on_settings)
        self._act_today.triggered.connect(self._on_today_tasks)
        self._act_all.triggered.connect(self._on_all_tasks)
        self._act_about.triggered.connect(self._on_about)

    def _init_overdue_timer(self):
        """Periodically refresh overdue status and check for daily/weekly resets."""
        self._overdue_timer = QTimer(self)
        self._overdue_timer.setInterval(15_000)  # 15 seconds
        self._overdue_timer.timeout.connect(self._on_timer_tick)
        self._overdue_timer.start()

    def _on_timer_tick(self):
        self._db.check_and_reset_tasks()
        self._refresh_view()

    def _on_tab_changed(self, index: int):
        task_type = TAB_TYPES[index]
        is_ddl = task_type == "ddl"

        # Show/hide status filter for DDL only
        self._status_label_widget.setVisible(is_ddl)
        self._status_combo.setVisible(is_ddl)
        if not is_ddl:
            self._status_combo.setCurrentIndex(0)

        # Update model
        self._model.set_task_type(task_type)
        self._current_filter.task_type = task_type

        # Reset sort
        self._model.sort(-1, Qt.SortOrder.AscendingOrder)

        # Adjust columns
        self._apply_column_layout(task_type)

        self._refresh_view()

    def _apply_filters(self):
        self._current_filter.search_text = self._search_box.text().strip()
        self._current_filter.priority = self._priority_combo.currentData()
        self._current_filter.status = self._status_combo.currentData()
        self._model.refresh_data(self._current_filter)
        self._update_status_bar()

    def _clear_filters(self):
        self._search_box.clear()
        self._priority_combo.setCurrentIndex(0)
        self._status_combo.setCurrentIndex(0)

    def _on_sort_changed(self, column: int, order: Qt.SortOrder):
        self._model.sort(column, order)

    def _on_add_task(self):
        dlg = TaskDialog(self)
        if dlg.exec() == TaskDialog.DialogCode.Accepted and dlg.result_task:
            # If adding from a different tab, task_type from dialog overrides
            self._db.add_task(dlg.result_task)
            # Switch to the tab matching the new task's type
            new_type = dlg.result_task.task_type
            if new_type != self._current_filter.task_type:
                idx = TAB_TYPES.index(new_type)
                self._tab_bar.setCurrentIndex(idx)
                self._on_tab_changed(idx)
            else:
                self._refresh_view()

    def _on_edit_current_task(self):
        row = self._table.currentIndex().row()
        task = self._model.get_task(row)
        if task is None:
            return
        self._edit_task(task)

    def _edit_task(self, task):
        dlg = TaskDialog(self, task)
        if dlg.exec() == TaskDialog.DialogCode.Accepted and dlg.result_task:
            dlg.result_task.id = task.id
            self._db.update_task(dlg.result_task)
            # Switch tab if type changed
            new_type = dlg.result_task.task_type
            if new_type != self._current_filter.task_type:
                idx = TAB_TYPES.index(new_type)
                self._tab_bar.setCurrentIndex(idx)
                self._on_tab_changed(idx)
            else:
                self._refresh_view()

    def _on_toggle_complete(self):
        rows = self._selected_rows()
        for task in rows:
            self._db.toggle_complete(task.id)
        self._refresh_view()

    def _on_delete_task(self):
        rows = self._selected_rows()
        if not rows:
            return
        count = len(rows)
        title = rows[0].title if count == 1 else f"({count}个任务)"
        reply = QMessageBox(
            QMessageBox.Icon.Question, "确认删除",
            f"确定要删除 {title} 吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self
        )
        reply.button(QMessageBox.StandardButton.Yes).setText("是")
        reply.button(QMessageBox.StandardButton.No).setText("否")
        if reply.exec() == QMessageBox.StandardButton.Yes:
            for task in rows:
                self._db.delete_task(task.id)
            self._refresh_view()

    def _show_context_menu(self, point: QPoint):
        index = self._table.indexAt(point)
        if not index.isValid():
            return
        task = self._model.get_task(index.row())
        if task is None:
            return

        menu = QMenu(self)
        act_edit = menu.addAction("编辑")
        act_edit.triggered.connect(lambda: self._edit_task(task))

        label = "标为已完成" if task.status == "pending" else "标为待完成"
        act_toggle = menu.addAction(label)
        act_toggle.triggered.connect(lambda: self._db.toggle_complete(task.id) or self._refresh_view())

        menu.addSeparator()
        act_del = menu.addAction("删除")
        act_del.triggered.connect(lambda: self._on_delete_single(task))

        menu.exec(self._table.viewport().mapToGlobal(point))

    def _on_delete_single(self, task):
        reply = QMessageBox(
            QMessageBox.Icon.Question, "确认删除",
            f"确定要删除「{task.title}」吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self
        )
        reply.button(QMessageBox.StandardButton.Yes).setText("是")
        reply.button(QMessageBox.StandardButton.No).setText("否")
        if reply.exec() == QMessageBox.StandardButton.Yes:
            self._db.delete_task(task.id)
            self._refresh_view()

    def _on_delete_by_id(self, task_id: int):
        task = self._model.get_task_by_id(task_id)
        if task is None:
            return
        reply = QMessageBox(
            QMessageBox.Icon.Question, "确认删除",
            f"确定要删除「{task.title}」吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self
        )
        reply.button(QMessageBox.StandardButton.Yes).setText("是")
        reply.button(QMessageBox.StandardButton.No).setText("否")
        if reply.exec() == QMessageBox.StandardButton.Yes:
            self._db.delete_task(task_id)
            self._refresh_view()

    def _on_settings(self):
        dlg = SettingsDialog(self, self._db)
        dlg.exec()

    def _on_about(self):
        QMessageBox.about(
            self, "关于 Todo-List",
            "<b>Todo-List</b> v1.0<br><br>"
            "一个简洁的桌面待办事项管理工具。<br>"
            "PyQt6 + SQLite 构建。"
        )

    def _on_today_tasks(self):
        from datetime import datetime
        today_str = datetime.now().strftime("%Y年%m月%d日")
        tasks = self._db.get_today_tasks()
        dlg = TodayTaskDialog(tasks, f"{today_str} 待完成任务", self)
        dlg.exec()

    def _on_all_tasks(self):
        tasks = self._db.get_all_tasks_combined()
        dlg = TodayTaskDialog(tasks, "全部任务", self)
        dlg.exec()

    def _selected_rows(self) -> list:
        rows = []
        for index in self._table.selectionModel().selectedRows():
            task = self._model.get_task(index.row())
            if task:
                rows.append(task)
        return rows

    def _refresh_view(self):
        self._model.refresh_data(self._current_filter)
        self._update_status_bar()

    def _update_status_bar(self):
        total, pending, completed = self._model.task_count()
        self._status_label.setText(
            f"共 {total} 个任务 | {pending} 待完成 | {completed} 已完成"
        )

    def _load_settings(self):
        geom_str = self._db.get_setting("window_geometry")
        if geom_str:
            try:
                self.restoreGeometry(QByteArray.fromHex(geom_str.encode()))
            except Exception:
                pass

    def _save_settings(self):
        self._db.set_setting("window_geometry", self.saveGeometry().toHex().data().decode())

    def _show_from_tray(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _quit_app(self):
        self._save_settings()
        if self._tray:
            self._tray.hide()
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()

    def closeEvent(self, event):
        minimize_to_tray = self._db.get_setting("minimize_to_tray", "1") == "1"
        if minimize_to_tray and self._tray and self._tray.is_available():
            self.hide()
            event.ignore()
        else:
            self._save_settings()
            if self._tray:
                self._tray.hide()
            event.accept()
