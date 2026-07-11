"""内核数据结构：命题状态、轮次记录、统一输出。

输出结构与 architecture.md §2.4 对齐：无论哪个领域实例，
辩证引擎的输出都是同一个形状，并附带认知审计追踪（rounds）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# 命题强度阶梯：幸存的无削弱轮数 → 强度
STRENGTH_SPECULATIVE = "speculative"
STRENGTH_TENTATIVE = "tentative"
STRENGTH_ROBUST = "robust"


def strength_of(rounds_survived: int) -> str:
    if rounds_survived >= 2:
        return STRENGTH_ROBUST
    if rounds_survived == 1:
        return STRENGTH_TENTATIVE
    return STRENGTH_SPECULATIVE


@dataclass
class PropositionState:
    """一个命题在辩证循环中的完整生命周期。"""

    id: int
    proposition: str
    argument_chain: list[str]
    premises_used: list[str] = field(default_factory=list)
    methods_used: list[str] = field(default_factory=list)
    status: str = "active"  # active | refuted
    rounds_survived: int = 0  # 连续未被实质性削弱的挑战轮数
    revision_count: int = 0
    challenges_survived: list[str] = field(default_factory=list)
    refutation: str = ""
    lesson: str = ""

    @property
    def strength(self) -> str:
        return strength_of(self.rounds_survived)


@dataclass
class RoundRecord:
    """单轮辩证循环的审计记录：谁说了什么、什么被削弱、反思者看到了什么。"""

    round: int
    question: str
    proposed: list[dict[str, Any]] = field(default_factory=list)
    assessments: list[dict[str, Any]] = field(default_factory=list)
    revisions: list[dict[str, Any]] = field(default_factory=list)
    reflection: dict[str, Any] = field(default_factory=dict)
    any_weakened: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "round": self.round,
            "question": self.question,
            "proposed": self.proposed,
            "assessments": self.assessments,
            "revisions": self.revisions,
            "reflection": self.reflection,
            "any_weakened": self.any_weakened,
        }


@dataclass
class EngineResult:
    """统一输出结构（architecture.md §2.4）+ 审计追踪。"""

    question: str
    domain: str
    surviving_propositions: list[dict[str, Any]]
    refuted_propositions: list[dict[str, Any]]
    epistemic_gains: list[str]
    unresolved_tensions: list[str]
    framework_critique: str
    confidence: str
    termination: str  # converged | max_rounds
    rounds: list[RoundRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "domain": self.domain,
            "surviving_propositions": self.surviving_propositions,
            "refuted_propositions": self.refuted_propositions,
            "epistemic_gains": self.epistemic_gains,
            "unresolved_tensions": self.unresolved_tensions,
            "framework_critique": self.framework_critique,
            "confidence": self.confidence,
            "termination": self.termination,
            "rounds": [r.to_dict() for r in self.rounds],
        }
