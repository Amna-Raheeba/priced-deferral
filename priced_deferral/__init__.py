"""Priced Deferral: expected-cost escalation for uncertain agents."""

from .models import (
    Alternative,
    Decision,
    DecisionCase,
    EvidenceItem,
    GatherPlan,
    HarmProfile,
    Packet,
    PacketItem,
    PricedOptions,
)
from .packet import build_packet
from .policy import always_answer, decide, evaluate, fixed_threshold, oracle
from .pricing import expected_answer_cost, expected_defer_cost, optimal_gather_plan, price_options

__version__ = "0.1.0"

__all__ = [
    "Alternative",
    "Decision",
    "DecisionCase",
    "EvidenceItem",
    "GatherPlan",
    "HarmProfile",
    "Packet",
    "PacketItem",
    "PricedOptions",
    "always_answer",
    "build_packet",
    "decide",
    "evaluate",
    "expected_answer_cost",
    "expected_defer_cost",
    "fixed_threshold",
    "optimal_gather_plan",
    "oracle",
    "price_options",
]
