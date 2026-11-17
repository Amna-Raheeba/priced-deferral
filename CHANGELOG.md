# Changelog

## 0.1.0 — 2026-11-17

- First release: expected-cost pricing for answer / gather / defer,
  optimal gather-then-redecide plans with signed confidence updates,
  minimal deferral packets (greedy + exact), and a benchmark against
  always-answer, fixed-threshold (0.62), and oracle baselines across
  three harm profiles (clinic, research, ops) on 60 seeded + 12
  hand-reasoned cases.
- Three bugs caught and fixed during evaluation, all documented in the
  README: unsigned evidence updates (opposing items raised confidence),
  double-counted decisiveness in the gather planner, and vacuous
  "gather" verdicts with empty plans.
