"""持久层：基于 SQLite 的 TaskRepository。

刻意使用标准库 sqlite3（不引入 ORM），目的是：
- 有真实的「集成测试」对象（落库、查询、更新）
- 配合 pytest 的 tmp_path fixture 可做到每个用例独立、可复现
- 配合 pytest-xdist 并行时，每个 worker 拿到自己的临时库，互不干扰
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Optional

from .models import Priority, Status, Task


class TaskRepository:
    """任务仓储，封装对 tasks 表的增删改查。"""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT DEFAULT '',
                status      TEXT NOT NULL,
                priority    TEXT NOT NULL,
                assignee    TEXT,
                due_date    TEXT,
                created_at  TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    # ---------- 写 ----------
    def add(self, task: Task) -> Task:
        """插入一条任务，并把自增 id 写回对象后返回。"""
        cur = self._conn.execute(
            """
            INSERT INTO tasks
                (title, description, status, priority, assignee, due_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.title,
                task.description,
                task.status.value,
                task.priority.value,
                task.assignee,
                task.due_date.isoformat() if task.due_date is not None else None,
                task.created_at.isoformat(),
            ),
        )
        self._conn.commit()
        task.id = cur.lastrowid
        return task

    def update(self, task: Task) -> Task:
        """按 id 全量更新任务字段。"""
        if task.id is None:
            raise ValueError("更新任务必须带有 id")
        self._conn.execute(
            """
            UPDATE tasks
            SET title=?, description=?, status=?, priority=?, assignee=?, due_date=?
            WHERE id=?
            """,
            (
                task.title,
                task.description,
                task.status.value,
                task.priority.value,
                task.assignee,
                task.due_date,
                task.id,
            ),
        )
        self._conn.commit()
        return task

    def update_status(self, task_id: int, status: Status) -> bool:
        """仅更新状态，返回是否命中并修改了记录。"""
        cur = self._conn.execute(
            "UPDATE tasks SET status=? WHERE id=?", (status.value, task_id)
        )
        self._conn.commit()
        return cur.rowcount > 0

    def delete(self, task_id: int) -> bool:
        """删除任务，返回是否命中记录。"""
        cur = self._conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self._conn.commit()
        return cur.rowcount > 0

    # ---------- 读 ----------
    def get(self, task_id: int) -> Optional[Task]:
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE id=?", (task_id,)
        ).fetchone()
        return self._row_to_task(row) if row else None

    def list(self, status: Optional[Status] = None, assignee: Optional[str] = None) -> List[Task]:
        """按状态 / 负责人过滤，返回任务列表。"""
        sql = "SELECT * FROM tasks"
        clauses: List[str] = []
        params: List[object] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(status.value)
        if assignee is not None:
            clauses.append("assignee = ?")
            params.append(assignee)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_task(r) for r in rows]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]

    def stats(self) -> dict:
        """统计各状态任务数量。"""
        rows = self._conn.execute(
            "SELECT status, COUNT(*) AS c FROM tasks GROUP BY status"
        ).fetchall()
        result = {s.value: 0 for s in Status}
        for r in rows:
            result[r["status"]] = r["c"]
        return result

    # ---------- 工具 ----------
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=Status(row["status"]),
            priority=Priority(row["priority"]),
            assignee=row["assignee"],
            due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] is not None else None,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def close(self) -> None:
        self._conn.close()
