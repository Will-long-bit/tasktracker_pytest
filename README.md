# pytest 进阶实战项目：tasktracker（含 13 个常用第三方插件）

> 这是上一版「购物车」项目的**进阶重做版**：删掉旧内容，引入了 **13 个常用的第三方 pytest 插件**，
> 并围绕一个**更有真实复杂度的业务领域**（任务 / 工单管理：持久层 + 业务层 + HTTP 通知 + 异步客户端）
> 把每个插件都用在「真实用例」上，而不是玩具示例。
>
> 已在本机调试跑通：**28 passed，2 rerun（flaky 用例重跑后通过），覆盖率 100%**，并产出 HTML 报告。
> 工程化程度（README / LICENSE / .gitignore / CI）完备，可直接上传 GitHub。

---

## 1. 用到的第三方插件清单

所有插件均已用 `pip install -r requirements.txt` 安装，并与 **pytest 9.1.1** 兼容。

| 插件 | 作用 | 在本项目中的演示位置 |
| --- | --- | --- |
| **pytest-cov** | 覆盖率统计 | `pytest --cov=tasktracker --cov-report=term-missing`（结果 100%） |
| **pytest-xdist** | 并行执行 | `pytest -n auto`；repository 用 `tmp_path` 隔离各 worker 的临时库 |
| **pytest-mock** | `mocker` fixture（封装 unittest.mock） | `tests/test_service.py` 用 `mocker.MagicMock()` 验证通知调用 |
| **pytest-timeout** | 单用例超时保护 | `tests/test_service.py::test_slow_operation_demo` 的 `@pytest.mark.timeout(5)` |
| **pytest-randomly** | 随机化执行顺序（验证用例独立性） | 默认开启；运行时可见 `--randomly-seed=...` |
| **pytest-rerunfailures** | 失败自动重跑 | `tests/test_flaky.py::test_flaky_simulated` 的 `@pytest.mark.flaky(reruns=3)` |
| **pytest-html** | 生成 HTML 测试报告 | `pytest --html=report.html --self-contained-html` |
| **pytest-asyncio** | 异步用例支持 | `tests/test_async.py` 的 `async def`（`asyncio_mode=auto` 免装饰器） |
| **pytest-httpx** | 拦截 / 模拟 httpx 请求 | `tests/test_notifier.py`、`tests/test_async.py` 的 `httpx_mock` |
| **pytest-freezegun** | `freezer` fixture 冻结时间 | `tests/test_service.py::test_overdue_with_freezegun`、`tests/test_models.py` |
| **pytest-factoryboy** | 测试数据工厂 | `tests/conftest.py` 注册 `TaskFactory` → `task` fixture |
| **pytest-check** | 软断言（一处失败不中断） | `tests/test_service.py::test_stats_with_datadir` 的 `check.equal(...)` |
| **pytest-datadir** | 从数据文件读取测试数据 | `tests/test_service.py::test_stats_with_datadir` 的 `shared_datadir` |

> 额外的第三方库（由上述插件自动拉入）：`httpx`、`factory_boy`、`freezegun`、`coverage` 等。

---

## 2. 环境要求与安装

- Python ≥ 3.10（本机 3.14.3 验证）
- pytest ≥ 7（本机 9.1.1）
- 一步安装全部插件：

```bash
pip install -r requirements.txt
```

本项目同样用 `pyproject.toml` 的 `pythonpath = ["."]` 免去 `pip install -e .`，直接 `pytest` 即可 import `tasktracker` 包。

---

## 3. 目录结构

