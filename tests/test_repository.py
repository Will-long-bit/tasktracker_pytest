"""TaskRepository 集成测试。

演示：
- pytest-factoryboy 的 task_factory 生成测试数据
- 基于 tmp_path 的临时 SQLite（真实落库，集成测试）
- @pytest.mark.parametrize 参数化
- 自定义 integration 标记（在 pyproject 中注册）
- pytest-randomly：用例间无状态依赖，随机顺序也能稳定通过
"""

from datetime import datetime

import pytest
from tasktracker.models import Priority, Status, Task

pytestmark = pytest.mark.integration


def test_add_and_get(repository, task):
    saved = repository.add(task)
    assert saved.id is not None
    fetched = repository.get(saved.id)
    assert fetched.title == task.title
    assert fetched.priority == task.priority


def test_roundtrip_due_date(repository):
    task = Task(title="截止任务", due_date=datetime(2026, 1, 1, 12, 0, 0))
    saved = repository.add(task)
    fetched = repository.get(saved.id)
    assert fetched.due_date == datetime(2026, 1, 1, 12, 0, 0)


def test_update_status(repository, task):
    t = repository.add(task)
    assert repository.update_status(t.id, Status.DONE) is True
    assert repository.get(t.id).status == Status.DONE
    # 不存在的 id 返回 False
    assert repository.update_status(99999, Status.DONE) is False


def test_list_filters(repository):
    repository.add(Task(title="a", status=Status.TODO, assignee="alice"))
    repository.add(Task(title="b", status=Status.DONE, assignee="alice"))
    repository.add(Task(title="c", status=Status.TODO, assignee="bob"))
    assert len(repository.list(status=Status.TODO)) == 2
    assert len(repository.list(assignee="alice")) == 2
    assert len(repository.list(status=Status.DONE, assignee="alice")) == 1


def test_delete(repository, task):
    t = repository.add(task)
    assert repository.delete(t.id) is True
    assert repository.get(t.id) is None
    assert repository.delete(t.id) is False


def test_count(repository):
    assert repository.count() == 0
    repository.add(Task(title="x"))
    repository.add(Task(title="y"))
    assert repository.count() == 2


@pytest.mark.parametrize("priority", [Priority.LOW, Priority.MEDIUM, Priority.HIGH])
def test_priority_persisted(repository, priority):
    t = repository.add(Task(title="p", priority=priority))
    assert repository.get(t.id).priority == priority


def test_update(repository, task):
    t = repository.add(task)
    t.title = "改名后"
    t.status = Status.IN_PROGRESS
    repository.update(t)
    fetched = repository.get(t.id)
    assert fetched.title == "改名后"
    assert fetched.status == Status.IN_PROGRESS


def test_update_requires_id(repository):
    with pytest.raises(ValueError):
        repository.update(Task(title="x"))

