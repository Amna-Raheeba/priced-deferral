"""Streamlit dashboard for Priced Deferral.

Tabs: (1) Decision Explorer — price one case three ways, see the verdict,
gather plan and deferral packet; (2) Cost Comparison — realized cost of
the priced policy vs baselines per profile; (3) Evaluation — full
benchmark table.
"""

import json
import os

import streamlit as st

from priced_deferral.evaluate import PROFILES, load_cases, run_all
from priced_deferral.policy import decide

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def _load_all_cases():
    cases = []
    for fname in ("cases.json", "hand_cases.json"):
        path = os.path.join(DATA, fname)
        if os.path.exists(path):
            cases.extend(load_cases(path))
    return cases


st.set_page_config(page_title="Priced Deferral", layout="wide")
st.title("Priced Deferral — expected-cost escalation for uncertain agents")

tab_decide, tab_costs, tab_eval = st.tabs(
    ["Decision Explorer", "Cost Comparison", "Evaluation"])

with tab_decide:
    cases = _load_all_cases()
    labels = ["%s (%s, p=%.2f)" % (c.case_id, c.domain, c.p_correct) for c in cases]
    choice = st.selectbox("Case", options=range(len(cases)),
                          format_func=lambda i: labels[i])
    profile_name = st.selectbox("Harm profile", options=sorted(PROFILES))
    case = cases[choice]
    profile = PROFILES[profile_name]
    decision = decide(case, profile)
    st.markdown("**Question:** %s" % case.question)
    st.markdown("**Candidate:** %s (p = %.2f)" % (case.candidate, case.p_correct))
    st.table({
        "Option": ["Answer now", "Gather then re-decide", "Defer to a human"],
        "Expected cost": ["%.2f" % decision.costs.answer,
                          "%.2f" % decision.costs.gather,
                          "%.2f" % decision.costs.defer],
    })
    st.markdown("**Verdict: %s**" % decision.verdict.upper())
    if decision.gather_plan is not None and decision.gather_plan.items:
        plan = decision.gather_plan
        st.markdown("Gather %d item(s), cost %.2f, p %.2f -> %.2f, then %s." % (
            len(plan.items), plan.gather_cost, case.p_correct,
            plan.p_after, plan.second_stage))
        for item in plan.items:
            st.markdown("- %s (decisiveness %.2f, cost %.2f)" % (
                item.item_id, item.decisiveness, item.cost))
    if decision.packet is not None:
        st.markdown("**Deferral packet** (%d items, compression %.2f, "
                    "sufficient: %s)" % (
                        len(decision.packet.items),
                        decision.packet.compression,
                        "yes" if decision.packet.sufficient else "no"))
        for item in decision.packet.items:
            st.markdown("- [%s] %s" % (item.kind, item.text))

with tab_costs:
    st.markdown("Realized total cost per policy (lower is better).")
    results = run_all(DATA)
    rows = []
    for key in sorted(results):
        r = results[key]
        rows.append({
            "Run": key,
            "Priced": round(r["priced"]["total_cost"], 2),
            "Always answer": round(r["always_answer"]["total_cost"], 2),
            "Fixed threshold": round(r["fixed_threshold_062"]["total_cost"], 2),
            "Oracle": round(r["oracle"]["total_cost"], 2),
            "Saving vs always (%)": round(100 * r["priced_saving_vs_always"], 1),
        })
    st.table(rows)

with tab_eval:
    results_path = os.path.join(HERE, "results", "evaluation.json")
    if os.path.exists(results_path):
        with open(results_path, encoding="utf-8") as fh:
            results = json.load(fh)
    else:
        results = run_all(DATA)
    for key in sorted(results):
        r = results[key]
        st.markdown("**%s** (n=%d)" % (key, r["n"]))
        st.table({
            "Policy": ["priced", "always_answer", "fixed_threshold_062", "oracle"],
            "Total cost": ["%.2f" % r[name]["total_cost"] for name in
                           ("priced", "always_answer", "fixed_threshold_062", "oracle")],
            "Error rate (answered)": ["%.3f" % r[name]["error_rate_answered"] for name in
                                      ("priced", "always_answer", "fixed_threshold_062", "oracle")],
            "Defer rate": ["%.2f" % r[name]["defer_rate"] for name in
                           ("priced", "always_answer", "fixed_threshold_062", "oracle")],
        })
        st.markdown("Saving vs always %.1f%%, vs threshold %.1f%%; "
                    "regret vs oracle %.1f%%; verdict agreement %.3f; "
                    "packet sufficient %.3f." % (
                        100 * r["priced_saving_vs_always"],
                        100 * r["priced_saving_vs_threshold"],
                        100 * r["priced_regret_vs_oracle"],
                        r["verdict_agreement_with_oracle"],
                        r["priced"]["packet_sufficient_rate"]))
