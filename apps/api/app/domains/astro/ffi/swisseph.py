from __future__ import annotations

import ctypes
import hashlib
import os
import platform
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import cast

SE_GREG_CAL = 1
SEFLG_SWIEPH = 2
SEFLG_SPEED = 256
CALCULATION_FLAGS = SEFLG_SWIEPH | SEFLG_SPEED
ERROR_BUFFER_SIZE = 256
EPHEMERIS_CHECKSUMS = {
    "sepl_18.se1": "20aa1c1d68d98895493aef8a4d67d596823309d55078f6d7a9bdbe0d0c7e8d80",
    "semo_18.se1": "1aca59fbd7f73d3882768a847890304261051c5ed965b952b4c9d7c5951833a4",
    "seas_18.se1": "df4e9a08186f91e2c91f454ee2d404bf5ecbe61500b2324c28d26e6da2076dc6",
}


class SwissEphemerisError(RuntimeError):
    pass


@dataclass(frozen=True)
class NativePosition:
    longitude: float
    latitude: float
    distance_au: float
    longitude_speed: float
    latitude_speed: float
    distance_speed: float


@dataclass(frozen=True)
class NativeHouses:
    cusps: tuple[float, ...]
    ascendant: float
    midheaven: float
    armc: float
    vertex: float


class SwissEphemerisNative:
    _lock = threading.RLock()

    def __init__(
        self,
        library_path: Path | None = None,
        ephemeris_path: Path | None = None,
    ) -> None:
        repository_root = Path(__file__).resolve().parents[6]
        suffix = "dylib" if platform.system() == "Darwin" else "so"
        resolved_library = library_path or Path(
            os.getenv(
                "LA_LANH_SWISSEPH_LIBRARY_PATH",
                repository_root / "vendor" / "swisseph" / "build" / f"libswe.{suffix}",
            )
        )
        resolved_ephemeris = ephemeris_path or Path(
            os.getenv(
                "LA_LANH_SWISSEPH_EPHEMERIS_PATH",
                repository_root / "vendor" / "swisseph" / "ephe",
            )
        )
        if not resolved_library.is_file():
            raise SwissEphemerisError(
                f"Swiss Ephemeris native library is missing: {resolved_library}. "
                "Run `make -C vendor/swisseph`."
            )
        missing = [
            name for name in EPHEMERIS_CHECKSUMS if not (resolved_ephemeris / name).is_file()
        ]
        if missing:
            raise SwissEphemerisError(
                f"Swiss Ephemeris data files are missing: {', '.join(missing)}"
            )
        corrupt = [
            name
            for name, expected in EPHEMERIS_CHECKSUMS.items()
            if hashlib.sha256((resolved_ephemeris / name).read_bytes()).hexdigest() != expected
        ]
        if corrupt:
            raise SwissEphemerisError(
                f"Swiss Ephemeris data checksum mismatch: {', '.join(corrupt)}"
            )

        self._library = ctypes.CDLL(str(resolved_library))
        self._configure_signatures()
        self._ephemeris_path = resolved_ephemeris
        with self._lock:
            self._library.swe_set_ephe_path(str(resolved_ephemeris).encode())

    def _configure_signatures(self) -> None:
        self._library.swe_set_ephe_path.argtypes = [ctypes.c_char_p]
        self._library.swe_set_ephe_path.restype = None
        self._library.swe_julday.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_double,
            ctypes.c_int,
        ]
        self._library.swe_julday.restype = ctypes.c_double
        self._library.swe_calc_ut.argtypes = [
            ctypes.c_double,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.POINTER(ctypes.c_double),
            ctypes.c_char_p,
        ]
        self._library.swe_calc_ut.restype = ctypes.c_int32
        self._library.swe_houses_ex.argtypes = [
            ctypes.c_double,
            ctypes.c_int32,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double),
        ]
        self._library.swe_houses_ex.restype = ctypes.c_int
        self._library.swe_version.argtypes = [ctypes.c_char_p]
        self._library.swe_version.restype = ctypes.c_char_p
        self._library.swe_close.argtypes = []
        self._library.swe_close.restype = None

    @property
    def version(self) -> str:
        buffer = ctypes.create_string_buffer(ERROR_BUFFER_SIZE)
        with self._lock:
            value = self._library.swe_version(buffer)
        return cast(bytes, value).decode()

    def julian_day(self, year: int, month: int, day: int, hour: float) -> float:
        with self._lock:
            return float(self._library.swe_julday(year, month, day, hour, SE_GREG_CAL))

    def calculate(self, julian_day_ut: float, body_id: int) -> NativePosition:
        values = (ctypes.c_double * 6)()
        error = ctypes.create_string_buffer(ERROR_BUFFER_SIZE)
        with self._lock:
            result_flags = self._library.swe_calc_ut(
                julian_day_ut,
                body_id,
                CALCULATION_FLAGS,
                values,
                error,
            )
        if result_flags < 0:
            message = error.value.decode(errors="replace") or f"body {body_id} failed"
            raise SwissEphemerisError(message)
        if result_flags & SEFLG_SWIEPH != SEFLG_SWIEPH:
            raise SwissEphemerisError(
                f"body {body_id} did not use Swiss Ephemeris files; fallback is forbidden"
            )
        return NativePosition(*map(float, values))

    def houses(
        self,
        julian_day_ut: float,
        latitude: float,
        longitude: float,
        house_code: str,
    ) -> NativeHouses:
        cusps = (ctypes.c_double * 13)()
        angles = (ctypes.c_double * 10)()
        with self._lock:
            result = self._library.swe_houses_ex(
                julian_day_ut,
                0,
                latitude,
                longitude,
                ord(house_code),
                cusps,
                angles,
            )
        if result < 0:
            raise SwissEphemerisError(
                f"house system {house_code} is unsupported at latitude {latitude}"
            )
        return NativeHouses(
            cusps=tuple(float(cusps[index]) for index in range(1, 13)),
            ascendant=float(angles[0]),
            midheaven=float(angles[1]),
            armc=float(angles[2]),
            vertex=float(angles[3]),
        )
