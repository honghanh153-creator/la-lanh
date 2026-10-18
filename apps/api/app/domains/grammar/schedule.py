"""Master schedule: a closed cycle of L master combinations (spec §3 step 6, plan §14.2).

Two neighbours, including last -> first, differ in every must-change slot; each master appears
once; every must-change value appears at least once. The search is a deterministic, bounded
depth-first search (Warnsdorff ordering, ties by a per-variant hash). No randomness and no
unbounded retries: an infeasible frame fails the build.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from hashlib import sha256

Master = tuple[str, ...]


@dataclass(frozen=True)
class ScheduleResult:
    order: tuple[Master, ...] | None
    steps: int


def adjacent(left: Master, right: Master) -> bool:
    return all(a != b for a, b in zip(left, right, strict=True))


def _rank(frame_id: str, variant: int, master: Master) -> bytes:
    return sha256(f"{frame_id}\x1f{variant}\x1f{'|'.join(master)}".encode()).digest()


def build_schedule(
    masters: Iterable[Master],
    *,
    length: int,
    required_values: Sequence[set[str]],
    frame_id: str,
    variant: int,
    max_steps: int,
) -> ScheduleResult:
    """Bounded search. A step is one adjacency test or one placed master (owner A4 budget).

    No neighbour graph is built: candidates are scanned lazily in the variant's hash order, so
    the work done before giving up is bounded by ``max_steps`` whatever the domain size (which
    the combination cap already bounds for the hash ordering).
    """

    nodes = sorted(set(masters), key=lambda master: _rank(frame_id, variant, master))
    if length < 2 or len(nodes) < length:
        return ScheduleResult(None, 0)
    steps = 0
    start = nodes[0]
    path: list[Master] = [start]
    cursors = [0]  # resume point of the candidate scan at each depth
    visited = {start}
    counts = [dict.fromkeys(values, 0) for values in required_values]

    def place(master: Master, delta: int) -> None:
        for slot, value in enumerate(master):
            counts[slot][value] = counts[slot].get(value, 0) + delta

    def coverage_possible() -> bool:
        remaining = length - len(path)
        return all(
            sum(1 for count in slot_counts.values() if count == 0) <= remaining
            for slot_counts in counts
        )

    place(start, 1)
    while path:
        if len(path) == length:
            if all(all(c > 0 for c in slot_counts.values()) for slot_counts in counts):
                return ScheduleResult(tuple(path), steps)
            nxt = None
        else:
            nxt = None
            current, index = path[-1], cursors[-1]
            closing = len(path) == length - 1
            while index < len(nodes):
                candidate = nodes[index]
                index += 1
                if candidate in visited:
                    continue
                steps += 1 + int(closing)
                if steps > max_steps:
                    return ScheduleResult(None, steps)
                if adjacent(current, candidate) and (not closing or adjacent(candidate, start)):
                    nxt = candidate
                    break
            cursors[-1] = index
        if nxt is None:
            last = path.pop()
            cursors.pop()
            visited.discard(last)
            place(last, -1)
            continue
        path.append(nxt)
        visited.add(nxt)
        place(nxt, 1)
        if not coverage_possible():
            path.pop()
            visited.discard(nxt)
            place(nxt, -1)
            continue
        cursors.append(0)
    return ScheduleResult(None, steps)


def canonical_cycle(order: Sequence[Master]) -> tuple[Master, ...]:
    """Rotation-free form, so two variants that are the same cycle count once."""

    pivot = min(range(len(order)), key=lambda index: order[index])
    return tuple(order[pivot:]) + tuple(order[:pivot])


def schedule_violations(
    order: Sequence[Master], *, required_values: Sequence[set[str]], allowed: set[Master]
) -> list[str]:
    problems: list[str] = []
    if len(set(order)) != len(order):
        problems.append("a master appears twice")
    for index, master in enumerate(order):
        if master not in allowed:
            problems.append(f"position {index} is not eligible in every bucket")
        if not adjacent(master, order[(index + 1) % len(order)]):
            problems.append(f"positions {index} and {(index + 1) % len(order)} share a value")
    for slot, values in enumerate(required_values):
        missing = values - {master[slot] for master in order}
        if missing:
            problems.append(f"slot {slot} misses values {sorted(missing)}")
    return problems
