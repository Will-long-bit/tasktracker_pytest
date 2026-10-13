"""通知器：通过 HTTP POST 调用外部 Webhook。

生产环境会真正发起网络请求；在单元测试中我们用 pytest-httpx 拦截 httpx，
从而「不联网」也能确定性地验证通知行为。
"""

from __future__ import annotations

from typing import Optional

import httpx

from .models import Task


class Notifier:
    """向外部 Webhook 发送任务相关通知。"""

    def __init__(
        self,
        webhook_url: str,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self.webhook_url = webhook_url
        # 允许注入 client（测试时可传入 mock）；默认 None 表示运行时再创建真实 client
        self._client = client

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client()
        return self._client

    def notify_assign(self, assignee: str, task: Task) -> httpx.Response:
        """任务被分配时通知负责人。"""
        return self._post(
            {
                "event": "assigned",
                "assignee": assignee,
                "task_id": task.id,
                "title": task.title,
            }
        )

    def notify_done(self, task: Task) -> httpx.Response:
        """任务完成时通知。"""
        return self._post(
            {"event": "done", "task_id": task.id, "title": task.title}
        )

    def _post(self, payload: dict) -> httpx.Response:
        resp = self._get_client().post(self.webhook_url, json=payload)
        resp.raise_for_status()
        return resp
