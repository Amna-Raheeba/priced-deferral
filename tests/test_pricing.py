"""Tests for expected-cost pricing."""

import pytest

from priced_deferral.models import EvidenceItem, HarmProfile
from priced_deferral.pricing import (
    clamp_p,
    expected_answer_cost,
    expected_defer_cost,
    optimal_gather_plan,
    price_options,
    updated_p,
)
from priced_deferral.models import DecisionCase

CLINIC = HarmProfile(name="clinic", harm_wrong=100000.0, human_cost=50.0,
                     delay_cost=20.0, human_accuracy=0.98)
RESEARCH = HarmProfile(name="research", harm_wrong=500.0, human_cost=15.0,
                       delay_cost=5.0, human_accuracy=0.97)


def test_clamp_p():
    assert clamp_p(1.5) == 1.0
    assert clamp_p(-0.2) == 0.0
    assert clamp_p(0.7) == 0.7


def test_expected_answer_cost():
    # p = 0.72, harm 100000 -> 0.28 * 100000 = 28000.
    assert expected_answer_cost(0.72, CLINIC) == pytest.approx(28000.0)
    assert expected_answer_cost(1.0, CLINIC) == pytest.approx(0.0)


def test_expected_defer_cost():
    # (1 - 0.98) * 100000 + 50 + 20 = 2070.
    assert expected_defer_cost(CLINIC) == pytest.approx(2070.0)
    assert expected_defer_cost(RESEARCH) == pytest.approx(35.0)


def _item(item_id, d, cost=1.0, supports="candidate", contradicts=False):
    return EvidenceItem(item_id=item_id, text="t", decisiveness=d,
                        cost=cost, supports=supports, contradicts=contradicts)


def test_updated_p_supporting_raises():
    assert updated_p(0.5, [_item("e1", 0.5)]) == pytest.approx(0.75)
    # Two d=0.5 items: 1 - 0.5*0.5*0.5 = 0.875 (no double-counting).
    assert updated_p(0.5, [_item("e1", 0.5), _item("e2", 0.5)]) == pytest.approx(0.875)


def test_updated_p_opposing_lowers():
    # An alternative-supporting item must NEVER raise p.
    assert updated_p(0.8, [_item("e1", 0.5, supports="alt")]) == pytest.approx(0.4)
    assert updated_p(0.8, [_item("e1", 0.5, contradicts=True)]) == pytest.approx(0.4)


def test_updated_p_mixed():
    # Support d=0.5 then oppose d=0.5: 0.5 -> 0.75 -> 0.375.
    items = [_item("e1", 0.5), _item("e2", 0.5, supports="alt")]
    assert updated_p(0.5, items) == pytest.approx(0.375)


def test_optimal_gather_empty_when_no_benefit():
    # p = 0.99 clinic: answering costs 1000 < defer 2070; gathering a
    # weak item cannot beat that.
    plan = optimal_gather_plan(0.99, [_item("e1", 0.1, cost=500.0)], CLINIC)
    assert plan.items == ()
    assert plan.expected_cost == pytest.approx(1000.0)
    assert plan.second_stage == "answer"


def test_optimal_gather_picks_cheap_decisive_item():
    # p = 0.80 research: item d=0.9 cost 1 -> p' = 0.98, answer 10.
    plan = optimal_gather_plan(0.80, [_item("e1", 0.9, cost=1.0)], RESEARCH)
    assert [i.item_id for i in plan.items] == ["e1"]
    assert plan.p_after == pytest.approx(0.98)
    assert plan.expected_cost == pytest.approx(11.0)
    assert plan.second_stage == "answer"


def test_optimal_gather_skips_expensive_item():
    # Same item at cost 400: benefit 90 < cost -> skip.
    plan = optimal_gather_plan(0.80, [_item("e1", 0.9, cost=400.0)], RESEARCH)
    assert plan.items == ()


def test_optimal_gather_value_per_cost_order():
    # Both items alone flip the second stage to "answer" (gain > 0), but
    # the cheap one wins on value per cost and is picked first; after
    # it, the expensive one no longer pays.
    items = [_item("e1", 0.9, cost=100.0), _item("e2", 0.85, cost=1.0)]
    plan = optimal_gather_plan(0.8, items, RESEARCH)
    assert [i.item_id for i in plan.items] == ["e2"]
    assert plan.p_after == pytest.approx(0.97)


def test_price_options_demo_case():
    case = DecisionCase(case_id="d", domain="clinic", question="q?",
                        candidate="yes", p_correct=0.72)
    costs = price_options(case, CLINIC)
    assert costs.answer == pytest.approx(28000.0)
    assert costs.defer == pytest.approx(2070.0)
    # No evidence: gather prices like the cheaper of answer/defer.
    assert costs.gather == pytest.approx(2070.0)
