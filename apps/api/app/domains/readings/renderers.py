from __future__ import annotations

from app.domains.readings.daily_psychology import apply_daily_psychology
from app.domains.readings.knowledge import (
    LENS_ACTIONS,
    LENS_HOOKS,
    LENS_MANIFESTATIONS,
    InterpretationFrame,
    body_label,
    full_frame,
    semantic_arena,
    transit_copy,
    use_runtime_catalog_snapshot,
    vibe_frame,
)
from app.domains.readings.models import (
    BackgroundLens,
    ClaimSlot,
    ClaimSlotName,
    ClaimTemplateId,
    DerivedFactor,
    EvidenceClaim,
    EvidenceDisclosure,
    FactorKind,
    FactorSource,
    PlanMode,
    ReadingCandidate,
    ReadingPlan,
    SemanticArena,
    SemanticBlueprint,
    SemanticRequirement,
    SemanticSection,
)

DETERMINISTIC_RENDERER_VERSION = "deterministic-vi-v7"

_SIGN_LABELS = {
    "aries": "Bạch Dương",
    "taurus": "Kim Ngưu",
    "gemini": "Song Tử",
    "cancer": "Cự Giải",
    "leo": "Sư Tử",
    "virgo": "Xử Nữ",
    "libra": "Thiên Bình",
    "scorpio": "Bọ Cạp",
    "sagittarius": "Nhân Mã",
    "capricorn": "Ma Kết",
    "aquarius": "Bảo Bình",
    "pisces": "Song Ngư",
}
_ASPECT_LABELS = {
    "conjunction": "đồng cung",
    "opposition": "đối đỉnh",
    "square": "vuông",
    "trine": "tam hợp",
    "sextile": "lục hợp",
    "quincunx": "quincunx",
}
_ANGLE_LABELS = {
    "ascendant": "Cung Mọc",
    "midheaven": "Thiên Đỉnh",
}
_PHASE_LABELS = {
    "approaching": "tiến gần",
    "exact": "chính xác",
    "separating": "tách dần",
}
_MOTION_LABELS = {"direct": "thuận hành", "retrograde": "nghịch hành"}

_DAILY_ISSUE_MARKERS: dict[str, tuple[str, ...]] = {
    "missing-context": (
        "tin nhắn",
        "câu trả lời",
        "chưa rõ",
        "thông tin",
        "suy đoán",
        "mơ hồ",
        "đoán",
        "dữ kiện",
        "câu chữ",
        "dấu hiệu",
    ),
    "too-many-open-loops": ("đầu việc", "thông báo", "bận", "danh sách", "đổi việc"),
    "changed-plan": ("kế hoạch", "lịch", "đổi giờ", "thay đổi", "sát giờ"),
    "comparison-loop": ("so sánh", "người khác", "tiến độ", "thành tích", "tụt lại"),
    "automatic-caretaking": ("chăm sóc", "giúp", "đủ sức", "trách nhiệm", "người khác"),
    "decision-fatigue": ("lựa chọn", "phân vân", "chọn", "quyết định", "mệt"),
    "perfect-before-start": ("hoàn hảo", "bắt đầu", "chuẩn bị", "sửa", "chưa đủ"),
    "group-pressure": (
        "mọi người",
        "nhóm",
        "đồng ý",
        "ý kiến",
        "theo số đông",
        "tiếng nói",
        "dữ kiện",
        "bằng chứng",
        "bạn bè",
        "phương án",
    ),
    "avoid-small-conflict": ("khó chịu", "bất đồng", "nói", "im lặng", "xung đột"),
    "defend-old-choice": ("lựa chọn", "quyết định", "đổi ý", "dữ kiện", "bảo vệ"),
}

_ARENA_REQUIREMENT_MARKERS: dict[SemanticArena, tuple[str, ...]] = {
    SemanticArena.GENERAL: ("việc", "chuyện", "điều", "phản xạ", "tình huống"),
    SemanticArena.RELATIONSHIPS: ("quan hệ", "người kia", "hai người", "thân thiết"),
    SemanticArena.COMMUNICATION: ("nói", "câu", "nhắn", "trò chuyện", "giao tiếp"),
    SemanticArena.WORK: ("công việc", "đầu việc", "ưu tiên", "làm", "tiến độ"),
    SemanticArena.ENERGY: ("cơ thể", "mệt", "năng lượng", "quá tải", "sức"),
    SemanticArena.SELF_CARE: ("nghỉ", "cơ thể", "chăm mình", "sức", "nhịp"),
    SemanticArena.STRUCTURAL: ("cấu trúc", "nhịp", "phản ứng", "tình huống"),
}

