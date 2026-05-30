from __future__ import annotations

import sqlite3
import os
from datetime import datetime

from .models import Task, FilterParams
from .utils import get_db_path


class DatabaseManager:
    def __init__(self):
        db_path = get_db_path()
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                priority    TEXT NOT NULL DEFAULT 'medium'
                            CHECK(priority IN ('high','medium','low')),
                due_date    TEXT,
                status      TEXT NOT NULL DEFAULT 'pending'
                            CHECK(status IN ('pending','completed')),
                created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                completed_at TEXT,
                task_type   TEXT NOT NULL DEFAULT 'ddl'
                            CHECK(task_type IN ('ddl','daily','weekly'))
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
            CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );

            INSERT OR IGNORE INTO settings (key, value) VALUES ('autostart', '0');
            INSERT OR IGNORE INTO settings (key, value) VALUES ('minimize_to_tray', '1');
            INSERT OR IGNORE INTO settings (key, value) VALUES ('window_geometry', '');
        """)
        # Migration: add task_type column if upgrading from old schema
        try:
            self._conn.execute("ALTER TABLE tasks ADD COLUMN task_type TEXT NOT NULL DEFAULT 'ddl'")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type)")
        except:
            pass
        self._conn.commit()

    def add_task(self, task: Task) -> int:
        cursor = self._conn.execute(
            "INSERT INTO tasks (title, description, priority, due_date, status, task_type) VALUES (?, ?, ?, ?, ?, ?)",
            (task.title, task.description, task.priority, task.due_date, task.status, task.task_type)
        )
        self._conn.commit()
        return cursor.lastrowid

    def update_task(self, task: Task):
        self._conn.execute(
            """UPDATE tasks SET title=?, description=?, priority=?, due_date=?,
               status=?, completed_at=?, task_type=? WHERE id=?""",
            (task.title, task.description, task.priority, task.due_date,
             task.status, task.completed_at, task.task_type, task.id)
        )
        self._conn.commit()

    def delete_task(self, task_id: int):
        self._conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self._conn.commit()

    def toggle_complete(self, task_id: int):
        task = self.get_task_by_id(task_id)
        if task is None:
            return
        if task.status == "pending":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._conn.execute(
                "UPDATE tasks SET status='completed', completed_at=? WHERE id=?",
                (now, task_id)
            )
        else:
            self._conn.execute(
                "UPDATE tasks SET status='pending', completed_at=NULL WHERE id=?",
                (task_id,)
            )
        self._conn.commit()

    def get_all_tasks(self, filter_params: FilterParams = None) -> list[Task]:
        if filter_params is None:
            filter_params = FilterParams()

        sql = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if filter_params.task_type:
            sql += " AND task_type = ?"
            params.append(filter_params.task_type)

        if filter_params.search_text:
            sql += " AND (title LIKE ? OR description LIKE ?)"
            like = f"%{filter_params.search_text}%"
            params.extend([like, like])

        if filter_params.priority != "All":
            sql += " AND priority = ?"
            params.append(filter_params.priority.lower())

        if filter_params.status != "All":
            status = "pending" if filter_params.status == "Pending" else "completed"
            sql += " AND status = ?"
            params.append(status)

        sql += " ORDER BY created_at DESC"
        cursor = self._conn.execute(sql, params)
        return [Task.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def _sort_tasks_by_type_priority(tasks: list[Task]) -> list[Task]:
        """Sort tasks: ddl → daily → weekly, within each high → medium → low."""
        type_order = {"ddl": 0, "daily": 1, "weekly": 2}
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (
            type_order.get(t.task_type, 99),
            priority_order.get(t.priority, 99)
        ))
        return tasks

    def get_today_tasks(self) -> list[Task]:
        """Return today's active tasks: all unfinished DDL, daily, and weekly tasks,
        sorted by type priority then priority level."""
        sql = """
            SELECT * FROM tasks WHERE status = 'pending'
            AND task_type IN ('ddl', 'daily', 'weekly')
        """
        cursor = self._conn.execute(sql)
        rows = cursor.fetchall()
        return self._sort_tasks_by_type_priority([Task.from_row(row) for row in rows])

    def get_all_tasks_combined(self) -> list[Task]:
        """Return all tasks (any status): DDL, daily, and weekly,
        sorted by type priority then priority level."""
        sql = "SELECT * FROM tasks WHERE task_type IN ('ddl', 'daily', 'weekly')"
        cursor = self._conn.execute(sql)
        rows = cursor.fetchall()
        return self._sort_tasks_by_type_priority([Task.from_row(row) for row in rows])

    def get_task_by_id(self, task_id: int) -> Task | None:
        cursor = self._conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        row = cursor.fetchone()
        return Task.from_row(row) if row else None

    def get_setting(self, key: str, default: str = "") -> str:
        cursor = self._conn.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self._conn.commit()
