"""Example: price one case from a JSON file.

Run: python examples/demo_run.py
Loads examples/demo_case.json (a research-domain case where gathering
one cheap decisive check beats both answering now and deferring) and
prints the priced decision.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from priced_deferral.cli import _case_from_dict
from priced_deferral.evaluate import PROFILES
from priced_deferral.policy import decide
from priced_deferral.report import decision_report

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "demo_case.json"), encoding="utf-8") as fh:
    raw = json.load(fh)

case = _case_from_dict(raw)
decision = decide(case, PROFILES["research"])
print(decision_report(decision, case))
