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
        # Schema-version based incremental migration
        current_version_str = self.get_setting("schema_version", "0")
        try:
            current_version = int(current_version_str)
        except ValueError:
            current_version = 0

        if current_version < 1:
            try:
                self._conn.execute(
                    "ALTER TABLE tasks ADD COLUMN task_type TEXT NOT NULL DEFAULT 'ddl'"
                )
                self._conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type)"
                )
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    raise
                # Column already exists (e.g. brand-new DB created with task_type)
            self.set_setting("schema_version", "1")

        if current_version < 2:
            try:
                self._conn.execute(
                    "ALTER TABLE tasks ADD COLUMN deleted_at TEXT"
                )
                self._conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tasks_deleted_at ON tasks(deleted_at)"
                )
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    raise
                # Column already exists (e.g. brand-new DB created with deleted_at)
            self.set_setting("schema_version", "2")

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

    def soft_delete_task(self, task_id: int):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._conn.execute(
            "UPDATE tasks SET deleted_at=? WHERE id=?",
            (now, task_id)
        )
        self._conn.commit()

    def restore_task(self, task_id: int):
        self._conn.execute(
            "UPDATE tasks SET deleted_at=NULL WHERE id=?",
            (task_id,)
        )
        self._conn.commit()

    def get_all_tasks(self, filter_params: FilterParams = None) -> list[Task]:
        if filter_params is None:
            filter_params = FilterParams()

        sql = "SELECT * FROM tasks WHERE deleted_at IS NULL"
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
            AND deleted_at IS NULL
        """
        cursor = self._conn.execute(sql)
        rows = cursor.fetchall()
        return self._sort_tasks_by_type_priority([Task.from_row(row) for row in rows])

    def get_all_tasks_combined(self) -> list[Task]:
        """Return all tasks (any status): DDL, daily, and weekly,
        sorted by type priority then priority level."""
        sql = "SELECT * FROM tasks WHERE task_type IN ('ddl', 'daily', 'weekly') AND deleted_at IS NULL"
        cursor = self._conn.execute(sql)
        rows = cursor.fetchall()
        return self._sort_tasks_by_type_priority([Task.from_row(row) for row in rows])

    def get_overdue_tasks(self) -> list[Task]:
        """Return tasks where status != 'completed', not deleted,
        due_date is set, and due_date is in the past. Ordered by due_date ASC."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = """
            SELECT * FROM tasks
            WHERE status != 'completed'
            AND deleted_at IS NULL
            AND due_date IS NOT NULL
            AND due_date != ''
            AND due_date < ?
            ORDER BY due_date ASC
        """
        cursor = self._conn.execute(sql, (now_str,))
        return [Task.from_row(row) for row in cursor.fetchall()]

    def get_task_counts(self) -> dict:
        """Return counts for status bar: today_due, overdue, incomplete."""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # today_due: DDL tasks due today (due_date date part == today),
        # not completed, not deleted
        cursor = self._conn.execute(
            """SELECT COUNT(*) FROM tasks
               WHERE task_type = 'ddl'
               AND status != 'completed'
               AND deleted_at IS NULL
               AND due_date IS NOT NULL
               AND due_date != ''
               AND due_date >= ?
               AND due_date < ?""",
            (today_str + " 00:00", today_str + " 24:00")
        )
        today_due = cursor.fetchone()[0]

        # overdue: same definition as get_overdue_tasks
        cursor = self._conn.execute(
            """SELECT COUNT(*) FROM tasks
               WHERE status != 'completed'
               AND deleted_at IS NULL
               AND due_date IS NOT NULL
               AND due_date != ''
               AND due_date < ?""",
            (now.strftime("%Y-%m-%d %H:%M"),)
        )
        overdue = cursor.fetchone()[0]

        # incomplete: all tasks not completed and not deleted
        cursor = self._conn.execute(
            """SELECT COUNT(*) FROM tasks
               WHERE status != 'completed'
               AND deleted_at IS NULL"""
        )
        incomplete = cursor.fetchone()[0]

        return {
            "today_due": today_due,
            "overdue": overdue,
            "incomplete": incomplete,
        }

    def get_all_tasks_for_export(self) -> list[Task]:
        """Return ALL tasks including soft-deleted, ordered by created_at DESC."""
        sql = "SELECT * FROM tasks ORDER BY created_at DESC"
        cursor = self._conn.execute(sql)
        return [Task.from_row(row) for row in cursor.fetchall()]

    def check_and_reset_tasks(self):
        """Reset daily tasks on date change and weekly tasks on ISO week change."""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # Daily reset: reset if last reset date != today
        last_daily = self.get_setting("last_daily_reset", "")
        if last_daily != today_str:
            self._conn.execute(
                "UPDATE tasks SET status='pending', completed_at=NULL "
                "WHERE task_type='daily' AND status='completed'"
            )
            self.set_setting("last_daily_reset", today_str)

        # Weekly reset: reset when ISO week changes (day-agnostic)
        iso_year, iso_week, _ = now.isocalendar()
        current_week_key = f"{iso_year}-W{iso_week}"
        last_weekly = self.get_setting("last_weekly_reset", "")
        if last_weekly != current_week_key:
            self._conn.execute(
                "UPDATE tasks SET status='pending', completed_at=NULL "
                "WHERE task_type='weekly' AND status='completed'"
            )
            self.set_setting("last_weekly_reset", current_week_key)
        self._conn.commit()

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
