"""Versioned, paraphrased relationship knowledge registry.

This module intentionally stores no book excerpts. Source concepts only guide
conditional reflection and two-person prompts; they are not diagnostic facts or
matching features.
"""

from hashlib import sha256

from app.domains.astro.models import RelationshipDimension, RelationshipDimensionEvidence
from app.domains.relationships.models import (
    BookSource,
    EditorialConcept,
    EvidenceClass,
    RelationshipEditorialPlan,
    RelationshipPrompt,
    RelationshipVoice,
    VoiceProfile,
)

RELATIONSHIP_KNOWLEDGE_VERSION = "relationship-corpus-v2-2026-09-17"

_ALWAYS_PROHIBITED = (
    "diagnose either person or assign an attachment/mental-health label",
    "infer traits, trauma, intent, orientation, consent, abuse or willingness from behavior",
    "rank, reject or recommend a candidate automatically",
    "tell a user to stay, leave, confront, have sex, spend money or ignore safety",
)

BOOK_SOURCES: tuple[BookSource, ...] = (
    BookSource(
        source_id="attached-levine-heller",
        title="Attached",
        authors=("Amir Levine", "Rachel Heller"),
        evidence_class=EvidenceClass.RELATIONSHIP_PSYCHOLOGY,
        official_url=(
            "https://www.penguinrandomhouse.com/books/303069/"
            "attached-by-amir-levine-md-and-rachel-sf-heller-ma/"
        ),
        concept_ids=("closeness_needs", "clear_reassurance"),
        allowed_uses=("offer language for discussing closeness and reassurance needs",),
        prohibited_uses=_ALWAYS_PROHIBITED,
    ),
    BookSource(
        source_id="hold-me-tight-johnson",
        title="Hold Me Tight",
        authors=("Sue Johnson",),
        evidence_class=EvidenceClass.RELATIONSHIP_PSYCHOLOGY,
        official_url="https://www.drsuejohnson.com/books/",
        concept_ids=("connection_cycle", "repair_reach"),
        allowed_uses=("invite both people to notice a recurring connection cycle",),
        prohibited_uses=_ALWAYS_PROHIBITED,
    ),
    BookSource(
        source_id="seven-principles-gottman-silver",
        title="The Seven Principles for Making Marriage Work",
        authors=("John Gottman", "Nan Silver"),
        evidence_class=EvidenceClass.RELATIONSHIP_PSYCHOLOGY,
        official_url=(
            "https://www.gottman.com/product/the-seven-principles-for-making-marriage-work/"
        ),
        concept_ids=("know_the_person", "turn_toward", "repair_attempt", "shared_meaning"),
        allowed_uses=("generate mutual curiosity and repair prompts",),
        prohibited_uses=_ALWAYS_PROHIBITED,
    ),
    BookSource(
        source_id="eight-dates-gottman-et-al",
        title="Eight Dates",
        authors=("John Gottman", "Julie Schwartz Gottman", "Doug Abrams", "Rachel Carlton Abrams"),
        evidence_class=EvidenceClass.RELATIONSHIP_PSYCHOLOGY,
        official_url="https://www.gottman.com/product/eight-dates/",
        concept_ids=("values_conversation", "play_and_growth", "boundaried_intimacy"),
        allowed_uses=("offer consented conversation themes, not compatibility tests",),
        prohibited_uses=_ALWAYS_PROHIBITED,
    ),
    BookSource(
        source_id="how-to-not-die-alone-ury",
        title="How to Not Die Alone",
        authors=("Logan Ury",),
        evidence_class=EvidenceClass.DATING_DECISION_SCIENCE,
        official_url=(
            "https://www.simonandschuster.com/books/How-to-Not-Die-Alone/Logan-Ury/9781982120634"
        ),
        concept_ids=("observable_experiment", "spark_is_not_evidence"),
        allowed_uses=("encourage small observable experiments and revisable choices",),
        prohibited_uses=_ALWAYS_PROHIBITED,
    ),
    BookSource(
        source_id="nonviolent-communication-rosenberg",
        title="Nonviolent Communication",
        authors=("Marshall B. Rosenberg",),
        evidence_class=EvidenceClass.COMMUNICATION_PRACTICE,
        official_url="https://www.cnvc.org/store/nonviolent-communication-a-language-of-life",
        concept_ids=("observation_feeling_need_request", "clean_request"),
        allowed_uses=("structure a low-pressure, specific request",),
        prohibited_uses=_ALWAYS_PROHIBITED,
    ),
    BookSource(
        source_id="person-to-person-astrology-arroyo",
        title="Person-to-Person Astrology",
        authors=("Stephen Arroyo",),
        evidence_class=EvidenceClass.ASTROLOGY_TRADITION,
        official_url=(
            "https://www.penguinrandomhouse.com/books/5118/"
            "person-to-person-astrology-by-stephen-arroyo/"
        ),
        concept_ids=("planetary_needs", "elemental_exchange"),
        allowed_uses=("map inspectable chart facts to conditional needs language",),
        prohibited_uses=_ALWAYS_PROHIBITED,
    ),
    BookSource(
        source_id="synastry-davison",
        title="Synastry: Understanding Human Relations Through Astrology",
        authors=("Ronald Davison",),
        evidence_class=EvidenceClass.ASTROLOGY_TRADITION,
        official_url="https://books.google.com/books/about/Synastry.html?id=QwySOAAACAAJ",
        concept_ids=("cross_chart_contacts", "house_interchange"),
        allowed_uses=("explain strict cross-aspects and bidirectional house overlays",),
        prohibited_uses=_ALWAYS_PROHIBITED,
    ),
    BookSource(
        source_id="planets-in-composite-hand",
        title="Planets in Composite",
        authors=("Robert Hand",),
        evidence_class=EvidenceClass.ASTROLOGY_TRADITION,
        official_url=(
            "https://www.schiffermilitary.com/collections/all-schiffer/"
            "products/planets-in-composite"
        ),
        concept_ids=("relationship_third_pattern", "composite_aspects"),
        allowed_uses=("frame Composite as a symbolic shared pattern, never either person",),
        prohibited_uses=_ALWAYS_PROHIBITED,
    ),
    BookSource(
        source_id="light-on-relationships-defouw-svoboda",
        title="Light on Relationships",
        authors=("Hart de Fouw", "Robert E. Svoboda"),
        evidence_class=EvidenceClass.ASTROLOGY_TRADITION,
        official_url="https://redwheelweiser.com/book/light-on-relationships-9781578631483/",
        concept_ids=("jyotish_free_will", "strength_and_challenge"),
        allowed_uses=("document factual Jyotish relationship research with free-will framing",),
        prohibited_uses=_ALWAYS_PROHIBITED,
    ),
)

