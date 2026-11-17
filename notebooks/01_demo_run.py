"""Notebook 01 — demo run: price one decision three ways.

Run: python notebooks/01_demo_run.py
Shows the expected costs of answer / gather / defer for the built-in
clinic demo case, the chosen verdict, and (for a deferral) the minimal
deferral packet.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from priced_deferral.cli import DEMO_CASE, _case_from_dict
from priced_deferral.evaluate import PROFILES
from priced_deferral.policy import decide
from priced_deferral.report import decision_report

case = _case_from_dict(DEMO_CASE)
decision = decide(case, PROFILES["clinic"])
print(decision_report(decision, case))

# Second demo: the same case with a low stated confidence — the priced
# verdict flips to defer, and the packet is printed with it.
low = dict(DEMO_CASE)
low["case_id"] = "demo-02"
low["p_correct"] = 0.55
low_case = _case_from_dict(low)
low_decision = decide(low_case, PROFILES["clinic"])
print(decision_report(low_decision, low_case))