_SEMANTIC_CONCEPT_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("data", ("dữ liệu", "dữ kiện", "giờ sinh", "nơi sinh", "chưa xác định")),
    ("safety", ("an toàn", "yên tâm", "hạ cảnh giác", "được bảo vệ")),
    ("recognition", ("trân trọng", "ghi nhận", "được thấy", "đóng góp")),
    ("control", ("quyền chủ động", "kiểm soát", "giữ chặt", "thế yếu")),
    ("tension", ("ma sát", "căng", "nén", "kéo và đẩy", "khó bị bỏ qua")),
    ("communication", ("nói rõ", "tự hiểu", "câu", "tin nhắn", "trò chuyện")),
    ("boundaries", ("ranh giới", "giới hạn", "không vượt qua", "khoảng riêng")),
    ("choice", ("lựa chọn", "quyết định", "chọn", "đổi hướng")),
    ("change", ("thay đổi", "đổi cách", "cách làm", "phản ứng mới")),
    ("energy", ("cơ thể", "mệt", "quá tải", "sức", "năng lượng")),
    ("care", ("chăm sóc", "giúp", "dịu", "tử tế", "nhu cầu")),
)


def _semantic_requirements(frame: InterpretationFrame) -> tuple[SemanticRequirement, ...]:
    scene_parts = frame.scene_key.split(":")
    if len(scene_parts) >= 2 and scene_parts[0] == "psychology":
        issue_key = scene_parts[1]
        markers = _DAILY_ISSUE_MARKERS.get(issue_key)
        if markers is not None:
            return (
                SemanticRequirement(
                    key=f"daily.{issue_key}",
                    section=SemanticSection.MANIFESTATION,
                    markers=markers,
                ),
            )
    concepts = tuple(
        SemanticRequirement(
            key=f"concept.{section.value}.{key}",
            section=section,
            markers=markers,
        )
        for section, text in (
            (SemanticSection.THESIS, frame.thesis.casefold()),
            (SemanticSection.MANIFESTATION, frame.manifestation.casefold()),
            (SemanticSection.MICRO_ACTION, frame.micro_action.casefold()),
        )
        for key, markers in _SEMANTIC_CONCEPT_MARKERS
        if any(marker in text for marker in markers)
    )
    if concepts:
        return concepts[:6]
    return (
        SemanticRequirement(
            key=f"arena.{frame.arena.value}",
            markers=_ARENA_REQUIREMENT_MARKERS[frame.arena],
        ),
    )


def _body(value: str) -> str:
    return body_label(value)


def _sign(value: str) -> str:
    return _SIGN_LABELS.get(value, value.replace("_", " ").title())


def _slot(name: ClaimSlotName, value: str) -> ClaimSlot:
    return ClaimSlot(name=name, value=value)


