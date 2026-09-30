import logging
from asyncio import to_thread
from dataclasses import replace
from datetime import UTC, date, datetime, time
from enum import StrEnum
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.domains.astro.aspects import TRANSIT_ORB_VERSION, transit_orb_limit
from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    BodyName,
    DateOnlySunResult,
    NatalChart,
    TimePrecision,
    TransitPhase,
    TransitToNatalContact,
    ZodiacSign,
)
from app.domains.birth.errors import BirthProfileNotFound
from app.domains.birth.models import BirthSnapshotRecord
from app.domains.birth.repository import BirthRepository
from app.domains.daily.models import (
    AuraAwakening,
    DailyNoteRecord,
    DailyNoteSnapshot,
    FallbackReason,
    PersonaLabel,
    PersonaMode,
    SkyChapter,
    SourceLevel,
)
from app.domains.daily.repository import DailyNoteRepository
from app.domains.readings.knowledge import ASPECTS as INTERPRETATION_ASPECTS
from app.domains.readings.knowledge import PLANETS as INTERPRETATION_PLANETS

CONTENT_VERSION = "daily-note-v3"
PERSONA_VERSION = "persona-v2"
AURA_SCORING_VERSION = "aura-element-modality-v1"
SKY_CHAPTER_RANKING_VERSION = "sky-chapter-salience-v1"
PRODUCT_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")

logger = logging.getLogger(__name__)


class Element(StrEnum):
    FIRE = "fire"
    EARTH = "earth"
    AIR = "air"
    WATER = "water"


class Modality(StrEnum):
    CARDINAL = "cardinal"
    FIXED = "fixed"
    MUTABLE = "mutable"


PERSONA_LABELS = dict(
    zip(
        ZodiacSign,
        (
            PersonaLabel.HOT,
            PersonaLabel.STEADY,
            PersonaLabel.QUICK,
            PersonaLabel.SOFT,
            PersonaLabel.RADIANT,
            PersonaLabel.NEAT,
            PersonaLabel.CHARMING,
            PersonaLabel.DEEP,
            PersonaLabel.WANDERING,
            PersonaLabel.GROUNDED,
            PersonaLabel.DIFFERENT,
            PersonaLabel.DREAMY,
        ),
        strict=True,
    )
)

SIGN_NAMES = dict(
    zip(
        ZodiacSign,
        (
            "Bạch Dương",
            "Kim Ngưu",
            "Song Tử",
            "Cự Giải",
            "Sư Tử",
            "Xử Nữ",
            "Thiên Bình",
            "Bọ Cạp",
            "Nhân Mã",
            "Ma Kết",
            "Bảo Bình",
            "Song Ngư",
        ),
        strict=True,
    )
)

