"""异步客户端：用 httpx.AsyncClient 拉取远程配置。

适合用 pytest-asyncio（运行异步用例）+ pytest-httpx（拦截异步请求）来测试。
"""

from __future__ import annotations

import httpx


async def fetch_remote_config(base_url: str = "https://api.example.com") -> dict:
    """异步获取远程配置，返回解析后的 JSON。"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{base_url}/config")
        resp.raise_for_status()
        return resp.json()
