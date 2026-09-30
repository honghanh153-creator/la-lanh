from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any

from app.domains.content.models import (
    ContentValidationFinding,
    ContentValidationReceipt,
    canonical_payload_hash,
)
from app.domains.readings import knowledge
from app.domains.readings.review_agent import (
    BANNED_CORE_FRAGMENTS,
    DISCLAIMER_ONLY_FRAGMENTS,
    OPAQUE_CORE_FRAGMENTS,
)

CONTENT_VALIDATOR_VERSION = "content-studio-validator-v1"
EXPECTED_GROUPS = {"planets", "signs", "houses", "aspects"}
REQUIRED_FIELDS = {
    "planets": {"drive", "stress", "action"},
    "signs": {"style", "stress", "manifestation", "practices", "hooks"},
    "houses": {"arena", "manifestation"},
    "aspects": {"bridge", "watch"},
}
REQUIRED_ENTRY_IDS = {
    "planets": frozenset(knowledge.PLANETS),
    "signs": frozenset(knowledge.SIGNS),
    "houses": frozenset(str(key) for key in knowledge.HOUSES),
    "aspects": frozenset(knowledge.ASPECTS),
}


def validate_daily_catalog(payload: dict[str, Any]) -> ContentValidationReceipt:
    findings: list[ContentValidationFinding] = []
    missing_groups = EXPECTED_GROUPS - payload.keys()
    extra_groups = payload.keys() - EXPECTED_GROUPS
    for group in sorted(missing_groups):
        findings.append(
            _finding("catalog-group-missing", "critical", group, "Thiếu nhóm nội dung.")
        )
    for group in sorted(extra_groups):
        findings.append(
            _finding("catalog-group-unknown", "critical", group, "Nhóm nội dung không được hỗ trợ.")
        )

    for group in sorted(EXPECTED_GROUPS & payload.keys()):
        entries = payload[group]
        if not isinstance(entries, dict) or not entries:
            findings.append(
                _finding("catalog-group-empty", "critical", group, "Nhóm phải có ít nhất một mục.")
            )
            continue
        missing_entries = REQUIRED_ENTRY_IDS[group] - entries.keys()
        extra_entries = entries.keys() - REQUIRED_ENTRY_IDS[group]
        if missing_entries:
            findings.append(
                _finding(
                    "catalog-entry-missing",
                    "critical",
                    group,
                    f"Thiếu mục bắt buộc: {', '.join(sorted(missing_entries))}.",
                )
            )
        if extra_entries:
            findings.append(
                _finding(
                    "catalog-entry-unknown",
                    "high",
                    group,
                    f"Mục chưa được engine hỗ trợ: {', '.join(sorted(extra_entries))}.",
                )
            )
        for entry_id, value in entries.items():
            path = f"{group}.{entry_id}"
            if not isinstance(entry_id, str) or not re.fullmatch(r"[a-z0-9_-]{1,64}", entry_id):
                findings.append(
                    _finding("entry-id-invalid", "critical", path, "ID mục không hợp lệ.")
                )
                continue
            if not isinstance(value, dict):
                findings.append(
                    _finding("entry-shape-invalid", "critical", path, "Mục phải là object.")
                )
                continue
            missing = REQUIRED_FIELDS[group] - value.keys()
            extra = value.keys() - REQUIRED_FIELDS[group]
            if missing:
                findings.append(
                    _finding(
                        "entry-field-missing",
                        "critical",
                        path,
                        f"Thiếu field: {', '.join(sorted(missing))}.",
                    )
                )
            if extra:
                findings.append(
                    _finding(
                        "entry-field-unknown",
                        "high",
                        path,
                        f"Field lạ: {', '.join(sorted(extra))}.",
                    )
                )
            findings.extend(_review_field_shapes(group, value, path))
            findings.extend(_review_value(value, path))

    signs = payload.get("signs")
    if isinstance(signs, dict):
        fingerprints: dict[str, str] = {}
        for entry_id, value in signs.items():
            if not isinstance(value, dict):
                continue
            fingerprint = json.dumps(value, ensure_ascii=False, sort_keys=True)
            previous = fingerprints.get(fingerprint)
            if previous is not None:
                findings.append(
                    _finding(
                        "duplicate-matrix-entry",
                        "high",
                        f"signs.{entry_id}",
                        f"Nội dung trùng toàn bộ với signs.{previous}.",
                    )
                )
            else:
                fingerprints[fingerprint] = entry_id

    return ContentValidationReceipt(
        validator_version=CONTENT_VALIDATOR_VERSION,
        payload_hash=canonical_payload_hash(payload),
        passed=not any(item.severity in {"critical", "high"} for item in findings),
        findings=tuple(findings),
    )


def _review_field_shapes(
    group: str, value: dict[str, Any], path: str
) -> Iterable[ContentValidationFinding]:
    list_fields = {"practices", "hooks"} if group == "signs" else set()
    for field in REQUIRED_FIELDS[group]:
        if field not in value:
            continue
        child = value[field]
        field_path = f"{path}.{field}"
        if field in list_fields:
            if not isinstance(child, list):
                yield _finding(
                    "field-type-invalid",
                    "critical",
                    field_path,
                    "Field này phải là danh sách text.",
                )
                continue
            if len(child) != 3:
                yield _finding(
                    "list-cardinality-invalid",
                    "high",
                    field_path,
                    "Danh sách phải có đúng 3 biến thể.",
                )
            if len({item.strip().casefold() for item in child if isinstance(item, str)}) != len(
                child
            ):
                yield _finding(
                    "list-duplicate",
                    "high",
                    field_path,
                    "Các biến thể trong danh sách không được trùng nhau.",
                )
        elif not isinstance(child, str):
            yield _finding(
                "field-type-invalid",
                "critical",
                field_path,
                "Field này phải là text thuần.",
            )


def _review_value(value: Any, path: str) -> Iterable[ContentValidationFinding]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _review_value(child, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        if not value:
            yield _finding("list-empty", "high", path, "Danh sách nội dung không được rỗng.")
        for index, child in enumerate(value):
            yield from _review_value(child, f"{path}[{index}]")
        return
    if not isinstance(value, str):
        yield _finding("copy-not-text", "critical", path, "Nội dung phải là text thuần.")
        return
    text = " ".join(value.split())
    folded = text.casefold()
    if len(text) < 8:
        yield _finding("copy-too-short", "high", path, "Nội dung quá ngắn để có nghĩa rõ ràng.")
    if len(text) > 360:
        yield _finding("copy-too-long", "high", path, "Nội dung vượt giới hạn 360 ký tự.")
    if "<" in text or ">" in text:
        yield _finding("raw-markup", "critical", path, "Không dùng HTML hoặc markup trong matrix.")
    if any(fragment in folded for fragment in BANNED_CORE_FRAGMENTS):
        yield _finding(
            "abstract-or-retired-copy", "critical", path, "Có cụm từ trừu tượng hoặc đã bị loại bỏ."
        )
    if any(fragment in folded for fragment in OPAQUE_CORE_FRAGMENTS):
        yield _finding(
            "opaque-or-translated-copy",
            "high",
            path,
            "Nội dung dùng cụm trừu tượng hoặc nghe như dịch máy.",
        )
    if any(fragment in folded for fragment in DISCLAIMER_ONLY_FRAGMENTS):
        yield _finding(
            "disclaimer-in-core-copy",
            "high",
            path,
            "Disclaimer không được nằm trong nội dung chính.",
        )


def _finding(rule_id: str, severity: str, path: str, message: str) -> ContentValidationFinding:
    return ContentValidationFinding(rule_id=rule_id, severity=severity, path=path, message=message)
