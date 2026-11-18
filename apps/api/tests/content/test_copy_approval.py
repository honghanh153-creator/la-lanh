"""Pending copy never reaches users (owner decision 06.11.2026). Synthetic sentences only."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domains.content import copy_approval
from app.domains.content.copy_approval import CopyEntry, copy_digest, parse_registry
from app.main import create_app

PENDING = "Câu thử nghiệm đang chờ duyệt, không được hiện ra."
APPROVED = "Câu thử nghiệm đã được duyệt."
FALLBACK_START = "Đừng cố nhớ hết cả bài."


def _entry(**overrides: Any) -> dict[str, Any]:
    entry = {
        "id": "tarot.closing_prompt",
        "category": "reading",
        "text": PENDING,
        "status": "pending",
    }
    entry.update(overrides)
    return entry


def _use(monkeypatch: pytest.MonkeyPatch, *entries: dict[str, Any]) -> None:
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": list(entries)})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


def _approved(text: str = APPROVED, **overrides: Any) -> dict[str, Any]:
    entry = _entry(
        text=text, status="approved", approver="codex", date="2026-11-06", digest=copy_digest(text)
    )
    entry.update(overrides)
    return entry


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as test_client:
        yield test_client


def _reading(client: TestClient) -> str:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "tarot-reflection-v1",
            "purpose": "tarot_reflection",
            "idempotency_key": "copy-flag-guest-1234567890",
        },
    )
    headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": guest.json()["csrf_token"]}
    started = client.post(
        "/v1/tarot/sessions",
        headers=headers,
        json={
            "context": "relationships",
            "question": "Mình nên nhìn rõ điều gì trước khi nhắn lại?",
            "spread": "one_card",
            "origin": "direct",
            "idempotency_key": "copy-flag-start-1234567890",
        },
    )
    selected = client.put(
        f"/v1/tarot/sessions/{started.json()['id']}/selections",
        headers=headers,
        json={"fan_index": 17, "expected_version": started.json()["version"]},
    )
    assert selected.status_code == 200
    return selected.text


def test_pending_copy_never_reaches_an_api_response(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use(monkeypatch, _entry())
    body = _reading(client)
    assert PENDING not in body
    assert FALLBACK_START in body


def test_approved_copy_is_served(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, _approved())
    assert APPROVED in _reading(client)


@pytest.mark.parametrize(
    "bad",
    [
        {"digest": copy_digest("câu khác")},
        {"approver": None},
        {"category": "privacy"},
        {"category": "crisis"},
    ],
)
def test_unsafe_approval_falls_back(monkeypatch: pytest.MonkeyPatch, bad: dict[str, Any]) -> None:
    _use(monkeypatch, _approved(**bad))
    assert copy_approval.copy_text("tarot.closing_prompt", "cũ") == "cũ"


def test_owner_may_approve_owner_only_category(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, _approved(category="consent", approver="owner"))
    assert copy_approval.copy_text("tarot.closing_prompt", "cũ") == APPROVED


def test_pin_ignores_pending_and_tracks_approved() -> None:
    empty = copy_approval.approved_pin({})
    pending = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": [_entry()]})
    approved = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": [_approved()]})
    assert copy_approval.approved_pin(pending) == empty
    assert copy_approval.approved_pin(approved) != empty


def test_registry_rejects_codex_approval_of_safety_copy() -> None:
    entry = CopyEntry(**_approved(category="safety"))
    assert any("owner" in problem for problem in entry.problems())


_LINT_BAD = [
    "Xem thêm tại https://vi-du.test/bai-viet nhé.",
    "Mở www.vi-du nếu cần đọc thêm.",
    "Ghé vidu.vn để xem thêm.",
    # Bare domains with any suffix, not only a fixed list (review of #411, PV-15).
    "Ghé vi-du.ai để đọc thêm.",
    "Ghé vi-du.site để đọc thêm.",
    "Ghé vi-du.edu để đọc thêm.",
    "Ghé VI-DU.SHOP để đọc thêm.",
    "Ghé bai.vi-du.com.vn/trang để đọc thêm.",
    "Đọc thêm ở vi-du.travel.",
    "Gửi thư cho ban-tro-giup@vi-du.test nếu cần.",
    "Theo dõi @lalanh_thu để nhận thêm.",
    "Gọi 0900 000 000 nếu cần nói chuyện.",
    "Gọi +84 90-000-0000 nếu cần.",
    "Chào {name}, hôm nay thế nào?",
    "Chào {{ten}}, hôm nay thế nào?",
    "Hôm nay hợp để <việc cần làm>.",
    "Hôm nay hợp để [điền việc].",
    "Chào %s, hôm nay thế nào?",
    "Chào %(name)s, hôm nay thế nào?",
    "Chào $ten, hôm nay thế nào?",
    "Hôm nay hợp để ___.",
    "TODO viết lại câu này.",
    "Câu này XXX chưa xong.",
    "Lorem ipsum dolor sit amet.",
    "Câu thù nghiệm chưa chuẩn hoá.",  # decomposed grave accent, not NFC
    # Review r4/r5 of #411: Unicode labels, any-case suffixes, printf slots with flags.
    "Ghé ví-dụ.test để đọc thêm.",
    "Ghé ĐỌC-THÊM.VN để đọc thêm.",
    "Ghé vi-du.TeSt/trang để đọc thêm.",
    "Ghé vi-du.tEST để đọc thêm.",
    "Ghé vi-du.Com để đọc thêm.",
    "Ghé vidu.Com/trang để đọc thêm.",
    "Còn %02d ngày nữa.",
    "Còn %.2f giờ nữa.",
    "Chào %-10s nhé.",
    "Bạn được %+d điểm.",
    "Chào %(ten)05.1f nhé.",
]


@pytest.mark.parametrize("text", _LINT_BAD)
@pytest.mark.parametrize("status", ["pending", "approved"])
def test_registry_lint_rejects_links_contacts_and_placeholders(text: str, status: str) -> None:
    raw = _approved(text) if status == "approved" else _entry(text=text)
    entries = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": [raw]})
    assert copy_approval.registry_problems(entries)


@pytest.mark.parametrize("text", _LINT_BAD)
def test_linted_approved_copy_falls_back(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    _use(monkeypatch, _approved(text))
    assert copy_approval.copy_text("tarot.closing_prompt", "cũ") == "cũ"


@pytest.mark.parametrize(
    "text",
    [
        APPROVED,
        "Đặt hẹn giờ 20 phút rồi làm tiếp một việc đang dở.",
        "Uống một cốc nước, rồi hít thở chậm 3 lần.",
        "Nghỉ 5-10 phút… rồi quay lại việc chính.",
        "Hỏi: “Mình cần gì lúc này?” — rồi ghi ra một dòng.",
        "Xong việc nhỏ.Rồi nghỉ.",  # missing space after a full stop is not a link
        "Ghi 1.5 giờ ngủ thêm vào sổ.",
        "Bạn ở TP. Hồ Chí Minh, v.v. vẫn ổn.",
        "Giảm 50% dung lượng rồi tiếp.",  # a percent sign before a word is not a slot
        "Pin còn 20%, sạc thêm 5% nữa.",
    ],
)
def test_registry_lint_accepts_plain_sentences(text: str) -> None:
    assert copy_approval.text_lint_problems(text) == ()


# Review r6 of #411: one table for the spelling-variant class. Each rule reads the NFKC, casefolded
# text, so case and full-width forms of a link, an address or a phone number are the same finding.
_VARIANTS = [
    "Ghé vidu.Com để đọc thêm.",
    "Ghé vidu.Vn để đọc thêm.",
    "Ghé VIDU.COM để đọc thêm.",
    "Ghé vidu.Com?muc=thu để đọc thêm.",
    "Ghé ViDu.CoM/trang để đọc thêm.",
    # Full-width letters and dot.
    "Ghé \uff56\uff49\uff44\uff55\uff0e\uff43\uff4f\uff4d để đọc thêm.",
    "Gửi thư cho Ban@Vi-Du.Test nếu cần.",
    "Gửi thư cho ban\uff20vi-du.test nếu cần.",  # full-width @
    # Full-width digits.
    "Gọi \uff10\uff19\uff10\uff10 \uff10\uff10\uff10 \uff10\uff10\uff10 nếu cần.",
    "Chào %S nhé.",
]


@pytest.mark.parametrize("text", _VARIANTS)
def test_case_and_width_variants_are_one_class(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    assert copy_approval.text_lint_problems(text)
    entries = parse_registry(
        {"version": copy_approval.REGISTRY_VERSION, "entries": [_approved(text)]}
    )
    assert copy_approval.registry_problems(entries)
    _use(monkeypatch, _approved(text))
    assert copy_approval.copy_text("tarot.closing_prompt", "cũ") == "cũ"


def test_a_word_glued_to_the_next_sentence_is_flagged_by_design() -> None:
    # Without the space, "xong.Sau" reads as a domain once case is folded; the copy adds the space.
    assert copy_approval.text_lint_problems("Ăn xong.Sau đó nghỉ một chút.") == ("contains a link",)
    assert copy_approval.text_lint_problems("Ăn xong. Sau đó nghỉ một chút.") == ()


def test_checked_in_registry_is_valid() -> None:
    assert copy_approval.registry_problems(copy_approval.load_registry()) == []


@pytest.mark.parametrize(
    "data",
    [
        [],
        {"version": copy_approval.REGISTRY_VERSION, "entries": {}},
        {"version": copy_approval.REGISTRY_VERSION, "entries": [None]},
        {"version": copy_approval.REGISTRY_VERSION, "entries": [{**_entry(), "text": None}]},
        {"version": copy_approval.REGISTRY_VERSION, "entries": [{**_entry(), "digest": 1}]},
        {"version": copy_approval.REGISTRY_VERSION, "entries": [{**_entry(), "extra": "x"}]},
    ],
)
def test_malformed_registry_shapes_fall_back(
    data: object, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    with pytest.raises(ValueError):
        parse_registry(data)
    path = tmp_path / "copy_registry.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(copy_approval, "REGISTRY_PATH", path)
    copy_approval._runtime_registry.cache_clear()
    try:
        assert copy_approval.copy_text("tarot.closing_prompt", "cũ") == "cũ"
    finally:
        copy_approval._runtime_registry.cache_clear()


def test_crisis_check_disclosure_is_the_owner_approved_privacy_copy() -> None:
    """Owner approved this /privacy sentence on 15.11.2026 ("D duyệt"), character for character."""

    text = (
        "Khi bạn gõ câu hỏi hoặc tên, Lá Lành đọc qua để xem bạn có đang muốn làm hại bản thân "
        "không. Nếu có, Lá không trả bài đọc mà chỉ gửi bạn một lời nhắn hỗ trợ. Câu đó không "
        "được lưu lại và không gửi cho ai khác. Lá có thể nhận nhầm hoặc bỏ sót."
    )
    entry = copy_approval.load_registry()["privacy.crisis-check-disclosure"]
    assert (entry.category, entry.text) == ("privacy", text)
    assert (entry.status, entry.approver, entry.date) == ("approved", "owner", "2026-11-15")
    assert entry.servable