SIGN_ELEMENTS = {
    **{sign: Element.FIRE for sign in (ZodiacSign.ARIES, ZodiacSign.LEO, ZodiacSign.SAGITTARIUS)},
    **{sign: Element.EARTH for sign in (ZodiacSign.TAURUS, ZodiacSign.VIRGO, ZodiacSign.CAPRICORN)},
    **{sign: Element.AIR for sign in (ZodiacSign.GEMINI, ZodiacSign.LIBRA, ZodiacSign.AQUARIUS)},
    **{sign: Element.WATER for sign in (ZodiacSign.CANCER, ZodiacSign.SCORPIO, ZodiacSign.PISCES)},
}
SIGN_MODALITIES = {
    **{
        sign: Modality.CARDINAL
        for sign in (ZodiacSign.ARIES, ZodiacSign.CANCER, ZodiacSign.LIBRA, ZodiacSign.CAPRICORN)
    },
    **{
        sign: Modality.FIXED
        for sign in (ZodiacSign.TAURUS, ZodiacSign.LEO, ZodiacSign.SCORPIO, ZodiacSign.AQUARIUS)
    },
    **{
        sign: Modality.MUTABLE
        for sign in (ZodiacSign.GEMINI, ZodiacSign.VIRGO, ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES)
    },
}
ELEMENT_ORDER = (Element.FIRE, Element.EARTH, Element.AIR, Element.WATER)
MODALITY_ORDER = (Modality.CARDINAL, Modality.FIXED, Modality.MUTABLE)
REQUIRED_BODY_NAMES = frozenset(
    {
        BodyName.SUN,
        BodyName.MOON,
        BodyName.MERCURY,
        BodyName.VENUS,
        BodyName.MARS,
        BodyName.JUPITER,
        BodyName.SATURN,
        BodyName.URANUS,
        BodyName.NEPTUNE,
        BodyName.PLUTO,
        BodyName.TRUE_NODE,
        BodyName.CHIRON,
    }
)
BODY_WEIGHTS = {
    BodyName.SUN: 2.0,
    BodyName.MOON: 2.0,
    BodyName.MERCURY: 1.25,
    BodyName.VENUS: 1.25,
    BodyName.MARS: 1.25,
    BodyName.JUPITER: 1.0,
    BodyName.SATURN: 1.0,
    BodyName.URANUS: 0.5,
    BodyName.NEPTUNE: 0.5,
    BodyName.PLUTO: 0.5,
    BodyName.TRUE_NODE: 0.25,
    BodyName.CHIRON: 0.25,
}
AURA_LABELS = {
    (Element.FIRE, Modality.CARDINAL): PersonaLabel.RADIANT,
    (Element.FIRE, Modality.FIXED): PersonaLabel.HOT,
    (Element.FIRE, Modality.MUTABLE): PersonaLabel.WANDERING,
    (Element.EARTH, Modality.CARDINAL): PersonaLabel.STEADY,
    (Element.EARTH, Modality.FIXED): PersonaLabel.GROUNDED,
    (Element.EARTH, Modality.MUTABLE): PersonaLabel.NEAT,
    (Element.AIR, Modality.CARDINAL): PersonaLabel.CHARMING,
    (Element.AIR, Modality.FIXED): PersonaLabel.DIFFERENT,
    (Element.AIR, Modality.MUTABLE): PersonaLabel.QUICK,
    (Element.WATER, Modality.CARDINAL): PersonaLabel.SOFT,
    (Element.WATER, Modality.FIXED): PersonaLabel.DEEP,
    (Element.WATER, Modality.MUTABLE): PersonaLabel.DREAMY,
}
ELEMENT_NAMES = {
    Element.FIRE: "Lửa",
    Element.EARTH: "Đất",
    Element.AIR: "Khí",
    Element.WATER: "Nước",
}
MODALITY_NAMES = {
    Modality.CARDINAL: "Khởi xướng",
    Modality.FIXED: "Kiên định",
    Modality.MUTABLE: "Linh hoạt",
}

SIGN_COPY = dict(
    zip(
        ZodiacSign,
        (
            (
                "Đừng lao quá nhanh.",
                "Hôm nay cứ để lửa sáng, nhưng đừng bắt mình cháy thay mọi thứ.",
            ),
            ("Chậm lại cũng là tiến.", "Một điều mềm và chắc sẽ ở lại lâu hơn một quyết định vội."),
            (
                "Nói ít hơn một nhịp.",
                "Có vài câu chỉ thật sự hay khi mình để chúng nghỉ trong đầu trước.",
            ),
            (
                "Giữ tim, đừng gồng.",
                "Nếu hôm nay nhạy cảm hơn bình thường, đó không phải lỗi của bạn.",
            ),
            (
                "Sáng nhưng không cần diễn.",
                "Bạn không cần chứng minh ánh sáng của mình với người đang nhắm mắt.",
            ),
            ("Đủ tốt là đủ đi tiếp.", "Một chi tiết lệch không có nghĩa cả ngày này hỏng."),
            (
                "Đừng hòa mình tới biến mất.",
                "Êm đẹp không đáng nếu bạn phải giấu hết điều mình muốn.",
            ),
            ("Không cần mở hết bí mật.", "Giữ lại một phần cho mình cũng là một cách tự bảo vệ."),
            ("Đi xa, nhưng nhớ thân mình.", "Tự do không phải lúc nào cũng cần một cú nhảy lớn."),
            ("Đừng biến mình thành deadline.", "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo."),
            ("Khác biệt cũng cần được ôm.", "Ý tưởng lạ hôm nay có thể là lối thoát ngày mai."),
            (
                "Mơ, nhưng giữ một sợi dây.",
                "Cảm xúc có thể đi trước, còn bạn vẫn có quyền chọn nhịp.",
            ),
        ),
        strict=True,
    )
)

