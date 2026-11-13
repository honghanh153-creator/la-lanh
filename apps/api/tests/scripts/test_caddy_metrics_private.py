from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SITES = (
    "infra/hetzner/Caddyfile",
    "infra/hetzner/staging/staging.caddy.example",
)


@pytest.mark.parametrize("site", SITES)
def test_public_sites_never_proxy_metrics(site: str) -> None:
    config = (REPO_ROOT / site).read_text(encoding="utf-8")

    # Caddy runs `respond` before `reverse_proxy`, so the route counters never
    # leave the compose network; `*` also covers `/metrics/` and query strings.
    assert "\trespond /metrics* 404\n" in config
    assert config.count("reverse_proxy ") == 1
