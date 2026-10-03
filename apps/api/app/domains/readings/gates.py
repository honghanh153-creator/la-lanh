from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from app.domains.readings.models import (
    EVIDENCE_DISCLOSURE_TITLE,
    FULL_FRAMEWORK_DISCLOSURE,
    SHORT_DISCLAIMER,
    BackgroundLens,
    CandidateEvaluation,
    ClaimSlotName,
    FactorSource,
    GateFailureCode,
    GateName,
    GateReport,
    PlanMode,
    ReadingCandidate,
    ReadingPlan,
    SemanticArena,
    SemanticSection,
)
from app.domains.readings.renderers import canonical_evidence_claim

EVIDENCE_GATE_VERSION = "evidence-gate-vi-v1"
ANTI_INFLUENCE_GATE_VERSION = "anti-influence-gate-vi-v1"
EDITORIAL_GATE_VERSION = "editorial-gate-vi-v3"
MEANING_GATE_VERSION = "meaning-gate-vi-v1"
PRIVACY_GATE_VERSION = "privacy-gate-vi-v1"

_BODY_TERMS = (
    "mặt trời",
    "mặt trăng",
    "sao thủy",
    "sao kim",
    "sao hỏa",
    "sao mộc",
    "sao thổ",
    "thiên vương",
    "hải vương",
    "diêm vương",
    "nút bắc",
    "nút nam",
    "chiron",
)
_SIGN_TERMS = (
    "bạch dương",
    "kim ngưu",
    "song tử",
    "cự giải",
    "sư tử",
    "xử nữ",
    "thiên bình",
    "bọ cạp",
    "nhân mã",
    "ma kết",
    "bảo bình",
    "song ngư",
)
_ASPECT_TERMS = ("đồng cung", "đối đỉnh", "vuông", "tam hợp", "lục hợp", "quincunx")
_ANGLE_TERMS = ("cung mọc", "thiên đỉnh", "rising", "ascendant", "midheaven")
_PHASE_TERMS = ("tiến gần", "chính xác", "tách dần")


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", unicodedata.normalize("NFC", text).casefold())
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_marks.replace("đ", "d")


def _label_fold(text: str) -> str:
    """Normalize canonical Vietnamese labels without erasing meaningful accents."""

    return unicodedata.normalize("NFC", text).casefold()


def _report(gate: GateName, version: str, failures: Iterable[GateFailureCode]) -> GateReport:
    unique = tuple(dict.fromkeys(failures))
    return GateReport(gate=gate, version=version, passed=not unique, failure_codes=unique)


def _candidate_prose(candidate: ReadingCandidate) -> str:
    return "\n".join(candidate.all_user_prose)


