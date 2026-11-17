"""The priced policy and its baselines.

decide() prices answer / gather / defer in one currency and takes the
cheapest. Ties break toward the least human burden: answer, then gather,
then defer.

Baselines for comparison:
- always_answer: answer every case.
- fixed_threshold: answer when p >= threshold (0.62, the abstention
  threshold of Amna's healthcare-research-agent), else defer.
- oracle: knows ground truth — answers when the candidate is correct,
  otherwise defers (or gathers first when gathering is cheaper than
  deferring and would reveal the error — the oracle never pays for
  information it does not need).

evaluate() runs a policy over cases with a harm profile and returns
realized totals: cost, error rate on answered cases, defer/gather rates,
packet sufficiency and compression on deferred cases, and regret vs the
oracle's realized cost.
"""

from .models import Decision
from .packet import build_packet
from .pricing import optimal_gather_plan, price_options


def decide(case, profile):
    """Priced verdict for one case.

    "Gather" is only a verdict when the optimal plan actually gathers
    something: an empty plan prices exactly like the cheaper of answer
    and defer, so calling it "gather" would be a vacuous verdict (a
    real bug in the first draft — the demo came back GATHER with zero
    items). A packet is built whenever the human will be involved: a
    direct defer, or a gather whose second stage defers.
    """
    costs = price_options(case, profile)
    plan = optimal_gather_plan(case.p_correct, case.evidence, profile)
    cheapest = min(costs.answer, costs.gather, costs.defer)
    if costs.answer <= cheapest:
        verdict = "answer"
    elif costs.gather <= cheapest and plan.items:
        verdict = "gather"
    else:
        verdict = "defer"
    packet = None
    if verdict == "defer":
        packet = build_packet(case)
    elif verdict == "gather" and plan.second_stage == "defer":
        packet = build_packet(case)
    return Decision(case_id=case.case_id, verdict=verdict, costs=costs,
                    gather_plan=plan if verdict == "gather" else None,
                    packet=packet)


def _realize(case, profile, verdict, plan=None):
    """Realized cost of one decision, given ground truth.

    Gathering buys information: after gathering, the second stage is
    re-priced with p'. The candidate's truth is fixed; gathering only
    changes what the policy chooses to do.
    """
    if verdict == "answer":
        cost = profile.answer_cost
        if not case.correct:
            cost += profile.harm_wrong
        return cost, "answered", (not case.correct)
    if verdict == "defer":
        cost = profile.human_cost + profile.delay_cost
        error = False
        if not case.human_correct:
            cost += profile.harm_wrong
            error = True
        return cost, "deferred", error
    # gather: pay, update p', re-price answer vs defer.
    plan = plan or optimal_gather_plan(case.p_correct, case.evidence, profile)
    cost = plan.gather_cost
    if plan.second_stage == "answer":
        cost += profile.answer_cost
        if not case.correct:
            cost += profile.harm_wrong
        return cost, "gathered_then_answered", (not case.correct)
    cost += profile.human_cost + profile.delay_cost
    error = False
    if not case.human_correct:
        cost += profile.harm_wrong
        error = True
    return cost, "gathered_then_deferred", error


def always_answer(case, profile):
    """Baseline: answer every case."""
    return Decision(case_id=case.case_id, verdict="answer",
                    costs=price_options(case, profile))


def fixed_threshold(case, profile, threshold=0.62):
    """Baseline: answer when p >= threshold, else defer (no gather)."""
    verdict = "answer" if case.p_correct >= threshold else "defer"
    packet = build_packet(case) if verdict == "defer" else None
    return Decision(case_id=case.case_id, verdict=verdict,
                    costs=price_options(case, profile), packet=packet)


def oracle(case, profile):
    """Baseline: knows ground truth; never pays for unneeded information.

    Answers when the candidate is right, defers when it is wrong. It
    never gathers — gathering buys information, and the oracle has none
    left to buy. This is the cost floor the priced policy is measured
    against.
    """
    verdict = "answer" if case.correct else "defer"
    packet = build_packet(case) if verdict == "defer" else None
    return Decision(case_id=case.case_id, verdict=verdict,
                    costs=price_options(case, profile), packet=packet)


def evaluate(cases, profile, policy_fn):
    """Run a policy over cases; return realized aggregate metrics."""
    total_cost = 0.0
    cost_on_correct = 0.0
    cost_on_wrong = 0.0
    answered = 0
    errors = 0
    deferred = 0
    gathered = 0
    packet_sufficient = 0
    packet_total = 0
    packet_items = 0
    packet_compression = 0.0
    for case in cases:
        decision = policy_fn(case, profile)
        plan = decision.gather_plan
        cost, outcome, error = _realize(case, profile, decision.verdict, plan)
        total_cost += cost
        if case.correct:
            cost_on_correct += cost
        else:
            cost_on_wrong += cost
        if outcome in ("answered", "gathered_then_answered"):
            answered += 1
            if error:
                errors += 1
        if outcome in ("deferred", "gathered_then_deferred"):
            deferred += 1
        if outcome.startswith("gathered"):
            gathered += 1
        if decision.packet is not None:
            packet_total += 1
            packet_items += len(decision.packet.items)
            packet_compression += decision.packet.compression
            if decision.packet.sufficient:
                packet_sufficient += 1
    n = len(cases) or 1
    return {
        "n": len(cases),
        "total_cost": total_cost,
        "mean_cost": total_cost / n,
        # Insurance split: what the policy spent on cases it got right
        # (mostly deferral/gather fees — the price of not knowing) vs
        # cases it got wrong (mostly realized harm). When deferral is
        # nearly free against the harm, regret vs the oracle is dominated
        # by insurance, not by errors — this split makes that checkable.
        "cost_on_correct": cost_on_correct,
        "cost_on_wrong": cost_on_wrong,
        "answered": answered,
        "error_rate_answered": (errors / answered) if answered else 0.0,
        "defer_rate": deferred / n,
        "gather_rate": gathered / n,
        "packet_sufficient_rate": (packet_sufficient / packet_total) if packet_total else 0.0,
        "mean_packet_items": (packet_items / packet_total) if packet_total else 0.0,
        "mean_packet_compression": (packet_compression / packet_total) if packet_total else 0.0,
    }
