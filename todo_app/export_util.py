import json
import csv
import os

from .models import Task


def export_to_json(tasks: list[Task], path: str) -> None:
    """Export tasks to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            [t.to_dict() for t in tasks],
            f,
            ensure_ascii=False,
            indent=2,
        )


def export_to_csv(tasks: list[Task], path: str) -> None:
    """Export tasks to a CSV file."""
    fieldnames = [
        "id", "title", "description", "priority", "due_date",
        "status", "created_at", "completed_at", "task_type", "deleted_at",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            writer.writerow(task.to_dict())
