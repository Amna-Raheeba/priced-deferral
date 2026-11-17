"""Data model for priced deferral.

A decision case is one uncertain answer: a candidate answer with a stated
probability of being correct, evidence that could be gathered, competing
alternatives, and a harm profile that prices a wrong answer. Everything is
plain data — no model calls, no randomness outside the seeded generators.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvidenceItem:
    """One piece of evidence that can be gathered before deciding.

    decisiveness is the fraction of the remaining error probability this
    item would remove if gathered (0 = useless, 1 = settles the question).
    cost is what gathering it costs, in the same currency as harm.
    """

    item_id: str
    text: str
    decisiveness: float
    cost: float
    supports: str = ""  # which alternative (or "candidate") this item supports
    contradicts: bool = False


@dataclass(frozen=True)
class Alternative:
    """A competing answer to the candidate."""

    label: str
    support: int = 0  # number of gathered items supporting it


@dataclass(frozen=True)
class HarmProfile:
    """Prices a wrong answer and a deferral, in one currency.

    harm_wrong: cost of letting a wrong answer through.
    human_cost: cost of a human's time to decide (per deferral).
    delay_cost: cost of the delay a deferral causes.
    human_accuracy: probability the human decides correctly.
    answer_cost: compute cost of answering (usually ~0).
    """

    name: str
    harm_wrong: float
    human_cost: float
    delay_cost: float
    human_accuracy: float = 0.98
    answer_cost: float = 0.0


@dataclass
class DecisionCase:
    """One uncertain decision to price."""

    case_id: str
    domain: str
    question: str
    candidate: str
    p_correct: float  # stated probability the candidate is correct
    evidence: list = field(default_factory=list)  # EvidenceItem, ungathered
    gathered: list = field(default_factory=list)  # EvidenceItem, already held
    alternatives: list = field(default_factory=list)  # Alternative
    conflicts: list = field(default_factory=list)  # texts contradicting candidate
    missing: list = field(default_factory=list)  # texts describing missing facts
    correct: bool = True  # ground truth: is the candidate actually correct?
    true_label: str = ""  # ground-truth answer label ("" means candidate)
    human_correct: bool = True  # would the human decide correctly if deferred?


@dataclass(frozen=True)
class PricedOptions:
    """Expected costs of the three options, in one currency."""

    answer: float
    gather: float
    defer: float


@dataclass(frozen=True)
class GatherPlan:
    """The optimal gather-then-redecide plan."""

    items: tuple  # EvidenceItem chosen, in gather order
    gather_cost: float
    p_after: float
    expected_cost: float  # gather cost + min(answer(p'), defer)
    second_stage: str  # "answer" or "defer"


@dataclass(frozen=True)
class Decision:
    """The priced verdict for one case."""

    case_id: str
    verdict: str  # "answer" | "gather" | "defer"
    costs: PricedOptions
    gather_plan: object = None  # GatherPlan when verdict is "gather"
    packet: object = None  # Packet when verdict is "defer"


@dataclass(frozen=True)
class PacketItem:
    """One item in a deferral packet."""

    kind: str  # "claim" | "conflict" | "alternative" | "missing"
    text: str
    covers: tuple  # decision questions this item covers


@dataclass(frozen=True)
class Packet:
    """Minimal deferral packet: what the human needs, nothing more."""

    items: tuple  # PacketItem
    questions_covered: tuple
    compression: float  # |packet| / |all evidence + conflicts + alternatives|
    sufficient: bool  # simulated human decides correctly from packet alone
