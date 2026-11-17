"""Markdown and text rendering for decisions, packets, and benchmarks."""


def decision_report(decision, case):
    """One-case report: the priced comparison and the verdict."""
    lines = []
    lines.append("# Priced decision: %s" % case.case_id)
    lines.append("")
    lines.append("Question: %s" % case.question)
    lines.append("Candidate: %s (stated p = %.2f)" % (case.candidate, case.p_correct))
    lines.append("")
    lines.append("## Expected costs")
    lines.append("")
    lines.append("- Answer now: %.2f" % decision.costs.answer)
    lines.append("- Gather then re-decide: %.2f" % decision.costs.gather)
    lines.append("- Defer to a human: %.2f" % decision.costs.defer)
    lines.append("")
    lines.append("Verdict: **%s**" % decision.verdict.upper())
    if decision.gather_plan is not None and decision.gather_plan.items:
        plan = decision.gather_plan
        lines.append("")
        lines.append("Gather plan: %d item(s), cost %.2f, p %.2f -> %.2f, "
                     "then %s." % (len(plan.items), plan.gather_cost,
                                   case.p_correct, plan.p_after,
                                   plan.second_stage))
        for item in plan.items:
            lines.append("- %s (decisiveness %.2f, cost %.2f)" % (
                item.item_id, item.decisiveness, item.cost))
    if decision.packet is not None:
        lines.append("")
        lines.append(packet_report(decision.packet))
    return "\n".join(lines) + "\n"


def packet_report(packet):
    """Render a deferral packet."""
    lines = []
    lines.append("## Deferral packet (%d items, compression %.2f)" % (
        len(packet.items), packet.compression))
    lines.append("")
    lines.append("Covers: %s" % ", ".join(packet.questions_covered))
    lines.append("Sufficient (simulated human decides correctly): %s" % (
        "yes" if packet.sufficient else "no"))
    lines.append("")
    for item in packet.items:
        lines.append("- [%s] %s" % (item.kind, item.text))
    return "\n".join(lines)


def benchmark_summary(results):
    """Render the multi-profile benchmark as Markdown."""
    lines = []
    lines.append("# Priced Deferral — benchmark summary")
    lines.append("")
    for key in sorted(results):
        r = results[key]
        lines.append("## %s (n=%d, calibration error %.3f)" % (
            key, r["n"], r["calibration_error"]))
        lines.append("")
        lines.append("| policy | total cost | error rate (answered) | defer rate | gather rate |")
        lines.append("|---|---|---|---|---|")
        for name in ("priced", "always_answer", "fixed_threshold_062", "oracle"):
            m = r[name]
            lines.append("| %s | %.2f | %.3f | %.3f | %.3f |" % (
                name, m["total_cost"], m["error_rate_answered"],
                m["defer_rate"], m["gather_rate"]))
        lines.append("")
        lines.append("- Priced saving vs always-answer: %.1f%%" % (100 * r["priced_saving_vs_always"]))
        lines.append("- Priced saving vs fixed threshold (0.62): %.1f%%" % (100 * r["priced_saving_vs_threshold"]))
        lines.append("- Priced regret vs oracle: %.1f%%" % (100 * r["priced_regret_vs_oracle"]))
        lines.append("- Verdict agreement with oracle: %.3f" % r["verdict_agreement_with_oracle"])
        lines.append("- Packet: sufficient %.3f, mean %.1f items, compression %.2f" % (
            r["priced"]["packet_sufficient_rate"],
            r["priced"]["mean_packet_items"],
            r["priced"]["mean_packet_compression"]))
        lines.append("")
    return "\n".join(lines)
