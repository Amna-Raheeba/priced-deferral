"""Benchmark runner: priced policy vs baselines over case sets.

Runs decide() (priced), always_answer, fixed_threshold (0.62) and oracle
over the same cases and harm profile, and reports realized costs, rates,
packet quality, calibration of the stated confidences, and regret vs the
oracle. All numbers are deterministic given the case files.
"""

import json
import os

from .models import Alternative, DecisionCase, EvidenceItem, HarmProfile
from .policy import always_answer, decide, evaluate, fixed_threshold, oracle

PROFILES = {
    "clinic": HarmProfile(name="clinic", harm_wrong=100000.0, human_cost=50.0,
                          delay_cost=20.0, human_accuracy=0.98),
    "research": HarmProfile(name="research", harm_wrong=500.0, human_cost=15.0,
                            delay_cost=5.0, human_accuracy=0.97),
    "ops": HarmProfile(name="ops", harm_wrong=50.0, human_cost=5.0,
                       delay_cost=2.0, human_accuracy=0.95),
}


def load_cases(path):
    """Load cases from a JSON file into DecisionCase objects."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    cases = []
    for item in raw:
        evidence = [EvidenceItem(**e) for e in item.get("evidence", [])]
        gathered = [EvidenceItem(**e) for e in item.get("gathered", [])]
        alternatives = [Alternative(**a) for a in item.get("alternatives", [])]
        cases.append(DecisionCase(
            case_id=item["case_id"],
            domain=item["domain"],
            question=item["question"],
            candidate=item["candidate"],
            p_correct=item["p_correct"],
            evidence=evidence,
            gathered=gathered,
            alternatives=alternatives,
            conflicts=item.get("conflicts", []),
            missing=item.get("missing", []),
            correct=item.get("correct", True),
            true_label=item.get("true_label", ""),
            human_correct=item.get("human_correct", True),
        ))
    return cases


def calibration_error(cases, bins=5):
    """Expected calibration error of stated p vs realized correctness."""
    edges = [i / bins for i in range(bins + 1)]
    total = 0.0
    for b in range(bins):
        lo, hi = edges[b], edges[b + 1]
        group = [c for c in cases if lo <= c.p_correct < hi or (b == bins - 1 and c.p_correct == hi)]
        if not group:
            continue
        mean_p = sum(c.p_correct for c in group) / len(group)
        acc = sum(1 for c in group if c.correct) / len(group)
        total += (len(group) / len(cases)) * abs(mean_p - acc)
    return total


def run_benchmark(cases_path, profile_name="clinic"):
    """Run all policies on one case file under one harm profile."""
    profile = PROFILES[profile_name]
    cases = load_cases(cases_path)
    priced = evaluate(cases, profile, decide)
    always = evaluate(cases, profile, always_answer)
    threshold = evaluate(cases, profile, fixed_threshold)
    orc = evaluate(cases, profile, oracle)
    # Verdict-choice agreement: how often the priced verdict matches the
    # oracle's verdict (answer when right, defer when wrong). Gather
    # counts as a match only when the oracle would defer and the priced
    # second stage is also defer.
    agree = 0
    for case in cases:
        d = decide(case, profile)
        want = "answer" if case.correct else "defer"
        got = d.verdict
        if got == "gather":
            got = d.gather_plan.second_stage if d.gather_plan else "defer"
        if got == want:
            agree += 1
    return {
        "profile": profile_name,
        "n": len(cases),
        "calibration_error": calibration_error(cases),
        "priced": priced,
        "always_answer": always,
        "fixed_threshold_062": threshold,
        "oracle": orc,
        "verdict_agreement_with_oracle": agree / len(cases) if cases else 0.0,
        "priced_saving_vs_always": (always["total_cost"] - priced["total_cost"]) / always["total_cost"] if always["total_cost"] else 0.0,
        "priced_saving_vs_threshold": (threshold["total_cost"] - priced["total_cost"]) / threshold["total_cost"] if threshold["total_cost"] else 0.0,
        "priced_regret_vs_oracle": (priced["total_cost"] - orc["total_cost"]) / orc["total_cost"] if orc["total_cost"] else 0.0,
    }


def run_all(data_dir):
    """Run the benchmark for every profile over cases.json + hand_cases.json."""
    results = {}
    for profile_name in PROFILES:
        for fname in ("cases.json", "hand_cases.json"):
            path = os.path.join(data_dir, fname)
            if os.path.exists(path):
                key = "%s/%s" % (profile_name, fname)
                results[key] = run_benchmark(path, profile_name)
    return results
