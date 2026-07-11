"""收敛门（Convergence Gate）。

循环不因"流程走完"而终止，终止条件来自对抗的质量（architecture.md §2.3）：
- 主要条件：连续 N 轮挑战未产生实质性削弱（默认 2）
- 辅助条件：反思者连续 M 轮未发现新的意外或框架转换机会
- 硬上限：达到预设的深度上限（防止无限循环）
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DepthConfig:
    """一次辩证运行的深度配置。能力越强，辩证越深（architecture.md §5）。"""

    max_rounds: int = 8
    n_no_weakening: int = 2  # 主要条件 N
    m_no_novelty: int = 1  # 辅助条件 M
    effort: str = "high"  # 传给 LLM 的思考深度


# 能力等级 → 深度预设（architecture.md §5）
LEVELS: dict[str, DepthConfig] = {
    # L1（弱）：1 轮攻击，攻击完成即终止，快速 sanity check
    "L1": DepthConfig(max_rounds=1, n_no_weakening=1, m_no_novelty=1, effort="low"),
    # L2（中）：2-3 轮循环，连续 2 轮无实质性削弱
    "L2": DepthConfig(max_rounds=3, n_no_weakening=2, m_no_novelty=1, effort="medium"),
    # L3（强）：收敛为止或硬上限，深度诊断、重要决策
    "L3": DepthConfig(max_rounds=8, n_no_weakening=2, m_no_novelty=2, effort="high"),
    # L4（极强）：收敛 + 反思者满意，框架突破、范式反思
    "L4": DepthConfig(max_rounds=12, n_no_weakening=3, m_no_novelty=2, effort="xhigh"),
}


class ConvergenceGate:
    """跟踪对抗质量，判定循环是否收敛。"""

    def __init__(self, config: DepthConfig):
        self.config = config
        self.no_weakening_streak = 0
        self.no_novelty_streak = 0
        self.rounds_seen = 0

    def observe(self, *, weakened: bool, novelty: bool) -> None:
        """记录一轮结果。weakened=本轮有命题被实质性削弱；novelty=反思者有新发现或框架转换。"""
        self.rounds_seen += 1
        self.no_weakening_streak = 0 if weakened else self.no_weakening_streak + 1
        self.no_novelty_streak = 0 if novelty else self.no_novelty_streak + 1

    @property
    def converged(self) -> bool:
        return (
            self.no_weakening_streak >= self.config.n_no_weakening
            and self.no_novelty_streak >= self.config.m_no_novelty
        )

    @property
    def hit_hard_limit(self) -> bool:
        return self.rounds_seen >= self.config.max_rounds

    @property
    def should_stop(self) -> bool:
        return self.converged or self.hit_hard_limit
