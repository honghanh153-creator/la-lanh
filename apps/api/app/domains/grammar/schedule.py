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
    nodes = sorted(set(masters), key=lambda master: _rank(frame_id, variant, master))
    if length < 2 or len(nodes) < length:
        return ScheduleResult(None, 0)
    neighbours = {node: [other for other in nodes if adjacent(node, other)] for node in nodes}
    start = nodes[0]
    path: list[Master] = [start]
    visited = {start}
    counts = [dict.fromkeys(values, 0) for values in required_values]
    for slot, value in enumerate(start):
        counts[slot][value] = counts[slot].get(value, 0) + 1
    steps = 1

    def options(node: Master) -> list[Master]:
        remaining = length - len(path)
        candidates = [n for n in neighbours[node] if n not in visited]
        if remaining == 1:
            candidates = [n for n in candidates if adjacent(n, start)]
        # Warnsdorff: fewest onward moves first; the variant hash breaks ties.
        return sorted(
            candidates,
            key=lambda n: (
                sum(1 for m in neighbours[n] if m not in visited),
                _rank(frame_id, variant, n),
            ),
        )

    def coverage_possible() -> bool:
        remaining = length - len(path)
        return all(
            sum(1 for count in slot_counts.values() if count == 0) <= remaining
            for slot_counts in counts
        )

    stack = [iter(options(start))]
    while stack:
        if len(path) == length:
            if adjacent(path[-1], start) and all(
                all(count > 0 for count in slot_counts.values()) for slot_counts in counts
            ):
                return ScheduleResult(tuple(path), steps)
            nxt = None
        else:
            nxt = next(stack[-1], None)
        if nxt is None:
            stack.pop()
            last = path.pop()
            visited.discard(last)
            for slot, value in enumerate(last):
                counts[slot][value] -= 1
            if not path:
                break
            continue
        steps += 1
        if steps > max_steps:
            return ScheduleResult(None, steps)
        path.append(nxt)
        visited.add(nxt)
        for slot, value in enumerate(nxt):
            counts[slot][value] = counts[slot].get(value, 0) + 1
        if not coverage_possible():
            path.pop()
            visited.discard(nxt)
            for slot, value in enumerate(nxt):
                counts[slot][value] -= 1
            continue
        stack.append(iter(options(nxt)) if len(path) < length else iter(()))
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
