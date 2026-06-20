from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    priority: str = "medium"
    due_date: Optional[str] = None
    status: str = "pending"
    created_at: str = ""
    completed_at: Optional[str] = None
    task_type: str = "ddl"
    deleted_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Task":
        return cls(
            id=row[0], title=row[1], description=row[2],
            priority=row[3], due_date=row[4],
            status=row[5], created_at=row[6], completed_at=row[7],
            task_type=row[8] if len(row) > 8 else "ddl",
            deleted_at=row[9] if len(row) > 9 else None
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "due_date": self.due_date,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "task_type": self.task_type,
            "deleted_at": self.deleted_at,
        }

    @property
    def is_overdue(self) -> bool:
        if self.status != "pending":
            return False
        if not self.due_date:
            return False
        try:
            due_dt = datetime.strptime(self.due_date, "%Y-%m-%d %H:%M")
            return due_dt < datetime.now()
        except ValueError:
            return self.due_date < datetime.now().strftime("%Y-%m-%d %H:%M")


# Priority constants — single source of truth
PRIORITY_LABELS = {"high": "高", "medium": "中", "low": "低"}
PRIORITY_LABELS_REVERSE = {"高": "high", "中": "medium", "低": "low"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
PRIORITY_COLORS = {"high": "#C0392B", "medium": "#E67E22", "low": "#A1887F"}


@dataclass
class FilterParams:
    search_text: str = ""
    priority: str = "All"
    status: str = "All"
    task_type: str = "ddl"
