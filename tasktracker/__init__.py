"""tasktracker —— 一个用于练习 pytest 进阶插件的「任务/工单管理」领域模型。

本包故意做成「有真实复杂度」的业务代码：
- models：领域模型（Task / 状态 / 优先级）
- repository：基于 SQLite 的持久层（适合做集成测试）
- service：业务逻辑层（含时间相关的「逾期」计算、统计）
- notifier：通过 HTTP 调用外部 Webhook 通知（适合用 pytest-httpx mock）
- async_client：异步拉取远程配置（适合用 pytest-asyncio + pytest-httpx）
"""

__version__ = "0.2.0"