EDITORIAL_CONCEPTS: tuple[EditorialConcept, ...] = (
    EditorialConcept(
        concept_id="closeness_needs",
        label="Nói mức gần gũi mình cần",
        source_ids=("attached-levine-heller",),
        dimensions=(RelationshipDimension.EMOTIONAL, RelationshipDimension.RELATING),
        prompt_pattern=(
            "Mỗi người nói một mức gần gũi mình thấy dễ chịu hôm nay, không bắt người kia đoán."
        ),
        safety_boundary=(
            "Never assign an attachment style or frame one need as healthier than another."
        ),
    ),
    EditorialConcept(
        concept_id="clear_reassurance",
        label="Xin một tín hiệu rõ",
        source_ids=("attached-levine-heller",),
        dimensions=(RelationshipDimension.EMOTIONAL, RelationshipDimension.COMMUNICATION),
        prompt_pattern=(
            "Nếu đang không chắc, thử xin một tín hiệu cụ thể có thể trả lời được thay vì thử lòng."
        ),
        safety_boundary=(
            "Reassurance is optional and must not become monitoring, pressure or proof of love."
        ),
    ),
    EditorialConcept(
        concept_id="connection_cycle",
        label="Nhìn vòng lặp, không quy lỗi",
        source_ids=("hold-me-tight-johnson",),
        dimensions=(RelationshipDimension.EMOTIONAL, RelationshipDimension.FRICTION),
        prompt_pattern=(
            "Cùng gọi tên vòng lặp vừa xảy ra: một người làm gì, người kia phản ứng ra sao, "
            "rồi nó quay lại thế nào."
        ),
        safety_boundary=(
            "Describe an interaction cycle conditionally; never diagnose, excuse harm or "
            "assign blame."
        ),
    ),
    EditorialConcept(
        concept_id="repair_reach",
        label="Đưa một nhịp quay lại",
        source_ids=("hold-me-tight-johnson",),
        dimensions=(RelationshipDimension.EMOTIONAL, RelationshipDimension.COMMUNICATION),
        prompt_pattern=(
            "Thử một câu quay lại ngắn: điều mình muốn bảo vệ và điều mình muốn hiểu thêm ở bạn."
        ),
        safety_boundary="Repair is never required when a person feels unsafe or wants distance.",
    ),
    EditorialConcept(
        concept_id="know_the_person",
        label="Cập nhật bản đồ về nhau",
        source_ids=("seven-principles-gottman-silver",),
        dimensions=(RelationshipDimension.COMMUNICATION, RelationshipDimension.RELATING),
        prompt_pattern=(
            "Hỏi một điều gần đây đã đổi trong lịch, mối bận tâm hoặc điều người kia đang mong chờ."
        ),
        safety_boundary="Curiosity must allow privacy and a genuine choice not to answer.",
    ),
    EditorialConcept(
        concept_id="clean_request",
        label="Nói điều có thể trả lời",
        source_ids=("nonviolent-communication-rosenberg",),
        dimensions=(RelationshipDimension.COMMUNICATION,),
        prompt_pattern="Thử nói một điều bạn quan sát được, điều bạn cần, rồi hỏi một câu cụ thể.",
        safety_boundary="A request must allow a genuine no and never pressure disclosure.",
    ),
    EditorialConcept(
        concept_id="turn_toward",
        label="Bắt một tín hiệu nhỏ",
        source_ids=("seven-principles-gottman-silver",),
        dimensions=(RelationshipDimension.EMOTIONAL, RelationshipDimension.RELATING),
        prompt_pattern="Mỗi người kể một tín hiệu quan tâm nhỏ mà mình dễ nhận ra nhất.",
        safety_boundary="Do not imply silence or delay proves rejection.",
    ),
    EditorialConcept(
        concept_id="observable_experiment",
        label="Thử nhỏ, xem thật",
        source_ids=("how-to-not-die-alone-ury",),
        dimensions=(RelationshipDimension.DRIVE, RelationshipDimension.GROWTH),
        prompt_pattern="Chọn một cuộc hẹn hoặc câu hỏi nhỏ; sau đó tự kiểm chứng cảm giác thật.",
        safety_boundary="Never frame the experiment as a test the other person must pass.",
    ),
    EditorialConcept(
        concept_id="repair_attempt",
        label="Quay lại sau va chạm",
        source_ids=("seven-principles-gottman-silver",),
        dimensions=(RelationshipDimension.FRICTION, RelationshipDimension.COMMUNICATION),
        prompt_pattern="Nếu câu chuyện nóng lên, thống nhất một câu để tạm dừng và giờ quay lại.",
        safety_boundary=(
            "Safety and boundaries override repair; never normalize intimidation or abuse."
        ),
    ),
    EditorialConcept(
        concept_id="values_conversation",
        label="So điều quan trọng",
        source_ids=("eight-dates-gottman-et-al",),
        dimensions=(RelationshipDimension.RELATING, RelationshipDimension.GROWTH),
        prompt_pattern="Mỗi người chọn một điều mình muốn giữ nguyên và một điều còn linh hoạt.",
        safety_boundary="Differences are information, not proof of incompatibility.",
    ),
    EditorialConcept(
        concept_id="shared_meaning",
        label="Đặt tên điều hai người cùng xây",
        source_ids=("seven-principles-gottman-silver",),
        dimensions=(RelationshipDimension.RELATING, RelationshipDimension.GROWTH),
        prompt_pattern=(
            "Mỗi người kể một nghi thức nhỏ hoặc giá trị muốn giữ nếu mối quan hệ tiếp tục lớn lên."
        ),
        safety_boundary=(
            "Shared meaning is co-created; never prescribe commitment or a relationship label."
        ),
    ),
    EditorialConcept(
        concept_id="play_and_growth",
        label="Chừa chỗ cho vui và mới",
        source_ids=("eight-dates-gottman-et-al",),
        dimensions=(RelationshipDimension.DRIVE, RelationshipDimension.GROWTH),
        prompt_pattern=(
            "Chọn một việc mới đủ nhỏ để cả hai có thể thử, rồi nói trước điều gì sẽ khiến "
            "nó vui thay vì thành bài test."
        ),
        safety_boundary="Do not pressure novelty, spending, travel or physical intimacy.",
    ),
    EditorialConcept(
        concept_id="boundaried_intimacy",
        label="Gần nhưng vẫn có ranh giới",
        source_ids=("eight-dates-gottman-et-al",),
        dimensions=(RelationshipDimension.EMOTIONAL, RelationshipDimension.RELATING),
        prompt_pattern=(
            "Mỗi người nói một điều giúp mình thấy gần hơn và một ranh giới cần được tôn trọng."
        ),
        safety_boundary=(
            "Consent must be ongoing, specific and reversible; never infer willingness."
        ),
    ),
    EditorialConcept(
        concept_id="spark_is_not_evidence",
        label="Đừng bắt tia lửa làm hết việc",
        source_ids=("how-to-not-die-alone-ury",),
        dimensions=(RelationshipDimension.DRIVE, RelationshipDimension.GROWTH),
        prompt_pattern=(
            "Tách cảm giác hút ban đầu khỏi ba điều quan sát được: cách giữ lời, "
            "cách lắng nghe và cách tôn trọng ranh giới."
        ),
        safety_boundary=(
            "Do not dismiss attraction or convert observations into an automated verdict."
        ),
    ),
    EditorialConcept(
        concept_id="observation_feeling_need_request",
        label="Tách chuyện đã xảy ra khỏi suy diễn",
        source_ids=("nonviolent-communication-rosenberg",),
        dimensions=(RelationshipDimension.COMMUNICATION, RelationshipDimension.FRICTION),
        prompt_pattern=(
            "Nói lần lượt điều quan sát được, cảm giác của mình, điều mình cần và một đề nghị "
            "có thể nhận câu không."
        ),
        safety_boundary=(
            "Do not use the structure to sanitize blame, demand disclosure or override a no."
        ),
    ),
    EditorialConcept(
        concept_id="planetary_needs",
        label="Hai nhu cầu đang lên tiếng",
        source_ids=("person-to-person-astrology-arroyo",),
        dimensions=(
            RelationshipDimension.EMOTIONAL,
            RelationshipDimension.RELATING,
            RelationshipDimension.DRIVE,
        ),
        prompt_pattern=(
            "Từ contact đang xét, gọi tên hai nhu cầu có thể cùng xuất hiện rồi mời mỗi người "
            "tự kiểm chứng nhu cầu của mình."
        ),
        safety_boundary=(
            "Planet symbols are reflective hypotheses, never personality facts or consent signals."
        ),
    ),
    EditorialConcept(
        concept_id="elemental_exchange",
        label="Đổi nhịp năng lượng",
        source_ids=("person-to-person-astrology-arroyo",),
        dimensions=(RelationshipDimension.COMMUNICATION, RelationshipDimension.RELATING),
        prompt_pattern=(
            "So hai nhịp biểu đạt đang khác nhau ở tốc độ, độ cụ thể hoặc khoảng riêng; "
            "chọn một cách dịch cho nhau."
        ),
        safety_boundary=(
            "Element language must not stereotype signs, genders or relationship roles."
        ),
    ),
    EditorialConcept(
        concept_id="cross_chart_contacts",
        label="Một điểm chạm giữa hai chart",
        source_ids=("synastry-davison",),
        dimensions=tuple(RelationshipDimension),
        prompt_pattern=(
            "Nêu đúng một cross-aspect, hai chức năng nó nối lại và một biểu hiện đời thường "
            "để cả hai kiểm chứng."
        ),
        safety_boundary=(
            "Always cite the exact contact and orb; no fate, soulmate or compatibility verdict."
        ),
    ),
    EditorialConcept(
        concept_id="house_interchange",
        label="Điểm chạm rơi vào vùng sống nào",
        source_ids=("synastry-davison",),
        dimensions=(RelationshipDimension.RELATING, RelationshipDimension.GROWTH),
        prompt_pattern=(
            "Nếu cả hai có giờ sinh đủ chính xác, mô tả vùng đời sống được kích hoạt "
            "theo hai chiều A→B và B→A."
        ),
        safety_boundary=(
            "Withhold the claim when either house set is ineligible; never infer private events."
        ),
    ),
    EditorialConcept(
        concept_id="relationship_third_pattern",
        label="Nhịp chung của mối quan hệ",
        source_ids=("planets-in-composite-hand",),
        dimensions=tuple(RelationshipDimension),
        prompt_pattern=(
            "Sau mutual, mô tả Composite như một nhịp chung cần hai người cùng kiểm chứng, "
            "không gán cho riêng ai."
        ),
        safety_boundary=(
            "Composite is a symbolic mathematical chart and is never used to rank or screen people."
        ),
    ),
    EditorialConcept(
        concept_id="composite_aspects",
        label="Cách nhịp chung tự vận hành",
        source_ids=("planets-in-composite-hand",),
        dimensions=(
            RelationshipDimension.EMOTIONAL,
            RelationshipDimension.COMMUNICATION,
            RelationshipDimension.FRICTION,
        ),
        prompt_pattern=(
            "Chọn một aspect Composite có bằng chứng mạnh, nêu nguồn lực và điểm dễ quá tay "
            "của chính nhịp chung."
        ),
        safety_boundary="Do not progress, return or predict from the Composite in launch content.",
    ),
    EditorialConcept(
        concept_id="jyotish_free_will",
        label="Dữ kiện không thay quyền chọn",
        source_ids=("light-on-relationships-defouw-svoboda",),
        dimensions=(RelationshipDimension.GROWTH,),
        prompt_pattern=(
            "Nếu lớp Jyotish đã qua expert gate, đặt dữ kiện cạnh một lựa chọn có thể "
            "thay đổi và một điều chưa đủ căn cứ."
        ),
        safety_boundary=(
            "Jyotish relationship copy remains disabled until expert review; never present "
            "karma as obligation."
        ),
    ),
    EditorialConcept(
        concept_id="strength_and_challenge",
        label="Nguồn lực đi cùng bài tập",
        source_ids=("light-on-relationships-defouw-svoboda",),
        dimensions=(RelationshipDimension.GROWTH, RelationshipDimension.FRICTION),
        prompt_pattern=(
            "Giữ đồng thời một nguồn lực và một điểm cần luyện; không cộng trừ thành điểm hợp nhau."
        ),
        safety_boundary=(
            "No Kuta score, deterministic marriage judgment or gendered role prescription."
        ),
    ),
)