FULL_BODY_TEMPLATE = (
    "{compact} Hôm nay, bạn có thể bắt đầu bằng một khoảng dừng nhỏ trước điều đang kéo mình "
    "đi quá nhanh. Chọn một việc thật sự cần thiết, làm nó với nhịp vừa đủ, rồi để phần còn lại "
    "được chờ. Nếu cảm xúc đổi hướng, hãy quan sát thay vì vội gọi tên hay phán xét. Một cuộc trò "
    "chuyện chân thành, một cốc nước hoặc vài phút rời màn hình đều có thể giúp bạn trở về với "
    "mình. Note này chỉ là lời gợi ý để soi ngày hôm nay; quyết định cuối cùng vẫn thuộc về bạn."
)

AURA_COPY = {
    Element.FIRE: (
        "Sáng, nhưng đừng tự đốt mình.",
        "Bạn có lực để khởi động, còn phần sâu hơn trong bạn cần một nhịp an toàn "
        "trước khi lao tới.",
    ),
    Element.EARTH: (
        "Vững không có nghĩa là đứng yên.",
        "Bạn muốn điều có thể chạm và giữ, nhưng một phần khác đang xin phép được đổi nhịp.",
    ),
    Element.AIR: (
        "Đầu đã hiểu, tim chưa chắc.",
        "Bạn nhìn thấy nhiều hướng rất nhanh; hôm nay hãy để cảm xúc chọn điều đáng giữ lại.",
    ),
    Element.WATER: (
        "Cảm được nhiều, nói vừa đủ.",
        "Cảm giác có thể tới trước lời giải thích; đừng ép mình gọi tên mọi điều ngay lập tức.",
    ),
}

BODY_LABELS = {
    BodyName.SUN: "Mặt Trời",
    BodyName.MOON: "Mặt Trăng",
    BodyName.MERCURY: "Sao Thủy",
    BodyName.VENUS: "Sao Kim",
    BodyName.MARS: "Sao Hỏa",
    BodyName.JUPITER: "Sao Mộc",
    BodyName.SATURN: "Sao Thổ",
    BodyName.URANUS: "Thiên Vương",
    BodyName.NEPTUNE: "Hải Vương",
    BodyName.PLUTO: "Diêm Vương",
    BodyName.TRUE_NODE: "Nút Bắc",
    BodyName.MEAN_NODE: "Nút Bắc",
    BodyName.SOUTH_NODE: "Nút Nam",
    BodyName.CHIRON: "Chiron",
}
ASPECT_LABELS = {
    "conjunction": "gặp nhau",
    "sextile": "mở lối cho",
    "square": "kéo căng",
    "trine": "nâng đỡ",
    "opposition": "đối thoại với",
}
SKY_CHAPTER_DISCLAIMER = (
    "Dùng như một giả thuyết để quan sát hôm nay, không phải lý do để quyết định thay bạn."
)

CURRENT_LIFE_SCENARIOS = {
    BodyName.SUN: "khi bạn phải chọn việc nào thật sự đáng mang dấu tay của mình",
    BodyName.MOON: "khi một phản hồi được chờ trong lúc bạn còn chưa gọi tên được cảm xúc",
    BodyName.MERCURY: "khi bạn soạn rồi sửa một tin nhắn hoặc mở thêm tài liệu để né câu chính",
    BodyName.VENUS: "khi bạn muốn được trân trọng nhưng chưa nói rõ mình cần điều gì",
    BodyName.MARS: "khi một ranh giới bị chạm và cơ thể muốn phản ứng trước đầu óc",
}


