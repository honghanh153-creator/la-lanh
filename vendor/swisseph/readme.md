# Swiss Ephemeris native dependency

This directory vendors the minimum official Swiss Ephemeris C release needed by Lá Lành.

- Upstream: `https://github.com/aloistr/swisseph`
- Release: `v2.10.3final`
- Commit: `af9823fe7b06ffefe3d3968fdc5680be8b5eec5f`
- Ephemeris range: the `_18` files cover 1800–2399.
- Runtime boundary: the API calls this C library directly through a narrow `ctypes` adapter. No community wrapper is used as the correctness boundary.

Build with `make -C vendor/swisseph`. Verify the three ephemeris files with `shasum -a 256 -c checksums.txt` from this directory.

Swiss Ephemeris is dual licensed. A public service or distributed product must either comply with AGPL-3.0 for the complete combined work or have a Swiss Ephemeris Professional License. Local product development does not remove that release gate. See `LICENSE.TXT` and `docs/legal/swiss-ephemeris-release-gate.md`.
