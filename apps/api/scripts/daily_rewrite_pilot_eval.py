"""daily_home pilot evaluation: synthetic catalog, sample, Luna generation, review page.

Subcommands (all offline unless ``generate --paid``):

* ``build-catalog`` writes the versioned 75-case synthetic catalog for the corpus's
  ``daily_home`` segment (deterministic search; no user data).
* ``select`` picks ~40 cases covering every Daily issue, lens, scene context, chart
  kind and roast-eligible context, and writes a ``PilotSampleSelection``.
* ``generate --dry-run`` renders the deterministic baselines and the exact rewrite
  requests, checks the privacy allowlist and estimates the ledger reservation. It
  makes zero network calls.
* ``generate --paid`` is for an operator inside the configured rewrite-worker
  container only. It refuses unless the worker Settings validate (key file, spend
  and governance approval, budgets, PostgreSQL), ``daily_home`` is in the approved
  rollout and ``--confirm-max-usd`` covers the worst case. Each call is debited on
  the same anonymous day/month ledger as the worker before it is sent. The key is
  read only by the shared provider factory and is never printed.
* ``html`` renders a self-contained, blinded review page that exports strict
  ``EvaluationRecord`` results for ``pnpm rewrite:release -- --selection``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    CalculationConfig,
    ChartInput,
    DateOnlySunResult,
    EngineProvenance,
    NatalChart,
    ZodiacSign,
)
from app.domains.content_rewrite.evaluation import PilotSampleSelection
from app.domains.content_rewrite.models import RewriteRequestEnvelope, RewriteSurface
from app.domains.content_rewrite.worker import reservation_estimate
from app.domains.readings.companion import companion_issue_entry
from app.domains.readings.daily_psychology import DAILY_ISSUES, split_scene_lead
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    BackgroundLens,
    ReadingCandidate,
    ReadingPlan,
    ReadingPlanRecord,
    ReadingProjectionRecord,
    ReadingPurpose,
    ReadingRevisionRecord,
    ReadingRevisionSource,
    SemanticArena,
    canonical_gate_policy_version,
    canonical_lens_variant,
    canonical_projection_scope_key,
    canonical_reading_plan_key,
    canonical_reading_revision_key,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.rewrite import DailyRewriteProjector, compile_daily_rewrite_request
from app.domains.readings.voice import DailySections, roast_daily_sections
from app.infrastructure.generation.base import RewriteGenerationProvider, RewriteGenerationSuccess
from app.infrastructure.generation.openai import OPENAI_REWRITE_PROMPT_VERSION
from app.infrastructure.generation.pricing import (
    GPT_6_LUNA_STANDARD_2026_10_04,
    USD_NANOS_PER_DOLLAR,
)
from app.infrastructure.generation.privacy import PrivacyMinimiser

CATALOG_PATH = Path(__file__).resolve().parent / "fixtures" / "daily_home_pilot_cases.json"
CATALOG_VERSION = "daily-home-cases-v1"
CORPUS_VERSION = "rewrite-corpus-2026-10-03-v1"
CORPUS_DAILY_HOME_CASES = 75
SELECTION_VERSION = "daily-home-pilot-sample-v1"
SAMPLE_SIZE = 40
MODEL = "gpt-6-luna"
TIMEZONE = "Asia/Ho_Chi_Minh"
_GENTLE = {SemanticArena.ENERGY.value, SemanticArena.SELF_CARE.value}
_ROAST_SHARP = (
    SemanticArena.RELATIONSHIPS.value,
    SemanticArena.COMMUNICATION.value,
    SemanticArena.WORK.value,
)
_NAMESPACE = uuid5(NAMESPACE_URL, "https://la-lanh.invalid/synthetic/daily-home-pilot")
_EPOCH = datetime(2026, 10, 1, tzinfo=UTC)


# --------------------------------------------------------------------------- catalog


class SyntheticDailyCase(BaseModel):
    """One synthetic reader-day. Coordinates and times are generated, never real."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(pattern=r"^daily_home-[0-9]{4}$")
    kind: Literal["exact", "date_only"]
    birth_utc: datetime | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    sign: ZodiacSign | None = None
    lens: BackgroundLens
    note_date: date

    @model_validator(mode="after")
    def validate_kind(self) -> SyntheticDailyCase:
        exact = (self.birth_utc, self.latitude, self.longitude)
        if self.kind == "exact" and (None in exact or self.sign is not None):
            raise ValueError("exact cases need birth time and place only")
        if self.kind == "date_only" and (any(v is not None for v in exact) or self.sign is None):
            raise ValueError("date-only cases carry a sign only")
        return self


class SyntheticCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    corpus_version: str
    surface: Literal["daily_home"] = "daily_home"
    synthetic_only: bool
    cases: tuple[SyntheticDailyCase, ...]

    @model_validator(mode="after")
    def validate_cases(self) -> SyntheticCatalog:
        if not self.synthetic_only:
            raise ValueError("catalog must be synthetic")
        expected = tuple(f"daily_home-{i:04d}" for i in range(1, CORPUS_DAILY_HOME_CASES + 1))
        if tuple(case.case_id for case in self.cases) != expected:
            raise ValueError("catalog must name every corpus daily_home case once, in order")
        return self


def load_catalog(path: Path = CATALOG_PATH) -> SyntheticCatalog:
    return SyntheticCatalog.model_validate_json(path.read_text(encoding="utf-8"))


def _synthetic_birth(k: int) -> tuple[datetime, float, float]:
    birth = datetime(
        1975 + (k * 7) % 35,
        (k * 5) % 12 + 1,
        (k * 11) % 27 + 1,
        (k * 13) % 24,
        (k * 17) % 60,
        tzinfo=UTC,
    )
    return birth, round(8.5 + ((k * 37) % 140) / 10, 2), round(102.2 + ((k * 53) % 70) / 10, 2)


def build_catalog(engine: NatalChartEngine | None = None) -> SyntheticCatalog:
    """Deterministic search over synthetic charts, then 12 date-only cases.

    Pass 1 takes up to three cases per Daily issue on distinct lenses (rare issues
    need many charts); pass 2 fills the exact quota with at most six per issue,
    always trying the least-used lens first.
    """

    engine = engine or NatalChartEngine()
    lenses = tuple(BackgroundLens)
    per_issue: Counter[str] = Counter()
    per_lens: Counter[BackgroundLens] = Counter()
    used_pairs: set[tuple[str, BackgroundLens]] = set()
    used_inputs: set[tuple[int, BackgroundLens, date]] = set()
    exact: list[tuple[int, BackgroundLens, date]] = []
    target_exact = CORPUS_DAILY_HOME_CASES - len(ZodiacSign)
    issue_cache: dict[tuple[int, BackgroundLens, date], str] = {}

    def issue_for(k: int, lens: BackgroundLens, note_date: date) -> str:
        key = (k, lens, note_date)
        if key not in issue_cache:
            birth, latitude, longitude = _synthetic_birth(k)
            case = SyntheticDailyCase(
                case_id="daily_home-0001",
                kind="exact",
                birth_utc=birth,
                latitude=latitude,
                longitude=longitude,
                lens=lens,
                note_date=note_date,
            )
            issue_cache[key] = _issue(render_case(case, engine)[1])
        return issue_cache[key]

    for cap, distinct, limit in ((3, True, 400), (6, False, 2_000)):
        for k in range(1, limit):
            if len(exact) >= target_exact:
                break
            if distinct and all(per_issue[issue.key] >= cap for issue in DAILY_ISSUES):
                break
            for offset in (0, 9):
                note_date = date(2026, 10, 1) + timedelta(days=(k * 3 + offset) % 61)
                for lens in sorted(lenses, key=lambda value: (per_lens[value], value.value)):
                    if (k, lens, note_date) in used_inputs:
                        continue
                    issue = issue_for(k, lens, note_date)
                    if per_issue[issue] >= cap or (distinct and (issue, lens) in used_pairs):
                        continue
                    used_pairs.add((issue, lens))
                    used_inputs.add((k, lens, note_date))
                    per_issue[issue] += 1
                    per_lens[lens] += 1
                    exact.append((k, lens, note_date))
                    break
                if len(exact) >= target_exact:
                    break
    cases: list[SyntheticDailyCase] = []
    for index, (k, lens, note_date) in enumerate(exact, start=1):
        birth, latitude, longitude = _synthetic_birth(k)
        cases.append(
            SyntheticDailyCase(
                case_id=f"daily_home-{index:04d}",
                kind="exact",
                birth_utc=birth,
                latitude=latitude,
                longitude=longitude,
                lens=lens,
                note_date=note_date,
            )
        )
    for offset, sign in enumerate(ZodiacSign):
        index = len(cases) + 1
        cases.append(
            SyntheticDailyCase(
                case_id=f"daily_home-{index:04d}",
                kind="date_only",
                sign=sign,
                lens=lenses[offset % len(lenses)],
                note_date=date(2026, 10, 1) + timedelta(days=offset * 5),
            )
        )
    return SyntheticCatalog(
        version=CATALOG_VERSION,
        corpus_version=CORPUS_VERSION,
        synthetic_only=True,
        cases=tuple(cases),
    )


