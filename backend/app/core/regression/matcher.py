"""
Group-level matching of defects between two runs.

Elements that share a stable fingerprint form a group.  Within a group the previous and
current items are paired one-to-one (by occurrence order), and the *counts* decide the outcome:

    current_count  > previous_count  -> the extra current items are NEW
    current_count  < previous_count  -> the extra previous items are FIXED (unmatched)
    otherwise                        -> every item is matched (Still Open / Reopened / ...)

Every element still gets its own row in the report; only the regression STATUS comes from the
group-level pairing.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass(eq=False)
class MatchItem:
    ref: Any                 # the defect / testcase / dict this item stands for
    fp: str                  # stable (group) fingerprint
    dynamic: bool = False    # live data was normalized away for this item
    priority: int = 0        # previous side only: lower pairs first (active before resolved)
    order: Any = 0           # tiebreaker inside the same priority (e.g. defect code / occurrence)
    seq: int = 0             # position in the input list (current side pairs in this order)


@dataclass
class MatchResult:
    pairs: List[Tuple[MatchItem, MatchItem]] = field(default_factory=list)  # (previous, current)
    new: List[MatchItem] = field(default_factory=list)                      # current without a partner
    unmatched_prev: List[MatchItem] = field(default_factory=list)           # previous without a partner
    dynamic_groups_matched: int = 0


def match_groups(prev: List[MatchItem], cur: List[MatchItem]) -> MatchResult:
    prev_by: Dict[str, List[MatchItem]] = defaultdict(list)
    cur_by: Dict[str, List[MatchItem]] = defaultdict(list)
    for i, it in enumerate(prev):
        it.seq = i
        prev_by[it.fp].append(it)
    for i, it in enumerate(cur):
        it.seq = i
        cur_by[it.fp].append(it)

    result = MatchResult()
    for fp in list(cur_by) + [k for k in prev_by if k not in cur_by]:
        p = sorted(prev_by.get(fp, []), key=lambda x: (x.priority, str(x.order), x.seq))
        c = sorted(cur_by.get(fp, []), key=lambda x: x.seq)
        n = min(len(p), len(c))
        result.pairs.extend(zip(p[:n], c[:n]))
        result.new.extend(c[n:])
        result.unmatched_prev.extend(p[n:])
        if n and any(it.dynamic for it in c[:n]):
            result.dynamic_groups_matched += 1
    result.new.sort(key=lambda x: x.seq)
    return result
