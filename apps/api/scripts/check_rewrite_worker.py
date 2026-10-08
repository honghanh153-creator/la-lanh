from __future__ import annotations

import asyncio

from app.config import Settings
from app.infrastructure.generation import (
    DisabledRewriteGenerationProvider,
    build_rewrite_generation_provider,
)
from scripts.check_database_tls import check_database_tls


async def check_rewrite_worker() -> None:
    settings = Settings()
    if not settings.generation_worker_enabled:
        raise RuntimeError("rewrite worker is disabled")
    if isinstance(
        build_rewrite_generation_provider(settings),
        DisabledRewriteGenerationProvider,
    ):
        raise RuntimeError("rewrite provider is disabled")
    await check_database_tls()


def main() -> int:
    try:
        asyncio.run(check_rewrite_worker())
    except Exception as error:
        print(f"rewrite-worker-unhealthy:{type(error).__name__}")
        return 1
    print("rewrite-worker-healthy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