VOICE_PROFILES: tuple[VoiceProfile, ...] = (
    VoiceProfile(
        voice=RelationshipVoice.STRAIGHT_WARM,
        label="Nói thẳng, không lạnh",
        description=(
            "Đi thẳng vào điều đáng chú ý, dùng ví dụ đời thường và chừa quyền tự kiểm chứng."
        ),
        sentence_budget=(4, 7),
        slang_budget=0,
        required_moves=("one concrete observation", "one reversible suggestion"),
        prohibited_moves=("verdict", "therapy voice", "mystical filler"),
    ),
    VoiceProfile(
        voice=RelationshipVoice.GENTLE_SPECIFIC,
        label="Mềm nhưng cụ thể",
        description="Giảm độ gắt của câu chữ nhưng không làm mờ dữ kiện, ranh giới hoặc hành động.",
        sentence_budget=(5, 8),
        slang_budget=0,
        required_moves=("conditional language", "specific boundary-aware prompt"),
        prohibited_moves=("vague reassurance", "infantilizing language", "verdict"),
    ),
    VoiceProfile(
        voice=RelationshipVoice.PLAYFUL_GROUNDED,
        label="Hơi cợt, vẫn có căn",
        description=(
            "Một chút dí dỏm hiện đại để dễ đọc; chart fact và ý chính vẫn đứng trước punchline."
        ),
        sentence_budget=(4, 7),
        slang_budget=1,
        required_moves=("evidence before wit", "one useful next question"),
        prohibited_moves=("forced slang", "mocking either person", "meme-only copy"),
    ),
    VoiceProfile(
        voice=RelationshipVoice.DEEP_DIVE,
        label="Đọc kỹ, có lớp lang",
        description=(
            "Nêu phương pháp, evidence và giới hạn trước khi tổng hợp thành câu hỏi hai người "
            "có thể dùng."
        ),
        sentence_budget=(8, 12),
        slang_budget=0,
        required_moves=("method provenance", "multiple evidence links", "explicit uncertainty"),
        prohibited_moves=("jargon without explanation", "scalar score", "prediction"),
    ),
)


