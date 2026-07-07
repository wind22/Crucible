from crucible.convergence import LEVELS, ConvergenceGate, DepthConfig


def test_converges_after_n_quiet_rounds():
    gate = ConvergenceGate(DepthConfig(max_rounds=10, n_no_weakening=2, m_no_novelty=1))
    gate.observe(weakened=False, novelty=False)
    assert not gate.converged
    gate.observe(weakened=False, novelty=False)
    assert gate.converged


def test_weakening_resets_primary_streak():
    gate = ConvergenceGate(DepthConfig(max_rounds=10, n_no_weakening=2, m_no_novelty=1))
    gate.observe(weakened=False, novelty=False)
    gate.observe(weakened=True, novelty=False)
    assert not gate.converged
    gate.observe(weakened=False, novelty=False)
    assert not gate.converged
    gate.observe(weakened=False, novelty=False)
    assert gate.converged


def test_novelty_resets_auxiliary_streak():
    gate = ConvergenceGate(DepthConfig(max_rounds=10, n_no_weakening=2, m_no_novelty=2))
    gate.observe(weakened=False, novelty=False)
    gate.observe(weakened=False, novelty=True)  # 反思者有新发现 → 未收敛
    assert not gate.converged
    gate.observe(weakened=False, novelty=False)
    assert not gate.converged  # m_no_novelty=2，还差一轮
    gate.observe(weakened=False, novelty=False)
    assert gate.converged


def test_hard_limit():
    gate = ConvergenceGate(DepthConfig(max_rounds=2, n_no_weakening=5, m_no_novelty=5))
    gate.observe(weakened=True, novelty=True)
    assert not gate.should_stop
    gate.observe(weakened=True, novelty=True)
    assert gate.hit_hard_limit and gate.should_stop and not gate.converged


def test_levels_are_monotonically_deeper():
    assert LEVELS["L1"].max_rounds < LEVELS["L2"].max_rounds
    assert LEVELS["L2"].max_rounds < LEVELS["L3"].max_rounds
    assert LEVELS["L3"].max_rounds < LEVELS["L4"].max_rounds
    # L1 的表现不应该比当前框架更差：1 轮攻击后即可终止
    assert LEVELS["L1"].max_rounds == 1
