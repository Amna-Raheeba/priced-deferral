"""Notebook 02 — evaluation experiment: priced policy vs baselines.

Run: python notebooks/02_evaluation_experiment.py
Runs the full benchmark (3 harm profiles x 2 case files) and prints the
headline comparison: realized cost, error rate on answered cases, and the
insurance split (cost spent on cases the policy got right vs wrong).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from priced_deferral.evaluate import run_all

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
results = run_all(DATA)
for key in sorted(results):
    r = results[key]
    print("== %s (n=%d) ==" % (key, r["n"]))
    print("priced total %.2f (insurance %.2f on correct, %.2f on wrong); "
          "always %.2f; threshold %.2f; oracle %.2f" % (
              r["priced"]["total_cost"], r["priced"]["cost_on_correct"],
              r["priced"]["cost_on_wrong"], r["always_answer"]["total_cost"],
              r["fixed_threshold_062"]["total_cost"], r["oracle"]["total_cost"]))
    print("error rate on answered: priced %.3f, always %.3f, threshold %.3f" % (
        r["priced"]["error_rate_answered"],
        r["always_answer"]["error_rate_answered"],
        r["fixed_threshold_062"]["error_rate_answered"]))
    print("defer %.2f, gather %.2f; packet sufficient %.3f, mean %.1f items, "
          "compression %.2f" % (
              r["priced"]["defer_rate"], r["priced"]["gather_rate"],
              r["priced"]["packet_sufficient_rate"],
              r["priced"]["mean_packet_items"],
              r["priced"]["mean_packet_compression"]))
    print("saving vs always %.1f%%, vs threshold %.1f%%; regret vs oracle %.1f%%" % (
        100 * r["priced_saving_vs_always"],
        100 * r["priced_saving_vs_threshold"],
        100 * r["priced_regret_vs_oracle"]))
    print()
