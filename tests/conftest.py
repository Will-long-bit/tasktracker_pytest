"""共享 fixture 与 factory 注册。

这里集中放置：
1. pytest-factoryboy 的 TaskFactory 注册（注册后自动产生 `task_factory` fixture）
2. repository fixture：基于 tmp_path 的临时 SQLite，用例结束自动关闭（setup/teardown）
3. service fixture：注入 repository（默认不接通知器，避免测试中误发网络请求）
"""

import factory
import pytest
from pytest_factoryboy import register

from tasktracker.models import Priority, Status, Task
from tasktracker.repository import TaskRepository
from tasktracker.service import TaskService

# ---------- pytest-factoryboy：注册工厂 ----------
@register
class TaskFactory(factory.Factory):
    """构造 Task 对象的工厂，便于批量生成测试数据。"""

    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f"任务{n}")
    description = "默认描述"
    status = Status.TODO
    priority = Priority.MEDIUM
    assignee = factory.Sequence(lambda n: f"user{n}")
    due_date = None


WEBHOOK_URL = "https://hooks.example.com/notify"


# ---------- 持久层 fixture（每个用例独立的临时库） ----------
@pytest.fixture
def repository(tmp_path):
    repo = TaskRepository(str(tmp_path / "tasks.db"))
    yield repo
    repo.close()


# ---------- 业务服务 fixture ----------
@pytest.fixture
def service(repository):
    # 默认不注入通知器；需要验证通知的用例自行用 Notifier + httpx_mock
    return TaskService(repository, notifier=None)


@pytest.fixture
def notifier():
    """返回一个真实 Notifier（其 HTTP 调用会被用例里的 httpx_mock 拦截）。"""
    from tasktracker.notifier import Notifier

    return Notifier(WEBHOOK_URL)
