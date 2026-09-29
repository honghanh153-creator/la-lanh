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
    "tin nhắn",
    "cuộc trò chuyện",
    "lịch ",
    "cơ thể",
    "người ",
    "việc ",
)
ACTION_MARKERS = (
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
)


@dataclass(frozen=True)
class ReviewSample:
    persona_id: str
    surface: Literal["daily", "tarot"]
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
    """Offline pre-publish reviewer; it never logs or returns source prose."""

    def review(self, samples: tuple[ReviewSample, ...]) -> ReviewResult:
        findings: list[ReviewFinding] = []
        fingerprints: dict[tuple[str, str], str] = {}

        for sample in samples:
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

            scene = self._normalize(section_map.get("scene", ""))
            action = self._normalize(section_map.get("action", ""))
            if len(scene.split()) < 12 or not any(marker in scene for marker in SCENE_MARKERS):
                findings.append(self._finding(sample, "scene", "scene-not-observable", "high"))
            if len(action.split()) < 6 or not any(marker in action for marker in ACTION_MARKERS):
                findings.append(self._finding(sample, "action", "action-not-testable", "high"))

            fingerprint = self._fingerprint(
                tuple(
                    (name, prose) for name, prose in sample.sections if name in {"scene", "action"}
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

    @classmethod
    def _fingerprint(cls, sections: tuple[tuple[str, str], ...]) -> str:
        joined = "|".join(cls._normalize(value) for _, value in sections)
        normalized = re.sub(r"\d+", "#", joined)
        return sha256(normalized.encode("utf-8")).hexdigest()