def evidence_gate(plan: ReadingPlan, candidate: ReadingCandidate) -> GateReport:
    failures: list[GateFailureCode] = []
    required = (candidate.hook, candidate.thesis, candidate.manifestation, candidate.micro_action)
    if any(not section.strip() for section in required):
        failures.append(GateFailureCode.EVIDENCE_REQUIRED_PROSE)
    if candidate.plan_hash != plan.plan_hash:
        failures.append(GateFailureCode.EVIDENCE_PLAN_MISMATCH)
    if (
        candidate.evidence.title != EVIDENCE_DISCLOSURE_TITLE
        or candidate.evidence.framework_disclosure != FULL_FRAMEWORK_DISCLOSURE
        or candidate.disclaimer != SHORT_DISCLAIMER
    ):
        failures.append(GateFailureCode.EVIDENCE_DISCLOSURE)

    factor_by_id = {factor.id: factor for factor in plan.factors}
    canonical_claim_by_id = {factor.id: canonical_evidence_claim(factor) for factor in plan.factors}
    seen: set[str] = set()
    for claim in candidate.evidence.claims:
        factor = factor_by_id.get(claim.factor_ref)
        if (
            factor is None
            or claim.factor_ref in seen
            or claim != canonical_claim_by_id.get(claim.factor_ref)
        ):
            failures.append(GateFailureCode.EVIDENCE_UNSUPPORTED_CLAIM)
        seen.add(claim.factor_ref)

    if plan.mode is not PlanMode.LIMITED and not set(plan.hero_factor_refs).issubset(seen):
        failures.append(GateFailureCode.EVIDENCE_MISSING_HERO)

    transit_factors = tuple(
        factor for factor in plan.factors if factor.source is FactorSource.TRANSIT
    )
    claimed_transits = tuple(factor for factor in transit_factors if factor.id in seen)
    if candidate.transit is not None:
        if not candidate.transit.strip() or len(transit_factors) != 1 or len(claimed_transits) != 1:
            failures.append(GateFailureCode.EVIDENCE_UNEXPECTED_TRANSIT)
        elif not plan.composition.accepts(candidate.natal_user_prose, candidate.transit):
            failures.append(GateFailureCode.EVIDENCE_COMPOSITION)
    elif claimed_transits:
        failures.append(GateFailureCode.EVIDENCE_UNEXPECTED_TRANSIT)

    prose = _candidate_prose(candidate)
    folded_prose = _fold(prose)
    label_prose = _label_fold(prose)
    allowed_values = {
        _label_fold(slot.value) for claim in canonical_claim_by_id.values() for slot in claim.slots
    }
    universe = (*_BODY_TERMS, *_SIGN_TERMS, *_ASPECT_TERMS, *_ANGLE_TERMS)
    if any(
        re.search(rf"(?<!\w){re.escape(_label_fold(term))}(?!\w)", label_prose) is not None
        and _label_fold(term) not in allowed_values
        for term in universe
    ):
        failures.append(GateFailureCode.EVIDENCE_ASTRO_LABEL)
    canonical_label_sets = tuple(
        {_label_fold(slot.value) for slot in claim.slots}
        for claim in canonical_claim_by_id.values()
    )
    known_labels = {_label_fold(term) for term in universe}.intersection(allowed_values)
    for sentence in re.split(r"[.!?;\n]+", label_prose):
        mentioned = {
            label
            for label in known_labels
            if re.search(rf"(?<!\w){re.escape(label)}(?!\w)", sentence)
        }
        if len(mentioned) > 1 and not any(
            mentioned.issubset(claim_labels) for claim_labels in canonical_label_sets
        ):
            failures.append(GateFailureCode.EVIDENCE_UNSUPPORTED_CLAIM)
            break
    house_mentions = re.findall(r"\b(?:nha|house)\s*(\d{1,2})\b", folded_prose)
    allowed_houses = {
        _label_fold(slot.value)
        for claim in canonical_claim_by_id.values()
        for slot in claim.slots
        if slot.name is ClaimSlotName.HOUSE
    }
    if any(house not in allowed_houses for house in house_mentions):
        failures.append(GateFailureCode.EVIDENCE_ASTRO_LABEL)
    phase_mentions = re.findall(r"\bpha\s+(tien gan|chinh xac|tach dan)\b", folded_prose)
    if any(phase not in allowed_values for phase in phase_mentions):
        failures.append(GateFailureCode.EVIDENCE_ASTRO_LABEL)
    if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b", prose):
        failures.append(GateFailureCode.EVIDENCE_UNSUPPORTED_TIMING)
    if re.search(r"\b(?:trong|suot)\s+\d+\s+(?:ngay|tuan|thang|nam)\b", folded_prose):
        failures.append(GateFailureCode.EVIDENCE_UNSUPPORTED_TIMING)
    return _report(GateName.EVIDENCE, EVIDENCE_GATE_VERSION, failures)


def _without_safe_examples(text: str) -> str:
    folded = _fold(text)
    quote_pattern = re.compile(
        '["\u201c\u2018\u00ab]([^"\u201d\u2019\u00bb]+)["\u201d\u2019\u00bb]'
    )
    pieces: list[str] = []
    cursor = 0
    for match in quote_pattern.finditer(folded):
        prefix = folded[max(0, match.start() - 45) : match.start()]
        if re.search(r"(?:vi du|cum tu|cau can tranh|khong nen noi|tranh noi)\s*:?\s*$", prefix):
            pieces.append(folded[cursor : match.start()])
            cursor = match.end()
    pieces.append(folded[cursor:])
    return " ".join(pieces)


def _remove_negated_phrases(text: str) -> str:
    safe_patterns = (
        r"khong\s+(?:he\s+)?chac chan",
        r"khong\s+phai\s+(?:la\s+)?dinh menh",
        r"khong\s+can\s+lam ngay",
        r"khong\s+phai\s+(?:la\s+)?(?:loi\s+)?chan doan",
        r"khong\s+thay the\s+tu van\s+(?:y te|phap ly|tai chinh)",
        r"dung\s+chi\s+(?:nghe|tin)\s+la",
    )
    for pattern in safe_patterns:
        text = re.sub(pattern, " ", text)
    return text


