"""角色协议：Proposer / Challenger / Reflector 的提示词与输出契约。

三个角色是同一模型的不同 prompt（architecture.md §2.1）。
内核只定义角色的职责与交互规范；领域知识全部来自实例描述符，
在系统提示词的共享段注入。
"""

from __future__ import annotations

from typing import Any

from crucible.instance import InstanceDescriptor
from crucible.schema import PropositionState

# ---------------------------------------------------------------------------
# 结构化输出 schema（structured outputs 要求所有 object 声明
# additionalProperties=false 且列出 required）
# ---------------------------------------------------------------------------

PROPOSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "propositions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "proposition": {"type": "string", "description": "命题本身，一句可被攻击的明确主张"},
                    "argument_chain": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "论证链，每一步显式可检验",
                    },
                    "premises_used": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "该命题依赖的全部前提（含此前隐含的假设）",
                    },
                    "methods_used": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "所使用的方法市场条目 id",
                    },
                },
                "required": ["proposition", "argument_chain", "premises_used", "methods_used"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["propositions"],
    "additionalProperties": False,
}

CHALLENGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "assessments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "proposition_id": {"type": "integer"},
                    "challenges": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "attack_type": {
                                    "type": "string",
                                    "description": "攻击类型：反例/隐藏前提/逻辑跳跃/概念偷换/替代解释/完整性违规等",
                                },
                                "content": {"type": "string"},
                                "severity": {
                                    "type": "string",
                                    "enum": ["fatal", "serious", "minor"],
                                },
                            },
                            "required": ["attack_type", "content", "severity"],
                            "additionalProperties": False,
                        },
                    },
                    "hidden_premises_exposed": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "integrity_violations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "违反的完整性约束 id 及说明",
                    },
                    "substantively_weakened": {"type": "boolean"},
                    "verdict_reason": {"type": "string"},
                },
                "required": [
                    "proposition_id",
                    "challenges",
                    "hidden_premises_exposed",
                    "integrity_violations",
                    "substantively_weakened",
                    "verdict_reason",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["assessments"],
    "additionalProperties": False,
}

REVISE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["revise", "abandon"]},
        "revised_proposition": {
            "type": "string",
            "description": "action=revise 时的修正命题；action=abandon 时为空字符串",
        },
        "revised_argument_chain": {"type": "array", "items": {"type": "string"}},
        "lesson": {"type": "string", "description": "这次攻击（无论修正还是放弃）教会我们什么"},
    },
    "required": ["action", "revised_proposition", "revised_argument_chain", "lesson"],
    "additionalProperties": False,
}

REFLECT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "framework_ok": {"type": "boolean"},
        "framework_critique": {"type": "string", "description": "对分析框架本身的评价"},
        "reframed_question": {
            "type": "string",
            "description": "若框架需要转换，给出重构后的问题；否则为空字符串",
        },
        "epistemic_gains": {
            "type": "array",
            "items": {"type": "string"},
            "description": "本轮认知增益：之前不知道的、被推翻的、新暴露的",
        },
        "unresolved_tensions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "当前框架无法解决的矛盾或悖论",
        },
        "has_new_insight": {
            "type": "boolean",
            "description": "本轮是否有新的意外发现或框架转换机会（没有则为收敛信号）",
        },
    },
    "required": [
        "framework_ok",
        "framework_critique",
        "reframed_question",
        "epistemic_gains",
        "unresolved_tensions",
        "has_new_insight",
    ],
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# 提示词
# ---------------------------------------------------------------------------


def shared_system(instance: InstanceDescriptor) -> str:
    """系统提示词的共享段：引擎信条 + 实例描述符注入。所有角色相同，可被缓存。"""
    lines = [
        "你是「Crucible 辩证引擎」中的一个角色。引擎的信条：好的想法不是写出来的，是在攻击中幸存下来的。",
        "引擎内核领域无关，你所在的领域由下面加载的实例决定。",
        "",
        f"【当前领域实例】{instance.name}（{instance.domain}）",
        instance.description,
        "",
        "【前提类型】（什么算有效输入）",
    ]
    for p in instance.premise_types:
        suffix = f"（校验：{p.validation}）" if p.validation else ""
        lines.append(f"- {p.type}：{p.description}{suffix}")
    lines += ["", "【完整性约束】（什么算不可接受的错误；severity=blocker 的违规必须被指出并处理）"]
    for r in instance.integrity_rules:
        lines.append(f"- [{r.id}] {r.description}（检查者：{r.checker}；级别：{r.severity}）")
    if instance.method_market:
        lines += ["", "【方法市场】（本领域可用的论证/分析工具，按需选用并注明所用方法的 id）"]
        for m in instance.method_market:
            when = f" —— 适用时机：{m.when_to_use}" if m.when_to_use else ""
            lines.append(f"- [{m.id}] {m.description}{when}")
    return "\n".join(lines)


PROPOSER_SYSTEM = """你的角色：倡议者（Proposer）。你要回答的问题是「最好的解释是什么？」

职责：基于给定前提构建尽可能强的论证、提出主张、建立解释框架。
要求：
- 每个命题是一句明确、可被攻击、可证伪的主张，不要含糊其辞
- 论证链每一步显式可检验，不允许逻辑跳跃
- 在 premises_used 中声明你依赖的全部前提，包括原本隐含的假设
- 从方法市场中选择合适的方法并在 methods_used 中注明 id
- 遵守全部完整性约束"""

