from __future__ import annotations

from typing import TYPE_CHECKING

from app.infrastructure.generation.base import (
    DisabledGenerationProvider,
    DisabledRewriteGenerationProvider,
    GenerationDisabled,
    GenerationIncomplete,
    GenerationPermanent,
    GenerationProvider,
    GenerationRefusal,
    GenerationResult,
    GenerationSuccess,
    GenerationTransient,
    RewriteGenerationProvider,
    RewriteGenerationResult,
    RewriteGenerationSuccess,
)

if TYPE_CHECKING:
    from app.config import Settings


def build_generation_provider(settings: Settings) -> GenerationProvider:
    # The legacy Reading worker has no atomic shared-budget reservation. New work is
    # exclusively routed through the content-rewrite ledger, so this boundary stays
    # network-disabled even when the new rewrite rollout is enabled.
    del settings
    return DisabledGenerationProvider()


def build_rewrite_generation_provider(settings: Settings) -> RewriteGenerationProvider:
    if (
        not settings.generation_enabled
        or not settings.generation_worker_enabled
        or settings.generation_provider == "disabled"
    ):
        return DisabledRewriteGenerationProvider()

    from app.infrastructure.generation.openai import (
        OpenAIRewriteProvider,
        OpenAISDKResponseTransport,
    )

    api_key = settings.generation_openai_api_key
    if api_key is None:
        return DisabledRewriteGenerationProvider()
    return OpenAIRewriteProvider(
        OpenAISDKResponseTransport(api_key=api_key.get_secret_value()),
        model=settings.generation_openai_model,
        timeout_seconds=settings.generation_timeout_seconds,
    )


__all__ = [
    "DisabledGenerationProvider",
    "DisabledRewriteGenerationProvider",
    "GenerationDisabled",
    "GenerationIncomplete",
    "GenerationPermanent",
    "GenerationProvider",
    "GenerationRefusal",
    "GenerationResult",
    "GenerationSuccess",
    "GenerationTransient",
    "RewriteGenerationProvider",
    "RewriteGenerationResult",
    "RewriteGenerationSuccess",
    "build_generation_provider",
    "build_rewrite_generation_provider",
]