def anti_influence_gate(candidate: ReadingCandidate) -> GateReport:
    original_text = unicodedata.normalize("NFC", _candidate_prose(candidate)).casefold()
    text = _remove_negated_phrases(_without_safe_examples(_candidate_prose(candidate)))
    rules: tuple[tuple[GateFailureCode, tuple[str, ...]], ...] = (
        (
            GateFailureCode.ANTI_ABSOLUTE_CERTAINTY,
            (
                r"\bchac chan\b",
                r"\bluon luon\b",
                r"\bkhong bao gio\b",
                r"\b100\s*%",
                r"\bbao dam\b",
            ),
        ),
        (
            GateFailureCode.ANTI_FATE,
            (r"\bdinh menh\b", r"\bso phan\b.*\ban bai\b", r"\btroi dinh\b"),
        ),
        (
            GateFailureCode.ANTI_DEPENDENCY,
            (r"\bchi la hieu ban\b", r"\bchi can (?:nghe|tin) la\b", r"\bkhong the thieu la\b"),
        ),
        (
            GateFailureCode.ANTI_URGENCY,
            (r"\blam ngay\b", r"\bngay lap tuc\b", r"\btruoc khi qua muon\b", r"\bdung chan chu\b"),
        ),
        (
            GateFailureCode.ANTI_ISOLATION,
            (r"\bdung noi voi ai\b", r"\btranh xa moi nguoi\b", r"\bchi mot minh\b"),
        ),
        (
            GateFailureCode.ANTI_GUILT_FEAR,
            (r"\bneu khong\b.{0,45}\bse hoi han\b", r"\bban se hoi han\b", r"\bdang trach\b"),
        ),
        (
            GateFailureCode.ANTI_DIAGNOSIS,
            (r"\bban (?:bi|mac)\b.{0,35}\b(?:tram cam|roi loan|benh)\b", r"\bchan doan ban\b"),
        ),
        (
            GateFailureCode.ANTI_LEGAL_COMMAND,
            (
                r"\b(?:hay|phai|nen)\b.{0,30}\b"
                r"(?:ky hop dong|khoi kien|kien tung|kien (?:ai|nguoi)|khieu nai)\b",
            ),
        ),
        (
            GateFailureCode.ANTI_FINANCIAL_COMMAND,
            (
                r"\b(?:hay|phai|nen|chuyen|don|vay)\b.{0,60}\b"
                r"(?:co phieu|tien tiet kiem|tien ao|bitcoin|crypto|coin|dau tu)\b",
                r"\b(?:toan bo|tat ca)\b.{0,35}\b(?:tien|tai san|tiet kiem)\b",
            ),
        ),
        (
            GateFailureCode.ANTI_SAFETY_COMMAND,
            (
                r"\b(?:cu|hay|phai)\b.{0,25}\b(?:lai xe|leo cao|bo bao ho)\b",
                r"\b(?:bi mat|len lut)\b.{0,45}\b(?:kiem tra|theo doi|doc)\b"
                r".{0,25}\b(?:dien thoai|tin nhan|tai khoan)\b",
                r"\b(?:lua doi|phan boi|ngoai tinh)\b.{0,40}\b"
                r"(?:kiem tra|theo doi|thu long)\b",
            ),
        ),
    )
    failures = [
        code for code, patterns in rules if any(re.search(pattern, text) for pattern in patterns)
    ]
    if re.search(
        r"\b(?:hãy|phải|nên|đừng|ngừng|uống|tăng|giảm)\b.{0,30}\b"
        r"(?:thuốc|liều điều trị)\b",
        original_text,
    ):
        failures.append(GateFailureCode.ANTI_MEDICAL_COMMAND)
    return _report(GateName.ANTI_INFLUENCE, ANTI_INFLUENCE_GATE_VERSION, failures)


