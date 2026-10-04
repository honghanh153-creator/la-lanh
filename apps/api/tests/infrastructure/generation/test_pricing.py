import pytest

from app.infrastructure.generation.pricing import (
    GPT_6_LUNA_STANDARD_2026_10_04,
    cents_to_nanos,
)


def test_pinned_luna_standard_price_uses_exact_integer_nanodollars() -> None:
    assert (
        GPT_6_LUNA_STANDARD_2026_10_04.cost_nanos(
            input_tokens=1_500,
            output_tokens=150,
        )
        == 225_000
    )
    assert cents_to_nanos(100) == 1_000_000_000


def test_pricing_rejects_negative_usage() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        GPT_6_LUNA_STANDARD_2026_10_04.cost_nanos(
            input_tokens=-1,
            output_tokens=0,
        )