# --------------------------------------------------------------------------- render


def _chart(case: SyntheticDailyCase, engine: NatalChartEngine) -> NatalChart | DateOnlySunResult:
    if case.kind == "date_only":
        if case.sign is None:
            raise ValueError("date-only case without a sign")
        return DateOnlySunResult(
            status="certain",
            sign=case.sign,
            candidates=(case.sign,),
            provenance=EngineProvenance(version="synthetic", profile="daily-home-pilot"),
        )
    if case.birth_utc is None or case.latitude is None or case.longitude is None:
        raise ValueError("exact case without birth time and place")
    return engine.calculate_chart(
        ChartInput(utc_datetime=case.birth_utc, latitude=case.latitude, longitude=case.longitude),
        CalculationConfig.western_recommended(),
    )


def _observed_at(case: SyntheticDailyCase) -> datetime:
    # Mirrors ReadingApplicationService: Daily transits are observed at 12:00 UTC.
    return datetime.combine(case.note_date, time(hour=12), tzinfo=UTC)


def render_case(
    case: SyntheticDailyCase, engine: NatalChartEngine | None = None
) -> tuple[ReadingPlan, ReadingCandidate]:
    engine = engine or NatalChartEngine()
    chart = _chart(case, engine)
    transits = (
        engine.calculate_transit_to_natal(chart, _observed_at(case))
        if isinstance(chart, NatalChart)
        else None
    )
    plan = ReadingPlanner().plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        transits=transits,
        background_lens=None if case.lens is BackgroundLens.AUTO else case.lens,
        editorial_seed=case.note_date.isoformat(),
    )
    return plan, DeterministicVietnameseRenderer().render(plan)


def _issue(candidate: ReadingCandidate) -> str:
    blueprint = candidate.semantic_blueprint
    if blueprint is None:
        raise ValueError("Daily baseline has no blueprint")
    return blueprint.mechanism_key.split(":", 1)[1]


@dataclass(frozen=True)
class CaseFacts:
    case_id: str
    issue: str
    lens: str
    arena: str
    kind: str
    roast_eligible: bool

    @property
    def gentle(self) -> bool:
        return self.arena in _GENTLE


def case_facts(case: SyntheticDailyCase, candidate: ReadingCandidate) -> CaseFacts:
    arena, _ = split_scene_lead(candidate.manifestation)
    sections = DailySections(
        candidate.hook, candidate.thesis, candidate.manifestation, candidate.micro_action
    )
    return CaseFacts(
        case_id=case.case_id,
        issue=_issue(candidate),
        lens=case.lens.value,
        arena=arena.value if arena is not None else "none",
        kind=case.kind,
        roast_eligible=roast_daily_sections(sections) != sections,
    )


# --------------------------------------------------------------------------- select


def _targets(facts: CaseFacts) -> set[str]:
    targets = {
        f"issue:{facts.issue}",
        f"lens:{facts.lens}",
        f"arena:{facts.arena}",
        f"kind:{facts.kind}",
    }
    if facts.roast_eligible:
        targets.add("roast:gentle" if facts.gentle else f"roast:{facts.arena}")
    return targets


def required_targets() -> set[str]:
    return {
        *(f"issue:{issue.key}" for issue in DAILY_ISSUES),
        *(f"lens:{lens.value}" for lens in BackgroundLens),
        *(f"arena:{arena}" for arena in (*_ROAST_SHARP, *sorted(_GENTLE))),
        "kind:exact",
        "kind:date_only",
        *(f"roast:{arena}" for arena in _ROAST_SHARP),
        "roast:gentle",
    }


