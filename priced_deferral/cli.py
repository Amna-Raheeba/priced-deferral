"""Command-line interface: demo, evaluate, decide, packet."""

import argparse
import json
import os
import sys

from .evaluate import PROFILES, run_all
from .policy import decide
from .report import benchmark_summary, decision_report

DEMO_CASE = {
    "case_id": "demo-01",
    "domain": "clinic",
    "question": "Does this patient need urgent referral for suspected sepsis?",
    "candidate": "Yes — urgent referral",
    "p_correct": 0.72,
    "evidence": [
        {"item_id": "e1", "text": "Lactate 3.1 mmol/L (elevated).",
         "decisiveness": 0.95, "cost": 8.0, "supports": "candidate"},
        {"item_id": "e2", "text": "Blood cultures pending; no result yet.",
         "decisiveness": 0.35, "cost": 12.0, "supports": "candidate"},
        {"item_id": "e3", "text": "Fever resolved after fluids; vitals stable.",
         "decisiveness": 0.30, "cost": 5.0, "supports": "alt-stable"},
    ],
    "gathered": [
        {"item_id": "g1", "text": "Temperature 38.9 C, heart rate 118.",
         "decisiveness": 0.0, "cost": 0.0, "supports": "candidate"},
    ],
    "alternatives": [
        {"label": "alt-stable", "support": 0},
    ],
    "conflicts": ["White cell count normal at 7.2 — argues against severe infection."],
    "missing": ["Blood culture result (pending).", "Repeat lactate after fluids."],
    "correct": True,
    "true_label": "",
    "human_correct": True,
}


def _case_from_dict(raw):
    from .models import Alternative, DecisionCase, EvidenceItem
    return DecisionCase(
        case_id=raw["case_id"],
        domain=raw["domain"],
        question=raw["question"],
        candidate=raw["candidate"],
        p_correct=raw["p_correct"],
        evidence=[EvidenceItem(**e) for e in raw.get("evidence", [])],
        gathered=[EvidenceItem(**e) for e in raw.get("gathered", [])],
        alternatives=[Alternative(**a) for a in raw.get("alternatives", [])],
        conflicts=raw.get("conflicts", []),
        missing=raw.get("missing", []),
        correct=raw.get("correct", True),
        true_label=raw.get("true_label", ""),
        human_correct=raw.get("human_correct", True),
    )


def cmd_demo(_args):
    case = _case_from_dict(DEMO_CASE)
    decision = decide(case, PROFILES["clinic"])
    print(decision_report(decision, case))


def write_benchmark(results, out_dir):
    """Write evaluation.json / .csv / summary / HEADLINE for a benchmark."""
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "evaluation.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, sort_keys=True)
    rows = ["key,profile,n,priced_cost,always_cost,threshold_cost,oracle_cost,"
            "priced_saving_vs_always,priced_saving_vs_threshold,"
            "priced_regret_vs_oracle,verdict_agreement,packet_sufficient,"
            "mean_packet_items,mean_packet_compression"]
    for key in sorted(results):
        r = results[key]
        rows.append("%s,%s,%d,%.2f,%.2f,%.2f,%.2f,%.4f,%.4f,%.4f,%.4f,%.4f,%.2f,%.4f" % (
            key, r["profile"], r["n"], r["priced"]["total_cost"],
            r["always_answer"]["total_cost"], r["fixed_threshold_062"]["total_cost"],
            r["oracle"]["total_cost"], r["priced_saving_vs_always"],
            r["priced_saving_vs_threshold"], r["priced_regret_vs_oracle"],
            r["verdict_agreement_with_oracle"],
            r["priced"]["packet_sufficient_rate"],
            r["priced"]["mean_packet_items"],
            r["priced"]["mean_packet_compression"]))
    with open(os.path.join(out_dir, "evaluation.csv"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows) + "\n")
    with open(os.path.join(out_dir, "evaluation_summary.md"), "w", encoding="utf-8") as fh:
        fh.write(benchmark_summary(results))
    headline = []
    for key in sorted(results):
        r = results[key]
        headline.append("%s: priced %.2f vs always %.2f (saving %.1f%%), "
                        "vs threshold %.2f (saving %.1f%%), regret vs oracle %.1f%%, "
                        "verdict agreement %.3f" % (
                            key, r["priced"]["total_cost"],
                            r["always_answer"]["total_cost"],
                            100 * r["priced_saving_vs_always"],
                            r["fixed_threshold_062"]["total_cost"],
                            100 * r["priced_saving_vs_threshold"],
                            100 * r["priced_regret_vs_oracle"],
                            r["verdict_agreement_with_oracle"]))
    with open(os.path.join(out_dir, "HEADLINE.md"), "w", encoding="utf-8") as fh:
        fh.write("# Headline\n\n" + "\n".join("- " + h for h in headline) + "\n")


def cmd_evaluate(args):
    data_dir = args.data or os.path.join(os.path.dirname(__file__), "..", "data")
    results = run_all(data_dir)
    write_benchmark(results, args.out)
    print("Wrote %s (profiles x case files: %d runs)" % (args.out, len(results)))


def cmd_decide(args):
    with open(args.case, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, list):
        raw = raw[0]
    case = _case_from_dict(raw)
    profile = PROFILES[args.profile]
    decision = decide(case, profile)
    print(decision_report(decision, case))


def build_parser():
    parser = argparse.ArgumentParser(prog="priced-deferral")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="Run the built-in demo decision")
    ev = sub.add_parser("evaluate", help="Run the full benchmark")
    ev.add_argument("--data", default=None, help="Data directory (default: data/)")
    ev.add_argument("--out", default="results", help="Output directory")
    dec = sub.add_parser("decide", help="Price one case from a JSON file")
    dec.add_argument("case", help="JSON file with one case (object or 1-list)")
    dec.add_argument("--profile", default="clinic",
                     choices=sorted(PROFILES), help="Harm profile")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        cmd_demo(args)
    elif args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "decide":
        cmd_decide(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
