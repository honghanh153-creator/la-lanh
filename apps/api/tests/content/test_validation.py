from copy import deepcopy

import pytest

from app.domains.astro.models import ZodiacSign
from app.domains.content.catalog import bundled_daily_catalog
from app.domains.content.review import validate_daily_release
from app.domains.content.validation import validate_daily_catalog
from app.domains.readings.review_agent import ContentReviewAgent, ReviewResult, ReviewSample


def test_bundled_daily_catalog_passes_content_studio_validation() -> None:
    result = validate_daily_catalog(bundled_daily_catalog())

    assert result.passed is True
    assert result.findings == ()


def test_validation_rejects_abstract_copy_and_markup() -> None:
    payload = deepcopy(bundled_daily_catalog())
    payload["signs"]["pisces"]["manifestation"] = (
        "Pattern này có thể lộ ra <strong>khi mọi thứ đổi mood</strong>."
    )

    result = validate_daily_catalog(payload)

    assert result.passed is False
    assert {finding.rule_id for finding in result.findings} >= {
        "abstract-or-retired-copy",
        "raw-markup",
    }


def test_validation_rejects_incomplete_entry_schema() -> None:
    payload = deepcopy(bundled_daily_catalog())
    del payload["planets"]["moon"]["action"]

    result = validate_daily_catalog(payload)

    assert result.passed is False
    assert any(
        finding.rule_id == "entry-field-missing" and finding.path == "planets.moon"
        for finding in result.findings
    )


def test_validation_rejects_missing_engine_entry() -> None:
    payload = deepcopy(bundled_daily_catalog())
    del payload["signs"]["pisces"]

    result = validate_daily_catalog(payload)

    assert result.passed is False
    assert any(
        finding.rule_id == "catalog-entry-missing" and finding.path == "signs"
        for finding in result.findings
    )


def test_validation_rejects_wrong_field_shapes_and_list_cardinality() -> None:
    payload = deepcopy(bundled_daily_catalog())
    payload["signs"]["pisces"]["hooks"] = "Đây là text, không phải danh sách."
    payload["signs"]["aquarius"]["practices"] = ["chỉ có một biến thể"]
    payload["planets"]["moon"]["drive"] = ["không phải text"]

    result = validate_daily_catalog(payload)

    assert result.passed is False
    findings = {(finding.rule_id, finding.path) for finding in result.findings}
    assert ("field-type-invalid", "signs.pisces.hooks") in findings
    assert ("list-cardinality-invalid", "signs.aquarius.practices") in findings
    assert ("field-type-invalid", "planets.moon.drive") in findings


def test_release_gate_rejects_duplicate_synthetic_readings() -> None:
    payload = deepcopy(bundled_daily_catalog())
    repeated = deepcopy(payload["signs"]["pisces"])
    for sign in payload["signs"]:
        payload["signs"][sign] = deepcopy(repeated)

    result = validate_daily_release(payload)

    assert result.passed is False
    assert "duplicate-matrix-entry" in {finding.rule_id for finding in result.findings}


def test_release_gate_renders_the_draft_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = deepcopy(bundled_daily_catalog())
    first_sign = next(iter(ZodiacSign)).value
    marker = "Dấu kiểm riêng của bản nháp"
    payload["signs"][first_sign]["hooks"] = [
        f"{marker} ở biến thể một.",
        f"{marker} ở biến thể hai.",
        f"{marker} ở biến thể ba.",
    ]
    observed: list[ReviewSample] = []
    original_review = ContentReviewAgent.review

    def capture_review(
        self: ContentReviewAgent,
        samples: tuple[ReviewSample, ...],
    ) -> ReviewResult:
        observed.extend(samples)
        return original_review(self, samples)

    monkeypatch.setattr(ContentReviewAgent, "review", capture_review)

    result = validate_daily_release(payload)

    assert result.passed is True
    hooks = [dict(sample.sections)["hook"] for sample in observed]
    assert any(marker.casefold() in hook.casefold() for hook in hooks)
