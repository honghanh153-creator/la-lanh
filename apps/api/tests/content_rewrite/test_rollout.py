from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteArtifactKey,
    RewriteSurface,
)
from app.domains.content_rewrite.rollout import RewriteRolloutMode, SurfaceRolloutPolicy


def _key(index: int, surface: RewriteSurface = RewriteSurface.DAILY_HOME) -> RewriteArtifactKey:
    return RewriteArtifactKey(
        surface=surface,
        owner=ArtifactOwnerKey(namespace="readings", key=f"synthetic-{index}"),
        blueprint_hash=f"{index:064x}",
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v1",
        schema_version="test-v1",
        gate_version="test-v1",
    )


def test_shadow_and_editorial_generate_but_never_publish() -> None:
    policy = SurfaceRolloutPolicy(
        {
            RewriteSurface.DAILY_HOME: RewriteRolloutMode.SHADOW,
            RewriteSurface.TAROT: RewriteRolloutMode.EDITORIAL,
        }
    )

    assert policy.should_generate(RewriteSurface.DAILY_HOME)
    assert not policy.should_publish(_key(1))
    assert policy.should_generate(RewriteSurface.TAROT)
    assert not policy.should_publish(_key(2, RewriteSurface.TAROT))
    assert not policy.should_generate(RewriteSurface.RADAR)


def test_percentage_cohorts_are_deterministic_and_independent() -> None:
    ten = SurfaceRolloutPolicy({RewriteSurface.DAILY_HOME: RewriteRolloutMode.BETA_10})
    fifty = SurfaceRolloutPolicy({RewriteSurface.DAILY_HOME: RewriteRolloutMode.BETA_50})
    keys = tuple(_key(index) for index in range(1, 1_001))

    first_pass = tuple(ten.should_publish(key) for key in keys)
    second_pass = tuple(ten.should_publish(key) for key in keys)

    assert first_pass == second_pass
    assert 70 <= sum(first_pass) <= 130
    assert 430 <= sum(fifty.should_publish(key) for key in keys) <= 570


def test_full_mode_publishes_and_unspecified_surface_stays_off() -> None:
    policy = SurfaceRolloutPolicy.from_settings({"tarot": "full"})

    assert policy.should_publish(_key(1, RewriteSurface.TAROT))
    assert not policy.should_generate(RewriteSurface.DAILY_HOME)