def editorial_gate(candidate: ReadingCandidate) -> GateReport:
    sections = tuple(_fold(section) for section in candidate.all_user_prose if section.strip())
    failures: list[GateFailureCode] = []
    joined = "\n".join(sections)
    searchable_joined = re.sub(r"\W+", " ", joined)
    cosmic_signal_phrases = (
        "vu tru thi tham",
        "tin hieu vu tru",
        "vu tru dang gui tin hieu",
        "vu tru gui tin hieu",
        "nhu cau nao dang cam lai",
        "goc rong chi la sac do nen",
    )
    if any(phrase in searchable_joined for phrase in cosmic_signal_phrases):
        failures.append(GateFailureCode.EDITORIAL_BANNED_PHRASE)
    generic_phrases = (
        "chua lanh dua tre ben trong",
        "nang tan so",
        "phien ban tot nhat cua ban",
        "moi thu xay ra deu co ly do",
        "tin vao hanh trinh",
    )
    if any(phrase in searchable_joined for phrase in generic_phrases):
        failures.append(GateFailureCode.EDITORIAL_GENERIC_HEALING)
    slang = ("slay", "flex", "cringe", "plot twist", "main character", "keo ly", "chill")
    if any(sum(section.count(term) for term in slang) > 1 for section in sections):
        failures.append(GateFailureCode.EDITORIAL_FORCED_SLANG)
    normalized_sections = tuple(re.sub(r"\W+", " ", section).strip() for section in sections)
    if len(normalized_sections) != len(set(normalized_sections)) or any(
        _has_near_duplicate_clause(section) for section in sections
    ):
        failures.append(GateFailureCode.EDITORIAL_REPETITION)
    word_counts = tuple(len(re.findall(r"\b\w+\b", section)) for section in sections)
    if any(count > 85 for count in word_counts) or sum(word_counts) > 240:
        failures.append(GateFailureCode.EDITORIAL_LENGTH)
    return _report(GateName.EDITORIAL, EDITORIAL_GATE_VERSION, failures)


def _has_near_duplicate_clause(section: str) -> bool:
    ignored = {"mot", "nhip", "kia", "con", "ben", "phan", "thu", "nhat", "hai"}
    clauses = []
    for clause in re.split(r"[.!?;:\n]+", section):
        tokens = [token for token in re.findall(r"\b\w+\b", clause) if token not in ignored]
        if len(tokens) >= 6:
            clauses.append(tokens)
    for index, left in enumerate(clauses):
        left_set = set(left)
        for right in clauses[index + 1 :]:
            right_set = set(right)
            shared = len(left_set.intersection(right_set))
            if shared / min(len(left_set), len(right_set)) >= 0.85:
                return True
    return False