def select_sample(facts: Sequence[CaseFacts], size: int = SAMPLE_SIZE) -> tuple[CaseFacts, ...]:
    """Greedy set cover of every required target, then balanced deterministic fill."""

    remaining = sorted(facts, key=lambda item: item.case_id)
    chosen: list[CaseFacts] = []
    uncovered = required_targets()
    while uncovered and remaining:
        best = max(remaining, key=lambda item: (len(_targets(item) & uncovered), -_order(item)))
        if not _targets(best) & uncovered:
            break
        chosen.append(best)
        remaining.remove(best)
        uncovered -= _targets(best)
    if uncovered:
        raise ValueError(f"catalog cannot cover: {sorted(uncovered)}")
    while len(chosen) < size and remaining:
        issues = Counter(item.issue for item in chosen)
        lenses = Counter(item.lens for item in chosen)
        arenas = Counter(item.arena for item in chosen)
        best = min(
            remaining,
            key=lambda item: (
                issues[item.issue],
                lenses[item.lens],
                arenas[item.arena],
                item.case_id,
            ),
        )
        chosen.append(best)
        remaining.remove(best)
    return tuple(sorted(chosen, key=lambda item: item.case_id))


def _order(item: CaseFacts) -> int:
    return int(item.case_id.rsplit("-", 1)[1])


def coverage(sample: Iterable[CaseFacts]) -> dict[str, dict[str, int]]:
    items = tuple(sample)
    return {
        "issue": dict(sorted(Counter(item.issue for item in items).items())),
        "lens": dict(sorted(Counter(item.lens for item in items).items())),
        "arena": dict(sorted(Counter(item.arena for item in items).items())),
        "kind": dict(sorted(Counter(item.kind for item in items).items())),
        "roast": dict(
            sorted(
                Counter(
                    ("gentle" if item.gentle else item.arena)
                    for item in items
                    if item.roast_eligible
                ).items()
            )
        ),
    }


def build_selection(
    catalog: SyntheticCatalog,
) -> tuple[PilotSampleSelection, tuple[CaseFacts, ...]]:
    engine = NatalChartEngine()
    facts = [case_facts(case, render_case(case, engine)[1]) for case in catalog.cases]
    sample = select_sample(facts)
    selection = PilotSampleSelection(
        version=SELECTION_VERSION,
        corpus_version=catalog.corpus_version,
        surface=RewriteSurface.DAILY_HOME,
        synthetic_only=True,
        case_ids=tuple(item.case_id for item in sample),
    )
    return selection, sample


# --------------------------------------------------------------------------- generate


class _MemoryDailyRepository:
    """In-process stand-in so the production projector gates synthetic output."""

    def __init__(self, plan: ReadingPlanRecord, projection: ReadingProjectionRecord) -> None:
        self.plan = plan
        self.projection = projection
        self.revisions: dict[UUID, ReadingRevisionRecord] = {}

    async def get_plan(
        self, guest_id: UUID, profile_id: UUID, plan_id: UUID
    ) -> ReadingPlanRecord | None:
        return self.plan if plan_id == self.plan.id else None

    async def get_projection(
        self, guest_id: UUID, profile_id: UUID, scope_key: str
    ) -> ReadingProjectionRecord | None:
        return self.projection if scope_key == self.projection.scope_key else None

    async def get_revision(
        self, guest_id: UUID, profile_id: UUID, revision_id: UUID
    ) -> ReadingRevisionRecord | None:
        return self.revisions.get(revision_id)

    async def save_or_replay_revision(
        self, record: ReadingRevisionRecord
    ) -> tuple[ReadingRevisionRecord, bool]:
        self.revisions[record.id] = record
        return record, False

    async def publish_available(
        self, guest_id: UUID, profile_id: UUID, scope_key: str, revision_id: UUID
    ) -> ReadingProjectionRecord:
        raise AssertionError("evaluation never publishes")


@dataclass(frozen=True)
class PreparedCase:
    case: SyntheticDailyCase
    facts: CaseFacts
    baseline: ReadingCandidate
    request: RewriteRequestEnvelope
    repository: _MemoryDailyRepository
    reserve_tokens: int
    reserve_cost_nanos: int


