"""Crucible：通用辩证推理引擎。

同一个内核。不同的前提。不同的任务。
好的想法不是写出来的，是在攻击中幸存下来的。
"""

from crucible.convergence import ConvergenceGate, DepthConfig, LEVELS
from crucible.engine import DialecticalEngine
from crucible.instance import InstanceDescriptor, list_bundled_instances, load_instance
from crucible.schema import EngineResult, PropositionState, RoundRecord

__version__ = "0.0.1"

__all__ = [
    "ConvergenceGate",
    "DepthConfig",
    "DialecticalEngine",
    "EngineResult",
    "InstanceDescriptor",
    "LEVELS",
    "PropositionState",
    "RoundRecord",
    "__version__",
    "list_bundled_instances",
    "load_instance",
]