def meaning_gate(plan: ReadingPlan, candidate: ReadingCandidate) -> GateReport:
    """Reject prose that drifted away from its compiled scene and evidence contract."""

    blueprint = candidate.semantic_blueprint
    if blueprint is None:
        return _report(
            GateName.MEANING,
            MEANING_GATE_VERSION,
            (GateFailureCode.MEANING_BLUEPRINT_REQUIRED,),
        )

    failures: list[GateFailureCode] = []
    for requirement in blueprint.requirements:
        section_text = {
            SemanticSection.ALL: _candidate_prose(candidate),
            SemanticSection.HOOK: candidate.hook,
            SemanticSection.THESIS: candidate.thesis,
            SemanticSection.MANIFESTATION: candidate.manifestation,
            SemanticSection.MICRO_ACTION: candidate.micro_action,
            SemanticSection.TRANSIT: candidate.transit or "",
        }[requirement.section]
        folded_section = _fold(section_text)
        matches = sum(_fold(marker) in folded_section for marker in requirement.markers)
        if matches < requirement.min_matches:
            failures.append(GateFailureCode.MEANING_REQUIRED_CONCEPT)
            break

    lens = plan.background_lens
    if plan.tradition.value == "jyotish":
        expected_arena = SemanticArena.STRUCTURAL
    elif lens is None or lens is BackgroundLens.AUTO:
        expected_arena = SemanticArena.GENERAL
    else:
        expected_arena = SemanticArena(lens.value)
    if blueprint.arena is not expected_arena:
        failures.append(GateFailureCode.MEANING_CONTEXT_MISMATCH)

    if plan.purpose.value == "daily_note" and plan.tradition.value == "western":
        scene_text = _fold(f"{candidate.hook} {candidate.manifestation}")
        advice_patterns = (
            r"(?:^|[.!?]\s+)(?:hay|thu|nen|dung)\s+",
            r"\bban (?:hay|nen|can phai)\b",
        )
        if any(re.search(pattern, scene_text) for pattern in advice_patterns):
            failures.append(GateFailureCode.MEANING_SCENE_CONTAINS_ADVICE)
        scene_parts = blueprint.scene_key.split(":")
        action_parts = blueprint.action_key.split(":")
        if (
            len(scene_parts) < 3
            or len(action_parts) < 3
            or scene_parts[:2] != action_parts[:2]
            or scene_parts[0] != "psychology"
        ):
            failures.append(GateFailureCode.MEANING_DAILY_MATRIX_MISMATCH)

    context_markers = {
        SemanticArena.RELATIONSHIPS: ("quan he", "nguoi kia", "tro chuyen", "than thiet"),
        SemanticArena.COMMUNICATION: ("giao tiep", "cau", "noi", "nhan"),
        SemanticArena.WORK: ("cong viec", "dau viec", "uu tien"),
        SemanticArena.ENERGY: ("nang luong", "co the", "suc chua", "qua tai"),
        SemanticArena.SELF_CARE: ("cham minh", "nghi ngoi", "cham co the"),
    }
    if expected_arena in context_markers:
        scene_text = _fold(f"{candidate.hook} {candidate.manifestation}")
        if not any(marker in scene_text for marker in context_markers[expected_arena]):
            failures.append(GateFailureCode.MEANING_UNOBSERVABLE_SCENE)

    action_text = _fold(candidate.micro_action)
    observable_action_verbs = (
        "thu ",
        "viet ",
        "chon ",
        "noi ",
        "hoi ",
        "giam ",
        "ghi ",
        "dat ",
        "bo sung ",
        "mo ",
        "xem ",
        "tam ",
        "tim ",
        "kiem tra ",
        "nhan ",
        "cho ",
        "giu ",
        "roi ",
        "an ",
        "xin ",
        "sua ",
        "tu hoi",
    )
    if not any(verb in action_text for verb in observable_action_verbs):
        failures.append(GateFailureCode.MEANING_ACTION_MISMATCH)

    factor_ids = {factor.id for factor in plan.factors}
    if not set(blueprint.evidence_factor_refs).issubset(factor_ids):
        failures.append(GateFailureCode.MEANING_UNSUPPORTED_FACTOR)
    if plan.mode is not PlanMode.LIMITED and not set(plan.hero_factor_refs).intersection(
        blueprint.evidence_factor_refs
    ):
        failures.append(GateFailureCode.MEANING_UNSUPPORTED_FACTOR)

    return _report(GateName.MEANING, MEANING_GATE_VERSION, failures)


def privacy_gate(candidate: ReadingCandidate) -> GateReport:
    text = _candidate_prose(candidate)
    folded = _fold(text)
    patterns = (
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        r"\b(?:\+?84|0)(?:[ .-]?\d){9,10}\b",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b(?:guest|account|session|chart|profile)_?id\s*[:=]",
        r"\btoa do\s+-?\d{1,3}\.\d+\s*,\s*-?\d{1,3}\.\d+",
        r"\b(?:vi do|kinh do|latitude|longitude)\s*[:=]?\s*-?\d{1,3}\.\d+",
        r"\bngay sinh\b.{0,30}\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    )
    if re.search(patterns[0], text, flags=re.IGNORECASE) or any(
        re.search(pattern, folded) for pattern in patterns[1:]
    ):
        return _report(
            GateName.PRIVACY,
            PRIVACY_GATE_VERSION,
            (GateFailureCode.PRIVACY_PERSONAL_DATA,),
        )
    return _report(GateName.PRIVACY, PRIVACY_GATE_VERSION, ())


def evaluate_candidate(plan: ReadingPlan, candidate: ReadingCandidate) -> CandidateEvaluation:
    """Run the five local gates in their fixed publish order."""

    reports = (
        evidence_gate(plan, candidate),
        anti_influence_gate(candidate),
        editorial_gate(candidate),
        meaning_gate(plan, candidate),
        privacy_gate(candidate),
    )
    accepted = all(report.passed for report in reports)
    return CandidateEvaluation(
        accepted=accepted,
        reports=reports,
        publishable_candidate=candidate if accepted else None,
    )
