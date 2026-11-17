# Priced decision: hand-07

Question: Should this patient start anticoagulation today?
Candidate: Yes — start today (stated p = 0.72)

## Expected costs

- Answer now: 28000.00
- Gather then re-decide: 2070.00
- Defer to a human: 2070.00

Verdict: **DEFER**

## Deferral packet (4 items, compression 0.80)

Covers: Q_alternatives, Q_claim, Q_missing, Q_why_wrong
Sufficient (simulated human decides correctly): yes

- [claim] Candidate: Yes — start today. Support: Initial observation supports the candidate.
- [conflict] Conflict 1: Platelets low at 90.
- [alternative] Alternative: No — wait for labs (support: 2 items).
- [missing] Missing 1: INR result.

