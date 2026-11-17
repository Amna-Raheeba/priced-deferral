"""Tests for the minimal deferral packet."""

from priced_deferral.models import Alternative, DecisionCase, EvidenceItem
from priced_deferral.packet import (
    QUESTIONS,
    build_candidate_items,
    build_packet,
    exact_minimal_packet,
    greedy_minimal_packet,
)


def _case(**over):
    base = {
        "case_id": "c1", "domain": "ops", "question": "q?", "candidate": "yes",
        "p_correct": 0.6,
        "gathered": [EvidenceItem(item_id="g1", text="g", decisiveness=0.0,
                                  cost=0.0, supports="candidate")],
        "alternatives": [Alternative(label="no", support=2)],
        "conflicts": ["A held fact contradicts the candidate."],
        "missing": ["The deciding measurement."],
        "correct": False, "true_label": "no", "human_correct": True,
    }
    base.update(over)
    return DecisionCase(**base)


def test_packet_covers_all_questions():
    packet = build_packet(_case())
    assert set(packet.questions_covered) == set(QUESTIONS)
    assert len(packet.items) == 4  # one per question: claim/conflict/alt/missing


def test_packet_fallback_items_when_nothing_to_show():
    case = _case(conflicts=[], alternatives=[], missing=[])
    packet = build_packet(case)
    assert set(packet.questions_covered) == set(QUESTIONS)
    texts = [i.text for i in packet.items]
    assert any("No known conflicts" in t for t in texts)
    assert any("No competing answer" in t for t in texts)
    assert any("Nothing known missing" in t for t in texts)


def test_greedy_equals_exact_on_small_pool():
    items = build_candidate_items(_case())
    greedy = greedy_minimal_packet(items)
    exact = exact_minimal_packet(items)
    assert exact is not None
    assert len(greedy) == len(exact)


def test_packet_sufficient_when_alternative_supported():
    # Wrong candidate, supported alternative, conflict present: the
    # simulated human doubts the candidate and takes the alternative.
    packet = build_packet(_case())
    assert packet.sufficient is True


def test_packet_insufficient_trap():
    # Tie, no conflict: the human keeps the candidate, which is wrong.
    # This is a documented limit, not a bug: with equal support and no
    # conflict, the packet cannot steer the human.
    case = _case(conflicts=[], alternatives=[Alternative(label="no", support=1)])
    packet = build_packet(case)
    assert packet.sufficient is False


def test_packet_compression_between_zero_and_one():
    packet = build_packet(_case())
    assert 0.0 < packet.compression <= 1.0


def test_packet_compression_drops_with_more_candidates():
    # Two conflicts + two alternatives + two missing = pool of 7;
    # the minimal packet still needs only 4 (one per question).
    case = _case(
        conflicts=["Conflict A.", "Conflict B."],
        alternatives=[Alternative(label="no", support=2),
                      Alternative(label="maybe", support=1)],
        missing=["Missing A.", "Missing B."])
    packet = build_packet(case)
    assert len(packet.items) == 4
    assert packet.compression == 4 / 7


def test_dual_coverage_item_shrinks_packet():
    # A held item that contradicts the candidate AND supports the
    # alternative covers Q_why_wrong and Q_alternatives at once, so the
    # minimal packet is 3 items, not 4 — and greedy still equals exact.
    gathered = [
        EvidenceItem(item_id="g1", text="g", decisiveness=0.0, cost=0.0,
                     supports="candidate"),
        EvidenceItem(item_id="g2", text="h", decisiveness=0.0, cost=0.0,
                     supports="no", contradicts=True),
    ]
    case = _case(gathered=gathered)
    packet = build_packet(case)
    assert len(packet.items) == 3
    assert packet.compression == 3 / 5
    items = build_candidate_items(case)
    assert len(greedy_minimal_packet(items)) == len(exact_minimal_packet(items))
