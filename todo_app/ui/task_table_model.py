from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor

from ..models import Task, FilterParams
from ..database import DatabaseManager

COLUMNS_DDL = ["标题", "优先级", "截止日期", "状态", "操作"]
COLUMNS_SIMPLE = ["标题", "优先级", "操作"]
ACTION_COL_DDL = 4
ACTION_COL_SIMPLE = 2

PRIORITY_MAP = {"high": "高", "medium": "中", "low": "低"}
STATUS_MAP = {"pending": "待完成", "completed": "已完成"}
OVERDUE_COLOR = QColor("#C0392B")


class TaskTableModel(QAbstractTableModel):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self._db = db
        self._tasks: list[Task] = []
        self._filter = FilterParams()
        self._sort_column = -1
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._task_type = "ddl"

    @property
    def columns(self) -> list[str]:
        return COLUMNS_DDL if self._task_type == "ddl" else COLUMNS_SIMPLE

    def set_task_type(self, task_type: str):
        self._task_type = task_type

    def rowCount(self, parent=QModelIndex()):
        return len(self._tasks)

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def _is_overdue(self, task: Task) -> bool:
        if self._task_type != "ddl":
            return False
        if not task.due_date or task.status != "pending":
            return False
        return task.due_date < datetime.now().strftime("%Y-%m-%d %H:%M")

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        task = self._tasks[index.row()]
        col = index.column()
        is_ddl = self._task_type == "ddl"

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return task.title
            elif col == 1:
                return PRIORITY_MAP.get(task.priority, task.priority)
            elif col == 2 and is_ddl:
                return task.due_date or ""
            elif col == 3 and is_ddl:
                if self._is_overdue(task):
                    return "已超时"
                return STATUS_MAP.get(task.status, task.status)

        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 1:
                return {"high": QColor("#C0392B"), "medium": QColor("#E67E22"),
                        "low": QColor("#A1887F")}.get(task.priority, QColor("#3E2723"))
            if col == 3 and is_ddl:
                if self._is_overdue(task):
                    return OVERDUE_COLOR
                return QColor("#6B8E6B") if task.status == "completed" else QColor("#6D4C41")

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (1, 2, 3) if is_ddl else col == 1:
                return Qt.AlignmentFlag.AlignCenter

        if role == Qt.ItemDataRole.ToolTipRole:
            return f"{task.title}\n{task.description}" if task.description else task.title

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.columns[section]
        return None

    def refresh_data(self, filter_params: FilterParams = None):
        self.beginResetModel()
        if filter_params is not None:
            self._filter = filter_params
        self._tasks = self._db.get_all_tasks(self._filter)
        if self._sort_column >= 0:
            self._sort()
        self.endResetModel()

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        self._sort_column = column
        self._sort_order = order
        self.beginResetModel()
        self._sort()
        self.endResetModel()

    def _sort(self):
        if self._task_type == "ddl":
            key_map = {
                0: lambda t: t.title.lower(),
                1: lambda t: {"high": 0, "medium": 1, "low": 2}[t.priority],
                2: lambda t: t.due_date or "9999",
                3: lambda t: t.status,
            }
        else:
            key_map = {
                0: lambda t: t.title.lower(),
                1: lambda t: {"high": 0, "medium": 1, "low": 2}[t.priority],
            }
        key = key_map.get(self._sort_column, lambda t: t.created_at)
        self._tasks.sort(key=key, reverse=self._sort_order == Qt.SortOrder.DescendingOrder)

    def get_task(self, row: int) -> Task | None:
        if 0 <= row < len(self._tasks):
            return self._tasks[row]
        return None

    def get_task_by_id(self, task_id: int) -> Task | None:
        for t in self._tasks:
            if t.id == task_id:
                return t
        return None

    def task_count(self) -> tuple[int, int, int]:
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks if t.status == "completed")
        return total, total - completed, completed
