# Priced Deferral

**When an agent is uncertain, "abstain" is not a decision — it is a price
you forgot to compare.** This tool prices the three things an uncertain
agent can do — answer now, gather more evidence, or defer to a human —
in one currency, picks the cheapest, and when it defers, builds the
minimal packet the human needs to decide: the claim, why it might be
wrong, what else it could be, and what is missing. Nothing more.

Fixed-threshold abstention (answer when p >= 0.62, else defer — the rule
in Amna's
[healthcare-research-agent](https://github.com/Amna-Raheeba/healthcare-research-agent))
cannot see that a deferral is cheap in one domain and ruinous in
another, or that one cheap check would settle the question. Cost-aware
cascades (Fanconi & van der Schaar, NeurIPS 2025) route base model →
large model → human on confidence thresholds, and learning-to-defer
methods (HILA, ICLR 2026; LLM Performance Predictors, AAMAS 2026) learn
the deferral policy from data — all LLM-based, all trained, none of
them prices a *gather* option against deferral in expected cost, and
none of them constructs a minimal deferral packet. This tool does both,
offline, deterministically, stdlib-only, no model calls.

It is the escalation companion to
[luck-audit](https://github.com/Amna-Raheeba/luck-audit) (which audits
whether an answer was earned by its evidence) and
[plan-change-attribution](https://github.com/Amna-Raheeba/plan-change-attribution)
(which finds what caused a plan change). Luck-audit asks whether the
evidence was sufficient; this tool asks what to *do* about it when it
is not.

## 1. The idea in 30 seconds

1. Every decision carries a harm profile: the cost of a wrong answer,
   the cost of a human's time, the cost of delay, and how often the
   human is right. Three profiles ship: **clinic** (harm 100,000 — a
   wrong triage), **research** (harm 500), **ops** (harm 50).
2. The three options are priced in that one currency:
   - **Answer now:** (1 − p) × harm + answer cost.
   - **Defer:** (1 − human accuracy) × harm + human cost + delay cost.
   - **Gather then re-decide:** pay for evidence, update p, then take
     the cheaper of answer(p′) and defer. Evidence updates p with a
     *signed* rule: supporting items remove a fraction of the remaining
     error probability; opposing items remove a fraction of the current
     confidence.
3. The verdict is the cheapest option (ties break toward the least
   human burden: answer, then gather, then defer). "Gather" is only a
   verdict when the optimal plan actually gathers something — an empty
   plan prices exactly like the cheaper of answer and defer, so calling
   it "gather" would be vacuous.
4. The optimal gather plan is greedy by marginal value: repeatedly add
   the item whose benefit (reduction in second-stage cost) per unit
   cost is largest, while the benefit exceeds the cost.
5. When the verdict is defer — directly, or as the second stage of a
   gather — the human gets a **minimal deferral packet**: the smallest
   set of items covering the four decision questions (what is claimed,
   why it might be wrong, what else it could be, what is missing),
   computed by greedy set cover and verified against the exact minimum
   by brute force. A held item that contradicts the candidate *and*
   supports an alternative covers two questions at once.

## 2. Quick start

```bash
python -m priced_deferral demo
python -m priced_deferral decide examples/demo_case.json --profile research
python -m priced_deferral evaluate --out results
```

## 3. The demo, priced

```
Question: Does this patient need urgent referral for suspected sepsis?
Candidate: Yes — urgent referral (stated p = 0.72)

- Answer now: 28000.00
- Gather then re-decide: 930.00
- Defer to a human: 2070.00

Verdict: GATHER — 2 items, cost 20.00, p 0.72 -> 0.99, then answer.
```

One cheap decisive check (lactate, decisiveness 0.95, cost 8) plus a
second (blood cultures, 0.35, cost 12) lifts confidence to 0.99, where
answering costs 1,000 — cheaper than the 2,070 deferral and far cheaper
than answering blind at 28,000.

## 4. Measured results

60 seeded cases (20 per domain) + 12 hand-reasoned edge cases, three
harm profiles. Realized costs — what actually happened, not what the
policy expected.

| run | priced | always-answer | fixed threshold (0.62) | oracle | saving vs always | saving vs threshold |
|---|---|---|---|---|---|---|
| clinic / cases | 303,536 | 1,400,000 | 900,420 | 980 | 78.3% | 66.3% |
| research / cases | 2,231 | 7,000 | 4,620 | 280 | 68.1% | 51.7% |
| ops / cases | 436 | 700 | 492 | 98 | 37.7% | 11.3% |
| clinic / hand | 100,961 | 600,000 | 300,350 | 100,420 | 83.2% | 66.4% |
| research / hand | 661 | 3,000 | 1,600 | 620 | 78.0% | 58.7% |
| ops / hand | 94 | 300 | 185 | 92 | 68.8% | 49.5% |

Error rate on answered cases (lower is safer):

| run | priced | always-answer | fixed threshold |
|---|---|---|---|
| clinic / cases | 0.182 | 0.233 | 0.167 |
| research / cases | 0.097 | 0.233 | 0.167 |
| ops / cases | 0.136 | 0.233 | 0.167 |
| all hand cases | 0.000 | 0.500 | 0.286 |

Deferral packets: mean 3.5 items on generated cases (exactly the four
decision questions, fewer when one item covers two), compression 0.63–
0.67 against the candidate pool; packet sufficiency 0.63 (clinic),
0.66 (research), 0.81 (ops) — the simulated human decides correctly
from the packet alone that often. On hand cases: 4.0 items,
sufficiency 0.67–0.75.

## 5. Reading the regret numbers honestly

Regret vs the oracle looks extreme — 30,873% on clinic cases — because
the oracle's cost is tiny (980: it answers the 46 right candidates for
free and defers the 14 wrong ones at 70 each). The priced policy's
303,536 splits into two parts, and the split is the story:

- **200,843 on wrong cases** — two wrong candidates the policy
  answered (see §6), plus deferral fees on wrong cases.
- **102,693 on correct cases** — "insurance": deferral and gather fees
  paid on candidates that were right all along. When a human review
  costs 70 against a 100,000 harm, the cost-minimal policy defers
  correct candidates too. That is not a bug; it is the price of not
  knowing.

The same logic explains the low verdict agreement with the oracle in
clinic (0.350): the oracle answers every right candidate, while the
priced policy rationally defers many of them. Agreement is a misleading
metric where deferral is nearly free; the cost columns are the real
measure. On hand cases, where the cases are reasoned rather than
random, regret is 0.5% (clinic), 6.6% (research), 1.6% (ops).

## 6. Honest limits

- **Pricing buys cost, not certainty.** On this seed the priced policy
  answers two wrong clinic candidates (error rate 0.182 on answered
  cases, slightly worse than the fixed threshold's 0.167 there).
  Misleading supporting evidence raised confidence past the deferral
  threshold. The policy still wins on cost by 66% in that domain, but
  anyone quoting the error rate must quote both numbers.
- **Harm values are declared policy, not measured.** Change the harm
  profile and the verdicts change — that is the point of the tool, but
  the numbers are only as honest as the profile.
- **Confidence p is an input, not an estimate.** The tool prices a
  stated probability; it does not calibrate it. Calibration error of
  the stated confidences is reported (0.076 on generated cases) but the
  policy takes p at face value.
- **Information gain is modelled, not measured.** Decisiveness values
  are declared per evidence item; the generator correlates them with
  ground truth (75% of items support a correct candidate, 30% support
  a wrong one), but on real traces they would need to be estimated.
- **The packet-sufficiency human is simulated.** It picks the
  most-supported answer from the packet; real humans bring judgement
  the simulation does not. One hand case (hand-09) is a deliberate
  trap: a tie with no conflict, where the simulated human keeps the
  (wrong) candidate — the packet cannot steer a human with equal
  support and no conflict, and the tool says so.
- **Greedy gather plans are near-optimal, not proven optimal**, and
  the exact minimal packet is brute-forced only for pools of 16 or
  fewer items.

## 7. What the evaluation caught

Three genuine bugs were found by running the benchmark, not by staring
at code, and all three are fixed:

1. **Unsigned evidence updates.** The first draft raised p for *every*
   gathered item, including ones arguing against the candidate. The
   clinic benchmark came back with verdict agreement 0.30 and the
   policy answering wrong candidates it had just gathered evidence
   against. Updates are now signed.
2. **Double-counted decisiveness.** The gather planner applied the
   already-chosen items' decisiveness a second time when scoring the
   next candidate, inflating p′. Fixed by applying only the candidate
   item to the current p.
3. **Vacuous "gather" verdicts.** An empty gather plan priced exactly
   like the cheaper of answer and defer, so the demo came back GATHER
   with zero items. "Gather" is now only a verdict when the plan
   gathers something, and a packet is built whenever the human is
   involved — including gather-then-defer.

## 8. Repo layout

```
priced_deferral/   models, pricing, packet, policy, evaluate, report, cli
data/              cases.json (60 seeded, seed 7), hand_cases.json (12)
tests/             53 tests
notebooks/         01_demo_run.py, 02_evaluation_experiment.py
examples/          demo_case.json, demo_run.py, sample_report.md
scripts/           build_cases.py, reproduce_results.py
results/           evaluation.json/.csv, evaluation_summary.md, HEADLINE.md
app.py             Streamlit dashboard (Decision Explorer, Cost Comparison, Evaluation)
```

`scripts/reproduce_results.py` regenerates `results/` and fails if any
headline total cost drifts by more than 0.01. Run the tests with
`pytest -q`. Python 3.10+; stdlib only at runtime (Streamlit optional,
for the dashboard).
