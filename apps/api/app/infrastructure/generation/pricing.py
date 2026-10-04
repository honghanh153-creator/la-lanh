from __future__ import annotations

from dataclasses import dataclass

USD_NANOS_PER_CENT = 10_000_000
USD_NANOS_PER_DOLLAR = 1_000_000_000


@dataclass(frozen=True, slots=True)
class GenerationPricing:
    """Pinned Standard-tier pricing expressed as integer nanodollars per token."""

    version: str
    input_nanos_per_token: int
    output_nanos_per_token: int

    def cost_nanos(self, *, input_tokens: int, output_tokens: int) -> int:
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("token counts must be non-negative")
        input_cost = input_tokens * self.input_nanos_per_token
        output_cost = output_tokens * self.output_nanos_per_token
        return input_cost + output_cost


# Official Standard short-context price on 2026-10-04:
# $0.10 / 1M input tokens and $0.50 / 1M output tokens.
GPT_6_LUNA_STANDARD_2026_10_04 = GenerationPricing(
    version="gpt-6-luna-standard-2026-10-04",
    input_nanos_per_token=100,
    output_nanos_per_token=500,
)


def cents_to_nanos(cents: int) -> int:
    if cents < 0:
        raise ValueError("cents must be non-negative")
    return cents * USD_NANOS_PER_CENT
