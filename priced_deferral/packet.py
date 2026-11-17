"""Minimal deferral packet construction.

When the priced verdict is "defer", the human gets a packet — the smallest
set of items that covers the four decision questions:

- Q_claim: what is being claimed (candidate + its top support)
- Q_why_wrong: why it might be wrong (conflicts)
- Q_alternatives: what else it could be (competing answers + support)
- Q_missing: what is missing (ungathered decisive facts)

Each packet item covers one or more questions. The minimal packet is the
smallest set covering all four questions (greedy set cover, plus the exact
minimum by brute force when the candidate pool is small). Compression is
|packet| / |everything the human could have been shown|.

Sufficiency is simulated deterministically: a simulated human picks the
answer with the most packet support — the candidate wins ties only if no
conflict is in the packet. The packet is sufficient when that pick matches
ground truth.
"""

import re
from itertools import combinations

from .models import Packet, PacketItem

QUESTIONS = ("Q_claim", "Q_why_wrong", "Q_alternatives", "Q_missing")


def build_candidate_items(case):
    """All items the packet could contain, with the questions each covers."""
    items = []
    support = [e for e in case.gathered if e.supports == "candidate"]
    support_text = "; ".join(e.text for e in support[:2]) or "no supporting evidence held"
    items.append(PacketItem(
        kind="claim",
        text="Candidate: %s. Support: %s" % (case.candidate, support_text),
        covers=("Q_claim",),
    ))
    # Held evidence that argues against the candidate is packet material
    # in its own right — and a contradicting item that also supports an
    # alternative covers TWO questions at once, which is what makes the
    # minimal-set computation non-trivial.
    for g in case.gathered:
        if g.contradicts:
            covers = ["Q_why_wrong"]
            text = "Held evidence against candidate: %s" % g.text
            if g.supports and g.supports != "candidate":
                covers.append("Q_alternatives")
                text += " — supports %s." % g.supports
            items.append(PacketItem(kind="conflict", text=text,
                                    covers=tuple(covers)))
        elif g.supports and g.supports != "candidate":
            items.append(PacketItem(
                kind="alternative",
                text="Held evidence supports %s: %s" % (g.supports, g.text),
                covers=("Q_alternatives",),
            ))
    if case.conflicts:
        for i, conflict in enumerate(case.conflicts):
            items.append(PacketItem(
                kind="conflict",
                text="Conflict %d: %s" % (i + 1, conflict),
                covers=("Q_why_wrong",),
            ))
    else:
        items.append(PacketItem(
            kind="conflict",
            text="No known conflicts on record.",
            covers=("Q_why_wrong",),
        ))
    if case.alternatives:
        for alt in case.alternatives:
            items.append(PacketItem(
                kind="alternative",
                text="Alternative: %s (support: %d item%s)." % (
                    alt.label, alt.support, "" if alt.support == 1 else "s"),
                covers=("Q_alternatives",),
            ))
    else:
        items.append(PacketItem(
            kind="alternative",
            text="No competing answer on record.",
            covers=("Q_alternatives",),
        ))
    if case.missing:
        for i, missing in enumerate(case.missing):
            items.append(PacketItem(
                kind="missing",
                text="Missing %d: %s" % (i + 1, missing),
                covers=("Q_missing",),
            ))
    else:
        items.append(PacketItem(
            kind="missing",
            text="Nothing known missing.",
            covers=("Q_missing",),
        ))
    return items


def _covers_all(items):
    covered = set()
    for item in items:
        covered.update(item.covers)
    return all(q in covered for q in QUESTIONS)


def greedy_minimal_packet(items):
    """Greedy set cover over the four questions (cheapest-first, ties by kind)."""
    chosen = []
    covered = set()
    remaining = list(items)
    while not all(q in covered for q in QUESTIONS) and remaining:
        best = None
        best_new = -1
        for item in remaining:
            new = len(set(item.covers) - covered)
            if new > best_new or (new == best_new and best is not None
                                  and (item.kind, item.text) < (best.kind, best.text)):
                best = item
                best_new = new
        if best is None or best_new == 0:
            break
        chosen.append(best)
        covered.update(best.covers)
        remaining.remove(best)
    return tuple(chosen)


def exact_minimal_packet(items):
    """Exact minimum by brute force (only when the pool is small)."""
    if len(items) > 16:
        return None
    for size in range(0, len(items) + 1):
        for combo in combinations(items, size):
            if _covers_all(combo):
                return tuple(combo)
    return tuple()


def _simulate_human(case, packet_items):
    """Deterministic simulated human: most-supported answer wins.

    Only evidence actually in the packet counts: the candidate's support
    is the gathered candidate-supporting items the claim item presents
    (at most 2); an alternative's support counts only when its item is
    in the packet. The candidate wins a tie only when the packet holds
    no conflict. Returns the label the human would pick ("candidate" or
    an alternative).
    """
    kinds = [item.kind for item in packet_items]
    support = {}
    if "claim" in kinds:
        held = [g for g in case.gathered if g.supports == "candidate"]
        support["candidate"] = min(len(held), 2)
    # An alternative counts only when the packet actually names it —
    # whether in its own item or in a contradicting item that supports
    # it. (An earlier draft parsed only "Alternative: ..." items, so a
    # dual-coverage held-evidence item never credited its alternative.)
    # Matching is phrase-boundary, not substring: a label like "no"
    # must not match the word "known" in a fallback item.
    for alt in case.alternatives:
        pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(alt.label)
                             + r"(?![A-Za-z0-9])")
        if any(pattern.search(item.text) for item in packet_items):
            support[alt.label] = alt.support
    # Only a REAL conflict breaks a tie — the "No known conflicts"
    # fallback item must not count (it says the opposite).
    has_conflict = any(
        item.kind == "conflict" and not item.text.startswith("No known conflicts")
        for item in packet_items)
    best_label = None
    best_score = -1
    for label in ["candidate"] + [a.label for a in case.alternatives]:
        score = support.get(label, 0)
        if score > best_score:
            best_label = label
            best_score = score
        elif (score == best_score and best_label == "candidate"
              and has_conflict and label != "candidate"):
            # A tie with a conflict in the packet: the human doubts the
            # candidate and takes the tied alternative instead.
            best_label = label
            best_score = score
    return best_label


def build_packet(case):
    """Build the minimal deferral packet for a case."""
    pool = build_candidate_items(case)
    greedy = greedy_minimal_packet(pool)
    exact = exact_minimal_packet(pool)
    chosen = exact if exact is not None and len(exact) <= len(greedy) else greedy
    # Compression is measured against the candidate pool — everything the
    # packet could have shown. (An earlier draft measured against raw
    # case size, which broke: a case with almost no raw material could
    # score compression above 1.0 because the "no known conflicts"
    # fallback items are packet content, not raw material.)
    compression = len(chosen) / len(pool) if pool else 0.0
    picked = _simulate_human(case, chosen)
    truth = case.true_label if case.true_label else "candidate"
    sufficient = (picked == truth)
    return Packet(
        items=tuple(chosen),
        questions_covered=tuple(sorted({q for i in chosen for q in i.covers})),
        compression=compression,
        sufficient=sufficient,
    )
