"""Regenerate results/ and guard against headline drift.

Run: python scripts/reproduce_results.py [--out DIR]
Regenerates the benchmark into --out (default: results/) and, when the
committed results/evaluation.json exists, fails if any headline total
cost moved by more than 0.01 — a changed number must come with a code
or data change, not silent drift.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from priced_deferral.cli import write_benchmark
from priced_deferral.evaluate import run_all

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "data")
COMMITTED = os.path.join(ROOT, "results", "evaluation.json")
TOLERANCE = 0.01


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(ROOT, "results"))
    args = parser.parse_args()
    # Load the committed numbers BEFORE overwriting them, then compare.
    committed = None
    if os.path.exists(COMMITTED):
        committed = json.load(open(COMMITTED, encoding="utf-8"))
    results = run_all(DATA)
    if committed is not None:
        for key, run in committed.items():
            if key not in results:
                print("MISSING RUN: %s" % key)
                return 1
            for policy in ("priced", "always_answer", "fixed_threshold_062", "oracle"):
                old = run[policy]["total_cost"]
                new = results[key][policy]["total_cost"]
                if abs(old - new) > TOLERANCE:
                    print("DRIFT: %s %s total cost %.2f -> %.2f" % (key, policy, old, new))
                    return 1
        print("No headline drift (tolerance %.2f)." % TOLERANCE)
    write_benchmark(results, args.out)
    print("Wrote %s." % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
