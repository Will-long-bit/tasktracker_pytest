"""演示 pytest-rerunfailures 的「偶发失败重跑」能力。

场景：某些用例在真实环境会偶发失败（网络抖动、竞态等）。
用 @pytest.mark.flaky(reruns=N) 让 pytest 在失败时自动重跑，
只要最终通过就不算失败——非常适合 Stabilize 不稳定用例。

本用例用模块级计数器「模拟」前两次失败、第三次成功：
- 第 1 次：失败 → 触发重跑
- 第 2 次：失败 → 再次重跑
- 第 3 次：成功 → 整体记为 PASSED（带 rerun 记录）
"""

import pytest

_state = {"attempts": 0}


@pytest.mark.flaky(reruns=3)
def test_flaky_simulated():
    _state["attempts"] += 1
    if _state["attempts"] < 3:
        raise AssertionError(f"模拟偶发失败（第 {_state['attempts']} 次）")
    assert True