class DailyNoteService:
    def __init__(
        self,
        repository: DailyNoteRepository,
        birth_repository: BirthRepository,
        engine: NatalChartEngine | None = None,
    ) -> None:
        self._repository = repository
        self._birth_repository = birth_repository
        self._engine = engine

    async def today(
        self,
        guest_id: UUID,
        *,
        today: date | None = None,
        observed_at: datetime | None = None,
    ) -> DailyNoteRecord:
        request_instant = observed_at or datetime.now(UTC)
        current_date = today or request_instant.astimezone(PRODUCT_TIMEZONE).date()
        chapter_instant = datetime.combine(current_date, time(hour=12), tzinfo=UTC)
        birth = await self._birth_repository.find_current(guest_id)
        if birth is None:
            raise BirthProfileNotFound
        snapshot = _snapshot_for(birth.result)
        persisted = await self._repository.get_or_create(
            DailyNoteRecord(
                id=uuid4(),
                guest_id=guest_id,
                note_date=current_date,
                title=snapshot.title,
                body=snapshot.body,
                full_body=snapshot.full_body,
                context_label=snapshot.context_label,
                content_version=snapshot.content_version,
                persona_mode=snapshot.persona_mode,
                persona_label=snapshot.persona_label,
                persona_version=snapshot.persona_version,
                source_level=snapshot.source_level,
                astrology_source_version=snapshot.astrology_source_version,
                fallback_used=snapshot.fallback_used,
                fallback_reason=snapshot.fallback_reason,
                chart_snapshot_id=birth.id,
                created_at=datetime.now(UTC),
            )
        )
        if (
            not isinstance(birth.result, NatalChart)
            or snapshot.persona_mode is not PersonaMode.AURA
        ):
            return persisted
        awakening = _awakening_for(birth.result)
        chapter = None
        if self._engine is not None and birth.result.time_precision is TimePrecision.EXACT:
            try:
                transits = await to_thread(
                    self._engine.calculate_transit_to_natal,
                    birth.result,
                    chapter_instant,
                )
                chapter = _chapter_for(transits.contacts, chapter_instant)
            except Exception:
                logger.exception("Sky Chapter calculation failed; returning the persisted note")
        return replace(persisted, awakening=awakening, sky_chapter=chapter)

    async def find_owned(self, guest_id: UUID, note_id: UUID) -> DailyNoteRecord:
        note = await self._repository.find(guest_id, note_id)
        if note is None:
            raise BirthProfileNotFound
        return note

    async def current_birth_snapshot(self, guest_id: UUID) -> BirthSnapshotRecord:
        """Expose the already owner-scoped source record to private application services."""

        birth = await self._birth_repository.find_current(guest_id)
        if birth is None:
            raise BirthProfileNotFound
        return birth


def _snapshot_for(result: DateOnlySunResult | NatalChart) -> DailyNoteSnapshot:
    source_version = _bounded_source_version(result.provenance.version)
    if isinstance(result, NatalChart):
        sun = next((body for body in result.bodies if body.body is BodyName.SUN), None)
        if sun is None:
            return _neutral_note(
                SourceLevel.NATAL_CHART, source_version, FallbackReason.MISSING_SUN
            )
        if (
            len(result.bodies) == len(REQUIRED_BODY_NAMES)
            and {body.body for body in result.bodies} == REQUIRED_BODY_NAMES
        ):
            if result.time_precision is not TimePrecision.EXACT:
                return _sign_note(
                    sun.sign,
                    SourceLevel.NATAL_CHART,
                    source_version,
                    fallback_reason=FallbackReason.INCOMPLETE_NATAL_CHART,
                )
            element, modality = _aura_dimensions(result, sun.sign)
            return _sign_note(
                sun.sign,
                SourceLevel.NATAL_CHART,
                source_version,
                persona_mode=PersonaMode.AURA,
                persona_label=AURA_LABELS[(element, modality)],
                context_label=(
                    f"{ELEMENT_NAMES[element]} · {MODALITY_NAMES[modality]} · "
                    f"Mặt Trời {SIGN_NAMES[sun.sign]}"
                ),
                chart=result,
                aura_element=element,
            )
        return _sign_note(
            sun.sign,
            SourceLevel.NATAL_CHART,
            source_version,
            fallback_reason=FallbackReason.INCOMPLETE_NATAL_CHART,
        )
    if result.status == "certain" and result.sign is not None:
        return _sign_note(result.sign, SourceLevel.DATE_ONLY_SUN, source_version)
    return _neutral_note(SourceLevel.DATE_ONLY_SUN, source_version, FallbackReason.AMBIGUOUS_SUN)


