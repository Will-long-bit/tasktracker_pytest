"""业务逻辑层：TaskService。

把 repository 与 notifier 作为构造参数注入（依赖倒置），
这样既能在生产环境接入真实实现，又能在测试中轻松替换 / mock。
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from .models import Priority, Status, Task
from .notifier import Notifier
from .repository import TaskRepository


class TaskService:
    """任务服务：编排仓储与通知。"""

    def __init__(
        self,
        repository: TaskRepository,
        notifier: Optional[Notifier] = None,
    ) -> None:
        self.repo = repository
        self.notifier = notifier

    # ---------- 用例：创建 ----------
    def create_task(
        self,
        title: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,
        assignee: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            priority=priority,
            assignee=assignee,
            due_date=due_date,
        )
        created = self.repo.add(task)
        # 若指定了负责人且提供了通知器，则发送「分配」通知
        if self.notifier is not None and assignee is not None:
            self.notifier.notify_assign(assignee, created)
        return created

    # ---------- 用例：完成 ----------
    def complete_task(self, task_id: int) -> Task:
        task = self.repo.get(task_id)
        if task is None:
            raise KeyError(f"任务 {task_id} 不存在")
        task.status = Status.DONE
        self.repo.update(task)
        if self.notifier is not None:
            self.notifier.notify_done(task)
        return task

    # ---------- 用例：逾期检测（时间相关，便于 freezegun 演示） ----------
    def overdue_tasks(self, now: Optional[datetime] = None) -> List[Task]:
        """返回所有「未完成且已过截止时间」的任务。

        now 参数默认取当前时间；测试时可用 freezegun 冻结时间，或显式传入固定值。
        """
        from .models import _utcnow

        now = now or _utcnow()
        result: List[Task] = []
        for task in self.repo.list(status=Status.TODO) + self.repo.list(
            status=Status.IN_PROGRESS
        ):
            if task.due_date is not None and task.due_date < now:
                result.append(task)
        return result

    # ---------- 用例：统计 ----------
    def stats(self) -> dict:
        return self.repo.stats()
