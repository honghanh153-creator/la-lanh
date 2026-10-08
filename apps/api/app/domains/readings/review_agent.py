from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal

ReviewSeverity = Literal["critical", "high", "medium"]

BANNED_CORE_FRAGMENTS = (
    "pattern này",
    "giả thuyết để soi",
    "không khớp việc thật thì bỏ qua",
    "tín hiệu vũ trụ",
    "vũ trụ thì thầm",
    "mọi thứ xảy ra đều có lý do",
    "điều đang chạy bên dưới",
    "một cách khác để thử",
    "một việc chưa hoàn hảo có thể nằm yên",
    "được hành động thẳng",
    "nhu cầu này dễ cùng bật lên",
    "giành phần ưu tiên",
    "mối liên hệ này rõ và dễ nhận ra ngoài đời",
    "ý kiến đông người dễ nghe giống ý kiến đúng",
    "sự tự tin của người nói có thể đang được nghe như bằng chứng",
    "cảm giác thuộc về nhóm đang đứng cạnh",
    "làm xong, xem tình hình có dễ hơn không",
)
OPAQUE_CORE_FRAGMENTS = (
    "pattern",
    "mood",
    "vận hành",
    "giữ nhịp",
    "kéo ánh nhìn",
    "mở một góc",
    "đang chạm vào",
    "lộ ra",
    "vùng mờ",
    "cơ chế này",
    "đặt lại sức chứa",
    "chuyển năng lượng",
    "một bước có giới hạn",
    "tiêu chí thật",
    "nhịp gây nhiễu",
    "nhịp có ích",
    "mở vòng mới",
    "điều đang bị né gọi tên",
    "mang dấu tay",
    "còn một dấu phẩy",
    "chốt hộ kết quả",
    "hai phần cùng có tiếng",
    "phần còn lại của người kia",
)
DISCLAIMER_ONLY_FRAGMENTS = (
    "không phải nhãn",
    "không phải chỉ dẫn",
    "không phải dự đoán",
    "quyền quyết định vẫn",
    "phần không khớp có thể bỏ qua",
    "bỏ thử nghiệm này",
)
SCENE_MARKERS = (
    "khi ",
    "lúc ",
    "lần ",
    "tin nhắn",
    "cuộc trò chuyện",
    "lịch ",
    "cơ thể",
    "người ",
    "việc ",
)
ACTION_MARKERS = (
    "làm ",
    "hỏi ",
    "viết ",
    "chọn ",
    "nói ",
    "đặt ",
    "tách ",
    "gọi tên",
    "bỏ bớt",
    "kiểm tra",
    "thử ",
    "nhắn ",
    "chờ ",
    "giữ ",
    "rời ",
    "ẩn ",
    "xin ",
    "sửa ",
    "tự hỏi",
)


@dataclass(frozen=True)
class ReviewSample:
    persona_id: str
    surface: Literal["daily", "natal", "tarot"]
    sections: tuple[tuple[str, str], ...]
    disclaimer: str
    provenance_ids: tuple[str, ...]
    evidence_validated: bool


@dataclass(frozen=True)
class ReviewFinding:
    rule_id: str
    persona_id: str
    surface: str
    section: str
    severity: ReviewSeverity


@dataclass(frozen=True)
class ReviewResult:
    passed: bool
    persona_count: int
    sample_count: int
    findings: tuple[ReviewFinding, ...]


