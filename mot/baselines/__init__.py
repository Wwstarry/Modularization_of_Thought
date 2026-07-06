"""
Baseline prompting methods for code generation.

All baselines are compared against MoT in the paper (arXiv:2503.12483).
Each class exposes a unified interface:
    generate(task_description: str, entry_point: str = "") -> str
"""
from mot.baselines.zero_shot import ZeroShot
from mot.baselines.few_shot import FewShot
from mot.baselines.cot import CoT
from mot.baselines.self_planning import SelfPlanning
from mot.baselines.scot import SCoT
from mot.baselines.codecot import CodeCoT

__all__ = ["ZeroShot", "FewShot", "CoT", "SelfPlanning", "SCoT", "CodeCoT"]