def concepts_for_dimension(dimension: RelationshipDimension) -> tuple[EditorialConcept, ...]:
    return tuple(concept for concept in EDITORIAL_CONCEPTS if dimension in concept.dimensions)


def voice_profile(voice: RelationshipVoice) -> VoiceProfile:
    """Resolve only an explicit user choice; callers must never infer this from chart data."""

    return next(profile for profile in VOICE_PROFILES if profile.voice is voice)


def build_editorial_plan(
    dimensions: tuple[RelationshipDimensionEvidence, ...],
    *,
    voice: RelationshipVoice = RelationshipVoice.STRAIGHT_WARM,
    limit: int = 3,
) -> RelationshipEditorialPlan:
    """Turn inspectable relationship evidence into a traceable content plan.

    This function does not render a verdict. It selects diverse, source-bound
    prompts that a later content gate may express in the user's chosen voice.
    """

    if limit < 1 or limit > 3:
        raise ValueError("relationship editorial plan limit must be between 1 and 3")
    ranked = sorted(
        (item for item in dimensions if item.evidence_ids),
        key=lambda item: (-item.strongest_strength, -item.contact_count, item.dimension.value),
    )
    selected: list[RelationshipPrompt] = []
    used_concepts: set[str] = set()
    for evidence in ranked:
        available = tuple(
            concept
            for concept in concepts_for_dimension(evidence.dimension)
            if concept.concept_id not in used_concepts
        )
        if not available:
            continue
        seed = "|".join((evidence.dimension.value, *evidence.evidence_ids))
        index = int.from_bytes(sha256(seed.encode()).digest()[:4], "big") % len(available)
        concept = available[index]
        selected.append(
            RelationshipPrompt(
                dimension=evidence.dimension,
                concept_id=concept.concept_id,
                source_ids=concept.source_ids,
                evidence_ids=evidence.evidence_ids[:3],
                label=concept.label,
                prompt_pattern=concept.prompt_pattern,
                safety_boundary=concept.safety_boundary,
            )
        )
        used_concepts.add(concept.concept_id)
        if len(selected) == limit:
            break
    if not selected:
        raise ValueError("relationship editorial plan requires inspectable evidence")
    return RelationshipEditorialPlan(
        knowledge_version=RELATIONSHIP_KNOWLEDGE_VERSION,
        voice_profile=voice_profile(voice),
        prompts=tuple(selected),
        disclaimer=(
            "Đây là một góc để hai người tự kiểm chứng, không phải kết luận về độ hợp, "
            "ý định hay tương lai của mối quan hệ."
        ),
    )
