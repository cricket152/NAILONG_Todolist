from dataclasses import dataclass, field
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

    @classmethod
    def from_row(cls, row: tuple) -> "Task":
        return cls(
            id=row[0], title=row[1], description=row[2],
            priority=row[3], due_date=row[4],
            status=row[5], created_at=row[6], completed_at=row[7],
            task_type=row[8] if len(row) > 8 else "ddl"
        )


@dataclass
class FilterParams:
    search_text: str = ""
    priority: str = "All"
    status: str = "All"
    task_type: str = "ddl"
