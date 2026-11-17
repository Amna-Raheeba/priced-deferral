"""Tests for the data model."""

from priced_deferral.models import (
    Alternative,
    DecisionCase,
    EvidenceItem,
    HarmProfile,
)


def test_evidence_item_defaults():
    item = EvidenceItem(item_id="e1", text="t", decisiveness=0.5, cost=3.0)
    assert item.supports == ""
    assert item.contradicts is False


def test_harm_profile_defaults():
    profile = HarmProfile(name="x", harm_wrong=100.0, human_cost=5.0, delay_cost=1.0)
    assert profile.human_accuracy == 0.98
    assert profile.answer_cost == 0.0


def test_decision_case_defaults():
    case = DecisionCase(case_id="c1", domain="ops", question="q?",
                        candidate="yes", p_correct=0.8)
    assert case.evidence == []
    assert case.correct is True
    assert case.true_label == ""
    assert case.human_correct is True


def test_alternative_support_default():
    assert Alternative(label="no").support == 0
