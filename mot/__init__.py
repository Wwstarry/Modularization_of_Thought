"""
MoT: Modularization-of-Thought Prompting for Effective Code Generation.

arXiv:2503.12483 — Ruwei Pan & Hongyu Zhang (Chongqing University, 2025)

Includes:
  MoTEngine     — paper-exact two-phase implementation (Phase 1 + Phase 2)
  MoTPlusEngine — enhanced three-phase implementation (Phase 1 + Phase 2 + repair)
"""
from mot.llm import LLMClient
from mot.mot_engine import MoTEngine
from mot.mot_plus import MoTPlusEngine
from mot.mot_sc import MoTSCEngine
from mot.executor import syntax_check, execute_code, count_passed

__all__ = [
    "LLMClient",
    "MoTEngine",
    "MoTPlusEngine",
    "MoTSCEngine",
    "syntax_check",
    "execute_code",
    "count_passed",
]
__version__ = "1.2.0"
