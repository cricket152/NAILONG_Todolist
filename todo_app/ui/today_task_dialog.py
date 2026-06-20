from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QDialogButtonBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from ..models import PRIORITY_LABELS

TYPE_LABELS = {"ddl": "DDL任务", "daily": "每日任务", "weekly": "每周任务"}


class TodayTaskDialog(QDialog):
    """Dialog showing a consolidated list of tasks from all task types."""

    def __init__(self, tasks: list, title: str, parent=None):
        super().__init__(parent)
        self._tasks = tasks

        self.setWindowTitle(title)
        self.resize(700, 420)
        self.setMinimumSize(500, 300)

        self._init_ui(title)
        self._load_data()

    def _init_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Title label
        title_label = QLabel(f"📋 {title}")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Summary label
        self._summary_label = QLabel()
        self._summary_label.setStyleSheet("color: #8D6E63; margin-bottom: 4px;")
        layout.addWidget(self._summary_label)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "任务类型", "标题", "优先级", "截止日期", "状态"
        ])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)

        # Column sizing
        h_header = self._table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h_header.resizeSection(0, 80)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h_header.resizeSection(2, 64)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h_header.resizeSection(3, 140)
        h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        h_header.resizeSection(4, 72)

        layout.addWidget(self._table)

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("关闭")
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        tasks = self._tasks
        self._table.setRowCount(len(tasks))

        overdue_count = 0
        completed_count = 0
        ddl_count = 0
        daily_count = 0
        weekly_count = 0

        for row, task in enumerate(tasks):
            # Task type
            type_item = QTableWidgetItem(TYPE_LABELS.get(task.task_type, task.task_type))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, type_item)

            # Title
            title_item = QTableWidgetItem(task.title)
            self._table.setItem(row, 1, title_item)

            # Priority
            prio_item = QTableWidgetItem(PRIORITY_LABELS.get(task.priority, task.priority))
            prio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 2, prio_item)

            # Due date (DDL only)
            due_str = task.due_date if task.task_type == "ddl" and task.due_date else "—"
            due_item = QTableWidgetItem(due_str)
            due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, due_item)

            # Status — check overdue
            is_overdue = task.is_overdue

            if task.status == "completed":
                status_text = "✅ 已完成"
            elif is_overdue:
                status_text = "⏰ 已超时"
            else:
                status_text = "待完成"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 4, status_item)

            # Color overdue rows red, completed rows green
            if is_overdue:
                red = QColor("#D32F2F")
                for col in range(5):
                    item = self._table.item(row, col)
                    if item:
                        item.setForeground(red)
                overdue_count += 1
            elif task.status == "completed":
                green = QColor("#4CAF50")
                for col in range(5):
                    item = self._table.item(row, col)
                    if item:
                        item.setForeground(green)
                completed_count += 1

            # Count by type
            if task.task_type == "ddl":
                ddl_count += 1
            elif task.task_type == "daily":
                daily_count += 1
            elif task.task_type == "weekly":
                weekly_count += 1

        # Summary text
        parts = []
        if ddl_count:
            parts.append(f"DDL: {ddl_count}")
        if daily_count:
            parts.append(f"每日: {daily_count}")
        if weekly_count:
            parts.append(f"每周: {weekly_count}")
        pending_count = len(tasks) - completed_count
        summary = f"共 {len(tasks)} 个任务"
        if pending_count:
            summary += f"（{pending_count} 待完成"
            if parts:
                summary += f" · {' · '.join(parts)}"
            summary += "）"
        if completed_count:
            summary += f"  ✅ {completed_count} 已完成"
        if overdue_count:
            summary += f"  ⚠ {overdue_count} 已超时"
        self._summary_label.setText(summary)
