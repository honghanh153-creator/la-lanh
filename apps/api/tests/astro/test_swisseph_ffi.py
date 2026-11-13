from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import get_ident, local

import pytest

from app.domains.astro.ffi.swisseph import (
    CALCULATION_FLAGS,
    SwissEphemerisError,
    SwissEphemerisNative,
)


class _ThreadLocalSwissLibrary:
    def __init__(self) -> None:
        self.state = local()
        self.initialized_threads: list[int] = []

    def swe_set_ephe_path(self, _path: bytes) -> None:
        self.state.ephemeris_ready = True
        self.initialized_threads.append(get_ident())

    def swe_calc_ut(self, _julian_day: float, _body_id: int, _flags: int, values, _error) -> int:  # type: ignore[no-untyped-def]
        if not getattr(self.state, "ephemeris_ready", False):
            return 0
        values[0] = 123.0
        return CALCULATION_FLAGS


def test_calculate_initializes_ephemeris_path_inside_each_worker_thread() -> None:
    native = object.__new__(SwissEphemerisNative)
    library = _ThreadLocalSwissLibrary()
    native._library = library  # type: ignore[assignment]
    native._ephemeris_path = Path("/verified/ephemeris")
    native._thread_state = local()

    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(native.calculate, 2_451_545.0, 0).result()
        second = pool.submit(native.calculate, 2_451_546.0, 0).result()

    assert first.longitude == 123.0
    assert second.longitude == 123.0
    assert len(library.initialized_threads) == 1


class _EclipseLibrary:
    def __init__(self, flags: int) -> None:
        self.flags = flags

    def swe_set_ephe_path(self, _path: bytes) -> None:
        return None

    def swe_sol_eclipse_when_glob(  # type: ignore[no-untyped-def]
        self, _start: float, _flags: int, _type: int, times, _backward: int, error
    ) -> int:
        times[0] = 2_461_000.25
        if self.flags < 0:
            error.value = b"no eclipse"
        return self.flags


def _eclipse_native(flags: int) -> SwissEphemerisNative:
    native = object.__new__(SwissEphemerisNative)
    native._library = _EclipseLibrary(flags)  # type: ignore[assignment]
    native._ephemeris_path = Path("/verified/ephemeris")
    native._thread_state = local()
    return native


def test_eclipse_search_returns_flags_and_maximum() -> None:
    found = _eclipse_native(4 | 1).next_solar_eclipse(2_461_000.0)
    assert found.flags == 5
    assert found.maximum_julian_day_ut == 2_461_000.25


def test_eclipse_search_error_is_raised() -> None:
    with pytest.raises(SwissEphemerisError, match="no eclipse"):
        _eclipse_native(-1).next_solar_eclipse(2_461_000.0)
