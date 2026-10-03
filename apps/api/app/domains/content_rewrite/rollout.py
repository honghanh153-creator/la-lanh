from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from hashlib import sha256

from app.domains.content_rewrite.models import RewriteArtifactKey, RewriteSurface


class RewriteRolloutMode(StrEnum):
    OFF = "off"
    SHADOW = "shadow"
    EDITORIAL = "editorial"
    BETA_10 = "beta_10"
    BETA_50 = "beta_50"
    FULL = "full"


class SurfaceRolloutPolicy:
    def __init__(
        self,
        modes: Mapping[RewriteSurface, RewriteRolloutMode],
        *,
        unspecified: RewriteRolloutMode = RewriteRolloutMode.OFF,
    ) -> None:
        self._modes = dict(modes)
        self._unspecified = unspecified

    @classmethod
    def from_settings(cls, modes: Mapping[str, str]) -> SurfaceRolloutPolicy:
        return cls(
            {RewriteSurface(surface): RewriteRolloutMode(mode) for surface, mode in modes.items()}
        )

    @classmethod
    def full_for_all(cls) -> SurfaceRolloutPolicy:
        return cls({}, unspecified=RewriteRolloutMode.FULL)

    def mode_for(self, surface: RewriteSurface) -> RewriteRolloutMode:
        return self._modes.get(surface, self._unspecified)

    def should_generate(self, surface: RewriteSurface) -> bool:
        return self.mode_for(surface) is not RewriteRolloutMode.OFF

    def should_publish(self, key: RewriteArtifactKey) -> bool:
        mode = self.mode_for(key.surface)
        if mode in {
            RewriteRolloutMode.OFF,
            RewriteRolloutMode.SHADOW,
            RewriteRolloutMode.EDITORIAL,
        }:
            return False
        if mode is RewriteRolloutMode.FULL:
            return True
        threshold = 10 if mode is RewriteRolloutMode.BETA_10 else 50
        digest = sha256(f"rewrite-rollout\x00{key.cache_key}".encode()).hexdigest()
        return int(digest[:8], 16) % 100 < threshold
