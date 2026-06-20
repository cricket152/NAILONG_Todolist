from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLineEdit, QPlainTextEdit, QComboBox, QCheckBox,
    QDateEdit, QTimeEdit, QRadioButton, QButtonGroup, QGroupBox,
    QDialogButtonBox, QMessageBox, QWidget, QLabel, QPushButton
)
from PyQt6.QtCore import QDate, QTime, QDateTime

from ..models import Task, PRIORITY_LABELS, PRIORITY_LABELS_REVERSE


class TaskDialog(QDialog):
    def __init__(self, parent=None, task: Task = None, default_task_type: str = "ddl"):
        super().__init__(parent)
        self._edit_mode = task is not None
        self._original_task = task
        self._default_task_type = default_task_type if default_task_type in {"ddl", "daily", "weekly"} else "ddl"
        self.result_task: Task | None = None

        self.setWindowTitle("编辑任务" if self._edit_mode else "添加任务")
        self.setMinimumWidth(460)
        self.resize(480, 400)

        self._init_ui(task)
        if task:
            self._populate(task)

    def _init_ui(self, task: Task = None):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # --- Task type selector ---
        type_group = QGroupBox("任务类型")
        type_layout = QHBoxLayout(type_group)
        self._type_group = QButtonGroup(self)
        self._radio_ddl = QRadioButton("DDL任务")
        self._radio_daily = QRadioButton("每日任务")
        self._radio_weekly = QRadioButton("每周任务")
        self._type_group.addButton(self._radio_ddl, 0)
        self._type_group.addButton(self._radio_daily, 1)
        self._type_group.addButton(self._radio_weekly, 2)
        type_layout.addWidget(self._radio_ddl)
        type_layout.addWidget(self._radio_daily)
        type_layout.addWidget(self._radio_weekly)
        type_layout.addStretch()
        layout.addWidget(type_group)

        form = QFormLayout()
        form.setSpacing(10)

        self._title_edit = QLineEdit()
        self._title_edit.setMaxLength(200)
        self._title_edit.setPlaceholderText("输入任务标题（必填）")
        form.addRow("标题:", self._title_edit)

        self._priority_combo = QComboBox()
        self._priority_combo.addItems(["中", "高", "低"])
        self._priority_combo.setCurrentText("中")
        form.addRow("优先级:", self._priority_combo)

        # DDL-only fields (stored for show/hide)
        desc_label = QLabel("描述:")
        self._desc_edit = QPlainTextEdit()
        self._desc_edit.setPlaceholderText("输入描述（可选）")
        self._desc_edit.setMaximumHeight(100)
        form.addRow(desc_label, self._desc_edit)
        self._desc_label = desc_label

        due_label = QLabel("截止日期:")
        due_layout = QHBoxLayout()
        self._due_check = QCheckBox("设置截止日期")
        self._due_date_edit = QDateEdit()
        self._due_date_edit.setCalendarPopup(True)
        self._due_date_edit.setDate(QDate.currentDate().addDays(1))
        self._due_date_edit.setEnabled(False)
        self._due_time_edit = QTimeEdit()
        self._due_time_edit.setDisplayFormat("HH:mm")
        self._due_time_edit.setTime(QTime(23, 59))
        self._due_time_edit.setEnabled(False)
        due_layout.addWidget(self._due_check)
        due_layout.addWidget(self._due_date_edit)
        due_layout.addWidget(self._due_time_edit)

        self._today_btn = QPushButton("今天")
        self._tomorrow_btn = QPushButton("明天")
        self._next_week_btn = QPushButton("下周")
        self._today_btn.setFixedWidth(54)
        self._tomorrow_btn.setFixedWidth(54)
        self._next_week_btn.setFixedWidth(54)
        due_layout.addWidget(self._today_btn)
        due_layout.addWidget(self._tomorrow_btn)
        due_layout.addWidget(self._next_week_btn)
        due_layout.addStretch()
        form.addRow(due_label, due_layout)
        self._due_label = due_label
        self._due_layout = due_layout

        self._due_check.toggled.connect(self._due_date_edit.setEnabled)
        self._due_check.toggled.connect(self._due_time_edit.setEnabled)
        self._today_btn.clicked.connect(lambda: self._set_due_date(QDate.currentDate()))
        self._tomorrow_btn.clicked.connect(lambda: self._set_due_date(QDate.currentDate().addDays(1)))
        self._next_week_btn.clicked.connect(lambda: self._set_due_date(QDate.currentDate().addDays(7)))

        layout.addLayout(form)

        # Connect type change
        self._radio_ddl.toggled.connect(self._on_type_changed)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("确认")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self._default_task_type == "daily":
            self._radio_daily.setChecked(True)
        elif self._default_task_type == "weekly":
            self._radio_weekly.setChecked(True)
        else:
            self._radio_ddl.setChecked(True)
        self._title_edit.setFocus()

    def _set_due_date(self, date: QDate):
        self._due_check.setChecked(True)
        self._due_date_edit.setDate(date)
        self._due_time_edit.setTime(QTime(23, 59))

    def _on_type_changed(self):
        is_ddl = self._radio_ddl.isChecked()
        # Description row
        self._desc_label.setVisible(is_ddl)
        self._desc_edit.setVisible(is_ddl)
        # Due date row
        self._due_label.setVisible(is_ddl)
        for i in range(self._due_layout.count()):
            w = self._due_layout.itemAt(i).widget()
            if w:
                w.setVisible(is_ddl)

    def _populate(self, task: Task):
        self._title_edit.setText(task.title)
        self._desc_edit.setPlainText(task.description)
        self._priority_combo.setCurrentText(PRIORITY_LABELS.get(task.priority, "中"))
        if task.task_type == "daily":
            self._radio_daily.setChecked(True)
        elif task.task_type == "weekly":
            self._radio_weekly.setChecked(True)
        else:
            self._radio_ddl.setChecked(True)
        if task.due_date:
            self._due_check.setChecked(True)
            dt = QDateTime.fromString(task.due_date, "yyyy-MM-dd HH:mm")
            if dt.isValid():
                self._due_date_edit.setDate(dt.date())
                self._due_time_edit.setTime(dt.time())
            else:
                d = QDate.fromString(task.due_date, "yyyy-MM-dd")
                if d.isValid():
                    self._due_date_edit.setDate(d)
                    self._due_time_edit.setTime(QTime(23, 59))

    def _on_accept(self):
        title = self._title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "输入错误", "任务标题不能为空。")
            self._title_edit.setFocus()
            return

        priority = PRIORITY_LABELS_REVERSE.get(self._priority_combo.currentText(), "medium")

        if self._radio_daily.isChecked():
            task_type = "daily"
        elif self._radio_weekly.isChecked():
            task_type = "weekly"
        else:
            task_type = "ddl"

        due_date = None
        description = ""
        if task_type == "ddl":
            description = self._desc_edit.toPlainText().strip()
            if self._due_check.isChecked():
                d = self._due_date_edit.date().toString("yyyy-MM-dd")
                t = self._due_time_edit.time().toString("HH:mm")
                due_date = f"{d} {t}"

        self.result_task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            status=self._original_task.status if self._original_task else "pending",
            completed_at=self._original_task.completed_at if self._original_task else None,
            task_type=task_type
        )
        self.accept()
