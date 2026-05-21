from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLineEdit, QPlainTextEdit, QComboBox, QCheckBox,
    QDateEdit, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import QDate

from ..models import Task


class TaskDialog(QDialog):
    def __init__(self, parent=None, task: Task = None):
        super().__init__(parent)
        self._edit_mode = task is not None
        self.result_task: Task | None = None

        self.setWindowTitle("编辑任务" if self._edit_mode else "添加任务")
        self.setMinimumWidth(420)
        self.resize(460, 350)

        self._init_ui(task)
        if task:
            self._populate(task)

    def _init_ui(self, task: Task = None):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)

        self._title_edit = QLineEdit()
        self._title_edit.setMaxLength(200)
        self._title_edit.setPlaceholderText("输入任务标题（必填）")
        form.addRow("标题:", self._title_edit)

        self._desc_edit = QPlainTextEdit()
        self._desc_edit.setPlaceholderText("输入描述（可选）")
        self._desc_edit.setMaximumHeight(100)
        form.addRow("描述:", self._desc_edit)

        self._priority_combo = QComboBox()
        self._priority_combo.addItems(["中", "高", "低"])
        self._priority_combo.setCurrentText("中")
        form.addRow("优先级:", self._priority_combo)

        due_layout = QHBoxLayout()
        self._due_check = QCheckBox("设置截止日期")
        self._due_edit = QDateEdit()
        self._due_edit.setCalendarPopup(True)
        self._due_edit.setDate(QDate.currentDate().addDays(1))
        self._due_edit.setEnabled(False)
        due_layout.addWidget(self._due_check)
        due_layout.addWidget(self._due_edit)
        due_layout.addStretch()
        form.addRow("截止日期:", due_layout)

        self._due_check.toggled.connect(self._due_edit.setEnabled)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self, task: Task):
        self._title_edit.setText(task.title)
        self._desc_edit.setPlainText(task.description)
        priority_labels = {"high": "高", "medium": "中", "low": "低"}
        self._priority_combo.setCurrentText(priority_labels.get(task.priority, "中"))
        if task.due_date:
            self._due_check.setChecked(True)
            self._due_edit.setDate(QDate.fromString(task.due_date, "yyyy-MM-dd"))

    def _on_accept(self):
        title = self._title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "输入错误", "任务标题不能为空。")
            self._title_edit.setFocus()
            return

        priority_map = {"高": "high", "中": "medium", "低": "low"}
        priority = priority_map.get(self._priority_combo.currentText(), "medium")

        due_date = None
        if self._due_check.isChecked():
            due_date = self._due_edit.date().toString("yyyy-MM-dd")

        self.result_task = Task(
            title=title,
            description=self._desc_edit.toPlainText().strip(),
            priority=priority,
            due_date=due_date,
            status="pending"
        )
        self.accept()
