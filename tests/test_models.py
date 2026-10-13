"""领域模型单元测试。

演示：
- pytest.raises 校验构造参数
- pytest-freezegun 的 freezer fixture 冻结时间，验证 is_overdue 属性
"""

from datetime import datetime

import pytest

from tasktracker.models import Priority, Status, Task


def test_title_required():
    with pytest.raises(ValueError):
        Task(title="")


def test_default_status_priority():
    t = Task(title="x")
    assert t.status == Status.TODO
    assert t.priority == Priority.MEDIUM
    assert t.created_at is not None


def test_is_overdue(freezer):
    freezer.move_to("2026-06-01")
    past = Task(title="a", due_date=datetime(2026, 1, 1))
    future = Task(title="b", due_date=datetime(2026, 12, 1))
    none = Task(title="c")
    assert past.is_overdue is True
    assert future.is_overdue is False
    assert none.is_overdue is False
