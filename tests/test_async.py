"""异步测试：pytest-asyncio + pytest-httpx。"""

import pytest

from tasktracker.async_client import fetch_remote_config


@pytest.mark.asyncio
async def test_fetch_remote_config(httpx_mock):
    httpx_mock.add_response(
        url="https://api.example.com/config",
        json={"features": ["a", "b"], "version": "1.0"},
    )
    cfg = await fetch_remote_config("https://api.example.com")
    assert cfg["features"] == ["a", "b"]
    assert cfg["version"] == "1.0"
