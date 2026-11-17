"""Tests for the priced policy and its baselines."""

import pytest

from priced_deferral.models import Alternative, DecisionCase, EvidenceItem, HarmProfile
from priced_deferral.policy import (
    always_answer,
    decide,
    evaluate,
    fixed_threshold,
    oracle,
)

CLINIC = HarmProfile(name="clinic", harm_wrong=100000.0, human_cost=50.0,
                     delay_cost=20.0, human_accuracy=0.98)
RESEARCH = HarmProfile(name="research", harm_wrong=500.0, human_cost=15.0,
                       delay_cost=5.0, human_accuracy=0.97)


def _case(case_id="c1", p=0.8, correct=True, domain="research", **over):
    base = {
        "case_id": case_id, "domain": domain, "question": "q?",
        "candidate": "yes", "p_correct": p,
        "evidence": [EvidenceItem(item_id="e1", text="t", decisiveness=0.9,
                                  cost=1.0, supports="candidate")],
        "gathered": [EvidenceItem(item_id="g1", text="g", decisiveness=0.0,
                                  cost=0.0, supports="candidate")],
        "alternatives": [Alternative(label="no", support=0)],
        "conflicts": [], "missing": ["The results table."],
        "correct": correct, "true_label": "" if correct else "no",
        "human_correct": True,
    }
    base.update(over)
    return DecisionCase(**base)


def test_decide_answers_when_p_is_one():
    decision = decide(_case(p=1.0), RESEARCH)
    assert decision.verdict == "answer"
    assert decision.costs.answer == pytest.approx(0.0)


def test_decide_defers_when_clinic_p_is_low():
    # p = 0.55 clinic: answer 45000, defer 2070 — defer wins outright.
    decision = decide(_case(p=0.55, domain="clinic", correct=False), CLINIC)
    assert decision.verdict == "defer"
    assert decision.packet is not None
    assert len(decision.packet.items) > 0


def test_decide_gathers_when_cheap_decisive_item_exists():
    # p = 0.80 research, d=0.9 item at cost 1: gather prices 11 < 35.
    decision = decide(_case(p=0.80), RESEARCH)
    assert decision.verdict == "gather"
    assert decision.gather_plan is not None
    assert [i.item_id for i in decision.gather_plan.items] == ["e1"]


def test_decide_never_returns_empty_gather():
    # Expensive evidence: the plan is empty, so the verdict cannot be
    # "gather" — it falls through to answer/defer by price.
    case = _case(p=0.80, evidence=[EvidenceItem(
        item_id="e1", text="t", decisiveness=0.9, cost=400.0,
        supports="candidate")])
    decision = decide(case, RESEARCH)
    assert decision.verdict in ("answer", "defer")
    if decision.verdict == "gather":
        assert decision.gather_plan.items != ()


def test_decide_builds_packet_on_gather_then_defer():
    # p = 0.5 research, weak item: gather buys nothing, but if the plan
    # existed with second stage defer, a packet must exist. Direct
    # check: a case that gathers then defers gets a packet.
    case = _case(p=0.60, evidence=[EvidenceItem(
        item_id="e1", text="t", decisiveness=0.95, cost=1.0,
        supports="alt")])
    decision = decide(case, RESEARCH)
    # Opposing item lowers p to 0.03: answer 485, defer 35 -> gather
    # cannot help (stage stays defer) -> verdict defer with packet.
    assert decision.verdict == "defer"
    assert decision.packet is not None


def test_always_answer_baseline():
    decision = always_answer(_case(p=0.3, correct=False), RESEARCH)
    assert decision.verdict == "answer"


def test_fixed_threshold_baseline():
    assert fixed_threshold(_case(p=0.62), RESEARCH).verdict == "answer"
    assert fixed_threshold(_case(p=0.61), RESEARCH).verdict == "defer"


def test_oracle_baseline():
    assert oracle(_case(correct=True), RESEARCH).verdict == "answer"
    assert oracle(_case(correct=False), RESEARCH).verdict == "defer"


def test_evaluate_priced_beats_always_answer():
    import os
    from priced_deferral.evaluate import load_cases
    data = os.path.join(os.path.dirname(__file__), "..", "data")
    cases = load_cases(os.path.join(data, "cases.json"))
    priced = evaluate(cases, RESEARCH, decide)
    always = evaluate(cases, RESEARCH, always_answer)
    assert priced["total_cost"] < always["total_cost"]
    assert priced["error_rate_answered"] < always["error_rate_answered"]


def test_evaluate_insurance_split_adds_up():
    import os
    from priced_deferral.evaluate import load_cases
    data = os.path.join(os.path.dirname(__file__), "..", "data")
    cases = load_cases(os.path.join(data, "cases.json"))
    result = evaluate(cases, RESEARCH, decide)
    assert result["cost_on_correct"] + result["cost_on_wrong"] == pytest.approx(
        result["total_cost"])
