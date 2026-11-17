"""Tests for report rendering."""

from priced_deferral.evaluate import PROFILES, load_cases, run_all
from priced_deferral.packet import build_packet
from priced_deferral.policy import decide
from priced_deferral.report import benchmark_summary, decision_report, packet_report
import os

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def test_decision_report_contains_verdict_and_costs():
    cases = load_cases(os.path.join(DATA, "hand_cases.json"))
    case = cases[0]  # hand-01: p = 1.0 -> answer
    decision = decide(case, PROFILES["clinic"])
    text = decision_report(decision, case)
    assert "ANSWER" in text
    assert "Answer now:" in text
    assert "Defer to a human:" in text


def test_packet_report_lists_items():
    cases = load_cases(os.path.join(DATA, "hand_cases.json"))
    case = [c for c in cases if c.case_id == "hand-07"][0]
    packet = build_packet(case)
    text = packet_report(packet)
    assert "Deferral packet" in text
    assert "conflict" in text.lower()
    assert "Sufficient" in text


def test_benchmark_summary_contains_policies():
    results = run_all(DATA)
    text = benchmark_summary(results)
    assert "priced" in text
    assert "always_answer" in text
    assert "oracle" in text
    assert "Priced saving vs always-answer" in text
