"""引擎端到端测试：用 FakeLLM 脚本化三个角色的回复，验证循环控制流。"""

from crucible.convergence import LEVELS, DepthConfig
from crucible.engine import DialecticalEngine
from crucible.instance import load_instance
from crucible.llm import FakeLLM

L2 = LEVELS["L2"]  # max_rounds=3, N=2, M=1


def propose(*props):
    return {
        "propositions": [
            {
                "proposition": p,
                "argument_chain": ["步骤一", "步骤二"],
                "premises_used": ["前提A"],
                "methods_used": ["reductio_ad_absurdum"],
            }
            for p in props
        ]
    }


def assessment(pid, weakened, severity="minor", reason="理由"):
    return {
        "proposition_id": pid,
        "challenges": [{"attack_type": "反例", "content": f"攻击命题{pid}", "severity": severity}],
        "hidden_premises_exposed": [],
        "integrity_violations": [],
        "substantively_weakened": weakened,
        "verdict_reason": reason,
    }


def challenge(*assessments):
    return {"assessments": list(assessments)}


def revise(action, new_prop="", lesson="教训"):
    return {
        "action": action,
        "revised_proposition": new_prop,
        "revised_argument_chain": ["修正步骤一"] if new_prop else [],
        "lesson": lesson,
    }


def reflect(novelty=False, reframe="", gains=(), tensions=(), critique="框架合适"):
    return {
        "framework_ok": not reframe,
        "framework_critique": critique,
        "reframed_question": reframe,
        "epistemic_gains": list(gains),
        "unresolved_tensions": list(tensions),
        "has_new_insight": novelty,
    }


def make_engine(script, depth=L2):
    fake = FakeLLM(script)
    instance = load_instance("pure-reasoning")
    return DialecticalEngine(llm=fake, instance=instance, depth=depth), fake


def test_survival_and_refutation_to_convergence():
    """命题1连续幸存 → robust；命题2被致命攻击 → 放弃并记录教训；自然收敛。"""
    engine, fake = make_engine(
        [
            propose("命题一", "命题二"),
            challenge(assessment(1, False), assessment(2, True, "fatal")),
            revise("abandon", lesson="命题二的教训"),
            reflect(gains=("增益1",)),
            challenge(assessment(1, False)),
            reflect(gains=("增益2", "增益1")),  # 重复项应被去重
            challenge(assessment(1, False)),
            reflect(),
        ]
    )
    result = engine.run("测试问题", premises=["前提A"])

    assert result.termination == "converged"
    assert len(result.rounds) == 3
    assert not fake.script  # 脚本刚好耗尽 → 调用序列与预期一致

    assert len(result.surviving_propositions) == 1
    survivor = result.surviving_propositions[0]
    assert survivor["proposition"] == "命题一"
    assert survivor["strength"] == "robust"  # 连续 3 轮未被削弱
    assert len(survivor["challenges_survived"]) == 3

    assert len(result.refuted_propositions) == 1
    refuted = result.refuted_propositions[0]
    assert refuted["proposition"] == "命题二"
    assert refuted["lesson"] == "命题二的教训"
    assert "攻击命题2" in refuted["refutation"]

    assert result.epistemic_gains == ["增益1", "增益2"]
    assert result.confidence.startswith("overall")
    # 统一输出结构（§2.4）字段齐全
    d = result.to_dict()
    for key in (
        "surviving_propositions",
        "refuted_propositions",
        "epistemic_gains",
        "unresolved_tensions",
        "framework_critique",
        "confidence",
    ):
        assert key in d