def prepare_case(case: SyntheticDailyCase, engine: NatalChartEngine) -> PreparedCase:
    plan, baseline = render_case(case, engine)
    evaluation = evaluate_candidate(plan, baseline)
    if not evaluation.accepted:
        raise ValueError(f"{case.case_id}: deterministic baseline failed its gates")
    guest_id = uuid5(_NAMESPACE, f"{case.case_id}:guest")
    profile_id = uuid5(_NAMESPACE, f"{case.case_id}:profile")
    plan_record = ReadingPlanRecord(
        id=uuid5(_NAMESPACE, f"{case.case_id}:plan"),
        guest_id=guest_id,
        profile_id=profile_id,
        plan_key=canonical_reading_plan_key(plan),
        plan=plan,
        created_at=_EPOCH,
    )
    lens_variant = canonical_lens_variant(plan.background_lens)
    observed_at = _observed_at(case)
    projection = ReadingProjectionRecord(
        id=uuid5(_NAMESPACE, f"{case.case_id}:projection"),
        guest_id=guest_id,
        profile_id=profile_id,
        scope_key=canonical_projection_scope_key(
            purpose=ReadingPurpose.DAILY_NOTE,
            tradition=plan.tradition,
            config_hash=plan.config_hash,
            local_date=case.note_date,
            timezone_name=TIMEZONE,
            observed_at=observed_at,
            lens_variant=lens_variant,
        ),
        purpose=ReadingPurpose.DAILY_NOTE,
        tradition=plan.tradition,
        config_hash=plan.config_hash,
        lens_variant=lens_variant,
        local_date=case.note_date,
        timezone_name=TIMEZONE,
        observed_at=observed_at,
        active_revision_id=uuid5(_NAMESPACE, f"{case.case_id}:baseline"),
        created_at=_EPOCH,
        updated_at=_EPOCH,
    )
    gate_policy = canonical_gate_policy_version(evaluation)
    baseline_revision = ReadingRevisionRecord(
        id=uuid5(_NAMESPACE, f"{case.case_id}:baseline"),
        guest_id=guest_id,
        profile_id=profile_id,
        plan_id=plan_record.id,
        revision_key=canonical_reading_revision_key(
            plan_key=plan_record.plan_key,
            source=ReadingRevisionSource.DETERMINISTIC,
            renderer_version=baseline.renderer_version,
            content_version="pilot-eval-baseline",
            schema_version=baseline.schema_version,
            rules_version=plan.rules_version,
            gate_policy_version=gate_policy,
        ),
        source=ReadingRevisionSource.DETERMINISTIC,
        renderer_version=baseline.renderer_version,
        content_version="pilot-eval-baseline",
        schema_version=baseline.schema_version,
        rules_version=plan.rules_version,
        gate_policy_version=gate_policy,
        evaluation=evaluation,
        created_at=_EPOCH,
    )
    repository = _MemoryDailyRepository(plan_record, projection)
    repository.revisions[baseline_revision.id] = baseline_revision
    request = compile_daily_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version=MODEL,
        prompt_version=OPENAI_REWRITE_PROMPT_VERSION,
    )
    # The exact allowlist the provider adapter applies before any send.
    PrivacyMinimiser().minimise(request.key.surface, request.safe_payload)
    tokens, cost = reservation_estimate(request)
    return PreparedCase(
        case=case,
        facts=case_facts(case, baseline),
        baseline=baseline,
        request=request,
        repository=repository,
        reserve_tokens=tokens,
        reserve_cost_nanos=cost,
    )


def prepare_selection(
    catalog: SyntheticCatalog, selection: PilotSampleSelection
) -> tuple[PreparedCase, ...]:
    if selection.corpus_version != catalog.corpus_version:
        raise ValueError("selection and catalog belong to different corpora")
    by_id = {case.case_id: case for case in catalog.cases}
    missing = [case_id for case_id in selection.case_ids if case_id not in by_id]
    if missing:
        raise ValueError(f"selection names unknown cases: {missing}")
    engine = NatalChartEngine()
    return tuple(prepare_case(by_id[case_id], engine) for case_id in selection.case_ids)


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return " ".join(
        "".join(char for char in normalized if unicodedata.category(char) != "Mn").split()
    )


def frame_fingerprint(title: str) -> str:
    return sha256(_fold(title).encode()).hexdigest()[:16]


async def gate_output(
    prepared: PreparedCase, output: dict[str, JsonValue]
) -> tuple[bool, list[str]]:
    """Run the production Daily projector (all rewrite + reading gates), never publishing."""

    decision = await DailyRewriteProjector(prepared.repository).validate_and_project(
        prepared.request, output, completed_at=_EPOCH, publish=False
    )
    if decision.accepted:
        return True, []
    return False, [decision.failure_code or "daily_rewrite_rejected"]


