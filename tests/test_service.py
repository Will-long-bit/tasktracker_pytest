"""TaskService 业务测试。

演示：
- pytest-mock 的 mocker fixture（mock 通知器，验证调用）
- pytest-freezegun 的 freezetime fixture（冻结时间，测「逾期」逻辑）
- pytest-check 的软断言（一处失败不中断，继续收集其他断言）
- pytest-datadir 的 shared_datadir（从数据文件读取期望值）
- pytest-timeout 的 @pytest.mark.timeout（慢用例超时保护）
"""

import json
import time
from datetime import datetime

import pytest
from pytest_check import check

from tasktracker.models import Priority, Status, Task
from tasktracker.service import TaskService


def test_create_task_persists(service):
    task = service.create_task("写文档", assignee="alice")
    assert task.id is not None
    assert service.repo.get(task.id).title == "写文档"


def test_create_task_notifies_when_assignee(mocker, repository):
    notifier = mocker.MagicMock()
    svc = TaskService(repository, notifier)
    svc.create_task("买菜", assignee="alice")
    notifier.notify_assign.assert_called_once()


def test_create_task_no_notify_without_assignee(mocker, repository):
    notifier = mocker.MagicMock()
    svc = TaskService(repository, notifier)
    svc.create_task("扫地")  # 无负责人
    notifier.notify_assign.assert_not_called()


def test_complete_task(service, task):
    t = service.repo.add(task)
    done = service.complete_task(t.id)
    assert done.status == Status.DONE
    assert service.repo.get(t.id).status == Status.DONE


def test_complete_missing_raises(service):
    with pytest.raises(KeyError):
        service.complete_task(12345)


def test_complete_task_notifies(mocker, repository):
    notifier = mocker.MagicMock()
    svc = TaskService(repository, notifier)
    t = repository.add(Task(title="x"))
    svc.complete_task(t.id)
    notifier.notify_done.assert_called_once()


def test_overdue_with_freezegun(service, freezer):
    # 冻结「当前时间」为 2026-06-01
    freezer.move_to("2026-06-01")
    service.repo.add(Task(title="已过期", due_date=datetime(2026, 1, 1)))
    service.repo.add(Task(title="未到期", due_date=datetime(2026, 12, 1)))
    service.repo.add(Task(title="已完成", status=Status.DONE, due_date=datetime(2025, 1, 1)))
    overdue = service.overdue_tasks()
    titles = {t.title for t in overdue}
    assert titles == {"已过期"}


def test_stats_with_datadir(service, shared_datadir):
    service.repo.add(Task(title="a", status=Status.TODO))
    service.repo.add(Task(title="b", status=Status.TODO))
    service.repo.add(Task(title="c", status=Status.DONE))
    service.repo.add(Task(title="d", status=Status.IN_PROGRESS))
    stats = service.stats()
    expected = json.loads(
        (shared_datadir / "expected_stats.json").read_text(encoding="utf-8")
    )
    # pytest-check 软断言：下面任意一条失败，其余仍会执行
    check.equal(stats["todo"], expected["todo"])
    check.equal(stats["done"], expected["done"])
    check.equal(stats["in_progress"], expected["in_progress"])
    check.equal(stats["cancelled"], expected["cancelled"])


@pytest.mark.timeout(5)
def test_slow_operation_demo():
    """演示 pytest-timeout：用标记声明超时上限。

    这里 sleep 0.2s < 5s，正常通过；若把 0.2 改大超过 5s，pytest-timeout 会杀掉该用例。
    """
    time.sleep(0.2)
    assert True
