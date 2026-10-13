from __future__ import annotations

import json
import re
import socket
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import JsonValue

from app.db.session import Database
from app.domains.content_rewrite.evaluation import (
    EvaluationRecord,
    HumanScores,
    PilotSampleSelection,
    evaluate_pilot_sample,
    load_manifest,
)
from app.domains.content_rewrite.models import RewriteRequestEnvelope, RewriteSurface
from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
from app.domains.content_rewrite.tables import (
    ContentRewriteSpendDayRow,
    ContentRewriteSpendMonthRow,
)
from app.domains.readings.daily_psychology import split_scene_lead
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider
from app.infrastructure.generation.base import (
    GenerationPermanent,
    RewriteGenerationResult,
    RewriteGenerationSuccess,
)
from scripts import daily_rewrite_pilot_eval as pilot
from scripts.audit_rewrite_release import DEFAULT_MANIFEST

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)


@pytest.fixture(scope="module")
def selection() -> PilotSampleSelection:
    return pilot.build_selection(pilot.load_catalog())[0]


@pytest.fixture(scope="module")
def prepared(selection: PilotSampleSelection) -> tuple[pilot.PreparedCase, ...]:
    return pilot.prepare_selection(pilot.load_catalog(), selection)


def test_catalog_is_the_synthetic_daily_home_segment_of_the_corpus() -> None:
    catalog = pilot.load_catalog()
    manifest = load_manifest(DEFAULT_MANIFEST)
    expected = tuple(case for case in manifest.case_ids if case.startswith("daily_home-"))
    assert catalog.corpus_version == manifest.version == pilot.CORPUS_VERSION
    assert catalog.synthetic_only
    assert tuple(case.case_id for case in catalog.cases) == expected
    assert {case.kind for case in catalog.cases} == {"exact", "date_only"}


def test_selection_covers_every_issue_lens_context_and_roast_arena(
    selection: PilotSampleSelection,
) -> None:
    catalog = pilot.load_catalog()
    by_id = {case.case_id: case for case in catalog.cases}
    facts = [pilot.case_facts(by_id[i], pilot.render_case(by_id[i])[1]) for i in selection.case_ids]
    covered = set().union(*(pilot._targets(item) for item in facts))

    assert len(selection.case_ids) == pilot.SAMPLE_SIZE
    assert pilot.required_targets() <= covered
    assert set(selection.case_ids) <= set(load_manifest(DEFAULT_MANIFEST).case_ids)
    assert selection == pilot.build_selection(catalog)[0]  # deterministic


def test_dry_run_makes_zero_network_calls_and_checks_the_privacy_allowlist(
    selection: PilotSampleSelection, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("dry-run attempted a network call")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)
    selection_path = tmp_path / "selection.json"
    selection_path.write_text(selection.model_dump_json())
    out = tmp_path / "cases.jsonl"

    pilot.main(["generate", "--selection", str(selection_path), "--out", str(out), "--dry-run"])

    rows = pilot.read_jsonl(out)
    assert [row["case_id"] for row in rows] == list(selection.case_ids)
    assert all(row["generated"] is None and row["gate"] is None for row in rows)
    assert oct(out.stat().st_mode & 0o777) == "0o600"
    assert {row["versions"]["prompt"] for row in rows} == {"surface-rewrite-v4"}
    assert {row["versions"]["gate"] for row in rows} == {"daily-rewrite-gates/v3"}
    worst_case = sum(row["reserved"]["cost_nanos"] for row in rows)
    assert 0 < worst_case < 3 * 10_000_000  # fits the proposed 3-cent staging day


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ([], "--confirm-max-usd is required"),
        (["--confirm-max-usd", "5"], "within (0, 0.90]"),
        (["--confirm-max-usd", "0.05"], "missing generation_enabled"),
    ],
)
def test_paid_run_refuses_without_explicit_spend_approval_and_never_prints_the_key(
    extra: list[str],
    message: str,
    selection: PilotSampleSelection,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_key = "sk-synthetic-never-real-" + "x" * 24
    monkeypatch.chdir(tmp_path)  # no local .env is read
    monkeypatch.setenv("LA_LANH_GENERATION_OPENAI_API_KEY", fake_key)
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **k: pytest.fail("network"))
    selection_path = tmp_path / "selection.json"
    selection_path.write_text(selection.model_dump_json())

    with pytest.raises(SystemExit) as refused:
        pilot.main(
            [
                "generate",
                "--selection",
                str(selection_path),
                "--out",
                str(tmp_path / "paid.jsonl"),
                "--paid",
                *extra,
            ]
        )

    assert message in str(refused.value.code)
    captured = capsys.readouterr()
    assert fake_key not in captured.out + captured.err + str(refused.value.code)
    assert not (tmp_path / "paid.jsonl").exists()


class _FakeProvider:
    def __init__(self, outputs: dict[str, dict[str, JsonValue] | None]) -> None:
        self.outputs = outputs
        self.calls: list[str] = []

    async def generate_rewrite(self, request: RewriteRequestEnvelope) -> RewriteGenerationResult:
        self.calls.append(request.key.blueprint_hash)
        output = self.outputs[request.key.blueprint_hash]
        if output is None:
            return GenerationPermanent(code="synthetic_refusal")
        return RewriteGenerationSuccess(
            key=request.key, output=output, input_tokens=700, output_tokens=60
        )


def _identity(item: pilot.PreparedCase) -> dict[str, JsonValue]:
    return {
        "title": item.baseline.hook,
        "scene": item.baseline.manifestation,
        "action": item.baseline.micro_action,
    }