def authored_companion(baseline: ReadingCandidate) -> str:
    """Lá's authored line for this card (content matrix), the reviewer's baseline."""

    blueprint = baseline.semantic_blueprint
    return companion_issue_entry(blueprint.mechanism_key if blueprint else None).line.direct


def case_row(
    prepared: PreparedCase,
    *,
    generated: dict[str, JsonValue] | None,
    gate: dict[str, Any] | None,
    usage: dict[str, Any] | None,
) -> dict[str, Any]:
    baseline = prepared.baseline
    title = str(generated["title"]) if generated else baseline.hook
    return {
        "case_id": prepared.case.case_id,
        "surface": RewriteSurface.DAILY_HOME.value,
        "issue": prepared.facts.issue,
        "lens": prepared.facts.lens,
        "arena": prepared.facts.arena,
        "kind": prepared.facts.kind,
        "roast_eligible": prepared.facts.roast_eligible,
        "baseline": {
            "hook": baseline.hook,
            "thesis": baseline.thesis,
            "manifestation": baseline.manifestation,
            "micro_action": baseline.micro_action,
            "companion": authored_companion(baseline),
        },
        "generated": generated,
        "gate": gate,
        "frame_fingerprint": frame_fingerprint(title),
        "reserved": {
            "tokens": prepared.reserve_tokens,
            "cost_nanos": prepared.reserve_cost_nanos,
        },
        "usage": usage,
        "versions": {
            "prompt": prepared.request.key.prompt_version,
            "gate": prepared.request.key.gate_version,
            "renderer": baseline.renderer_version,
        },
    }


class SpendLedger(Protocol):
    async def reserve_standalone_budget(
        self,
        *,
        requested_tokens: int,
        daily_token_limit: int,
        requested_cost_nanos: int,
        daily_cost_limit_nanos: int,
        monthly_cost_limit_nanos: int,
        updated_at: datetime,
    ) -> bool: ...


@dataclass(frozen=True)
class LedgerLimits:
    daily_tokens: int
    daily_cost_nanos: int
    monthly_cost_nanos: int


