"""The alias contact check stays linear and keeps the old accept/refuse results."""

import random
import re
import time
from pathlib import Path

import pytest

from app.db.session import Database
from app.domains.la_chung.models import IdentityMode
from app.domains.la_chung.service import (
    ALIAS_CONTACT,
    ALIAS_MAX_LENGTH,
    STATEMENTS,
    LaChungInvalid,
    LaChungService,
)
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider

# The pattern before the CodeQL py/polynomial-redos fix, kept only as the oracle.
LEGACY_ALIAS_CONTACT = re.compile(r"(?:\+?\d[\d .-]{7,}|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})")


@pytest.mark.parametrize(
    "alias",
    [
        "Mây",
        "Bạn cũ lớp 12",
        "0901234567",
        "+84 90 123 4567",
        "090.123.4567",
        "1234567",
        "12345678",
        "a@b.co",
        "mail me a@b.c",
        "a.b+c@x-y.vn",
        "@b.co",
        "x@.co",
        "x@b.c1",
        "đ@ư.vn",
        "٣٣٣٣٣٣٣٣",
        "ngày 12 - 3 - 2020",
        "+-+@a.bc",
    ],
)
def test_alias_contact_matches_the_legacy_result(alias: str) -> None:
    assert bool(ALIAS_CONTACT.search(alias)) is bool(LEGACY_ALIAS_CONTACT.search(alias))


def test_alias_contact_agrees_with_the_legacy_pattern_on_random_aliases() -> None:
    rng = random.Random(20261102)  # noqa: S311 - seeded fuzz, not a secret
    alphabet = "a1Z.+-@ _đ٣x9"
    for _ in range(20_000):
        alias = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, ALIAS_MAX_LENGTH)))
        assert bool(ALIAS_CONTACT.search(alias)) is bool(LEGACY_ALIAS_CONTACT.search(alias))


@pytest.mark.parametrize(
    "text",
    ["+" * 50_000, "a." * 25_000, "a@" * 25_000, "1" + " " * 50_000, "a@" + "a" * 50_000 + "1"],
)
def test_alias_contact_is_fast_on_long_adversarial_text(text: str) -> None:
    started = time.perf_counter()
    ALIAS_CONTACT.search(text)
    assert time.perf_counter() - started < 0.25


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", [IdentityMode.ALIAS, IdentityMode.ANONYMOUS])
async def test_submit_refuses_an_overlong_alias_before_any_parsing(
    tmp_path: Path, mode: IdentityMode
) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'la-chung-alias.db'}")
    await database.initialize()
    service = LaChungService(
        database.sessions,
        SecretHasher(b"h" * 32),
        AesGcmEnvelopeCipher(StaticDataKeyProvider(b"e" * 32)),
    )
    try:
        started = time.perf_counter()
        with pytest.raises(LaChungInvalid):
            await service.submit(
                token="A" * 43,
                selections=tuple(item.id for item in STATEMENTS[:3]),
                identity_mode=mode,
                display_alias="+" * 200_000,
                idempotency_key="synthetic-idem-0001",
            )
        assert time.perf_counter() - started < 0.25
    finally:
        await database.dispose()