def _sign_note(
    sign: ZodiacSign,
    source_level: SourceLevel,
    source_version: str,
    *,
    persona_mode: PersonaMode = PersonaMode.VIBE,
    persona_label: PersonaLabel | None = None,
    context_label: str | None = None,
    fallback_reason: FallbackReason | None = None,
    chart: NatalChart | None = None,
    aura_element: Element | None = None,
) -> DailyNoteSnapshot:
    if persona_mode is PersonaMode.AURA:
        if chart is None or aura_element is None:
            raise ValueError("Aura note requires a complete natal chart")
        title, compact = AURA_COPY[aura_element]
        full_body = _aura_full_body(chart, aura_element, compact)
    else:
        title, compact = SIGN_COPY[sign]
        full_body = FULL_BODY_TEMPLATE.format(compact=compact)
    return DailyNoteSnapshot(
        title=title,
        body=compact,
        full_body=full_body,
        context_label=context_label or f"Mặt Trời {SIGN_NAMES[sign]}",
        content_version=CONTENT_VERSION,
        persona_mode=persona_mode,
        persona_label=persona_label or PERSONA_LABELS[sign],
        persona_version=PERSONA_VERSION,
        source_level=source_level,
        astrology_source_version=source_version,
        fallback_used=fallback_reason is not None,
        fallback_reason=fallback_reason,
    )


def _neutral_note(
    source_level: SourceLevel, source_version: str, reason: FallbackReason
) -> DailyNoteSnapshot:
    compact = (
        "Hôm nay cảm xúc có thể đi trước lý trí một nhịp. Cho mình vài phút trước "
        "khi nói điều sẽ phải giải thích cả tối."
    )
    return DailyNoteSnapshot(
        title="Đừng vội rep.",
        body=compact,
        full_body=FULL_BODY_TEMPLATE.format(compact=compact),
        context_label="Chưa chốt được cung Mặt Trời",
        content_version=CONTENT_VERSION,
        persona_mode=PersonaMode.VIBE,
        persona_label=PersonaLabel.SOFT,
        persona_version=PERSONA_VERSION,
        source_level=source_level,
        astrology_source_version=source_version,
        fallback_used=True,
        fallback_reason=reason,
    )


def _aura_dimensions(chart: NatalChart, sun_sign: ZodiacSign) -> tuple[Element, Modality]:
    element_scores = {item: 0.0 for item in ELEMENT_ORDER}
    modality_scores = {item: 0.0 for item in MODALITY_ORDER}
    for position in chart.bodies:
        weight = BODY_WEIGHTS.get(position.body, 0.0)
        element_scores[SIGN_ELEMENTS[position.sign]] += weight
        modality_scores[SIGN_MODALITIES[position.sign]] += weight

    def choose[T: StrEnum](scores: dict[T, float], order: tuple[T, ...], sun_value: T) -> T:
        highest = max(scores.values())
        tied = {item for item, score in scores.items() if score == highest}
        if sun_value in tied:
            return sun_value
        return next(item for item in order if item in tied)

    return (
        choose(element_scores, ELEMENT_ORDER, SIGN_ELEMENTS[sun_sign]),
        choose(modality_scores, MODALITY_ORDER, SIGN_MODALITIES[sun_sign]),
    )


def _bounded_source_version(version: str) -> str:
    normalized = version.strip()
    return normalized[:64] if normalized else "unknown"


def _personal_factor_labels(chart: NatalChart) -> tuple[str, ...]:
    factors = []
    for body in (BodyName.SUN, BodyName.MOON, BodyName.MERCURY, BodyName.VENUS, BodyName.MARS):
        try:
            position = chart.body(body)
        except KeyError:
            continue
        factors.append(f"{BODY_LABELS[body]} · {SIGN_NAMES[position.sign]}")
    return tuple(factors)


def _aura_full_body(chart: NatalChart, element: Element, compact: str) -> str:
    placements = {body.body: body for body in chart.bodies}
    sun = placements[BodyName.SUN]
    moon = placements[BodyName.MOON]
    mercury = placements[BodyName.MERCURY]
    venus = placements[BodyName.VENUS]
    mars = placements[BodyName.MARS]
    return (
        f"{compact} Mặt Trời {SIGN_NAMES[sun.sign]} cho bạn cách bước vào ngày mới, "
        f"còn Mặt Trăng {SIGN_NAMES[moon.sign]} giữ nhu cầu cảm xúc theo một nhịp riêng. "
        f"Sao Thủy {SIGN_NAMES[mercury.sign]} kể cách bạn gọi tên điều đang xảy ra; "
        f"Sao Kim {SIGN_NAMES[venus.sign]} nhắc điều thật sự quý, còn Sao Hỏa "
        f"{SIGN_NAMES[mars.sign]} cho thấy nơi năng "
        f"lượng muốn được dùng. Tổng hòa chart làm nguyên tố {ELEMENT_NAMES[element]} nổi bật, "
        "nhưng không phải nhãn cố định. Hôm nay, chọn một hành động thật với mình và chừa chỗ "
        "cho phần còn do dự. Nếu chưa rõ, dừng vài phút trước khi trả lời. "
        "Đây là gợi ý chiêm nghiệm, không phải dự đoán hay quyết định thay bạn."
    )


