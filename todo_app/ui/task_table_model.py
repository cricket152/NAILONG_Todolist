from __future__ import annotations

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor

from ..models import Task, FilterParams, PRIORITY_LABELS, PRIORITY_ORDER, PRIORITY_COLORS
from ..database import DatabaseManager

COLUMNS_DDL = ["标题", "优先级", "截止日期", "状态", "完成", "删除"]
COLUMNS_SIMPLE = ["标题", "优先级", "完成", "删除"]
ACTION_COL_DDL = 5
ACTION_COL_SIMPLE = 3
CHECK_COL_DDL = 4
CHECK_COL_SIMPLE = 2

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
        self._search_text = ""

    @property
    def columns(self) -> list[str]:
        return COLUMNS_DDL if self._task_type == "ddl" else COLUMNS_SIMPLE

    def set_task_type(self, task_type: str):
        self._task_type = task_type

    def set_search_text(self, text: str) -> None:
        self._search_text = (text or "").lower()
        if self.rowCount() > 0 and self.columnCount() > 0:
            top_left = self.index(0, 0)
            bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
            self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])

    def search_text(self) -> str:
        return self._search_text

    def rowCount(self, parent=QModelIndex()):
        return len(self._tasks)

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        task = self._tasks[index.row()]
        col = index.column()
        is_ddl = self._task_type == "ddl"
        check_col = CHECK_COL_DDL if is_ddl else CHECK_COL_SIMPLE

        if role == Qt.ItemDataRole.CheckStateRole and col == check_col:
            return Qt.CheckState.Checked if task.status == "completed" else Qt.CheckState.Unchecked

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return task.title
            elif col == 1:
                return PRIORITY_LABELS.get(task.priority, task.priority)
            elif col == 2 and is_ddl:
                return task.due_date or ""
            elif col == 3 and is_ddl:
                if task.is_overdue:
                    return "已超时"
                return STATUS_MAP.get(task.status, task.status)

        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 1:
                return QColor(PRIORITY_COLORS.get(task.priority, "#3E2723"))
            if col == 3 and is_ddl:
                if task.is_overdue:
                    return OVERDUE_COLOR
                return QColor("#6B8E6B") if task.status == "completed" else QColor("#6D4C41")

        if role == Qt.ItemDataRole.TextAlignmentRole:
            center_cols = (1, 2, 3, check_col) if is_ddl else (1, check_col)
            if col in center_cols:
                return Qt.AlignmentFlag.AlignCenter

        if role == Qt.ItemDataRole.ToolTipRole:
            return f"{task.title}\n{task.description}" if task.description else task.title

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.columns[section]
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        is_ddl = self._task_type == "ddl"
        check_col = CHECK_COL_DDL if is_ddl else CHECK_COL_SIMPLE
        if index.column() == check_col:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        is_ddl = self._task_type == "ddl"
        check_col = CHECK_COL_DDL if is_ddl else CHECK_COL_SIMPLE
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == check_col:
            task = self._tasks[index.row()]
            new_status = "completed" if value == Qt.CheckState.Checked else "pending"
            self._db.toggle_complete(task.id)
            # Re-read to get accurate completed_at from the DB
            updated = self._db.get_task_by_id(task.id)
            if updated is not None:
                task.status = updated.status
                task.completed_at = updated.completed_at
            else:
                task.status = new_status
                task.completed_at = None if new_status != "completed" else task.completed_at
            self.dataChanged.emit(index, index, [role])
            # Also emit dataChanged for status column (col 3 in DDL) to update display
            if is_ddl:
                status_idx = self.index(index.row(), 3)
                self.dataChanged.emit(status_idx, status_idx, [Qt.ItemDataRole.DisplayRole])
            return True
        return False

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
                1: lambda t: PRIORITY_ORDER[t.priority],
                2: lambda t: t.due_date or "9999",
                3: lambda t: t.status,
                4: lambda t: t.status,   # checkbox column sorts by status
            }
        else:
            key_map = {
                0: lambda t: t.title.lower(),
                1: lambda t: PRIORITY_ORDER[t.priority],
                2: lambda t: t.status,   # checkbox column sorts by status
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
