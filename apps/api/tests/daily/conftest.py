from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
import time_machine

# Daily tests open a note, act on it, then read the note again. With the real clock, a
# run that crosses 00:00 Asia/Ho_Chi_Minh (17:00 UTC) reads two different note days and
# fails (#459). Start every test at noon Vietnam time; the clock still ticks so leases
# and expiries behave as in production. The rollover itself is covered by
# test_product_timezone_rolls_daily_note_at_vietnam_midnight, which passes explicit instants.
PINNED_START = datetime(2026, 6, 15, 5, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _pinned_clock() -> Iterator[None]:
    with time_machine.travel(PINNED_START, tick=True):
        yield