```
pytest/project/
├── pyproject.toml              # 项目元数据 + pytest 配置（asyncio_mode / cov / markers / filterwarnings）
├── requirements.txt            # 13 个第三方插件
├── requirements-dev.txt        # 等价于 requirements.txt（便于 CI）
├── .gitignore
├── LICENSE                     # MIT
├── README.md                   # 本文档
├── report.html                 # 运行 --html 后生成的报告（已 gitignore）
├── .github/workflows/pytest.yml# GitHub Actions：多版本 Python + 并行 + 覆盖率
├── tasktracker/                # 被测业务代码（tasktracker 包）
│   ├── __init__.py
│   ├── models.py               # Task 领域模型 + Status/Priority 枚举
│   ├── repository.py           # 基于 SQLite 的持久层（集成测试对象）
│   ├── service.py              # 业务逻辑层（逾期检测、统计、编排通知）
│   ├── notifier.py             # 通过 httpx 调用外部 Webhook
│   └── async_client.py         # 异步拉取远程配置
└── tests/
    ├── conftest.py             # TaskFactory 注册 + repository/service/notifier fixture
    ├── test_models.py          # 模型单测（raises + freezer）
    ├── test_repository.py       # 集成测试（factory + tmp_path + 参数化）
    ├── test_service.py          # 业务测试（mocker + freezer + check + datadir + timeout）
    ├── test_notifier.py         # HTTP 测试（httpx_mock）
    ├── test_async.py            # 异步测试（asyncio + httpx_mock）
    ├── test_flaky.py            # 偶发失败重跑（flaky）
    └── data/
        └── expected_stats.json  # pytest-datadir 读取的期望值
```

---

## 4. 业务代码概览（tasktracker）

- **models.py**：`Task` 数据类 + `Status`/`Priority` 枚举。时间统一用 naive UTC。
- **repository.py**：用标准库 `sqlite3` 实现 `TaskRepository`（增删改查 + 统计）。**刻意不引入 ORM**，
  以便做「真实落库」的集成测试，且每个用例用 `tmp_path` 拿到独立临时库，可并行、可复现。
- **service.py**：`TaskService` 把 `repository` 与 `notifier` 作为**构造参数注入**（依赖倒置），
  因此测试时可轻松替换为 mock。`overdue_tasks()` 依赖「当前时间」——用 freezegun 冻结即可确定性测试。
- **notifier.py**：`Notifier` 用 `httpx.Client().post(...)` 调外部 Webhook；测试时用 `httpx_mock` 拦截，不联网。
- **async_client.py**：`fetch_remote_config` 用 `httpx.AsyncClient`；用 pytest-asyncio + pytest-httpx 测试。

---

## 5. 怎么运行

> 全部在项目根目录（`pyproject.toml` 所在目录）执行。

```bash
# 基础运行（静默 + 摘要）
python -m pytest

# 详细模式
python -m pytest -v

# 并行执行（pytest-xdist）
python -m pytest -n auto

# 覆盖率（pytest-cov）——本机结果 100%
python -m pytest --cov=tasktracker --cov-report=term-missing

# 生成 HTML 报告（pytest-html）
python -m pytest --html=report.html --self-contained-html

# 查看随机种子（pytest-randomly 默认开启，每次顺序不同但结果稳定）
python -m pytest -v    # 输出里可见 --randomly-seed=...

# 失败自动重跑（pytest-rerunfailures 已在用例上用标记，也可命令行全局）
python -m pytest --reruns 2

# 组合拳：并行 + 覆盖率 + HTML 报告 + 摘要
python -m pytest -n auto --cov=tasktracker --cov-report=term-missing --html=report.html --self-contained-html -ra

# 只跑某文件 / 某用例
python -m pytest tests/test_notifier.py
python -m pytest tests/test_async.py::test_fetch_remote_config
```

**典型输出：**

```
28 passed, 2 rerun in 19.63s        # 2 rerun = flaky 用例前两次失败后重跑通过
```

---

## 6. 各插件「在哪看、怎么看」

