"""Expected-cost pricing for the three options: answer, gather, defer.

All costs are in one currency (the harm profile's units). The formulas are
deliberately simple and auditable:

- answer now: (1 - p) * harm + answer_cost
- defer: (1 - human_accuracy) * harm + human_cost + delay_cost
- gather: pay for evidence, update p, then take the cheaper of
  answer(p') and defer. Evidence with decisiveness d removes that
  fraction of the remaining error probability:
  p' = 1 - (1 - p) * prod(1 - d_i).

The optimal gather plan is greedy by marginal value: repeatedly add the
item whose marginal benefit (reduction in expected error cost) per unit
cost is largest, while that benefit exceeds the item's cost. Deterministic
tie-break by item id.
"""

from .models import GatherPlan, PricedOptions


def clamp_p(p):
    """Keep a probability inside [0, 1]."""
    return max(0.0, min(1.0, p))


def updated_p(p, items):
    """p after gathering items with decisiveness d_i.

    Signed update: items supporting the candidate remove that fraction
    of the remaining error probability (p rises toward 1); items
    supporting an alternative or contradicting the candidate remove
    that fraction of the current confidence (p falls toward 0). An
    opposing item must never raise p — that was a real bug in v0.1.0's
    first draft, caught by the benchmark (gathering "evidence" that
    argued against the candidate still raised confidence).
    """
    p = clamp_p(p)
    remaining_error = 1.0 - p
    for item in items:
        if item.supports == "candidate" and not item.contradicts:
            d = max(0.0, min(1.0, item.decisiveness))
            remaining_error *= 1.0 - d
    p = 1.0 - remaining_error
    for item in items:
        if item.supports != "candidate" or item.contradicts:
            d = max(0.0, min(1.0, item.decisiveness))
            p *= 1.0 - d
    return clamp_p(p)


def expected_answer_cost(p, profile):
    """Expected cost of answering now at confidence p."""
    return (1.0 - clamp_p(p)) * profile.harm_wrong + profile.answer_cost


def expected_defer_cost(profile):
    """Expected cost of deferring to a human."""
    residual = (1.0 - profile.human_accuracy) * profile.harm_wrong
    return residual + profile.human_cost + profile.delay_cost


def optimal_gather_plan(p, items, profile):
    """Best gather-then-redecide plan, or None if gathering never pays.

    Returns a GatherPlan with the chosen items (possibly empty, meaning
    gather-then-redecide is priced but buys nothing — callers treat an
    empty plan as "gather is not useful").
    """
    defer_cost = expected_defer_cost(profile)
    chosen = []
    current_p = clamp_p(p)
    spent = 0.0
    remaining = list(items)
    while remaining:
        best = None
        best_ratio = 0.0
        best_gain = 0.0
        for item in remaining:
            # current_p already includes the chosen items: apply only
            # this candidate item (applying chosen again would
            # double-count their decisiveness — a real bug in the
            # first draft, caught by the benchmark).
            new_p = updated_p(current_p, [item])
            # Benefit: what the second stage costs now vs after this item.
            now_stage = min(expected_answer_cost(current_p, profile), defer_cost)
            after_stage = min(expected_answer_cost(new_p, profile), defer_cost)
            gain = now_stage - after_stage
            if item.cost <= 0:
                ratio = float("inf") if gain > 0 else 0.0
            else:
                ratio = gain / item.cost
            if gain > 0 and (best is None or ratio > best_ratio
                             or (ratio == best_ratio and item.item_id < best.item_id)):
                best = item
                best_ratio = ratio
                best_gain = gain
        if best is None or best_gain <= best.cost:
            break
        chosen.append(best)
        remaining.remove(best)
        spent += best.cost
        current_p = updated_p(p, chosen)
    p_after = updated_p(p, chosen)
    stage_cost = min(expected_answer_cost(p_after, profile), defer_cost)
    second = "answer" if expected_answer_cost(p_after, profile) <= defer_cost else "defer"
    return GatherPlan(
        items=tuple(chosen),
        gather_cost=spent,
        p_after=p_after,
        expected_cost=spent + stage_cost,
        second_stage=second,
    )


def price_options(case, profile):
    """Expected costs of answer / gather / defer for one case."""
    answer = expected_answer_cost(case.p_correct, profile)
    defer = expected_defer_cost(profile)
    plan = optimal_gather_plan(case.p_correct, case.evidence, profile)
    gather = plan.expected_cost
    return PricedOptions(answer=answer, gather=gather, defer=defer)