def canonical_evidence_claim(factor: DerivedFactor) -> EvidenceClaim:
    """Join a closed claim template using only canonical factor identifiers."""

    parts = factor.id.split(":")
    slots: tuple[ClaimSlot, ...]
    display: str
    template: ClaimTemplateId
    if factor.kind is FactorKind.DATE_ONLY_VIBE:
        status = parts[3]
        signs = ", ".join(_sign(item) for item in parts[4].split(","))
        slots = (
            _slot(ClaimSlotName.BODY, _body("sun")),
            _slot(ClaimSlotName.STATUS, status),
            _slot(ClaimSlotName.SIGN, signs),
        )
        display = f"{_body('sun')}: {signs} (chỉ từ ngày sinh)"
        template = ClaimTemplateId.DATE_ONLY_VIBE
    elif factor.kind is FactorKind.PLANET_PLACEMENT:
        body, sign = parts[1], parts[3]
        degree_ref = next(
            (ref for ref in factor.evidence_refs if ":degree_in_sign:" in ref),
            None,
        )
        motion_ref = next(
            (ref for ref in factor.evidence_refs if ":motion:" in ref),
            None,
        )
        degree = degree_ref.rsplit(":", 1)[1] if degree_ref else None
        motion = motion_ref.rsplit(":", 1)[1] if motion_ref else None
        slots = (
            _slot(ClaimSlotName.BODY, _body(body)),
            _slot(ClaimSlotName.SIGN, _sign(sign)),
            *((_slot(ClaimSlotName.DEGREE, degree),) if degree is not None else ()),
            *(
                (_slot(ClaimSlotName.MOTION, _MOTION_LABELS.get(motion, motion)),)
                if motion is not None
                else ()
            ),
        )
        detail = f", {degree}°" if degree is not None else ""
        if motion is not None:
            detail = f"{detail} ({_MOTION_LABELS.get(motion, motion)})"
        display = f"{_body(body)} ở {_sign(sign)}{detail}"
        template = ClaimTemplateId.PLANET_IN_SIGN
    elif factor.kind is FactorKind.HOUSE_PLACEMENT:
        body, house = parts[1], parts[3]
        slots = (
            _slot(ClaimSlotName.BODY, _body(body)),
            _slot(ClaimSlotName.HOUSE, house),
        )
        display = f"{_body(body)} ở Nhà {house}"
        template = ClaimTemplateId.PLANET_IN_HOUSE
    elif factor.kind is FactorKind.ANGLE:
        angle, longitude = parts[2], parts[4]
        slots = (
            _slot(ClaimSlotName.ANGLE, _ANGLE_LABELS.get(angle, angle)),
            _slot(ClaimSlotName.LONGITUDE, longitude),
        )
        display = f"{_ANGLE_LABELS.get(angle, angle)} tại {longitude}°"
        template = ClaimTemplateId.ANGLE_LONGITUDE
    elif factor.kind is FactorKind.NATAL_ASPECT:
        body_a, aspect, body_b, orb = parts[2], parts[3], parts[4], parts[6]
        slots = (
            _slot(ClaimSlotName.BODY_A, _body(body_a)),
            _slot(ClaimSlotName.BODY_B, _body(body_b)),
            _slot(ClaimSlotName.ASPECT, _ASPECT_LABELS.get(aspect, aspect)),
            _slot(ClaimSlotName.ORB, orb),
        )
        display = (
            f"{_body(body_a)} {_ASPECT_LABELS.get(aspect, aspect)} {_body(body_b)} (orb {orb}°)"
        )
        template = ClaimTemplateId.NATAL_ASPECT
    elif factor.kind is FactorKind.NAKSHATRA:
        body, pada = parts[1], parts[5]
        name_ref = next(
            ref for ref in factor.evidence_refs if ref.startswith("jyotish:nakshatra:name:")
        )
        nakshatra = name_ref.removeprefix("jyotish:nakshatra:name:")
        slots = (
            _slot(ClaimSlotName.BODY, _body(body)),
            _slot(ClaimSlotName.NAKSHATRA, nakshatra),
            _slot(ClaimSlotName.PADA, pada),
        )
        display = f"{_body(body)} ở Nakshatra {nakshatra}, pada {pada}"
        template = ClaimTemplateId.NAKSHATRA_POSITION
    elif factor.kind is FactorKind.GRAHA_DRISHTI:
        body_a, body_b, houses_apart, kind = parts[2], parts[3], parts[5], parts[6]
        slots = (
            _slot(ClaimSlotName.BODY_A, _body(body_a)),
            _slot(ClaimSlotName.BODY_B, _body(body_b)),
            _slot(ClaimSlotName.HOUSES_APART, houses_apart),
            _slot(ClaimSlotName.DRISHTI_KIND, kind),
        )
        display = f"Drishti {kind}: {_body(body_a)} → {_body(body_b)} ({houses_apart} nhà)"
        template = ClaimTemplateId.GRAHA_DRISHTI
    elif factor.kind is FactorKind.TRANSIT_CONTACT:
        body_a, aspect, body_b, orb, phase = (
            parts[1],
            parts[2],
            parts[4],
            parts[6],
            parts[8],
        )
        slots = (
            _slot(ClaimSlotName.BODY_A, _body(body_a)),
            _slot(ClaimSlotName.BODY_B, _body(body_b)),
            _slot(ClaimSlotName.ASPECT, _ASPECT_LABELS.get(aspect, aspect)),
            _slot(ClaimSlotName.ORB, orb),
            _slot(ClaimSlotName.PHASE, _PHASE_LABELS.get(phase, phase)),
        )
        display = (
            f"{_body(body_a)} đang {_ASPECT_LABELS.get(aspect, aspect)} {_body(body_b)} "
            f"(orb {orb}°, pha {_PHASE_LABELS.get(phase, phase)})"
        )
        template = ClaimTemplateId.TRANSIT_CONTACT
    else:  # pragma: no cover - FactorKind is a closed enum and every member is handled.
        raise ValueError(f"unsupported factor kind: {factor.kind.value}")
    return EvidenceClaim(
        factor_ref=factor.id,
        template_id=template,
        slots=slots,
        display_text=display,
    )


