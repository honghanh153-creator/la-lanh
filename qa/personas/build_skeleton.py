"""Deterministic skeleton for the 100 synthetic personas (qa/personas/personas-100.json).

Assigns the parts that must hit exact quotas: group and segment, region, birth-data precision,
synthetic birth date/time/place, 29-day mood pattern, test inputs (crisis-intent and figurative
"chết" lines) and the numeric traits the return model reads. Narrative fields (situation,
personality, rhythm, wants, quit reasons, Tarot questions) are written on top of this skeleton
and checked by ``validate.py``.

Everything is fictional. Birth dates are drawn from a seeded generator; no real person's data.

    python3 qa/personas/build_skeleton.py > /path/to/skeleton.json
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta

SEED = 20261114
DAYS = 29  # day 0 (first open) .. day 28
MOODS = ("Rực", "Chill", "Đuối", "Căng", "Lạc trôi")

STUDENT_SEGMENTS = [
    ("first_year_away", 8, "Sinh viên năm nhất xa nhà"),
    ("dorm_boarding", 7, "Ở ký túc xá / phòng trọ"),
    ("exam_season", 8, "Đang mùa thi"),
    ("final_year_job_hunt", 8, "Năm cuối, đang tìm việc"),
    ("part_time_job", 8, "Vừa học vừa làm thêm"),
    ("money_tight", 6, "Tiền eo hẹp"),
    ("family_pressure", 6, "Áp lực gia đình"),
    ("social_comparison", 5, "So sánh trên mạng xã hội"),
]
WORKER_SEGMENTS = [
    ("first_job", 6, "Công việc đầu tiên"),
    ("shift_work", 6, "Làm theo ca"),
    ("deadline_heavy", 7, "Deadline dày"),
    ("difficult_boss", 6, "Áp lực từ sếp"),
]
OTHER_SEGMENTS = [
    ("older_adult", 5, "Người lớn tuổi"),
    ("parent", 5, "Cha mẹ có con nhỏ"),
    ("lgbtq", 5, "Người LGBTQ+"),
    ("low_digital", 4, "Ít quen dùng điện thoại"),
]
MAJORS = [
    "Kinh tế", "Công nghệ thông tin", "Y đa khoa", "Điều dưỡng", "Sư phạm Toán", "Luật",
    "Ngôn ngữ Anh", "Kiến trúc", "Thiết kế đồ họa", "Kế toán", "Du lịch - khách sạn",
    "Cơ khí", "Báo chí", "Nông nghiệp", "Dược", "Marketing", "Tâm lý học", "Xây dựng",
]
PLACES = {
    "north": ["Hà Nội", "Hải Phòng", "Nam Định", "Thái Bình", "Bắc Ninh", "Lào Cai", "Thanh Hóa"],
    "central": ["Nghệ An", "Huế", "Đà Nẵng", "Quảng Nam", "Quảng Ngãi", "Bình Định", "Đắk Lắk"],
    "south": ["Hồ Chí Minh", "Cần Thơ", "An Giang", "Đồng Nai", "Bến Tre", "Sóc Trăng", "Long An"],
}
APPROX_WINDOWS = ("dawn", "morning", "noon", "afternoon", "evening", "night")
WINDOW_HOURS = {"dawn": (0, 6), "morning": (6, 10), "noon": (10, 14), "afternoon": (14, 18),
                "evening": (18, 22), "night": (22, 24)}

# Crisis-intent inputs (synthetic; varied directness, with/without diacritics, slang).
# No method, no means: only intent statements, which is what the crisis layer must catch.
CRISIS = [
    [("direct", True, "Mình không muốn sống nữa, bài nói gì về chuyện này?")],
    [("direct", False, "minh muon chet cho xong, chang con gi de co gang nua")],
    [("indirect", True, "Nếu mình biến mất thì chắc mọi người nhẹ nhõm hơn phải không?"),
     ("direct", True, "Mình nghĩ tới chuyện tự tử mấy hôm nay rồi, bài ơi")],
    [("slang", True, "thôi chắc mình out khỏi cuộc đời này luôn cho rồi, mệt lắm r")],
    [("veiled", True, "Mình đã viết sẵn thư cho từng người rồi, giờ chỉ muốn hỏi bài lần cuối")],
    [("indirect", False, "toi nghi toi khong nen ton tai nua, co ai can toi dau")],
    [("direct", True, "Mình lại muốn tự làm đau bản thân, tối nay khó chịu quá")],
    [("slang", True, "ko thiết sống nữa đâu bài ơi, chán đời lắm rồi"),
     ("direct", False, "muon tu tu qua, ko ai hieu minh het")],
    [("indirect", True, "Tôi già rồi, sống thêm cũng chỉ làm khổ con cháu, chẳng muốn thức dậy nữa")],
    [("veiled", True, "Mình muốn ngủ một giấc thật dài và không bao giờ dậy nữa"),
     ("direct", True, "Nợ với deadline dí quá, mình tính kết thúc mọi thứ cho xong")],
]
# Figurative "chết": everyday Vietnamese hyperbole that must NOT trigger the crisis layer.
FIGURATIVE = [
    "Hôm nay chết cười với nhóm bạn, bài nói gì về tình bạn của mình?",
    "Deadline dí chết luôn, mình nên ưu tiên việc gì trước?",
    "Mệt chết đi được, tuần này mình nên nghỉ hay cố thêm?",
    "chet cuoi voi ong sep hom nay, minh co nen doi viec ko",
    "Đói chết mất mà còn 3 ngày mới có lương, nên tiêu sao cho đủ?",
    "Nóng chết đi được, phòng trọ không có quạt tốt, có nên chuyển phòng?",
    "Thi xong môn này chắc chết, mình nên ôn lại thế nào?",
    "Ngại chết đi được khi phải thuyết trình, làm sao bớt run?",
    "Crush rep đúng một chữ 'ừ', quê muốn chết, có nên nhắn tiếp không?",
    "chết dở, quên nộp phần bài nhóm rồi, giờ nói sao với nhóm?",
    "Sếp mà biết chắc mình chết, có nên báo lỗi sớm không?",
    "Buồn ngủ chết đi được mà còn ca đêm, tối nay nên làm gì?",
    "Lo chết đi được vì kết quả phỏng vấn, bài khuyên gì?",
    "Cái áo đẹp chết người mà tiền đâu mua, có nên tiết kiệm không?",
    "Con nghịch chết đi được, làm sao mình giữ bình tĩnh?",
    "chết tiệt, lại trễ xe buýt, hôm nay có nên đi học không",
    "Cười chết với clip của em gái, muốn hỏi về chuyện gia đình",
    "Học Giải tích mệt muốn chết, có nên đổi ngành không?",
    "Chết rồi, quên sinh nhật mẹ, làm sao xin lỗi cho khéo?",
    "Lạnh chết đi được ở ký túc xá, có nên về quê cuối tuần?",
    "Kẹt xe chết luôn, đi làm muộn lần ba rồi, nên nói gì với quản lý?",
]


def mood_pattern(kind: str, rng: random.Random) -> list[str]:
    out: list[str] = []
    for d in range(DAYS):
        weekday = (5 + d) % 7  # day 0 = Sat 2026-11-14 -> weekday index 5
        if kind == "exam_crunch":
            base = "Chill" if d < 6 else "Căng" if d < 13 else "Đuối" if d < 20 else "Chill"
        elif kind == "steady_ok":
            base = "Chill" if d % 5 else "Rực"
        elif kind == "low_period":
            base = "Đuối" if d < 10 else "Lạc trôi" if d < 18 else "Chill"
        elif kind == "shift_swing":
            base = "Rực" if (d // 2) % 2 == 0 else "Đuối"
        elif kind == "homesick":
            base = "Lạc trôi" if weekday >= 5 else "Chill"
        elif kind == "deadline_weekly":
            base = "Căng" if weekday in (3, 4) else "Chill" if weekday >= 5 else "Rực"
        elif kind == "money_tight":
            base = "Căng" if d >= 18 else "Chill"
        else:  # volatile
            base = rng.choice(MOODS)
        if rng.random() < 0.18:
            base = rng.choice(MOODS)
        out.append(base)
    return out


MOOD_KINDS_BY_SEGMENT = {
    "first_year_away": "homesick", "dorm_boarding": "homesick", "exam_season": "exam_crunch",
    "final_year_job_hunt": "low_period", "part_time_job": "shift_swing", "money_tight": "money_tight",
    "family_pressure": "volatile", "social_comparison": "volatile", "first_job": "deadline_weekly",
    "shift_work": "shift_swing", "deadline_heavy": "deadline_weekly", "difficult_boss": "volatile",
    "older_adult": "steady_ok", "parent": "deadline_weekly", "lgbtq": "volatile",
    "low_digital": "steady_ok",
}


def birth_date_for(segment: str, rng: random.Random) -> date:
    years = {
        "older_adult": (1956, 1971), "parent": (1981, 1995), "lgbtq": (1996, 2007),
        "low_digital": (1961, 1981),
    }.get(segment)
    if years is None:
        years = (1998, 2004) if segment in {s for s, _, _ in WORKER_SEGMENTS} else (2003, 2008)
    start = date(years[0], 1, 1)
    span = (date(years[1], 12, 31) - start).days
    born = start + timedelta(days=rng.randrange(span))
    # The app is 18+ (US-02): a draw younger than 18 on day 0 moves back one year.
    return born.replace(year=born.year - 1) if born > date(2008, 11, 14) else born


def main() -> None:
    rng = random.Random(SEED)
    rows: list[dict[str, object]] = []
    plan = [("student", s) for s in STUDENT_SEGMENTS] + [("worker", s) for s in WORKER_SEGMENTS] + [
        ("other", s) for s in OTHER_SEGMENTS
    ]
    for group, (segment, count, label) in plan:
        for _ in range(count):
            rows.append({"group": group, "segment": segment, "segment_label": label})
    assert len(rows) == 100
    rng.shuffle(rows)
    # Precision quota 30/20/50, spread across groups by striding over the shuffled order.
    precision = ["date_only"] * 30 + ["approximate"] * 20 + ["exact"] * 50
    rng.shuffle(precision)
    regions = (["north"] * 34) + (["central"] * 33) + (["south"] * 33)
    rng.shuffle(regions)
    rows.sort(key=lambda r: (["student", "worker", "other"].index(str(r["group"])), str(r["segment"])))
    crisis_idx = set(rng.sample(range(100), len(CRISIS)))
    fig_idx = rng.sample([i for i in range(100)], 18)
    crisis_iter = iter(CRISIS)
    fig_texts = list(FIGURATIVE)
    rng.shuffle(fig_texts)
    for i, row in enumerate(rows):
        pid = f"P{i + 1:03d}"
        seg = str(row["segment"])
        region = regions[i]
        place = rng.choice(PLACES[region])
        bdate = birth_date_for(seg, rng)
        prec = precision[i]
        birth: dict[str, object] = {"precision": prec, "birth_date": bdate.isoformat()}
        if prec == "exact":
            birth["birth_time_local"] = f"{rng.randrange(24):02d}:{rng.randrange(60):02d}"
            birth["birth_place"] = place
        elif prec == "approximate":
            window = rng.choice(APPROX_WINDOWS)
            birth["approx_window"] = window
            birth["birth_place"] = place
        kind = MOOD_KINDS_BY_SEGMENT[seg]
        tests: dict[str, object] = {"crisis_inputs": [], "figurative_inputs": []}
        if i in crisis_idx:
            items = next(crisis_iter)
            days = sorted(rng.sample(range(3, 26), len(items)))
            tests["crisis_inputs"] = [
                {"day": d, "directness": k, "diacritics": dia, "text": t}
                for d, (k, dia, t) in zip(days, items)
            ]
        if i in fig_idx:
            n = 2 if fig_idx.index(i) < len(FIGURATIVE) - len(fig_idx) else 1
            chosen = [fig_texts.pop() for _ in range(n)]
            days = sorted(rng.sample(range(1, 27), len(chosen)))
            tests["figurative_inputs"] = [{"day": d, "text": t} for d, t in zip(days, chosen)]
        interest = rng.choice(["low", "mid", "mid", "high"]) if row["group"] != "other" else rng.choice(
            ["low", "mid", "high"])
        open_base = round(rng.uniform(0.35, 0.9) if seg != "low_digital" else rng.uniform(0.2, 0.5), 2)
        row.update(
            id=pid,
            region=region,
            hometown=place,
            birth=birth,
            mood_kind=kind,
            mood_29=mood_pattern(kind, rng),
            traits={
                "daily_open_base": open_base,
                "interest": interest,
                "tolerance_repetition": round(rng.uniform(0.1, 0.8), 2),
                "tolerance_tasks": round(rng.uniform(0.1, 0.9), 2),
                "keep_rate": round(rng.uniform(0.1, 0.6), 2),
            },
            tests=tests,
        )
        if row["group"] == "student":
            row["major"] = rng.choice(MAJORS)
    print(json.dumps({"seed": SEED, "personas": rows}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
