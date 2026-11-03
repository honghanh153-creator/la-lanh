"""The twelve houses as sourced sets of meanings (Daily v2 plan, section 1.1, rule N-1).

A house is never one label. Each house is an ordered tuple of short, plain meanings, and every
meaning records where it comes from, whether it is a sensitive topic (⚠) and whether it may ever
reach a daily reading. Which meaning a reading shows is decided by later layers (planet, contact
with a natal point, time span); this module only holds the data and the display-safe order.

Sources, from ``docs/research/2026-11-03-sach-chiem-tinh-nha-va-transit.md`` (12-house table):

* CLASSICAL: William Lilly, *Christian Astrology* (1647), book I pp. 50-56, with or without
  BPHS 11.2-11.13 (Santhanam) agreeing.
* JYOTISH: BPHS 11.2-11.13 and/or Phaladeepika ch. 1 only, not in Lilly.
* MODERN: Sasportas, *The Twelve Houses* / Hand, *Planets in Transit* only. These two books
  were not checked against the printed text (owner decided 03.11.2026 not to buy them), so a
  MODERN-only meaning is only ever one door of a many-door sentence: never first, never a chip.
* BOTH: a classical source (Lilly or BPHS) and the modern books agree.

Where the report was unsure, the meaning is marked MODERN. Nothing here quotes Hand or
Sasportas, and none of these texts names a house, a sign, a planet or an aspect: they are the
plain words a reading may use.

Not wired into ``knowledge.HOUSES`` or ``daily_personalization.HOUSE_ARENAS`` yet (HM-2/HM-3).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

HOUSE_MEANINGS_VERSION = "house-meanings-2026-11-03-v1"


class MeaningSource(StrEnum):
    CLASSICAL = "classical"
    MODERN = "modern"
    BOTH = "both"
    JYOTISH = "jyotish"


# A reading may open with a meaning only when a classical Western source stands behind it.
LEAD_SOURCES = frozenset({MeaningSource.CLASSICAL, MeaningSource.BOTH, MeaningSource.JYOTISH})


@dataclass(frozen=True)
class SourcedMeaning:
    key: str
    text: str
    source: MeaningSource
    sensitive: bool = False
    daily_allowed: bool = True


_C = MeaningSource.CLASSICAL
_M = MeaningSource.MODERN
_B = MeaningSource.BOTH
_J = MeaningSource.JYOTISH


def _m(
    key: str,
    text: str,
    source: MeaningSource,
    *,
    sensitive: bool = False,
    daily_allowed: bool = True,
) -> SourcedMeaning:
    return SourcedMeaning(key, text, source, sensitive=sensitive, daily_allowed=daily_allowed)


# Order inside a house is the curated order of the sources (house 5 opens with children, as in
# Lilly and BPHS). ``display_order`` decides what a reader sees first.
HOUSE_MEANINGS: dict[int, tuple[SourcedMeaning, ...]] = {
    1: (
        _m("body_appearance", "thân thể và vẻ ngoài", _B),
        _m("temperament", "tính cách, con người mình", _B),
        _m("vitality", "sức sống, sức bền", _C),
        _m("new_beginnings", "cách bước vào việc mới", _M),
        _m("inner_joy_sorrow", "vui buồn trong lòng", _J),
        _m("mind_intellect", "trí óc, sự tỉnh táo", _J),
    ),
    2: (
        _m("money_wealth", "tiền bạc, của cải", _B),
        _m("gain_loss", "chuyện được và mất về tiền", _C),
        _m("belongings", "đồ đạc mình đang có", _M),
        _m("self_worth", "cảm giác mình có giá trị", _M),
        _m("family_table", "gia đình, bữa ăn chung", _J),
        _m("precious_things", "trang sức, đồ quý", _J),
    ),
    3: (
        _m("siblings", "anh chị em", _B),
        _m("messages_news", "tin nhắn, thư từ, tin tức", _B),
        _m("everyday_learning", "việc học hằng ngày", _B),
        _m("neighbours_kin", "hàng xóm, họ hàng gần", _C),
        _m("short_trips", "những chuyến đi gần", _C),
        _m("courage", "lòng can đảm", _J),
        _m("ways_of_speaking", "cách nghĩ, cách nói năng", _M),
    ),
    4: (
        _m("home_dwelling", "nhà cửa, chỗ ở", _B),
        _m("parents_home", "cha mẹ", _B, sensitive=True),
        _m("land", "đất đai", _C),
        _m("how_things_close", "cách một việc khép lại", _C),
        _m("roots", "gốc rễ, nơi mình lớn lên", _M),
        _m("home_contentment", "niềm an vui trong nhà", _J),
        _m("vehicles", "xe cộ", _J),
    ),
    5: (
        _m("children", "chuyện con cái", _C, sensitive=True),
        _m("pleasure_feasts", "niềm vui, giải trí, tiệc tùng", _B),
        _m("creativity", "sáng tạo, tự thể hiện", _M),
        _m("romance", "tình yêu, rung động", _M),
        _m("sport_play", "thể thao, trò chơi", _M),
        _m("risk_taking", "chuyện may rủi, liều thử", _B, sensitive=True),
        _m("learning_intelligence", "việc học, trí tuệ", _J),
    ),
    6: (
        _m("daily_work", "công việc hằng ngày", _M),
        _m("body_care_habits", "thói quen chăm sóc cơ thể", _M),
        _m("small_animals", "vật nuôi nhỏ", _B),
        _m("helpers", "người giúp việc, người làm thuê", _C),
        _m("service", "giúp đỡ, phục vụ người khác", _M),
        _m("uncles_aunts", "cô dì chú bác", _C),
        _m("illness", "bệnh tật", _C, sensitive=True, daily_allowed=False),
    ),
    7: (
        _m("love", "tình yêu, người thương", _B),
        _m("marriage", "hôn nhân, vợ chồng", _B, sensitive=True),
        _m("business_partners", "đối tác làm ăn", _B),
        _m("open_opponents", "người đối đầu công khai", _B),
        _m("agreements", "thỏa thuận giữa hai người", _M),
        _m("desire_passion", "ham muốn, đam mê", _J),
        _m("lawsuits", "kiện tụng, tranh chấp", _C, sensitive=True, daily_allowed=False),
    ),
    8: (
        _m("shared_money", "tiền chung với người khác", _B),
        _m("deep_fears", "nỗi sợ sâu trong lòng", _C),
        _m("intimacy", "sự thân mật sâu", _M),
        _m("inner_change", "đổi thay từ bên trong", _M),
        _m("debts", "nợ nần", _M, sensitive=True),
        _m("legacy", "của người đã khuất để lại", _C, sensitive=True, daily_allowed=False),
        _m("longevity", "tuổi thọ", _J, sensitive=True, daily_allowed=False),
        _m("death_loss", "cái chết, mất người thân", _C, sensitive=True, daily_allowed=False),
    ),
    9: (
        _m("long_journeys", "những chuyến đi xa", _B),
        _m("higher_learning", "học cao, sách vở", _B),
        _m("faith", "niềm tin, tín ngưỡng", _B),
        _m("dreams", "giấc mơ", _C),
        _m("in_laws", "họ hàng bên vợ hoặc chồng", _C, sensitive=True),
        _m("life_philosophy", "triết lý sống, cách nhìn rộng", _M),
        _m("blessings", "phúc phần, điều lành", _J),
    ),
    10: (
        _m("career", "nghề nghiệp, sự nghiệp", _B),
        _m("reputation", "danh dự, tiếng tăm", _B),
        _m("position", "chức vụ, vị trí", _C),
        _m("authority", "cấp trên, người có quyền", _C),
        _m("parent_public", "cha hoặc mẹ", _B, sensitive=True),
        _m("lifelong_goal", "điều muốn xây lâu dài", _M),
        _m("living_abroad", "sống xa quê", _J),
    ),
    11: (
        _m("friends", "bạn bè", _B),
        _m("hopes_wishes", "hy vọng, mong ước", _B),
        _m("trust", "lòng tin, chỗ dựa", _C),
        _m("groups", "nhóm, cộng đồng", _M),
        _m("gains_income", "thu nhập, khoản được thêm", _J),
    ),
    12: (
        _m("rest_sleep", "nghỉ ngơi, giấc ngủ", _J),
        _m("quiet_sorrow", "nỗi buồn giữ trong lòng", _C),
        _m("solitude", "khoảng lặng, ở một mình", _M),
        _m("spiritual_life", "đời sống tâm linh", _M),
        _m("expenses", "chi tiêu, khoản tiền đi ra", _J),
        _m("hidden_opponents", "người ngầm chống mình", _C, sensitive=True, daily_allowed=False),
        _m("confinement", "tù tội, bị giam giữ", _C, sensitive=True, daily_allowed=False),
        _m("hospital", "bệnh viện", _M, sensitive=True, daily_allowed=False),
    ),
}


def _can_lead(meaning: SourcedMeaning) -> bool:
    return not meaning.sensitive and meaning.source in LEAD_SOURCES


def display_order(house: int, *, daily: bool) -> tuple[SourcedMeaning, ...]:
    """Meanings of ``house`` in display-safe order.

    The first meaning is never sensitive and never MODERN-only: it is the first meaning in
    curated order that a classical source (Lilly, BPHS or Phaladeepika) stands behind and that
    is not ⚠.
    The rest keep their curated order. ``daily=True`` drops every meaning that must never reach
    a daily reading (death, loss, illness, hospital, prison, lawsuits and the like).
    """

    if house not in HOUSE_MEANINGS:
        raise ValueError(f"house must be 1-12, got {house!r}")
    meanings = tuple(m for m in HOUSE_MEANINGS[house] if m.daily_allowed or not daily)
    lead = next(m for m in meanings if _can_lead(m))
    return (lead, *(m for m in meanings if m is not lead))


def meaning_by_key(key: str) -> SourcedMeaning:
    for meanings in HOUSE_MEANINGS.values():
        for meaning in meanings:
            if meaning.key == key:
                return meaning
    raise KeyError(key)