def _awakening_for(chart: NatalChart) -> AuraAwakening:
    return AuraAwakening(
        headline="Aura của bạn vừa thức tỉnh",
        summary=(
            "Note giờ được đọc từ cách các hành tinh cá nhân thương lượng với nhau, "
            "không còn chỉ từ cung Mặt Trời."
        ),
        factors=_personal_factor_labels(chart),
        precision_label=(
            "Chart chính xác theo giờ, nơi sinh và múi giờ đã chọn"
            if chart.time_precision is TimePrecision.EXACT
            else "Chart dùng khoảng giờ; các kết luận nhạy với House đã được giới hạn"
        ),
        scoring_version=AURA_SCORING_VERSION,
        confidence="high" if chart.time_precision is TimePrecision.EXACT else "limited",
    )


def _chapter_for(
    contacts: tuple[TransitToNatalContact, ...], observed_at: datetime
) -> SkyChapter | None:
    personal = {BodyName.SUN, BodyName.MOON, BodyName.MERCURY, BodyName.VENUS, BodyName.MARS}
    candidates = [contact for contact in contacts if contact.natal_body in personal]
    if not candidates:
        return None
    contact = max(candidates, key=_chapter_salience)
    phase_labels = {
        TransitPhase.APPROACHING: "Đang rõ dần",
        TransitPhase.EXACT: "Đang rõ nhất",
        TransitPhase.SEPARATING: "Đang hạ dần",
    }
    transit = BODY_LABELS[contact.transit_body]
    natal = BODY_LABELS[contact.natal_body]
    transit_meaning = INTERPRETATION_PLANETS[contact.transit_body.value]
    natal_meaning = INTERPRETATION_PLANETS[contact.natal_body.value]
    aspect_meaning = INTERPRETATION_ASPECTS.get(contact.kind)
    bridge = aspect_meaning.bridge if aspect_meaning else "đang cùng làm chủ đề này rõ hơn"
    scenario = CURRENT_LIFE_SCENARIOS[contact.natal_body]
    return SkyChapter(
        title="Món quà: một điều đáng để ý hôm nay",
        summary=(
            f"Nhu cầu {natal_meaning.drive} đang gặp một lực muốn {transit_meaning.drive}; "
            f"hai nhịp {bridge}. Ngoài đời, thử để ý {scenario}."
        ),
        phase=contact.phase,
        phase_label=phase_labels[contact.phase],
        signal_label=f"{transit} x {natal} · {ASPECT_LABELS.get(contact.kind, contact.kind)}",
        orb=contact.orb,
        observed_at=observed_at.astimezone(UTC),
        orb_policy_version=TRANSIT_ORB_VERSION,
        ranking_version=SKY_CHAPTER_RANKING_VERSION,
        disclaimer=SKY_CHAPTER_DISCLAIMER,
    )


def _chapter_salience(contact: TransitToNatalContact) -> tuple[float, float, str, str]:
    body_weight = {
        BodyName.SUN: 0.8,
        BodyName.MOON: 0.55,
        BodyName.MERCURY: 0.65,
        BodyName.VENUS: 0.7,
        BodyName.MARS: 0.75,
        BodyName.JUPITER: 1.0,
        BodyName.SATURN: 1.1,
        BodyName.URANUS: 1.15,
        BodyName.NEPTUNE: 1.15,
        BodyName.PLUTO: 1.2,
        BodyName.TRUE_NODE: 0.9,
        BodyName.MEAN_NODE: 0.9,
        BodyName.SOUTH_NODE: 0.9,
        BodyName.CHIRON: 0.8,
    }[contact.transit_body]
    natal_weight = 1.2 if contact.natal_body in {BodyName.SUN, BodyName.MOON} else 1.0
    maximum_orb = transit_orb_limit(contact.transit_body, contact.kind)
    exactness = max(0.0, 1.0 - contact.orb / maximum_orb)
    score = exactness * body_weight * natal_weight
    return (score, -contact.orb, contact.transit_body.value, contact.natal_body.value)
