"""辩证引擎内核：循环控制流。

内核只拥有（architecture.md §4.2）：
- 辩证循环的控制流（本文件）
- 角色协议（roles.py）
- 收敛判断逻辑（convergence.py）
- 认知增益的记录结构（schema.py）

它不拥有任何领域特定的方法、约束或输出格式——那些来自实例描述符。
"""

from __future__ import annotations

from typing import Any, Callable

from crucible import roles
from crucible.convergence import ConvergenceGate, DepthConfig
from crucible.instance import InstanceDescriptor
from crucible.llm import LLM
from crucible.schema import EngineResult, PropositionState, RoundRecord


class DialecticalEngine:
    """倡议者提出 → 挑战者攻击 → 倡议者修正/放弃 → 反思者审视 → 收敛判断。"""

    def __init__(
        self,
        llm: LLM,
        instance: InstanceDescriptor,
        depth: DepthConfig | None = None,
        on_event: Callable[[str], None] | None = None,
    ):
        self.llm = llm
        self.instance = instance
        self.depth = depth or DepthConfig()
        self._on_event = on_event or (lambda _msg: None)
        self._system_shared = roles.shared_system(instance)

    # -- 角色调用 -----------------------------------------------------------

    def _call(self, system_role: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        return self.llm.complete(self._system_shared, system_role, user, schema)

    def _propose(
        self, question: str, premises: list[str], lessons: list[str], next_id: int
    ) -> list[PropositionState]:
        out = self._call(
            roles.PROPOSER_SYSTEM, roles.propose_user(question, premises, lessons), roles.PROPOSE_SCHEMA
        )
        props = []
        for i, p in enumerate(out.get("propositions", [])):
            props.append(
                PropositionState(
                    id=next_id + i,
                    proposition=p["proposition"],
                    argument_chain=list(p["argument_chain"]),
                    premises_used=list(p.get("premises_used", [])),
                    methods_used=list(p.get("methods_used", [])),
                )
            )
        return props

    def _challenge(
        self, question: str, premises: list[str], props: list[PropositionState]
    ) -> list[dict[str, Any]]:
        out = self._call(
            roles.CHALLENGER_SYSTEM, roles.challenge_user(question, premises, props), roles.CHALLENGE_SCHEMA
        )
        return list(out.get("assessments", []))

    def _revise(self, question: str, prop: PropositionState, assessment: dict[str, Any]) -> dict[str, Any]:
        return self._call(
            roles.REVISER_SYSTEM, roles.revise_user(question, prop, assessment), roles.REVISE_SCHEMA
        )

    def _reflect(
        self,
        question: str,
        original_question: str,
        round_no: int,
        active: list[PropositionState],
        refuted: list[PropositionState],
        any_weakened: bool,
    ) -> dict[str, Any]:
        return self._call(
            roles.REFLECTOR_SYSTEM,
            roles.reflect_user(question, original_question, round_no, active, refuted, any_weakened),
            roles.REFLECT_SCHEMA,
        )

    # -- 主循环 -------------------------------------------------------------

    def run(self, question: str, premises: list[str] | None = None) -> EngineResult:
        premises = premises or []
        props: list[PropositionState] = []
        lessons: list[str] = []
        gains: list[str] = []
        tensions: list[str] = []
        records: list[RoundRecord] = []
        framework_critique = ""
        current_question = question
        need_propose = True
        reframed_ever = False

        gate = ConvergenceGate(self.depth)

        for round_no in range(1, self.depth.max_rounds + 1):
            record = RoundRecord(round=round_no, question=current_question)
            active = [p for p in props if p.status == "active"]

            # 1. 倡议者：无存活命题或框架刚转换时（重新）提出
            if need_propose or not active:
                self._on_event(f"第 {round_no} 轮：倡议者构建论证……")
                new_props = self._propose(current_question, premises, lessons, next_id=len(props) + 1)
                props.extend(new_props)
                active = [p for p in props if p.status == "active"]
                record.proposed = [
                    {"id": p.id, "proposition": p.proposition, "argument_chain": p.argument_chain}
                    for p in new_props
                ]
                need_propose = False
            if not active:
                # 倡议者一个命题都提不出来：无从对抗，直接终止
                break

            # 2. 挑战者：攻击全部存活命题
            self._on_event(f"第 {round_no} 轮：挑战者发起攻击……")
            assessments = self._challenge(current_question, premises, active)
            record.assessments = assessments
            by_id = {p.id: p for p in active}
            any_weakened = False
            for a in assessments:
                prop = by_id.get(a.get("proposition_id"))
                if prop is None:
                    continue
                summary = "；".join(
                    f"[{c['attack_type']}] {c['content']}" for c in a.get("challenges", [])
                )
                if a.get("substantively_weakened"):
                    any_weakened = True
                    # 3. 倡议者修正或放弃
                    self._on_event(f"第 {round_no} 轮：命题 #{prop.id} 被实质性削弱，倡议者回应……")
                    rev = self._revise(current_question, prop, a)
                    record.revisions.append({"proposition_id": prop.id, **rev})
                    if rev.get("lesson"):
                        lessons.append(rev["lesson"])
                    if rev.get("action") == "revise" and rev.get("revised_proposition"):
                        prop.proposition = rev["revised_proposition"]
                        prop.argument_chain = list(rev.get("revised_argument_chain", []))
                        prop.revision_count += 1
                        prop.rounds_survived = 0  # 修正后的命题需要重新经受攻击
                        prop.lesson = rev.get("lesson", "")
                    else:
                        prop.status = "refuted"
                        prop.refutation = summary or a.get("verdict_reason", "")
                        prop.lesson = rev.get("lesson", "")
                else:
                    # 未被削弱 → 命题强度提升
                    prop.rounds_survived += 1
                    if summary:
                        prop.challenges_survived.append(summary)

            # 4. 反思者：元层面审视
            self._on_event(f"第 {round_no} 轮：反思者审视框架……")
            active = [p for p in props if p.status == "active"]
            refuted = [p for p in props if p.status == "refuted"]
            reflection = self._reflect(
                current_question, question, round_no, active, refuted, any_weakened
            )
            record.reflection = reflection
            record.any_weakened = any_weakened
            framework_critique = reflection.get("framework_critique", framework_critique)
            for g in reflection.get("epistemic_gains", []):
                if g not in gains:
                    gains.append(g)
            for t in reflection.get("unresolved_tensions", []):
                if t not in tensions:
                    tensions.append(t)

            reframe = reflection.get("reframed_question", "").strip()
            novelty = bool(reflection.get("has_new_insight")) or bool(reframe)
            if reframe and reframe != current_question:
                self._on_event(f"第 {round_no} 轮：框架转换 → {reframe}")
                current_question = reframe
                need_propose = True
                reframed_ever = True

            records.append(record)

            # 5. 收敛判断
            gate.observe(weakened=any_weakened, novelty=novelty)
            if gate.converged:
                break

        termination = "converged" if gate.converged else "max_rounds"
        surviving = [p for p in props if p.status == "active"]
        refuted = [p for p in props if p.status == "refuted"]

        return EngineResult(
            question=question,
            domain=self.instance.domain,
            surviving_propositions=[
                {
                    "proposition": p.proposition,
                    "argument_chain": p.argument_chain,
                    "premises_used": p.premises_used,
                    "methods_used": p.methods_used,
                    "challenges_survived": p.challenges_survived,
                    "revisions": p.revision_count,
                    "strength": p.strength,
                }
                for p in surviving
            ],
            refuted_propositions=[
                {"proposition": p.proposition, "refutation": p.refutation, "lesson": p.lesson}
                for p in refuted
            ],
            epistemic_gains=gains,
            unresolved_tensions=tensions,
            framework_critique=framework_critique,
            confidence=self._confidence(termination, surviving, reframed_ever, gate),
            termination=termination,
            rounds=records,
        )

    @staticmethod
    def _confidence(
        termination: str,
        surviving: list[PropositionState],
        reframed_ever: bool,
        gate: ConvergenceGate,
    ) -> str:
        if not surviving:
            return "low — 没有命题在攻击中幸存"
        if termination != "converged":
            return f"low — 达到 {gate.rounds_seen} 轮硬上限仍未收敛，对抗尚未穷尽"
        has_robust = any(p.strength == "robust" for p in surviving)
        base = (
            f"连续 {gate.no_weakening_streak} 轮攻击未产生实质性削弱，"
            f"反思者连续 {gate.no_novelty_streak} 轮无新发现"
        )
        if has_robust and not reframed_ever:
            return f"overall — {base}"
        if has_robust and reframed_ever:
            return f"conditional — {base}，但运行中发生过框架转换，结论依赖新框架成立"
        return f"conditional — {base}，但幸存命题尚未达到 robust 强度"