@pytest.mark.asyncio
async def test_paid_path_debits_the_shared_ledger_before_each_send_and_stops_at_the_cap(
    prepared: tuple[pilot.PreparedCase, ...], tmp_path: Path
) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'ledger.db'}")
    await database.initialize()
    ledger = PostgresContentRewriteRepository(
        database.sessions, AesGcmEnvelopeCipher(StaticDataKeyProvider(b"l" * 32))
    )
    sample = prepared[:4]
    with_lead = next(
        item for item in sample if split_scene_lead(item.baseline.manifestation)[0] is not None
    )
    outputs: dict[str, dict[str, JsonValue] | None] = {
        item.request.key.blueprint_hash: _identity(item) for item in sample
    }
    # A rewrite that drops the v7 context clause is rejected by the production projector.
    outputs[with_lead.request.key.blueprint_hash] = _identity(with_lead) | {
        "scene": split_scene_lead(with_lead.baseline.manifestation)[1]
    }
    outputs[sample[1].request.key.blueprint_hash] = None
    provider = _FakeProvider(outputs)
    # Room for exactly three reservations today.
    limit = sum(item.reserve_cost_nanos for item in sample[:3])
    try:
        rows = await pilot.generate_paid(
            sample,
            provider=provider,
            ledger=ledger,
            limits=pilot.LedgerLimits(
                daily_tokens=1_000_000, daily_cost_nanos=limit, monthly_cost_nanos=limit
            ),
            clock=lambda: NOW,
        )
        async with database.sessions() as session:
            day = await session.get(ContentRewriteSpendDayRow, "2026-10-13")
            month = await session.get(ContentRewriteSpendMonthRow, "2026-10")
    finally:
        await database.dispose()

    assert len(provider.calls) == 3  # the fourth never reached the provider
    assert day is not None and month is not None
    assert day.reserved_cost_nanos == month.reserved_cost_nanos == limit
    assert rows[3]["gate"] == {"passed": False, "failure_codes": ["budget_blocked"]}
    assert rows[1]["generated"] is None
    assert rows[1]["gate"]["failure_codes"] == ["provider_synthetic_refusal"]
    for item, row in zip(sample[:3], rows[:3], strict=True):
        if item is sample[1]:
            continue
        expected = item is not with_lead
        assert row["gate"]["passed"] is expected, row["gate"]
        if not expected:
            assert row["gate"]["failure_codes"] == ["daily_scene_context_lost"]
        assert row["usage"]["cost_nanos"] == 700 * 100 + 60 * 500


def test_review_page_is_self_contained_blinded_and_escaped(
    prepared: tuple[pilot.PreparedCase, ...],
) -> None:
    item = prepared[0]
    hostile = _identity(item) | {"title": "</script><script>alert(1)</script>"}
    rows = [
        pilot.case_row(
            item, generated=hostile, gate={"passed": True, "failure_codes": []}, usage=None
        ),
        pilot.case_row(prepared[1], generated=None, gate=None, usage=None),
    ]
    page = pilot.review_page(rows)

    assert "Content-Security-Policy" in page and "noindex" in page
    assert re.search(r"(?:src|href)=[\"']https?://", page) is None
    assert "</script><script>alert" not in page
    data = json.loads(
        page.split('<script id="data" type="application/json">', 1)[1].split("</script>", 1)[0]
    )
    cases = {case["case_id"]: case for case in data["cases"]}
    first = cases[item.case.case_id]
    assert first["luna_card"]["thesis"] == item.baseline.thesis  # Luna never writes the thesis
    assert first["luna_card"]["hook"] == hostile["title"]
    assert cases[prepared[1].case.case_id]["luna_card"] is None
    assert {case["luna_first"] for case in data["cases"]} <= {True, False}


def _record(case_id: str, *, baseline: int, candidate: int, passed: bool = True) -> dict[str, Any]:
    return EvaluationRecord(
        case_id=case_id,
        surface=RewriteSurface.DAILY_HOME,
        baseline=HumanScores(**dict.fromkeys(HumanScores.model_fields, baseline)),
        candidate=HumanScores(**dict.fromkeys(HumanScores.model_fields, candidate)),
        gate_passed=passed,
        failure_codes=() if passed else ("human_rejected",),
        frame_fingerprint=f"{case_id[-4:]:0>16}",
    ).model_dump(mode="json")


def test_pilot_sample_gate_uses_release_thresholds_on_the_declared_sample_only(
    selection: PilotSampleSelection,
) -> None:
    manifest = load_manifest(DEFAULT_MANIFEST)
    good = tuple(
        EvaluationRecord.model_validate(_record(case_id, baseline=3, candidate=4))
        for case_id in selection.case_ids
    )
    assert evaluate_pilot_sample(manifest, selection, good).passed

    missing = evaluate_pilot_sample(manifest, selection, good[:-1])
    assert not missing.passed and "corpus_coverage_mismatch" in missing.findings

    rejected = (
        *good[:-1],
        EvaluationRecord.model_validate(
            _record(selection.case_ids[-1], baseline=3, candidate=4, passed=False)
        ),
    )
    assert not evaluate_pilot_sample(manifest, selection, rejected).passed

    not_better = tuple(
        EvaluationRecord.model_validate(_record(case_id, baseline=4, candidate=4))
        for case_id in selection.case_ids
    )
    assert not evaluate_pilot_sample(manifest, selection, not_better).passed