class DeterministicVietnameseRenderer:
    """Production fallback renderer: local, deterministic, and fact-closed."""

    version = DETERMINISTIC_RENDERER_VERSION

    def render(self, plan: ReadingPlan) -> ReadingCandidate:
        with use_runtime_catalog_snapshot() as catalog:
            return self._render_snapshot(plan, catalog.version)

    def _render_snapshot(self, plan: ReadingPlan, catalog_version: str | None) -> ReadingCandidate:
        if plan.mode is PlanMode.VIBE_FALLBACK:
            frame = vibe_frame(plan)
            hook, thesis, manifestation, micro_action = (
                frame.hook,
                frame.thesis,
                frame.manifestation,
                frame.micro_action,
            )
        elif plan.mode is PlanMode.LIMITED:
            frame = self._limited_frame(plan)
            hook, thesis, manifestation, micro_action = (
                frame.hook,
                frame.thesis,
                frame.manifestation,
                frame.micro_action,
            )
        else:
            frame = full_frame(plan)
            hook, thesis, manifestation, micro_action = (
                frame.hook,
                frame.thesis,
                frame.manifestation,
                frame.micro_action,
            )

        frame = apply_daily_psychology(plan, frame)
        hook, thesis, manifestation, micro_action = (
            frame.hook,
            frame.thesis,
            frame.manifestation,
            frame.micro_action,
        )

        transit_factor = next(
            (factor for factor in plan.factors if factor.source is FactorSource.TRANSIT),
            None,
        )
        transit = transit_copy(transit_factor) if transit_factor is not None else None
        claims = self._evidence_claims(plan, transit_factor, frame)
        renderer_version = (
            f"{self.version}+content-{catalog_version}"
            if catalog_version is not None
            else self.version
        )
        candidate = ReadingCandidate(
            renderer_version=renderer_version,
            plan_hash=plan.plan_hash,
            hook=hook,
            thesis=thesis,
            manifestation=manifestation,
            transit=transit,
            micro_action=micro_action,
            evidence=EvidenceDisclosure(claims=claims),
            semantic_blueprint=SemanticBlueprint(
                arena=frame.arena,
                mechanism_key=frame.mechanism_key,
                scene_key=frame.scene_key,
                action_key=frame.action_key,
                hook=hook,
                thesis=thesis,
                manifestation=manifestation,
                micro_action=micro_action,
                evidence_factor_refs=frame.evidence_factor_refs,
                requirements=_semantic_requirements(frame),
            ),
        )
        if (
            transit_factor is not None
            and transit is not None
            and not plan.composition.accepts(candidate.natal_user_prose, transit)
        ):
            candidate = candidate.model_copy(
                update={
                    "transit": None,
                    "evidence": EvidenceDisclosure(
                        claims=tuple(
                            claim for claim in claims if claim.factor_ref != transit_factor.id
                        )
                    ),
                }
            )
        return candidate

    @staticmethod
    def _limited_frame(plan: ReadingPlan) -> InterpretationFrame:
        hook = "Chưa cần đoán cho đầy trang."
        manifestation = (
            "Giữ phần trống này trung thực sẽ hữu ích hơn một đoạn nghe có vẻ riêng nhưng lại "
            "không bám vào lá số của bạn."
        )
        micro_action = (
            "Bạn có thể bổ sung giờ sinh chính xác và nơi sinh khi sẵn sàng; Lá sẽ đọc lại từ "
            "đầu với dữ liệu đó."
        )
        lens = plan.background_lens
        if lens is not None and lens is not BackgroundLens.AUTO:
            hook = f"{LENS_HOOKS[lens]}, Lá chưa cần đoán cho đầy trang."
            manifestation = (
                f"Bạn đang muốn soi điều dễ xảy ra {LENS_MANIFESTATIONS[lens]}. "
                "Dữ kiện hiện tại chưa đủ để nối bối cảnh đó với một đặc điểm riêng có căn cứ."
            )
            micro_action = (
                f"Trong lúc chưa bổ sung giờ và nơi sinh, bạn có thể {LENS_ACTIONS[lens]}. "
                "Khi dữ liệu đủ, Lá sẽ đọc lại từ đầu thay vì giữ kết luận tạm này."
            )
        return InterpretationFrame(
            hook=hook,
            thesis="Chưa đủ dữ liệu để Lá tạo một bản tổng hợp có căn cứ.",
            manifestation=manifestation,
            micro_action=micro_action,
            evidence_factor_refs=(),
            knowledge_refs=("mode:limited",),
            arena=semantic_arena(lens),
            mechanism_key="limited-data",
            scene_key=f"{semantic_arena(lens).value}:insufficient-data",
            action_key="complete-birth-data",
        )

    @staticmethod
    def _evidence_claims(
        plan: ReadingPlan,
        transit_factor: DerivedFactor | None,
        frame: InterpretationFrame | None,
    ) -> tuple[EvidenceClaim, ...]:
        factor_by_id = {factor.id: factor for factor in plan.factors}
        selected_ids = list(frame.evidence_factor_refs if frame else plan.hero_factor_refs)
        if transit_factor is not None:
            selected_ids.append(transit_factor.id)
        return tuple(
            canonical_evidence_claim(factor_by_id[factor_id])
            for factor_id in dict.fromkeys(selected_ids)
        )
