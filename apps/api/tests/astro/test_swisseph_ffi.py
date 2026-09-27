from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import get_ident, local

from app.domains.astro.ffi.swisseph import CALCULATION_FLAGS, SwissEphemerisNative


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
