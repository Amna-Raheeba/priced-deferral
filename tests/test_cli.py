"""Tests for the CLI."""

import json
import os

import pytest

from priced_deferral.cli import main

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def test_cli_demo(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "Priced decision: demo-01" in out
    assert "Verdict:" in out


def test_cli_decide_on_hand_case(tmp_path, capsys):
    hand = json.load(open(os.path.join(DATA, "hand_cases.json")))
    path = tmp_path / "case.json"
    path.write_text(json.dumps(hand[3]), encoding="utf-8")  # hand-04: gather
    assert main(["decide", str(path), "--profile", "research"]) == 0
    out = capsys.readouterr().out
    assert "GATHER" in out


def test_cli_evaluate_writes_results(tmp_path):
    out_dir = tmp_path / "results"
    assert main(["evaluate", "--out", str(out_dir)]) == 0
    assert (out_dir / "evaluation.json").exists()
    assert (out_dir / "evaluation.csv").exists()
    assert (out_dir / "evaluation_summary.md").exists()
    assert (out_dir / "HEADLINE.md").exists()
    data = json.load(open(out_dir / "evaluation.json"))
    assert "clinic/cases.json" in data
    assert "research/hand_cases.json" in data


def test_cli_decide_unknown_profile_fails():
    with pytest.raises(SystemExit):
        main(["decide", "nope.json", "--profile", "nope"])
