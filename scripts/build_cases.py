"""Regenerate data/cases.json (seeded, 60 cases) and data/hand_cases.json (12).

Run: python scripts/build_cases.py
Seed 7. Generated cases: 20 per domain (clinic, research, ops), p drawn
in low/mid/high bands, correctness sampled Bernoulli(p), human correctness
sampled Bernoulli(human_accuracy). Hand cases are written out literally —
they pin edge behaviours (p = 1.0, gather-cheaper-than-defer, packet
sufficiency and its trap, expensive gather, unreliable human).
"""

import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

DOMAINS = {
    "clinic": {
        "questions": [
            "Does this patient need urgent referral for suspected sepsis?",
            "Is this chest pain cardiac in origin?",
            "Should this patient start anticoagulation today?",
            "Does this rash indicate a drug allergy?",
        ],
        "candidates": ["Yes — urgent referral", "Yes — cardiac", "Yes — start today",
                       "Yes — drug allergy"],
        "alternatives": ["No — observe", "No — non-cardiac", "No — wait for labs",
                         "No — viral rash"],
        "cost_lo": 5.0,
        "cost_hi": 15.0,
        "human_accuracy": 0.98,
    },
    "research": {
        "questions": [
            "Does this paper claim a state-of-the-art result on ImageNet?",
            "Is the proposed method a variant of LoRA?",
            "Does the study use a randomized controlled trial?",
            "Is the dataset publicly available?",
        ],
        "candidates": ["Yes — SOTA on ImageNet", "Yes — LoRA variant",
                       "Yes — RCT", "Yes — public"],
        "alternatives": ["No — SOTA on CIFAR only", "No — full fine-tuning",
                         "No — observational", "No — on request only"],
        "cost_lo": 1.0,
        "cost_hi": 5.0,
        "human_accuracy": 0.97,
    },
    "ops": {
        "questions": [
            "Is the 09:00 flight the cheapest option for Friday?",
            "Does the hotel offer free cancellation?",
            "Is the downtown venue available on Saturday?",
            "Does the supplier deliver within 48 hours?",
        ],
        "candidates": ["Yes — cheapest", "Yes — free cancellation",
                       "Yes — available Saturday", "Yes — delivers in 48h"],
        "alternatives": ["No — 14:00 is cheaper", "No — cancellation fee applies",
                         "No — booked Saturday", "No — 72h delivery"],
        "cost_lo": 0.5,
        "cost_hi": 2.0,
        "human_accuracy": 0.95,
    },
}


def _make_case(rng, domain, idx):
    cfg = DOMAINS[domain]
    band = rng.random()
    if band < 0.2:
        p = round(rng.uniform(0.50, 0.70), 2)
    elif band < 0.6:
        p = round(rng.uniform(0.70, 0.90), 2)
    else:
        p = round(rng.uniform(0.90, 0.99), 2)
    correct = rng.random() < p
    q = rng.randrange(len(cfg["questions"]))
    n_evidence = rng.randint(2, 5)
    evidence = []
    # Evidence must be genuinely informative: when the candidate is
    # correct, most items support it; when it is wrong, most items
    # support an alternative. Otherwise gathering would raise stated
    # confidence without raising the chance of being right, and the
    # priced policy's expected-cost math would be dishonest.
    support_rate = 0.75 if correct else 0.30
    for j in range(n_evidence):
        supports = "candidate" if rng.random() < support_rate else "alt-%d" % rng.randint(0, 1)
        evidence.append({
            "item_id": "e%d" % (j + 1),
            "text": "%s evidence %d: %s." % (domain, j + 1, "supports the candidate" if supports == "candidate" else "supports an alternative"),
            "decisiveness": round(rng.uniform(0.10, 0.60), 2),
            "cost": round(rng.uniform(cfg["cost_lo"], cfg["cost_hi"]), 2),
            "supports": supports,
            "contradicts": False,
        })
    n_alt = rng.randint(1, 2)
    # Support counts must be truth-correlated like the evidence: when
    # the candidate is wrong, the true alternative (first listed) is
    # genuinely well supported; when it is right, alternatives are
    # weakly supported at most. Otherwise the packet-sufficiency
    # simulation would measure random numbers, not the packet.
    alternatives = [{
        "label": cfg["alternatives"][q] if i == 0 else "alt-%d" % i,
        "support": (2 if (not correct and i == 0) else rng.randint(0, 1)),
    } for i in range(n_alt)]
    gathered = [{
        "item_id": "g1",
        "text": "Initial observation supports the candidate.",
        "decisiveness": 0.0,
        "cost": 0.0,
        "supports": "candidate",
        "contradicts": False,
    }]
    # In 40% of cases a second held item contradicts the candidate and
    # supports the leading alternative — the dual-coverage item that
    # makes the minimal-packet computation non-trivial.
    if rng.random() < 0.4:
        gathered.append({
            "item_id": "g2",
            "text": "A held measurement argues against the candidate.",
            "decisiveness": 0.0,
            "cost": 0.0,
            "supports": alternatives[0]["label"],
            "contradicts": True,
        })
    conflicts = []
    if rng.random() < 0.5:
        conflicts.append("One held fact contradicts the candidate.")
    if rng.random() < 0.25:
        conflicts.append("A second held fact weakens the candidate.")
    missing = ["The key deciding measurement is not yet held."]
    if rng.random() < 0.5:
        missing.append("A corroborating source is not yet checked.")
    return {
        "case_id": "%s-%02d" % (domain, idx),
        "domain": domain,
        "question": cfg["questions"][q],
        "candidate": cfg["candidates"][q],
        "p_correct": p,
        "evidence": evidence,
        "gathered": gathered,
        "alternatives": alternatives,
        "conflicts": conflicts,
        "missing": missing,
        "correct": correct,
        "true_label": "" if correct else alternatives[0]["label"],
        "human_correct": rng.random() < cfg["human_accuracy"],
    }