async def generate_paid(
    prepared: Sequence[PreparedCase],
    *,
    provider: RewriteGenerationProvider,
    ledger: SpendLedger,
    limits: LedgerLimits,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> list[dict[str, Any]]:
    """Reserve on the shared ledger, then send; a refused reservation stops the run."""

    rows: list[dict[str, Any]] = []
    blocked = False
    for item in prepared:
        if blocked:
            rows.append(_failed_row(item, "budget_blocked"))
            continue
        reserved = await ledger.reserve_standalone_budget(
            requested_tokens=item.reserve_tokens,
            daily_token_limit=limits.daily_tokens,
            requested_cost_nanos=item.reserve_cost_nanos,
            daily_cost_limit_nanos=limits.daily_cost_nanos,
            monthly_cost_limit_nanos=limits.monthly_cost_nanos,
            updated_at=clock(),
        )
        if not reserved:
            blocked = True
            rows.append(_failed_row(item, "budget_blocked"))
            continue
        result = await provider.generate_rewrite(item.request)
        if not isinstance(result, RewriteGenerationSuccess):
            code = getattr(result, "code", None) or result.kind
            rows.append(_failed_row(item, f"provider_{code}"))
            continue
        passed, codes = await gate_output(item, result.output)
        usage = None
        if result.input_tokens is not None and result.output_tokens is not None:
            usage = {
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "cost_nanos": GPT_6_LUNA_STANDARD_2026_10_04.cost_nanos(
                    input_tokens=result.input_tokens, output_tokens=result.output_tokens
                ),
            }
        output = {key: result.output[key] for key in ("title", "scene", "action", "companion")}
        rows.append(
            case_row(
                item,
                generated=output,
                gate={"passed": passed, "failure_codes": codes},
                usage=usage,
            )
        )
    return rows


def _failed_row(item: PreparedCase, code: str) -> dict[str, Any]:
    return case_row(
        item, generated=None, gate={"passed": False, "failure_codes": [code]}, usage=None
    )


def generate_dry_run(prepared: Sequence[PreparedCase]) -> list[dict[str, Any]]:
    return [case_row(item, generated=None, gate=None, usage=None) for item in prepared]


def _usd(nanos: int) -> Decimal:
    return Decimal(nanos) / Decimal(USD_NANOS_PER_DOLLAR)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


class PaidRunRefused(SystemExit):
    pass


def _parse_confirmed_usd(raw: str | None) -> Decimal:
    if raw is None:
        raise PaidRunRefused("Paid run refused: --confirm-max-usd is required")
    try:
        value = Decimal(raw)
    except InvalidOperation as error:
        raise PaidRunRefused("Paid run refused: --confirm-max-usd must be a decimal") from error
    if not Decimal("0") < value <= Decimal("0.90"):
        raise PaidRunRefused("Paid run refused: --confirm-max-usd must be within (0, 0.90]")
    return value


async def _run_paid(prepared: Sequence[PreparedCase], confirmed: Decimal) -> list[dict[str, Any]]:
    from app.config import Settings
    from app.db.session import Database
    from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
    from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider, decode_key
    from app.infrastructure.generation import (
        DisabledRewriteGenerationProvider,
        build_rewrite_generation_provider,
    )
    from app.infrastructure.generation.pricing import cents_to_nanos

    try:
        settings = Settings()
    except Exception as error:
        # Never echo validation details: they may quote configured values.
        raise PaidRunRefused(
            f"Paid run refused: worker Settings are invalid ({type(error).__name__})"
        ) from None
    reasons = [
        name
        for name, ok in (
            ("generation_enabled", settings.generation_enabled),
            ("generation_worker_enabled", settings.generation_worker_enabled),
            ("generation_governance_approved", settings.generation_governance_approved),
            ("generation_spend_approved", settings.generation_spend_approved),
            (
                "daily_home rollout",
                settings.generation_surface_rollout.get("daily_home", "off") != "off",
            ),
            ("monthly budget", settings.generation_monthly_budget_cents > 0),
            ("PostgreSQL ledger", settings.database_url.startswith("postgresql+asyncpg://")),
        )
        if not ok
    ]
    if reasons:
        raise PaidRunRefused(f"Paid run refused: missing {', '.join(reasons)}")
    worst_case = _usd(sum(item.reserve_cost_nanos for item in prepared))
    if worst_case > confirmed:
        raise PaidRunRefused(
            f"Paid run refused: worst-case reservation {worst_case:.6f} USD exceeds "
            f"--confirm-max-usd {confirmed}"
        )
    provider = build_rewrite_generation_provider(settings)
    if isinstance(provider, DisabledRewriteGenerationProvider):
        raise PaidRunRefused("Paid run refused: provider is disabled")
    database = Database(str(settings.database_url))
    await database.initialize()
    try:
        ledger = PostgresContentRewriteRepository(
            database.sessions,
            AesGcmEnvelopeCipher(
                StaticDataKeyProvider(
                    decode_key(settings.guest_encryption_key.get_secret_value(), expected_bytes=32)
                )
            ),
        )
        return await generate_paid(
            prepared,
            provider=provider,
            ledger=ledger,
            limits=LedgerLimits(
                daily_tokens=settings.generation_daily_token_budget,
                daily_cost_nanos=cents_to_nanos(settings.generation_daily_budget_cents),
                monthly_cost_nanos=cents_to_nanos(settings.generation_monthly_budget_cents),
            ),
        )
    finally:
        await database.dispose()


def summarise(rows: Sequence[dict[str, Any]]) -> str:
    reserved = sum(int(row["reserved"]["cost_nanos"]) for row in rows)
    generated = sum(row["generated"] is not None for row in rows)
    passed = sum(bool(row["gate"] and row["gate"]["passed"]) for row in rows)
    actual = sum(int(row["usage"]["cost_nanos"]) for row in rows if row["usage"])
    failures = Counter(code for row in rows if row["gate"] for code in row["gate"]["failure_codes"])
    return json.dumps(
        {
            "cases": len(rows),
            "generated": generated,
            "gate_passed": passed,
            "failure_codes": dict(sorted(failures.items())),
            "worst_case_reservation_usd": f"{_usd(reserved):.6f}",
            "observed_cost_usd": f"{_usd(actual):.6f}",
            "pricing_version": GPT_6_LUNA_STANDARD_2026_10_04.version,
        },
        sort_keys=True,
    )


# --------------------------------------------------------------------------- html

_DIMENSIONS = (
    ("comprehension", "Hiểu ngay lần đọc đầu"),
    ("natural_vietnamese", "Tiếng Việt tự nhiên"),
    ("recognisable_situation", "Nhận ra tình huống"),
    ("action_linkage", "Việc nhỏ khớp với tình huống"),
    ("specificity", "Cụ thể, không chung chung"),
    ("return_value", "Muốn quay lại đọc"),
)

# Static template; ``__DATA__``/``__DIMS__`` are replaced with escaped JSON only.
REVIEW_TEMPLATE_PATH = Path(__file__).resolve().parent / "fixtures" / "daily_rewrite_review.html"


def review_page(rows: Sequence[dict[str, Any]]) -> str:
    cases = []
    for row in rows:
        generated = row["generated"]
        baseline = row["baseline"]
        luna = (
            {
                "hook": generated["title"],
                "thesis": baseline["thesis"],
                "manifestation": generated["scene"],
                "micro_action": generated["action"],
                "companion": generated["companion"],
            }
            if generated
            else None
        )
        cases.append(
            {
                "case_id": row["case_id"],
                "surface": row["surface"],
                "issue": row["issue"],
                "lens": row["lens"],
                "arena": row["arena"],
                "kind": row["kind"],
                "baseline_card": baseline,
                "luna_card": luna,
                "gate": row["gate"],
                "frame_fingerprint": row["frame_fingerprint"],
                # Deterministic blinding: the reviewer cannot infer order from position.
                "luna_first": int(sha256(row["case_id"].encode()).hexdigest(), 16) % 2 == 0,
            }
        )
    payload = json.dumps(cases, ensure_ascii=False, sort_keys=True)
    data = {"fingerprint": sha256(payload.encode()).hexdigest()[:16], "cases": cases}
    encoded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")
    dims = json.dumps([list(item) for item in _DIMENSIONS], ensure_ascii=False)
    template = REVIEW_TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("__DIMS__", dims).replace("__DATA__", encoded)


# --------------------------------------------------------------------------- cli


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build-catalog", help="Write the synthetic 75-case catalog")
    build.add_argument("--out", type=Path, default=CATALOG_PATH)
    select = commands.add_parser("select", help="Write the ~40-case pilot selection")
    select.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    select.add_argument("--out", type=Path, required=True)
    generate = commands.add_parser("generate", help="Render baselines, optionally call Luna")
    generate.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    generate.add_argument("--selection", type=Path, required=True)
    generate.add_argument("--out", type=Path, required=True)
    mode = generate.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Zero network calls")
    mode.add_argument("--paid", action="store_true", help="Operator-only; see module docstring")
    generate.add_argument("--confirm-max-usd")
    page = commands.add_parser("html", help="Render the blinded review page")
    page.add_argument("--cases", type=Path, required=True)
    page.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.command == "build-catalog":
        catalog = build_catalog()
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(catalog.model_dump(mode="json"), ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {len(catalog.cases)} synthetic cases ({catalog.version}) to {args.out}")
        return
    if args.command == "select":
        selection, sample = build_selection(load_catalog(args.catalog))
        args.out.write_text(selection.model_dump_json(indent=1) + "\n", encoding="utf-8")
        print(json.dumps({"cases": len(sample), "coverage": coverage(sample)}, sort_keys=True))
        return
    if args.command == "generate":
        selection = PilotSampleSelection.model_validate_json(
            args.selection.read_text(encoding="utf-8")
        )
        if args.paid:
            # Validate the confirmation before rendering, and never read secrets here.
            confirmed = _parse_confirmed_usd(args.confirm_max_usd)
            prepared = prepare_selection(load_catalog(args.catalog), selection)
            rows = asyncio.run(_run_paid(prepared, confirmed))
        else:
            prepared = prepare_selection(load_catalog(args.catalog), selection)
            rows = generate_dry_run(prepared)
        write_jsonl(args.out, rows)
        print(summarise(rows))
        return
    if args.command == "html":
        rows = read_jsonl(args.cases)
        args.out.write_text(review_page(rows), encoding="utf-8")
        print(f"Wrote review page for {len(rows)} cases to {args.out}")
        return


if __name__ == "__main__":
    try:
        main()
    except PaidRunRefused as refusal:
        print(refusal.code, file=sys.stderr)
        raise SystemExit(2) from None
