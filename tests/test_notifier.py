"""Notifier 测试：用 pytest-httpx 拦截真实的 HTTP 请求。

演示：不联网也能确定性地验证「通知确实以正确的方法/URL/body 发出」。
"""

import json

import pytest

from tasktracker.models import Task
from tasktracker.notifier import Notifier

WEBHOOK = "https://hooks.example.com/notify"


def test_notify_assign_posts(httpx_mock, notifier):
    httpx_mock.add_response(url=WEBHOOK, method="POST", json={"ok": True})
    resp = notifier.notify_assign("alice", Task(id=1, title="买菜"))
    assert resp.status_code == 200

    request = httpx_mock.get_request()
    assert request.method == "POST"
    body = json.loads(request.content)
    assert body["event"] == "assigned"
    assert body["assignee"] == "alice"


def test_notify_done_posts(httpx_mock, notifier):
    httpx_mock.add_response(url=WEBHOOK, method="POST", json={"ok": True})
    resp = notifier.notify_done(Task(id=2, title="完成"))
    assert resp.status_code == 200


def test_notify_raises_on_http_error(httpx_mock, notifier):
    httpx_mock.add_response(url=WEBHOOK, method="POST", status_code=500)
    with pytest.raises(Exception):
        notifier.notify_assign("bob", Task(id=3, title="x"))