def _hand_cases():
    """12 hand-written edge cases (case ids hand-01 .. hand-12)."""
    base_evidence = lambda d, cost: [
        {"item_id": "e1", "text": "Decisive check result.",
         "decisiveness": d, "cost": cost, "supports": "candidate",
         "contradicts": False},
    ]
    gathered_one = [{
        "item_id": "g1", "text": "Initial observation supports the candidate.",
        "decisiveness": 0.0, "cost": 0.0, "supports": "candidate",
        "contradicts": False,
    }]
    cases = []
    # 1. p = 1.0: answering is free of expected error — always answer.
    cases.append({"case_id": "hand-01", "domain": "clinic",
                  "question": "Is the diagnosis confirmed by the gold-standard test?",
                  "candidate": "Yes — confirmed", "p_correct": 1.0,
                  "evidence": [], "gathered": gathered_one,
                  "alternatives": [], "conflicts": [], "missing": [],
                  "correct": True, "true_label": "", "human_correct": True})
    # 2. p = 0.99 clinic: answer (error cost 1000 < defer 2070).
    cases.append({"case_id": "hand-02", "domain": "clinic",
                  "question": "Is this chest pain cardiac in origin?",
                  "candidate": "Yes — cardiac", "p_correct": 0.99,
                  "evidence": [], "gathered": gathered_one,
                  "alternatives": [{"label": "No — non-cardiac", "support": 0}],
                  "conflicts": [], "missing": [],
                  "correct": True, "true_label": "", "human_correct": True})
    # 3. p = 0.55 clinic: defer — gathering cannot beat a cheap deferral.
    cases.append({"case_id": "hand-03", "domain": "clinic",
                  "question": "Does this patient need urgent referral?",
                  "candidate": "Yes — urgent referral", "p_correct": 0.55,
                  "evidence": base_evidence(0.5, 8.0), "gathered": gathered_one,
                  "alternatives": [{"label": "No — observe", "support": 1}],
                  "conflicts": ["White cell count normal."],
                  "missing": ["Blood culture result."],
                  "correct": False, "true_label": "No — observe",
                  "human_correct": True})
    # 4. p = 0.80 research, one decisive cheap item: gather wins.
    cases.append({"case_id": "hand-04", "domain": "research",
                  "question": "Does this paper claim SOTA on ImageNet?",
                  "candidate": "Yes — SOTA on ImageNet", "p_correct": 0.80,
                  "evidence": base_evidence(0.9, 1.0), "gathered": gathered_one,
                  "alternatives": [{"label": "No — SOTA on CIFAR only", "support": 0}],
                  "conflicts": [], "missing": ["The results table."],
                  "correct": True, "true_label": "", "human_correct": True})
    # 5. p = 0.60 ops, decisive cheap item: gather wins.
    cases.append({"case_id": "hand-05", "domain": "ops",
                  "question": "Is the 09:00 flight the cheapest option?",
                  "candidate": "Yes — cheapest", "p_correct": 0.60,
                  "evidence": base_evidence(0.8, 0.5), "gathered": gathered_one,
                  "alternatives": [{"label": "No — 14:00 is cheaper", "support": 0}],
                  "conflicts": [], "missing": ["The fare table."],
                  "correct": True, "true_label": "", "human_correct": True})
    # 6. p = 0.97 ops: answer outright.
    cases.append({"case_id": "hand-06", "domain": "ops",
                  "question": "Does the hotel offer free cancellation?",
                  "candidate": "Yes — free cancellation", "p_correct": 0.97,
                  "evidence": [], "gathered": gathered_one,
                  "alternatives": [], "conflicts": [], "missing": [],
                  "correct": True, "true_label": "", "human_correct": True})
    # 7. Conflict-heavy defer: wrong candidate, strong alternative, conflict.
    cases.append({"case_id": "hand-07", "domain": "clinic",
                  "question": "Should this patient start anticoagulation today?",
                  "candidate": "Yes — start today", "p_correct": 0.72,
                  "evidence": base_evidence(0.2, 10.0), "gathered": gathered_one,
                  "alternatives": [{"label": "No — wait for labs", "support": 2}],
                  "conflicts": ["Platelets low at 90.", "Recent bleeding episode noted."],
                  "missing": ["INR result."],
                  "correct": False, "true_label": "No — wait for labs",
                  "human_correct": True})
    # 8. Packet sufficiency: defer, human picks the supported alternative.
    cases.append({"case_id": "hand-08", "domain": "research",
                  "question": "Is the proposed method a variant of LoRA?",
                  "candidate": "Yes — LoRA variant", "p_correct": 0.58,
                  "evidence": base_evidence(0.1, 4.0), "gathered": gathered_one,
                  "alternatives": [{"label": "No — full fine-tuning", "support": 2}],
                  "conflicts": ["Method updates all weights."],
                  "missing": ["The methods section."],
                  "correct": False, "true_label": "No — full fine-tuning",
                  "human_correct": True})
    # 9. Packet insufficiency trap: tie, no conflict — human keeps candidate.
    cases.append({"case_id": "hand-09", "domain": "ops",
                  "question": "Is the downtown venue available on Saturday?",
                  "candidate": "Yes — available Saturday", "p_correct": 0.55,
                  "evidence": base_evidence(0.1, 1.5), "gathered": gathered_one,
                  "alternatives": [{"label": "No — booked Saturday", "support": 1}],
                  "conflicts": [],
                  "missing": ["The booking calendar."],
                  "correct": False, "true_label": "No — booked Saturday",
                  "human_correct": True})
    # 10. No evidence at all: gather buys nothing, price decides.
    cases.append({"case_id": "hand-10", "domain": "research",
                  "question": "Is the dataset publicly available?",
                  "candidate": "Yes — public", "p_correct": 0.66,
                  "evidence": [], "gathered": [],
                  "alternatives": [{"label": "No — on request only", "support": 0}],
                  "conflicts": [], "missing": ["The data-availability statement."],
                  "correct": False, "true_label": "No — on request only",
                  "human_correct": True})
    # 11. Expensive gather: item costs more than the error it could prevent.
    cases.append({"case_id": "hand-11", "domain": "research",
                  "question": "Does the study use a randomized controlled trial?",
                  "candidate": "Yes — RCT", "p_correct": 0.85,
                  "evidence": [{"item_id": "e1", "text": "Full protocol review.",
                                "decisiveness": 0.9, "cost": 400.0,
                                "supports": "candidate", "contradicts": False}],
                  "gathered": gathered_one,
                  "alternatives": [{"label": "No — observational", "support": 0}],
                  "conflicts": [], "missing": ["The protocol document."],
                  "correct": True, "true_label": "", "human_correct": True})
    # 12. Unreliable human: defer is still cheapest ex ante, but the human
    # is wrong — realized regret. (p = 0.5 clinic, human_correct False.)
    cases.append({"case_id": "hand-12", "domain": "clinic",
                  "question": "Does this rash indicate a drug allergy?",
                  "candidate": "Yes — drug allergy", "p_correct": 0.50,
                  "evidence": base_evidence(0.3, 8.0), "gathered": gathered_one,
                  "alternatives": [{"label": "No — viral rash", "support": 1}],
                  "conflicts": ["No prior exposure to the drug."],
                  "missing": ["Allergy history."],
                  "correct": False, "true_label": "No — viral rash",
                  "human_correct": False})
    return cases


def main():
    rng = random.Random(7)
    cases = []
    for domain in ("clinic", "research", "ops"):
        for i in range(1, 21):
            cases.append(_make_case(rng, domain, i))
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "cases.json"), "w", encoding="utf-8") as fh:
        json.dump(cases, fh, indent=2)
    with open(os.path.join(DATA, "hand_cases.json"), "w", encoding="utf-8") as fh:
        json.dump(_hand_cases(), fh, indent=2)
    print("Wrote %d cases + %d hand cases" % (len(cases), 12))


if __name__ == "__main__":
    main()
