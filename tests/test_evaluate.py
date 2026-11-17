"""Tests for the benchmark runner."""

import os

from priced_deferral.evaluate import (
    PROFILES,
    calibration_error,
    load_cases,
    run_benchmark,
)

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def test_load_cases():
    cases = load_cases(os.path.join(DATA, "cases.json"))
    assert len(cases) == 60
    assert {c.domain for c in cases} == {"clinic", "research", "ops"}
    hand = load_cases(os.path.join(DATA, "hand_cases.json"))
    assert len(hand) == 12


def test_profiles():
    assert PROFILES["clinic"].harm_wrong == 100000.0
    assert PROFILES["research"].harm_wrong == 500.0
    assert PROFILES["ops"].harm_wrong == 50.0


def test_calibration_error_bounded():
    cases = load_cases(os.path.join(DATA, "cases.json"))
    error = calibration_error(cases)
    assert 0.0 <= error <= 1.0


def test_run_benchmark_hand_cases_research():
    result = run_benchmark(os.path.join(DATA, "hand_cases.json"), "research")
    assert result["n"] == 12
    # Priced policy must beat both naive baselines on realized cost.
    assert result["priced"]["total_cost"] < result["always_answer"]["total_cost"]
    assert result["priced"]["total_cost"] < result["fixed_threshold_062"]["total_cost"]
    # ...and never beat the oracle (it knows the truth).
    assert result["priced"]["total_cost"] >= result["oracle"]["total_cost"]
    # Safety: zero errors on answered cases in the hand set.
    assert result["priced"]["error_rate_answered"] == 0.0
    assert 0.0 <= result["verdict_agreement_with_oracle"] <= 1.0


def test_run_benchmark_cases_clinic_safety():
    result = run_benchmark(os.path.join(DATA, "cases.json"), "clinic")
    # In the highest-harm domain the priced policy must beat both naive
    # baselines on realized cost — and it does, by a wide margin.
    assert result["priced"]["total_cost"] < result["always_answer"]["total_cost"]
    assert result["priced"]["total_cost"] < result["fixed_threshold_062"]["total_cost"]
    # Honest limit, documented in the README: the priced policy is NOT
    # error-free in clinic on this seed (error rate 0.182 on answered
    # cases). Misleading supporting evidence can raise confidence past
    # the deferral threshold, so it answers two wrong candidates that
    # the fixed threshold would have deferred. Pricing buys cost, not
    # certainty — the error rate stays below always-answer's.
    assert result["priced"]["error_rate_answered"] < result["always_answer"]["error_rate_answered"]