CHALLENGER_SYSTEM = """你的角色：挑战者（Challenger）。你要回答的问题是「这个论证在什么地方最脆弱？」

职责：全力攻击论证的薄弱环节、暴露隐藏假设、寻找反例。
攻击手段：反例、隐藏前提、逻辑跳跃、概念偷换、替代解释、边界条件、完整性约束违规。
判定纪律：
- 只有当攻击确实动摇论证核心（而非措辞或次要细节）时，才判定 substantively_weakened=true
- 任何 severity=blocker 的完整性违规都构成实质性削弱
- 不要为攻击而攻击：如果找不到新的有效攻击角度，如实判定未被削弱并说明理由——这正是收敛的信号
- 对每个命题分别给出评估，proposition_id 使用输入中标注的编号"""

REVISER_SYSTEM = """你的角色：倡议者（Proposer），当前处于修正阶段。你的命题刚被挑战者实质性削弱。

职责：诚实面对攻击。二选一：
- revise：如果命题可以在吸收攻击后被修正（收窄范围、补上前提、修补论证链），给出修正后的命题与论证链
- abandon：如果攻击是致命的、命题核心无法挽救，果断放弃
无论哪种选择，都要在 lesson 中写下这次驳斥教会我们什么。禁止用措辞游戏假装修正。"""

REFLECTOR_SYSTEM = """你的角色：反思者（Reflector）。你要回答的问题是「我们是不是在问错误的问题？」

职责：退后一步，在元层面审视论证框架本身，而不是参与具体攻防。
产出：
- framework_critique：对当前框架的评价（问题问对了吗？前提类型合适吗？方法用对了吗？）
- epistemic_gains：本轮认知增益——之前不知道的 X、被推翻的假设 Y、新暴露的问题 Z
- unresolved_tensions：当前框架无法解决的矛盾或悖论
- reframed_question：只有当框架确实需要转换时才给出重构后的问题，否则留空字符串
判定纪律：只有确实发现新的意外或框架转换机会时才设置 has_new_insight=true；
连续没有新发现是收敛的信号，如实报告。"""


def _format_premises(premises: list[str]) -> str:
    if not premises:
        return "（调用方未提供显式前提；请自行声明你采用的前提，并遵守实例的前提类型约定）"
    return "\n".join(f"{i + 1}. {p}" for i, p in enumerate(premises))


def _format_propositions(props: list[PropositionState]) -> str:
    blocks = []
    for p in props:
        chain = "\n".join(f"   {i + 1}) {s}" for i, s in enumerate(p.argument_chain))
        used = "；".join(p.premises_used) if p.premises_used else "（未声明）"
        blocks.append(
            f"[命题 #{p.id}]（已连续幸存 {p.rounds_survived} 轮，修正 {p.revision_count} 次）\n"
            f"主张：{p.proposition}\n论证链：\n{chain}\n依赖前提：{used}"
        )
    return "\n\n".join(blocks)


def propose_user(question: str, premises: list[str], lessons: list[str]) -> str:
    parts = [f"问题：{question}", "", "前提：", _format_premises(premises)]
    if lessons:
        parts += ["", "此前被驳斥的命题留下的教训（不要重蹈覆辙）："]
        parts += [f"- {l}" for l in lessons]
    parts += ["", "请提出 1-3 个候选命题及其论证链。"]
    return "\n".join(parts)


def challenge_user(question: str, premises: list[str], props: list[PropositionState]) -> str:
    return "\n".join(
        [
            f"问题：{question}",
            "",
            "前提：",
            _format_premises(premises),
            "",
            "待攻击的命题：",
            _format_propositions(props),
            "",
            "请对每个命题分别发起攻击并给出判定。",
        ]
    )


def revise_user(question: str, prop: PropositionState, assessment: dict[str, Any]) -> str:
    challenges = "\n".join(
        f"- [{c['severity']}/{c['attack_type']}] {c['content']}" for c in assessment.get("challenges", [])
    )
    extra = []
    if assessment.get("hidden_premises_exposed"):
        extra.append("被暴露的隐藏前提：" + "；".join(assessment["hidden_premises_exposed"]))
    if assessment.get("integrity_violations"):
        extra.append("完整性违规：" + "；".join(assessment["integrity_violations"]))
    chain = "\n".join(f"{i + 1}) {s}" for i, s in enumerate(prop.argument_chain))
    return "\n".join(
        [
            f"问题：{question}",
            "",
            f"你的命题（#{prop.id}）：{prop.proposition}",
            f"论证链：\n{chain}",
            "",
            "挑战者的攻击：",
            challenges,
            *extra,
            "",
            f"判定理由：{assessment.get('verdict_reason', '')}",
            "",
            "请决定 revise 或 abandon，并写下 lesson。",
        ]
    )


def reflect_user(
    question: str,
    original_question: str,
    round_no: int,
    props: list[PropositionState],
    refuted: list[PropositionState],
    any_weakened: bool,
) -> str:
    parts = [f"第 {round_no} 轮辩证循环刚结束。", ""]
    if question != original_question:
        parts.append(f"最初的问题：{original_question}")
    parts.append(f"当前的问题：{question}")
    parts.append(f"本轮是否有命题被实质性削弱：{'是' if any_weakened else '否'}")
    parts.append("")
    if props:
        parts += ["当前存活的命题：", _format_propositions(props), ""]
    else:
        parts += ["当前没有存活的命题（全部被驳斥）。", ""]
    if refuted:
        parts.append("已被驳斥的命题及教训：")
        parts += [f"- {p.proposition} —— 教训：{p.lesson or p.refutation}" for p in refuted]
        parts.append("")
    parts.append("请在元层面审视：框架对吗？有什么意外发现？有什么张力无法在当前框架内解决？")
    return "\n".join(parts)
