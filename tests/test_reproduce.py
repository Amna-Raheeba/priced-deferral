"""Tests for scripts/reproduce_results.py (headline-drift guard)."""

import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
RESULTS = os.path.join(ROOT, "results")


def test_reproduce_regenerates_results(tmp_path):
    out = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "reproduce_results.py"),
         "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr
    assert (tmp_path / "evaluation.json").exists()
    assert (tmp_path / "HEADLINE.md").exists()


def test_committed_results_match_reproduction():
    """The committed results/ must match a fresh run (tolerance 0.01)."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "reproduce_results.py"),
             "--out", tmp],
            capture_output=True, text=True, cwd=ROOT)
        assert out.returncode == 0, out.stderr
        fresh = json.load(open(os.path.join(tmp, "evaluation.json")))
        committed = json.load(open(os.path.join(RESULTS, "evaluation.json")))
        for key in committed:
            assert key in fresh
            for policy in ("priced", "always_answer", "fixed_threshold_062", "oracle"):
                assert fresh[key][policy]["total_cost"] == committed[key][policy]["total_cost"]