| 插件 | 关键代码 | 怎么确认它生效 |
| --- | --- | --- |
| pytest-cov | `pyproject [tool.coverage.run] source=["tasktracker"]` | 加 `--cov=tasktracker` 后输出覆盖率表（100%） |
| pytest-xdist | 无代码侵入 | 加 `-n auto` 后头部显示 `created: N workers` |
| pytest-mock | `test_service.py`：`notifier = mocker.MagicMock()` | 断言 `notifier.notify_assign.assert_called_once()` |
| pytest-timeout | `test_service.py`：`@pytest.mark.timeout(5)` | 把 `time.sleep(0.2)` 改成 `time.sleep(6)` 会 `TIMEOUT` 杀掉 |
| pytest-randomly | 无代码侵入 | 运行头部 `Using --randomly-seed=...`，多次运行顺序不同但全绿 |
| pytest-rerunfailures | `test_flaky.py`：`@pytest.mark.flaky(reruns=3)` | 输出 `R` 表示重跑；用例用计数器模拟「前两次失败、第三次成功」 |
| pytest-html | 命令行 `--html=report.html` | 生成 `report.html`（自包含，浏览器直接打开） |
| pytest-asyncio | `test_async.py`：`async def` | 配置 `asyncio_mode="auto"`，无需 `@pytest.mark.asyncio` |
| pytest-httpx | `test_notifier.py`/`test_async.py`：`httpx_mock` | 不发真实请求即可断言请求方法/URL/body |
| pytest-freezegun | `test_service.py`/`test_models.py`：`freezer.move_to("2026-06-01")` | 冻结时间后 `overdue_tasks()` 结果确定 |
| pytest-factoryboy | `conftest.py`：`register(TaskFactory)` | 产生 `task`（实例）与 `task_factory`（工厂类）两个 fixture |
| pytest-check | `test_service.py`：`check.equal(...)` | 软断言：一处失败不中断，收集全部断言结果 |
| pytest-datadir | `test_service.py`：`shared_datadir / "expected_stats.json"` | 从 `tests/data/` 读取期望值，与统计结果软断言对比 |

---

## 7. 关键踩坑 & 知识点（都是本项目的真实教训）

1. **factory_boy 的 fixture 命名**：`register(TaskFactory)` 会注册两个 fixture——`task`（**构建出的实例**）
   和 `task_factory`（**工厂类本身**）。想拿到可直接 `repository.add(task)` 的对象，要用 `task` 而不是 `task_factory`，
   否则会得到工厂类而报 `AttributeError`。
2. **pytest-freezegun 的 fixture 叫 `freezer`**，不是 `freezetime`；用法是 `freezer.move_to("2026-06-01")`。
3. **sqlite3 的 datetime 适配器在 Python 3.12+ 已弃用**：本项目改为把时间存成 **ISO 字符串**（TEXT），
   读取时用 `datetime.fromisoformat` 解析，彻底消除弃用警告，也更直观。
4. **异步用例**：配置 `asyncio_mode = "auto"` 后，`async def` 测试函数无需加 `@pytest.mark.asyncio` 也能跑。
5. **pytest-httpx 拦截的是「所有 httpx 请求」**：只要用例请求了 `httpx_mock` fixture，真实 `httpx.Client()`
   的调用就会被拦截，因此 `Notifier` 里 `httpx.Client()` 不用改造也能被测试。
6. **pytest-randomly + 并行**：repository 用 `tmp_path` 保证每个用例 / 每个 worker 独立，因此随机顺序与并行都不会互相干扰——
   这正是「可测试代码」该有的样子。
7. **failures 重跑 vs xfail**：rerunfailures 是「真失败了我再试几次」，xfail 是「我预期它会失败」。本项目演示的是前者。

---

## 8. 持续集成（GitHub Actions）

`.github/workflows/pytest.yml` 在 `push`/`pull_request` 时，于 Python 3.10/3.11/3.12 矩阵上
`pip install -r requirements.txt` 并运行 `pytest -n auto --cov=tasktracker --cov-report=xml`，
还把 `coverage.xml` 作为 artifact 上传。推到 GitHub 即开箱可用。

---

## 9. 上传到 GitHub 的步骤

```bash
git init
git add .
git commit -m "feat: 进阶 pytest 项目（13 个第三方插件 + tasktracker 领域）"

# 在 GitHub 新建空仓库后：
git remote add origin https://github.com/<用户名>/<仓库名>.git
git branch -M main
git push -u origin main
```

> 注意：`report.html`、`.coverage`、`__pycache__` 等已被 `.gitignore` 忽略，不会进仓库。

---

祝学习顺利 🚀 想深入哪一块，直接改 `tasktracker/` 里的实现，再给 `tests/` 补用例即可。