def test_revision_resets_survival_and_keeps_proposition_alive():
    """被削弱但可修正 → 修正后重新经受攻击，rounds_survived 归零重计。"""
    engine, fake = make_engine(
        [
            propose("原命题"),
            challenge(assessment(1, True, "serious")),
            revise("revise", new_prop="修正后的命题", lesson="收窄了范围"),
            reflect(),
            challenge(assessment(1, False)),
            reflect(),
            challenge(assessment(1, False)),
            reflect(),
        ]
    )
    result = engine.run("测试问题")

    assert result.termination == "converged"
    assert not fake.script
    assert len(result.surviving_propositions) == 1
    survivor = result.surviving_propositions[0]
    assert survivor["proposition"] == "修正后的命题"
    assert survivor["revisions"] == 1
    assert survivor["strength"] == "robust"  # 修正后连续 2 轮幸存
    assert not result.refuted_propositions
    # 修正的教训会传给后续倡议者调用
    assert result.rounds[0].revisions[0]["lesson"] == "收窄了范围"


def test_reframe_triggers_new_proposal_round():
    """反思者转换框架 → 下一轮重新提出命题，置信度降为 conditional。"""
    engine, fake = make_engine(
        [
            propose("旧框架命题"),
            challenge(assessment(1, False)),
            reflect(novelty=True, reframe="重构后的问题"),
            propose("新框架命题"),
            challenge(assessment(1, False), assessment(2, False)),
            reflect(),
        ]
    )
    result = engine.run("原始问题")

    assert result.termination == "converged"
    assert not fake.script
    assert len(result.surviving_propositions) == 2
    assert result.rounds[1].question == "重构后的问题"
    assert result.rounds[1].proposed  # 框架转换后有新命题被提出
    assert result.confidence.startswith("conditional")
    assert "框架转换" in result.confidence
    # 第二轮的倡议者调用应针对重构后的问题
    propose_calls = [c for c in fake.calls if c["schema"] is not None and "propositions" in c["schema"]["properties"]]
    assert "重构后的问题" in propose_calls[1]["user"]


def test_l1_single_attack_round_all_refuted():
    """L1：1 轮攻击即终止；全军覆没时置信度为 low。"""
    engine, fake = make_engine(
        [
            propose("脆弱命题"),
            challenge(assessment(1, True, "fatal")),
            revise("abandon", lesson="经不起第一击"),
            reflect(novelty=True),
        ],
        depth=LEVELS["L1"],
    )
    result = engine.run("测试问题")

    assert result.termination == "max_rounds"
    assert len(result.rounds) == 1
    assert not fake.script
    assert not result.surviving_propositions
    assert result.confidence.startswith("low")


def test_hard_limit_yields_low_confidence():
    """一直有削弱 → 不收敛，撞硬上限，置信度 low。"""
    depth = DepthConfig(max_rounds=2, n_no_weakening=2, m_no_novelty=1)
    engine, fake = make_engine(
        [
            propose("反复被削弱的命题"),
            challenge(assessment(1, True, "serious")),
            revise("revise", new_prop="修正v1", lesson="教训1"),
            reflect(),
            challenge(assessment(1, True, "serious")),
            revise("revise", new_prop="修正v2", lesson="教训2"),
            reflect(),
        ],
        depth=depth,
    )
    result = engine.run("测试问题")

    assert result.termination == "max_rounds"
    assert not fake.script
    assert result.confidence.startswith("low")
    assert result.surviving_propositions[0]["proposition"] == "修正v2"
    assert result.surviving_propositions[0]["strength"] == "speculative"


def test_prompts_carry_instance_and_ids():
    """实例描述符注入共享系统提示词；挑战者提示词中带命题编号。"""
    engine, fake = make_engine(
        [
            propose("命题一"),
            challenge(assessment(1, False)),
            reflect(),
            challenge(assessment(1, False)),
            reflect(),
        ]
    )
    engine.run("测试问题", premises=["前提A"])

    shared = fake.calls[0]["system_shared"]
    assert "纯思辨实例" in shared
    assert "no_hidden_premises" in shared
    assert "reductio_ad_absurdum" in shared
    assert all(c["system_shared"] == shared for c in fake.calls)  # 共享段稳定 → 可缓存

    challenger_call = fake.calls[1]
    assert "挑战者" in challenger_call["system_role"]
    assert "[命题 #1]" in challenger_call["user"]
    assert "前提A" in challenger_call["user"]
