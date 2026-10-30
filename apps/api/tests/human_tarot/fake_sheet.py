"""An in-memory stand-in for one Google Sheet, for the human Tarot tests (US-24 U5).

It understands only the ranges the bridge uses (``'Tab'!A1:Q11`` style) and can be told to fail
before a call, or to apply a write and then fail (the ambiguous timeout of plan KTD4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.infrastructure.google_sheets.client import SheetsError

_RANGE = re.compile(r"^'(?P<tab>[^']+)'!(?P<c1>[A-Z])(?P<r1>\d+):(?P<c2>[A-Z])(?P<r2>\d+)$")


def _column(letter: str) -> int:
    return ord(letter) - ord("A")


@dataclass
class FakeSheet:
    columns: int = 17
    rows: int = 11
    tabs: dict[str, list[list[Any]]] = field(default_factory=dict)
    calls: list[str] = field(default_factory=list)
    fail_before: list[SheetsError] = field(default_factory=list)
    fail_after_write: list[SheetsError] = field(default_factory=list)

    def grid(self, tab: str) -> list[list[Any]]:
        if tab not in self.tabs:
            self.tabs[tab] = [["" for _ in range(self.columns)] for _ in range(self.rows)]
        return self.tabs[tab]

    def set_row(self, tab: str, row: int, values: list[Any], start: str = "A") -> None:
        grid = self.grid(tab)
        for offset, value in enumerate(values):
            grid[row - 1][_column(start) + offset] = value

    def cell(self, tab: str, a1: str) -> Any:
        match = re.fullmatch(r"([A-Z])(\d+)", a1)
        if match is None:
            raise ValueError(f"unsupported cell {a1}")
        return self.grid(tab)[int(match.group(2)) - 1][_column(match.group(1))]

    def _parse(self, range_a1: str) -> tuple[list[list[Any]], int, int, int, int]:
        match = _RANGE.fullmatch(range_a1)
        if match is None:
            raise ValueError(f"unsupported range {range_a1}")
        grid = self.grid(match["tab"])
        return (
            grid,
            int(match["r1"]) - 1,
            int(match["r2"]) - 1,
            _column(match["c1"]),
            _column(match["c2"]),
        )

    def _maybe_fail(self) -> None:
        if self.fail_before:
            raise self.fail_before.pop(0)

    async def read(self, range_a1: str) -> list[list[Any]]:
        self.calls.append("read")
        self._maybe_fail()
        grid, r1, r2, c1, c2 = self._parse(range_a1)
        rows = [list(grid[index][c1 : c2 + 1]) for index in range(r1, r2 + 1)]
        # Google omits trailing empty cells and rows.
        trimmed = []
        for row in rows:
            while row and row[-1] in ("", None):
                row.pop()
            trimmed.append(row)
        while trimmed and not trimmed[-1]:
            trimmed.pop()
        return trimmed

    async def write(self, updates: list[tuple[str, list[list[str]]]]) -> None:
        self.calls.append("write")
        self._maybe_fail()
        for range_a1, values in updates:
            grid, r1, _, c1, _ = self._parse(range_a1)
            for row_offset, row in enumerate(values):
                for column_offset, value in enumerate(row):
                    grid[r1 + row_offset][c1 + column_offset] = value
        if self.fail_after_write:
            raise self.fail_after_write.pop(0)

    async def clear(self, ranges: list[str]) -> None:
        self.calls.append("clear")
        self._maybe_fail()
        for range_a1 in ranges:
            grid, r1, r2, c1, c2 = self._parse(range_a1)
            for index in range(r1, r2 + 1):
                for column in range(c1, c2 + 1):
                    grid[index][column] = ""
        if self.fail_after_write:
            raise self.fail_after_write.pop(0)