class ContentReviewAgent:
    """Core content reviewer; independent from Content Studio and personal data."""

    def review(self, samples: tuple[ReviewSample, ...]) -> ReviewResult:
        findings: list[ReviewFinding] = []
        fingerprints: dict[tuple[str, str], str] = {}

        for sample in samples:
            sentence_sections: dict[str, str] = {}
            if not sample.evidence_validated:
                findings.append(
                    self._finding(sample, "provenance", "evidence-not-validated", "critical")
                )
            if not sample.provenance_ids:
                findings.append(
                    self._finding(sample, "provenance", "missing-provenance", "critical")
                )
            if len(sample.disclaimer.strip()) < 20:
                findings.append(self._finding(sample, "disclaimer", "weak-disclaimer", "high"))

            section_map = dict(sample.sections)
            for section_name, prose in sample.sections:
                normalized = self._normalize(prose)
                if any(fragment in normalized for fragment in BANNED_CORE_FRAGMENTS):
                    findings.append(
                        self._finding(sample, section_name, "retired-or-abstract-copy", "critical")
                    )
                if any(fragment in normalized for fragment in DISCLAIMER_ONLY_FRAGMENTS):
                    findings.append(
                        self._finding(sample, section_name, "disclaimer-inside-core-copy", "high")
                    )
                if any(fragment in normalized for fragment in OPAQUE_CORE_FRAGMENTS):
                    findings.append(
                        self._finding(sample, section_name, "opaque-or-translated-copy", "high")
                    )
                sentences = self._sentences(normalized)
                if len(sentences) != len(set(sentences)):
                    findings.append(
                        self._finding(sample, section_name, "repeated-sentence", "high")
                    )
                for sentence in sentences:
                    previous_section = sentence_sections.get(sentence)
                    if previous_section is not None and previous_section != section_name:
                        findings.append(
                            self._finding(
                                sample,
                                section_name,
                                "repeated-sentence-across-sections",
                                "medium" if sample.surface == "tarot" else "high",
                            )
                        )
                    sentence_sections.setdefault(sentence, section_name)
                if any(len(sentence.split()) > 28 for sentence in sentences):
                    findings.append(
                        self._finding(sample, section_name, "sentence-too-dense", "high")
                    )

            scene_sections = tuple(
                (name, self._normalize(value))
                for name, value in section_map.items()
                if name == "scene" or name.startswith("scene_")
            )
            action_sections = tuple(
                (name, self._normalize(value))
                for name, value in section_map.items()
                if name == "action" or name.startswith("action_")
            )
            if not scene_sections:
                findings.append(self._finding(sample, "scene", "scene-missing", "critical"))
            for section_name, scene in scene_sections:
                if len(scene.split()) < 12 or not any(marker in scene for marker in SCENE_MARKERS):
                    findings.append(
                        self._finding(sample, section_name, "scene-not-observable", "high")
                    )
                if sample.surface == "daily" and (
                    re.search(r"(?:^|[.!?,;]\s+)(?:hãy|thử|đừng)\s+", scene)
                    or re.search(r"(?:^|[.!?]\s+)nên\s+|\bbạn nên\s+", scene)
                ):
                    findings.append(
                        self._finding(sample, section_name, "advice-inside-scene", "high")
                    )
            if not action_sections:
                findings.append(self._finding(sample, "action", "action-missing", "critical"))
            for section_name, action in action_sections:
                has_action_marker = any(marker in action for marker in ACTION_MARKERS)
                if len(action.split()) < 6 or not has_action_marker:
                    findings.append(
                        self._finding(sample, section_name, "action-not-testable", "high")
                    )

            fingerprint = self._fingerprint(
                tuple(
                    (name, prose)
                    for name, prose in sample.sections
                    if name == "scene"
                    or name.startswith("scene_")
                    or name == "action"
                    or name.startswith("action_")
                )
            )
            duplicate_key = (sample.surface, fingerprint)
            if duplicate_key in fingerprints:
                findings.append(self._finding(sample, "all", "duplicate-core-reading", "high"))
            else:
                fingerprints[duplicate_key] = sample.persona_id

        return ReviewResult(
            passed=not any(item.severity in {"critical", "high"} for item in findings),
            persona_count=len({sample.persona_id for sample in samples}),
            sample_count=len(samples),
            findings=tuple(findings),
        )

    @staticmethod
    def _finding(
        sample: ReviewSample,
        section: str,
        rule_id: str,
        severity: ReviewSeverity,
    ) -> ReviewFinding:
        return ReviewFinding(
            rule_id=rule_id,
            persona_id=sample.persona_id,
            surface=sample.surface,
            section=section,
            severity=severity,
        )

    @staticmethod
    def _normalize(prose: str) -> str:
        return " ".join(prose.casefold().split())

    @staticmethod
    def _sentences(prose: str) -> tuple[str, ...]:
        return tuple(
            sentence.strip(" .!?…")
            for sentence in re.split(r"(?<=[.!?…])[”\"']?\s+", prose)
            if sentence.strip(" .!?…")
        )

    @classmethod
    def _fingerprint(cls, sections: tuple[tuple[str, str], ...]) -> str:
        joined = "|".join(cls._normalize(value) for _, value in sections)
        normalized = re.sub(r"\d+", "#", joined)
        return sha256(normalized.encode("utf-8")).hexdigest()
