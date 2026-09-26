from __future__ import annotations

from typing import TYPE_CHECKING

from app.infrastructure.generation.base import (
    DisabledGenerationProvider,
    GenerationDisabled,
    GenerationIncomplete,
    GenerationPermanent,
    GenerationProvider,
    GenerationRefusal,
    GenerationResult,
    GenerationSuccess,
    GenerationTransient,
)

if TYPE_CHECKING:
    from app.config import Settings


def build_generation_provider(settings: Settings) -> GenerationProvider:
    if not settings.generation_enabled or settings.generation_provider == "disabled":
        return DisabledGenerationProvider()

    from app.infrastructure.generation.openai import (
        OpenAIResponsesProvider,
        OpenAISDKResponseTransport,
    )

    api_key = settings.generation_openai_api_key
    if api_key is None:  # Settings validation protects this fail-closed boundary too.
        return DisabledGenerationProvider()
    return OpenAIResponsesProvider(
        OpenAISDKResponseTransport(api_key=api_key.get_secret_value()),
        model=settings.generation_openai_model,
        timeout_seconds=settings.generation_timeout_seconds,
    )


__all__ = [
    "DisabledGenerationProvider",
    "GenerationDisabled",
    "GenerationIncomplete",
    "GenerationPermanent",
    "GenerationProvider",
    "GenerationRefusal",
    "GenerationResult",
    "GenerationSuccess",
    "GenerationTransient",
    "build_generation_provider",
]
