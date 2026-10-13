"""领域模型：Task 以及状态/优先级枚举。

注意：为简化时区处理，所有时间统一使用「去掉时区信息的 UTC 时间」（naive UTC）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Status(str, Enum):
    """任务状态。"""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """任务优先级。"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def _utcnow() -> datetime:
    """返回 naive UTC 当前时间（避免 aware/naive 比较错误）。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass
class Task:
    """一个任务。"""

    title: str
    description: str = ""
    status: Status = Status.TODO
    priority: Priority = Priority.MEDIUM
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime = None  # type: ignore[assignment]
    id: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("title 不能为空")
        if self.created_at is None:
            self.created_at = _utcnow()

    @property
    def is_overdue(self) -> bool:
        """是否已过截止时间（基于当前时间）。"""
        if self.due_date is None:
            return False
        return self.due_date < _utcnow()
