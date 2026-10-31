"""Deterministic, evidence-bound relationship readings for Hợp gu (Radar).

The projector receives chart facts, never raw birth inputs. Renderer ``radar-readable-v2``
(29/10/2026, owner feedback + research report "Phương án sửa Tarot và Hợp gu", Phần B):

- a named tier per context with a one-line reason, ranked against a fixed synthetic reference
  distribution, instead of three compressed 0-100 numbers (no number by default; see
  ``SHOW_TIER_SCORE``);
- one headline about how the two interact, without a forced "nhưng";
- a "cần để ý" paragraph only when a friction signal crosses ``TENSION_THRESHOLD``;
- context-specific areas (crush / friend / partner / someone) and copy;
- plain Vietnamese in the default view; astrology terms only in the "Xem thêm" layer;
- one fixed calm closing line instead of a hedging kicker.

It describes how two people interact; it never says what the absent person thinks, feels or
wants, and makes no fate or success claim.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from typing import Any

from app.domains.astro.models import (
    BodyName,
    CompositeAspect,
    HouseOverlay,
    RelationshipBundle,
    SynastryContact,
)
from app.domains.relationships.knowledge import (
    RELATIONSHIP_KNOWLEDGE_VERSION,
    build_editorial_plan,
    voice_profile,
)
from app.domains.relationships.models import RelationshipPrompt, RelationshipVoice

RESULT_VERSION = "radar-result-v2"
RENDERER_VERSION = "radar-readable-v2"
# Readings stored by the previous renderer stay as they were until they expire.
PREVIOUS_RENDERER_VERSIONS = ("radar-living-dossier-v1",)
GATE_VERSION = "conditional-reflection-v4"
TIER_CALIBRATION_VERSION = "radar-tier-ref-v1"

# Owner switch (decision 6 of the research report). False: the tier has no number, which keeps
# the spec invariant "no scalar compatibility score". True adds ``tier.score``, the pair's rank
# (0-100) against the reference distribution; turning it on lifts that invariant and needs the
# owner's explicit decision, a new GATE_VERSION and a fallback-approval refresh.
SHOW_TIER_SCORE = False

# Weight of friction against coordination in the ease signal that ranks a pair.
EASE_FRICTION_WEIGHT = 0.6
# A cluster whose friction reaches this value (and exceeds its coordination) gets a "cần để ý"
# paragraph. At 0.6 about 40% of reference pairs show one (owner decision 9).
TENSION_THRESHOLD = 0.6
# A calm cluster reads "hợp" (and may join "Điều trôi chảy" as a second theme) only when its
# coordination reaches this value; below it, "cân bằng". Calibrated so "hợp" tracks the tier.
GOOD_MIN_COORDINATION = 0.45

# Ease quantiles of the reference distribution ``radar-tier-ref-v1`` at p0, p5, ..., p100:
# 2,000 synthetic pairs from a fixed seed (``scripts.radar_tier_reference``), no user data.
TIER_REFERENCE = (
    -0.2216,
    -0.013,
    0.0445,
    0.08,
    0.1095,
    0.129,
    0.1466,
    0.1645,
    0.1835,
    0.1999,
    0.2145,
    0.2305,
    0.246,
    0.265,
    0.2857,
    0.305,
    0.3273,
    0.3487,
    0.3857,
    0.4298,
    0.6565,
)

# Tier by rank against the reference: top 15%, next 25%, middle 30%, next 20%, last 10%.
TIER_BANDS = (
    ("very_easy", 85.0),
    ("easy", 60.0),
    ("complementary", 30.0),
    ("warming_up", 10.0),
    ("patient", 0.0),
)

CONTEXTS = ("crush", "friend", "partner", "someone")


@dataclass(frozen=True)
class Motif:
    key: str
    label: str
    contact: SynastryContact
    evidence_id: str
    resonance: float
    coordination: float
    friction: float


@dataclass(frozen=True)
class ThemeCluster:
    key: str
    label: str
    motifs: tuple[Motif, ...]
    resonance: float
    coordination: float
    friction: float


@dataclass(frozen=True)
class PairSignals:
    """Everything the copy is chosen from; no text, so it can be calibrated and tested."""

    motifs: tuple[Motif, ...]
    clusters: tuple[ThemeCluster, ...]
    ease: float
    percentile: float
    tier: str
    # The easiest theme that is not "watch"; positive copy is used only for a "good" one.
    fit: ThemeCluster | None
    support: ThemeCluster | None
    tension: ThemeCluster | None
    levels: dict[str, str]


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
    "conjunction": "đồng vị",
    "trine": "tam hợp",
    "sextile": "lục hợp",
    "square": "vuông",
    "opposition": "đối đỉnh",
}

ASPECT_CHANNELS = {
    "conjunction": (0.95, 0.60, 0.42),
    "trine": (0.76, 0.96, 0.08),
    "sextile": (0.65, 0.84, 0.06),
    "square": (0.78, 0.24, 0.98),
    "opposition": (0.86, 0.28, 0.94),
}

BODY_WEIGHT = {
    BodyName.SUN: 1.00,
    BodyName.MOON: 1.00,
    BodyName.MERCURY: 1.00,
    BodyName.VENUS: 1.00,
    BodyName.MARS: 1.00,
    BodyName.JUPITER: 0.82,
    BodyName.SATURN: 0.92,
    BodyName.URANUS: 0.76,
    BodyName.NEPTUNE: 0.80,
    BodyName.PLUTO: 0.82,
    BodyName.TRUE_NODE: 0.58,
    BodyName.MEAN_NODE: 0.58,
    BodyName.SOUTH_NODE: 0.52,
    BodyName.CHIRON: 0.58,
}

# Plain areas of life, used only in the "Xem thêm" layer (two sides of the same meeting).
HOUSE_AREAS = {
    1: "ấn tượng đầu tiên khi gặp nhau",
    2: "cảm giác an tâm và chuyện cho - nhận",
    3: "chuyện trò, nhắn tin hằng ngày",
    4: "chuyện nhà, chuyện riêng tư",
    5: "niềm vui, sở thích và cách thể hiện sự thích",
    6: "nếp sinh hoạt và những việc nhỏ hằng ngày",
    7: "sự công bằng giữa hai người",
    8: "niềm tin và những chuyện khó nói",
    9: "trải nghiệm mới và chuyện học hỏi",
    10: "mục tiêu và hình ảnh bên ngoài",
    11: "bạn bè, nhóm chung và kế hoạch phía trước",
    12: "những điều nhạy cảm, cần thời gian mới nói ra",
}

BODY_SHARED_ROLES = {
    BodyName.SUN: "nhu cầu được ghi nhận",
    BodyName.MOON: "tâm trạng và cảm giác an tâm",
    BodyName.MERCURY: "cách hai người nói và hiểu",
    BodyName.VENUS: "sự dễ chịu và quan tâm",
    BodyName.MARS: "sự chủ động",
    BodyName.JUPITER: "sự lạc quan và muốn thử thêm",
    BodyName.SATURN: "sự nghiêm túc và giữ lời",
    BodyName.URANUS: "nhu cầu tự do và đổi mới",
    BodyName.NEPTUNE: "trí tưởng tượng và những điều còn để ngỏ",
    BodyName.PLUTO: "độ sâu của mối quan hệ",
    BodyName.TRUE_NODE: "một hướng còn mới với cả hai",
    BodyName.MEAN_NODE: "một hướng còn mới với cả hai",
    BodyName.SOUTH_NODE: "những thói quen đã quen",
    BodyName.CHIRON: "những điểm dễ tổn thương",
}

LOW_PERSONALIZATION_BODIES = {
    BodyName.URANUS,
    BodyName.NEPTUNE,
    BodyName.PLUTO,
    BodyName.TRUE_NODE,
    BodyName.MEAN_NODE,
    BodyName.SOUTH_NODE,
    BodyName.CHIRON,
}

THEME_PLAIN = {
    "communication": "cách nói chuyện",
    "emotional": "cách nhận ra cảm xúc của nhau",
    "attraction": "sự hào hứng khi ở gần nhau",
    "pace": "sự đều đặn và giữ lời",
    "clarity": "trí tưởng tượng chung",
    "freedom": "sự mới mẻ khi ở cạnh nhau",
    "intensity": "độ sâu khi trò chuyện",
    "visibility": "cách cổ vũ nhau",
}

# Owner decision 8: one set of tier names per context, no "định mệnh", lowest tier not a verdict.
TIER_LABELS = {
    "crush": {
        "very_easy": "Dễ bắt nhịp",
        "easy": "Dễ bắt chuyện",
        "complementary": "Có nhiều điều để tò mò",
        "warming_up": "Cần thêm thời gian làm quen",
        "patient": "Nhịp khá khác nhau",
        "unclear": "Chưa đủ dữ kiện để xếp bậc",
    },
    "friend": {
        "very_easy": "Rất hợp cạ",
        "easy": "Hợp chuyện",
        "complementary": "Bổ sung cho nhau",
        "warming_up": "Cần thời gian làm quen",
        "patient": "Khác nhịp, cần kiên nhẫn",
        "unclear": "Chưa đủ dữ kiện để xếp bậc",
    },
    "partner": {
        "very_easy": "Rất ăn ý",
        "easy": "Ăn ý",
        "complementary": "Bổ sung cho nhau",
        "warming_up": "Cần thêm thời gian hiểu nhau",
        "patient": "Khác nhịp, cần nhiều kiên nhẫn",
        "unclear": "Chưa đủ dữ kiện để xếp bậc",
    },
    "someone": {
        "very_easy": "Rất ăn ý",
        "easy": "Ăn ý",
        "complementary": "Bổ sung cho nhau",
        "warming_up": "Cần làm quen",
        "patient": "Khác nhịp, cần kiên nhẫn",
        "unclear": "Chưa đủ dữ kiện để xếp bậc",
    },
}

TIER_REASONS = {
    "very_easy": "Nhiều điểm của hai bạn đi cùng chiều, rõ nhất là {fit}.",
    "easy": "Hai bạn có khá nhiều điểm dễ đi cùng, nổi bật là {fit}.",
    "complementary": "Hai bạn có chỗ giống, có chỗ khác; chỗ dễ bắt đầu nhất là {fit}.",
    "warming_up": "Nhiều điểm của hai bạn cần thời gian để quen nhịp; chỗ dễ bắt đầu là {fit}.",
    "patient": "Hai bạn khác nhịp ở nhiều chỗ, nên cần kiên nhẫn hơn; chỗ dễ bắt đầu là {fit}.",
}

HEADLINES = {
    "communication": {
        "crush": "Hai bạn dễ bắt chuyện với nhau.",
        "friend": "Hai bạn có thể nói chuyện hàng giờ mà không thấy mệt.",
        "partner": "Hai bạn dễ nói cho nhau hiểu.",
        "someone": "Nói chuyện với nhau là điểm dễ nhất của hai bạn.",
    },
    "emotional": {
        "crush": "Hai bạn dễ cảm được tâm trạng của nhau.",
        "friend": "Hai bạn là kiểu bạn dễ để ý tới nhau.",
        "partner": "Hai bạn dễ chăm cho nhau qua những điều nhỏ.",
        "someone": "Hai bạn dễ đồng cảm với nhau.",
    },
    "attraction": {
        "crush": "Ở gần nhau, không khí giữa hai bạn dễ sôi nổi.",
        "friend": "Hai bạn dễ rủ nhau làm gì đó cho vui.",
        "partner": "Hai bạn dễ giữ được sự hào hứng khi ở bên nhau.",
        "someone": "Ở gần nhau, hai bạn dễ có thêm năng lượng.",
    },
    "pace": {
        "crush": "Hai bạn dễ giữ được một nhịp trò chuyện đều.",
        "friend": "Hai bạn dễ thành bạn đáng tin của nhau.",
        "partner": "Hai bạn dễ cùng xây một nhịp sống ổn định.",
        "someone": "Hai bạn dễ phối hợp với nhau.",
    },
    "clarity": {
        "crush": "Hai bạn dễ cùng nhau mơ mộng.",
        "friend": "Hai bạn dễ có một thế giới riêng.",
        "partner": "Hai bạn dễ có chung những ước mơ.",
        "someone": "Hai bạn dễ hiểu nhau mà không cần nói nhiều.",
    },
    "freedom": {
        "crush": "Ở cạnh nhau, mọi thứ dễ thấy mới mẻ.",
        "friend": "Hai bạn hay kéo nhau đi thử điều mới.",
        "partner": "Hai bạn dễ vừa gắn bó vừa thoải mái.",
        "someone": "Hai bạn dễ làm mới nhau.",
    },
    "intensity": {
        "crush": "Hai bạn ít khi chỉ nói chuyện xã giao.",
        "friend": "Hai bạn dễ thành bạn để nói chuyện thật lòng.",
        "partner": "Hai bạn dễ gắn bó sâu với nhau.",
        "someone": "Hai bạn dễ đi sâu khi trò chuyện.",
    },
    "visibility": {
        "crush": "Hai bạn dễ làm nhau cười và tự tin hơn.",
        "friend": "Hai bạn dễ thành cổ động viên của nhau.",
        "partner": "Hai bạn dễ làm nhau thấy được trân trọng.",
        "someone": "Hai bạn dễ làm nhau tỏa sáng hơn.",
    },
}

FIT_COPY = {
    "communication": {
        "crush": (
            "Câu chuyện giữa hai bạn dễ đi từ chuyện vặt sang chuyện thật. Một câu hỏi nhỏ "
            "cũng đủ mở ra cả buổi trò chuyện."
        ),
        "friend": (
            "Hai bạn bắt ý nhau nhanh và hay đùa cùng một kiểu. Nhắn qua nhắn lại vài câu là "
            "đủ hiểu bạn mình đang muốn nói gì."
        ),
        "partner": (
            "Chuyện lớn hay chuyện nhỏ, hai bạn đều dễ tìm ra cách nói cho nhau hiểu. Lúc cần "
            "bàn việc chung, hai bạn ít phải vòng vo."
        ),
        "someone": (
            "Hai bạn dễ nối câu và hiểu ý nhau. Cuộc trò chuyện thường tự trôi mà không cần cố."
        ),
    },
    "emotional": {
        "crush": (
            "Không cần nói nhiều, hai bạn vẫn dễ bắt được không khí khi gặp nhau. Điều đó làm "
            "những lần gặp đầu bớt gượng."
        ),
        "friend": (
            "Hai bạn dễ thấy khi bạn mình đang không ổn. Một câu hỏi han đúng lúc giữa hai bạn "
            "thường có sức nặng."
        ),
        "partner": (
            "Hai bạn dễ nhận ra khi nào nhau cần được ở gần, khi nào cần yên. Một tin nhắn hỏi "
            "han đúng lúc thường đủ để cả hai thấy yên lòng."
        ),
        "someone": (
            "Hai bạn dễ nhận ra tâm trạng của nhau. Một lời hỏi thăm nhẹ thường đủ để không khí "
            "dễ chịu hơn."
        ),
    },
    "attraction": {
        "crush": (
            "Những việc nhỏ như chủ động hỏi han hay dành thời gian cho nhau thường dễ được để "
            "ý. Gặp nhau vài lần là hai bạn đã có chuyện để nhắc lại."
        ),
        "friend": (
            "Hai bạn có năng lượng hợp nhau, đi đâu cũng dễ vui. Ở cạnh nhau, hai bạn ít khi "
            "thấy chán."
        ),
        "partner": (
            "Sau những ngày bận, hai bạn vẫn dễ tìm lại cảm giác muốn ở gần nhau. Những cử chỉ "
            "quan tâm nhỏ giữa hai bạn thường có tác dụng."
        ),
        "someone": (
            "Ở gần nhau, việc chủ động bắt chuyện hay rủ nhau làm gì đó thường không khó. Không "
            "khí giữa hai bạn dễ sôi nổi."
        ),
    },
    "pace": {
        "crush": ("Hai bạn không dồn dập cũng không bỏ lửng nhau. Hẹn gì thì dễ nhớ và dễ giữ."),
        "friend": (
            "Hai bạn dễ thành kiểu bạn hẹn là đến, nói là làm. Kế hoạch chung giữa hai bạn ít "
            "khi bị bỏ dở."
        ),
        "partner": (
            "Hai bạn dễ xây những thói quen chung đáng tin, như giờ gọi nhau hay cách chia việc. "
            "Sự đều đặn này giúp cả hai thấy yên tâm."
        ),
        "someone": (
            "Việc chung giữa hai bạn thường được làm tới nơi tới chốn. Phần ai nấy lo cũng dễ "
            "rõ ràng."
        ),
    },
    "clarity": {
        "crush": (
            "Từ bộ phim muốn xem tới nơi muốn đi, hai bạn dễ nghĩ ra những điều thú vị cùng "
            "nhau. Trò chuyện vì thế dễ có màu sắc."
        ),
        "friend": (
            "Hai bạn dễ có những câu đùa mà chỉ hai đứa hiểu. Một ánh mắt hay một từ khoá là đủ."
        ),
        "partner": (
            "Hai bạn dễ cùng nhau hình dung những điều đẹp phía trước. Nói về tương lai, hai bạn "
            "dễ thấy mình đi cùng một hướng."
        ),
        "someone": "Hai bạn dễ bắt được ý ngầm và câu đùa của nhau. Trò chuyện vì thế nhẹ và vui.",
    },
    "freedom": {
        "crush": (
            "Gặp nhau, hai bạn dễ nảy ra những ý tưởng bất ngờ. Không ai phải đóng một vai cố định."
        ),
        "friend": (
            "Đi với nhau, hai bạn dễ có những trải nghiệm chưa từng có. Mỗi người cũng dễ tôn "
            "trọng khoảng riêng của người còn lại."
        ),
        "partner": (
            "Mỗi người vẫn giữ được không gian riêng trong khi ở bên nhau. Những thay đổi trong "
            "cuộc sống chung ít làm hai bạn hoảng."
        ),
        "someone": "Hai bạn dễ kéo nhau ra khỏi lối quen. Ở cạnh nhau, hai bạn khó thấy nhàm.",
    },
    "intensity": {
        "crush": (
            "Chỉ vài lần trò chuyện, hai bạn đã có thể chạm tới những điều thật. Câu chuyện giữa "
            "hai bạn dễ có chiều sâu."
        ),
        "friend": (
            "Những chuyện khó nói thường dễ được kể với nhau. Tình bạn kiểu này thường bền hơn "
            "sau vài chuyện khó."
        ),
        "partner": (
            "Khi đã tin, cả hai dễ mở lòng về những điều ít ai biết. Sự nghiêm túc giữa hai bạn "
            "thường đến sớm."
        ),
        "someone": (
            "Hai bạn khó chỉ dừng ở chuyện bề mặt. Một cuộc trò chuyện ngắn cũng có thể để lại "
            "ấn tượng."
        ),
    },
    "visibility": {
        "crush": (
            "Hai bạn dễ khen nhau đúng chỗ. Ở cạnh nhau, mỗi người dễ thể hiện mặt tốt của mình."
        ),
        "friend": (
            "Từ chuyện học, chuyện làm tới sở thích riêng, hai bạn dễ đứng về phía nhau. Có bạn "
            "bên cạnh, mỗi người dám thử hơn."
        ),
        "partner": (
            "Một lời ghi nhận nhỏ giữa hai bạn thường đi đúng chỗ. Hai bạn dễ nhớ và nhắc lại "
            "điều nhau làm tốt."
        ),
        "someone": (
            "Hai bạn dễ làm nhau tự tin hơn. Sự ghi nhận qua lại khiến những lần gặp dễ chịu."
        ),
    },
}

# A situation and one step. Shown only above TENSION_THRESHOLD.
TENSION_COPY = {
    "communication": {
        "crush": (
            "Lúc nhắn tin, một câu trả lời cụt hay chậm dễ bị hiểu thành lạnh nhạt. Nếu thấy "
            "chột dạ, hỏi lại một câu thay vì tự đoán."
        ),
        "friend": (
            "Khi đang vội hoặc mệt, cách nói thẳng của một người dễ làm người còn lại chạnh "
            'lòng. Lúc đó, nói rõ "mình đang vội, không phải giận" là đủ.'
        ),
        "partner": (
            "Khi bàn chuyện quan trọng, hai bạn dễ phản ứng với giọng nói trước khi nghe hết ý. "
            "Thử nhắc lại ý của nhau một lần trước khi trả lời."
        ),
        "someone": (
            "Một câu nói thiếu ngữ cảnh dễ làm hai bạn hiểu lệch nhau. Hỏi lại một ý cụ thể sẽ "
            "nhanh hơn đoán thái độ."
        ),
    },
    "emotional": {
        "crush": (
            "Hai bạn có thể có cách quan tâm khác nhau: một người muốn được hỏi han ngay, một "
            "người cần yên một lúc. Nói trước mình thuộc kiểu nào sẽ đỡ hụt nhau."
        ),
        "friend": (
            "Khi một người cần ở một mình, người còn lại dễ hiểu thành bị bỏ rơi. Thử hẹn trước "
            'một câu báo hiệu như "mình cần sạc pin, mai nói tiếp nhé".'
        ),
        "partner": (
            "Lúc một người buồn, người còn lại dễ lao vào sửa vấn đề trong khi điều cần là được "
            "nghe. Hỏi trước một câu: cần mình nghe, hay cần mình cùng tìm cách?"
        ),
        "someone": (
            'Hai bạn có thể cần được an ủi theo những cách khác nhau. Hỏi thẳng "lúc này bạn '
            'cần gì?" sẽ đỡ phải đoán.'
        ),
    },
    "attraction": {
        "crush": (
            "Sự hào hứng lúc đầu dễ làm nhịp của hai bạn lệch nhau: một người muốn tiến nhanh, "
            "một người muốn từ từ. Để cả hai cùng chủ động sẽ dễ chịu hơn."
        ),
        "friend": (
            "Hai bạn đều có ý riêng, nên chuyện chọn chỗ đi hay việc làm chung dễ thành giành "
            "phần. Thay phiên nhau quyết là cách đơn giản."
        ),
        "partner": (
            "Khi một người muốn gần gũi mà người còn lại đang mệt, dễ có cảm giác bị từ chối. "
            'Nói rõ "không phải lúc này, không phải không muốn" giúp cả hai nhẹ lòng.'
        ),
        "someone": (
            "Năng lượng mạnh dễ làm hai bạn tranh nhau dẫn dắt. Chia rõ ai lo việc gì sẽ đỡ "
            "va chạm."
        ),
    },
    "pace": {
        "crush": (
            "Một người có thể muốn rõ ràng sớm, người còn lại muốn để mọi thứ tự nhiên. Không cần "
            "chốt gì vội; hỏi nhau về nhịp thấy thoải mái là đủ."
        ),
        "friend": (
            "Khi kế hoạch bị đổi hoặc trễ hẹn, chuyện nhỏ dễ thành khó chịu. Báo sớm khi có thay "
            "đổi sẽ giữ được sự tin nhau."
        ),
        "partner": (
            "Hai bạn có thể khác nhau về tốc độ cam kết hay cách chia trách nhiệm. Nói rõ điều "
            "mỗi người mong đợi sẽ giúp sự nghiêm túc không thành áp lực."
        ),
        "someone": (
            "Hai bạn có thể khác nhau về tốc độ và mức chặt chẽ. Thống nhất trước việc gì cần "
            "đúng hạn sẽ đỡ căng."
        ),
    },
    "clarity": {
        "crush": (
            "Những điều chưa nói rõ dễ được trí tưởng tượng tự điền vào. Nếu đang mong chờ điều "
            "gì, hỏi nhẹ một câu sẽ tốt hơn tự đoán."
        ),
        "friend": (
            'Lời hẹn kiểu "để tính" dễ làm một người chờ, một người quên. Chốt rõ ngày giờ sẽ '
            "tránh hụt hẫng."
        ),
        "partner": (
            "Những kỳ vọng chưa nói ra dễ thành hiểu lầm. Thỉnh thoảng nói thẳng điều mình mong "
            "sẽ giúp ước mơ chung không thành gánh nặng."
        ),
        "someone": (
            "Một lời hẹn hay một ý chưa nói rõ dễ làm hai bạn hiểu mỗi người một kiểu. Nhắc lại "
            "điều đã thống nhất sẽ đỡ nhầm."
        ),
    },
    "freedom": {
        "crush": (
            "Một người thích bất ngờ, một người cần biết trước, nên nhịp gặp nhau dễ chập chờn. "
            "Báo trước khi đổi kế hoạch là đủ để cả hai yên tâm."
        ),
        "friend": (
            "Khi một người cần biến mất một thời gian, người còn lại dễ thấy bị gạt ra. Nhắn một "
            'câu ngắn trước khi "tắt sóng" sẽ giữ được tình bạn.'
        ),
        "partner": (
            "Nhu cầu tự do của một người có thể làm người còn lại thấy chông chênh. Thoả thuận "
            "trước về khoảng riêng giúp cả hai không phải đoán."
        ),
        "someone": "Sự thay đổi phút chót dễ làm hai bạn lệch nhau. Báo trước một chút là đủ.",
    },
    "intensity": {
        "crush": (
            "Vì dễ đi sâu, một câu nói vô tình cũng có thể chạm tự ái. Giữ nhịp nhẹ nhàng ở "
            "những lần đầu sẽ giúp cả hai thoải mái."
        ),
        "friend": (
            "Khi có chuyện không vui, hai bạn dễ để nó âm ỉ lâu hơn bình thường. Nói ra sớm, "
            "dù chỉ một câu, sẽ nhẹ hơn để dồn."
        ),
        "partner": (
            "Cảm xúc mạnh dễ làm một chuyện nhỏ thành căng thẳng lớn. Tạm dừng khi cả hai đang "
            "nóng và hẹn quay lại sau là cách an toàn."
        ),
        "someone": (
            "Độ sâu cũng làm phản ứng mạnh hơn mức chuyện đáng có. Dừng một nhịp trước khi trả "
            "lời sẽ giúp ích."
        ),
    },
    "visibility": {
        "crush": (
            "Hai bạn có thể thích được ghi nhận theo những cách khác nhau. Một lời khen cụ thể "
            "thường đi xa hơn một lời khen chung chung."
        ),
        "friend": (
            "Khi cả hai đều muốn được chú ý, có lúc một người thấy mình bị lu mờ. Thay phiên làm "
            '"nhân vật chính" của buổi gặp sẽ công bằng hơn.'
        ),
        "partner": (
            "Mỗi người có thể cần được ghi nhận theo một kiểu: lời nói, hành động hay thời gian. "
            "Hỏi nhau kiểu nào hợp sẽ đỡ cố mà không trúng."
        ),
        "someone": (
            "Hai bạn có thể muốn được ghi nhận theo cách khác nhau. Một lời cảm ơn cụ thể thường "
            "hiệu quả hơn lời khen chung."
        ),
    },
}

# One small thing to do and one question the user can ask (never a guess about the other).
SUGGESTIONS = {
    "communication": {
        "crush": (
            "Lần tới nhắn tin, thử hỏi một câu mở về điều bạn ấy đang thích dạo này.",
            "Dạo này có gì làm cậu thấy vui không?",
        ),
        "friend": (
            "Rủ nhau một buổi nói chuyện không điện thoại, chỉ hai đứa.",
            "Có chuyện gì gần đây cậu muốn kể mà chưa có dịp không?",
        ),
        "partner": (
            "Dành mười phút cuối ngày để kể nhau nghe một chuyện nhỏ.",
            "Hôm nay có lúc nào bạn thấy được hiểu, hoặc chưa được hiểu không?",
        ),
        "someone": (
            "Lần tới gặp, thử hỏi một câu mà bạn thật sự muốn biết câu trả lời.",
            "Bạn thích được nói chuyện theo kiểu nào nhất?",
        ),
    },
    "emotional": {
        "crush": (
            "Khi thấy không khí trầm xuống, hỏi nhẹ một câu rồi để bạn ấy tự chọn kể hay không.",
            "Hôm nay của cậu thế nào?",
        ),
        "friend": (
            "Hẹn với nhau một câu báo hiệu khi ai đó cần ở một mình.",
            "Khi mệt, cậu muốn được hỏi han hay được để yên?",
        ),
        "partner": (
            "Thử nói với nhau một điều nhỏ giúp mình thấy được thương.",
            "Điều gì nhỏ thôi nhưng làm bạn thấy được quan tâm?",
        ),
        "someone": (
            "Thử hỏi thăm một câu đơn giản và nghe trọn câu trả lời.",
            "Lúc buồn, bạn thích được an ủi theo cách nào?",
        ),
    },
    "attraction": {
        "crush": (
            "Rủ nhau làm một việc nhỏ cùng nhau, như đi uống nước hay cùng xem một bộ phim.",
            "Cuối tuần này cậu có muốn làm gì cho vui không?",
        ),
        "friend": (
            "Lên một kế hoạch đi chơi mà mỗi người chọn một phần.",
            "Có chỗ nào cậu muốn đi mà chưa đi được không?",
        ),
        "partner": (
            "Thử làm lại một điều hai bạn từng rất thích làm cùng nhau.",
            "Có việc gì bạn muốn hai đứa làm cùng nhau thêm không?",
        ),
        "someone": (
            "Thử cùng nhau làm một việc nhỏ, ít áp lực.",
            "Bạn thường nạp năng lượng bằng cách nào?",
        ),
    },
    "pace": {
        "crush": (
            "Giữ một nhịp nhắn tin thoải mái và để mọi thứ tiến từ từ.",
            "Cậu thích nói chuyện thường xuyên hay thỉnh thoảng thôi?",
        ),
        "friend": (
            "Chốt một kế hoạch cụ thể với ngày giờ rõ ràng.",
            "Lần tới mình gặp vào hôm nào thì tiện cho cậu?",
        ),
        "partner": (
            "Cùng nhau chọn một thói quen nhỏ muốn giữ mỗi tuần.",
            "Có thói quen chung nào bạn muốn hai đứa giữ không?",
        ),
        "someone": (
            "Thống nhất trước một việc nhỏ cần làm chung và hạn của nó.",
            "Bạn thích làm việc theo kế hoạch hay linh hoạt?",
        ),
    },
    "clarity": {
        "crush": (
            "Khi đang mong chờ điều gì, nói nhẹ ra thay vì chờ được đoán.",
            "Cậu có hay thích lên kế hoạch trước không?",
        ),
        "friend": (
            "Biến một câu đùa riêng của hai đứa thành một kế hoạch thật.",
            'Có điều gì hai đứa hay nói "để hôm nào" mà chưa làm không?',
        ),
        "partner": (
            "Kể cho nhau nghe một điều mình mong cho năm tới.",
            "Một năm nữa, bạn mong hai đứa đang làm gì?",
        ),
        "someone": (
            "Nhắc lại điều hai bạn đã thống nhất bằng một tin nhắn ngắn.",
            "Mình hiểu đúng ý bạn chưa?",
        ),
    },
    "freedom": {
        "crush": (
            "Rủ nhau thử một chỗ mới hay một việc chưa ai làm.",
            "Có điều gì cậu muốn thử mà chưa có ai đi cùng không?",
        ),
        "friend": (
            "Thử một hoạt động mới toanh cùng nhau, kể cả khi hơi ngớ ngẩn.",
            "Điều điên rồ nhất cậu muốn thử là gì?",
        ),
        "partner": (
            "Thống nhất với nhau một khoảng thời gian riêng cho mỗi người.",
            "Bạn cần bao nhiêu thời gian riêng để thấy thoải mái?",
        ),
        "someone": (
            "Thử đổi một thói quen quen thuộc khi gặp nhau.",
            "Bạn thích mọi thứ được lên kế hoạch hay để tự nhiên?",
        ),
    },
    "intensity": {
        "crush": (
            "Giữ những lần trò chuyện đầu nhẹ nhàng, để sự tin tưởng đến từ từ.",
            "Điều gì làm cậu thấy thoải mái khi nói chuyện với một người mới?",
        ),
        "friend": (
            "Khi có chuyện chưa vui, nói ra một câu ngắn trong ngày.",
            "Có chuyện gì giữa hai đứa cậu muốn nói rõ không?",
        ),
        "partner": (
            "Thống nhất một cách tạm dừng khi cả hai đang nóng.",
            "Khi mình căng thẳng, bạn muốn mình làm gì?",
        ),
        "someone": (
            "Dành thời gian cho một cuộc trò chuyện không vội.",
            "Điều gì quan trọng nhất với bạn lúc này?",
        ),
    },
    "visibility": {
        "crush": (
            "Khen một điều cụ thể bạn thật sự thấy hay ở bạn ấy.",
            "Gần đây cậu tự hào về điều gì?",
        ),
        "friend": (
            "Có mặt ở một dịp quan trọng của bạn mình, dù chỉ là nhắn chúc.",
            "Dạo này cậu đang cố gắng cho chuyện gì?",
        ),
        "partner": (
            "Nói cảm ơn về một việc cụ thể nhau đã làm trong tuần.",
            "Bạn thích được ghi nhận bằng lời, bằng hành động hay bằng thời gian?",
        ),
        "someone": (
            "Gửi một lời cảm ơn cụ thể sau lần gặp tới.",
            "Điều gì làm bạn thấy được tôn trọng?",
        ),
    },
}

LOW_SIGNAL_SUGGESTIONS = {
    "crush": (
        "Lần tới nhắn tin, hỏi một câu có thể trả lời thẳng và xem cuộc trò chuyện đi tới đâu.",
        "Dạo này cậu đang thích điều gì?",
    ),
    "friend": (
        "Chốt một kế hoạch nhỏ cùng nhau và xem hai bạn phối hợp ra sao.",
        "Lần tới mình làm gì cùng nhau nhỉ?",
    ),
    "partner": (
        "Chọn một chuyện nhỏ trong tuần để cùng bàn và cùng quyết.",
        "Tuần này có điều gì bạn muốn hai đứa làm khác đi không?",
    ),
    "someone": (
        "Thử một cuộc trò chuyện ít áp lực và để ý xem hai bạn có qua lại dễ không.",
        "Bạn thích được bắt chuyện theo cách nào?",
    ),
}

# Areas per context (research option B/C): each theme belongs to exactly one area.
AREAS = {
    "crush": (
        ("spark", "Điểm thu hút", ("attraction", "visibility", "intensity")),
        ("opening", "Cách mở lời", ("communication", "clarity")),
        ("closeness", "Nhịp tiến gần", ("pace", "freedom", "emotional")),
    ),
    "friend": (
        ("talk", "Nói chuyện", ("communication", "clarity")),
        ("fun", "Chơi chung", ("attraction", "freedom", "visibility")),
        ("support", "Hỗ trợ nhau", ("emotional", "pace", "intensity")),
    ),
    "partner": (
        ("bond", "Gắn bó", ("emotional", "intensity", "attraction")),
        ("disagree", "Xử lý bất đồng", ("communication", "clarity", "visibility")),
        ("life", "Nhịp sống chung", ("pace", "freedom")),
    ),
    "someone": (
        ("talk", "Nói chuyện", ("communication", "clarity")),
        ("feel", "Cảm xúc", ("emotional", "intensity", "attraction")),
        ("rhythm", "Nhịp phối hợp", ("pace", "freedom", "visibility")),
    ),
}

LEVEL_LABELS = {
    "good": "hợp",
    "balanced": "cân bằng",
    "watch": "cần để ý",
    "quiet": "chưa rõ",
}

FACTOR_COPY = {
    "communication": {
        "good": "Cách hai bạn nói và nghe dễ khớp nhau.",
        "balanced": "Cách nói chuyện có chỗ khớp, có chỗ cần hỏi lại.",
        "watch": "Cách nói của hai bạn dễ lệch nhau khi vội.",
    },
    "emotional": {
        "good": "Hai bạn dễ nhận ra cảm xúc của nhau.",
        "balanced": "Cảm xúc của hai bạn có lúc hợp, có lúc cần nói ra mới hiểu.",
        "watch": "Hai bạn có thể cần được quan tâm theo cách khác nhau.",
    },
    "attraction": {
        "good": "Khi gặp nhau, hai bạn dễ thấy hào hứng.",
        "balanced": "Sự hào hứng giữa hai bạn có lúc lên, có lúc xuống.",
        "watch": "Nhịp chủ động của hai bạn dễ lệch nhau.",
    },
    "pace": {
        "good": "Hai bạn dễ giữ nhịp và giữ lời với nhau.",
        "balanced": "Nhịp giữ hẹn, giữ lời của hai bạn cần thống nhất thêm.",
        "watch": "Tốc độ và mức chặt chẽ của hai bạn dễ khác nhau.",
    },
    "clarity": {
        "good": "Hai bạn dễ hiểu ý ngầm và tưởng tượng cùng nhau.",
        "balanced": "Có điều hai bạn hiểu ngay, có điều cần nói rõ.",
        "watch": "Điều chưa nói rõ dễ được hiểu theo nhiều cách.",
    },
    "freedom": {
        "good": "Hai bạn dễ cho nhau sự mới mẻ và khoảng riêng.",
        "balanced": "Nhu cầu tự do của hai bạn cần cân lại một chút.",
        "watch": "Thay đổi bất ngờ dễ làm hai bạn lệch nhịp.",
    },
    "intensity": {
        "good": "Hai bạn dễ đi sâu và tin nhau.",
        "balanced": "Độ sâu giữa hai bạn cần thời gian để lớn dần.",
        "watch": "Cảm xúc mạnh dễ làm chuyện nhỏ thành lớn.",
    },
    "visibility": {
        "good": "Hai bạn dễ cổ vũ và ghi nhận nhau.",
        "balanced": "Cách ghi nhận nhau của hai bạn có lúc trúng, có lúc lệch.",
        "watch": "Cách hai bạn muốn được ghi nhận dễ khác nhau.",
    },
}

SECTION_LABELS = {
    "fit": "Điều trôi chảy",
    "friction": "Điều cần để ý",
    "check": "Một gợi ý",
    "why": "Vì sao ra kết quả này?",
    "perspective": "Hai phía có thể thấy khác nhau",
    "practice": "Thêm vài cách thử",
}

# Owner decision 10: one fixed calm line, once, in one place, for every pair.
CLOSING_LINE = "Kết quả để tham khảo, cách hai bạn đối xử với nhau mới là điều quyết định."

# Codex r55: when no theme is "good". Draft copy, owner reading pending like the rest of US-22.
UNCLEAR_FIT_HEADLINES = {
    "crush": "Hai bạn còn đang dò nhịp của nhau.",
    "friend": "Hai bạn còn đang tìm nhịp chung.",
    "partner": "Hai bạn đang học dần nhịp của nhau.",
    "someone": "Giữa hai bạn chưa có một điểm dễ đi cùng thật rõ.",
}
NO_CLEAR_FIT_REASON = {
    "tension": (
        "Lá chưa thấy chỗ nào thật sự dễ đi cùng giữa hai bạn; điều cần để ý nằm ngay bên dưới."
    ),
    "even": "Các điểm chạm của hai bạn đều ở mức vừa, chưa có chỗ nào nổi lên thật rõ.",
}
UNCLEAR_FIT_LABEL = "Điều ở mức vừa"
BALANCED_FIT_COPY = "Ở {theme}, hai bạn ở mức vừa: có lúc thuận, có lúc cần nói rõ thêm."

LOW_SIGNAL_COPY = {
    "headline": "Lá chưa thấy đủ điểm riêng để kể về hai bạn.",
    "summary": (
        "Những dữ kiện còn lại quá chung để nói đây là nét riêng của hai bạn, nên bài đọc này ngắn."
    ),
    "fit": (
        "Lá chưa thấy điểm dễ đi cùng nào đủ rõ. Cách hai bạn trò chuyện thật sẽ nói nhiều hơn "
        "mọi phỏng đoán."
    ),
    "why": "Sau bước lọc, không còn điểm chạm nào đủ riêng của hai bạn để dùng.",
}


def build_radar_reading(
    bundle: RelationshipBundle,
    *,
    context: str,
    voice: RelationshipVoice = RelationshipVoice.STRAIGHT_WARM,
) -> dict[str, Any]:
    """Project relationship facts into a short default reading plus one "Xem thêm" layer."""

    safe_context = context if context in CONTEXTS else "someone"
    signals = pair_signals(bundle)
    if signals is None:
        return _low_signal_reading(bundle, context=safe_context, voice=voice)

    fit, tension = signals.fit, signals.tension
    focus = tension if tension is not None else fit
    if focus is None:  # pragma: no cover - a pair has at least one theme, watch or calm
        return _low_signal_reading(bundle, context=safe_context, voice=voice)
    tier_label = TIER_LABELS[safe_context][signals.tier]
    action, question = SUGGESTIONS[focus.key][safe_context]
    support = signals.support
    tension_receipts = _cluster_receipts(tension, mode="friction") if tension else []
    if fit is not None and signals.levels[fit.key] == "good":
        headline = HEADLINES[fit.key][safe_context]
        summary = TIER_REASONS[signals.tier].format(fit=THEME_PLAIN[fit.key])
        fit_receipts = _cluster_receipts(fit, mode="fit")
        fit_body = FIT_COPY[fit.key][safe_context]
        if support is not None:
            fit_body = f"{fit_body} {FIT_COPY[support.key][safe_context]}"
        fit_section = _section(
            "fit",
            body=fit_body,
            topics=[fit.label, *([support.label] if support else [])],
            evidence=_dedupe_receipts(
                [*fit_receipts, *(_cluster_receipts(support, mode="fit") if support else [])]
            ),
        )
    else:
        # Codex r55: no theme is "good" (or the only one is "watch"), so nothing is presented as
        # easy. The tier and the friction classification are unchanged.
        headline = UNCLEAR_FIT_HEADLINES[safe_context]
        summary = NO_CLEAR_FIT_REASON["tension" if tension is not None else "even"]
        fit_receipts = _cluster_receipts(fit, mode="fit") if fit is not None else []
        fit_section = _section(
            "fit",
            label=UNCLEAR_FIT_LABEL,
            body=(
                BALANCED_FIT_COPY.format(theme=THEME_PLAIN[fit.key])
                if fit is not None
                else LOW_SIGNAL_COPY["fit"]
            ),
            topics=[fit.label] if fit is not None else [],
            evidence=fit_receipts or tension_receipts[:1],
        )
    sections: list[dict[str, Any]] = [fit_section]
    if tension is not None:
        sections.append(
            _section(
                "friction",
                body=TENSION_COPY[tension.key][safe_context],
                topics=[tension.label],
                evidence=tension_receipts,
            )
        )
    sections.append(
        _section(
            "check",
            body=action,
            question=question,
            topics=[focus.label],
            evidence=[(tension_receipts or fit_receipts)[0]],
        )
    )

    tier_receipts = _tier_receipts(list(signals.motifs))
    factors, factor_receipts = _factors(signals)
    sections.append(
        _section(
            "why",
            layer="more",
            title="Những điểm chạm Lá đã dùng",
            body=(
                "Mỗi dòng là một điểm chạm giữa hai lá số, kèm tên gọi trong chiêm tinh cho ai "
                "muốn tra thêm. Bậc được xếp bằng cách so cặp này với nhiều cặp mẫu."
            ),
            factors=factors,
            evidence=_dedupe_receipts([*factor_receipts, *tier_receipts]),
        )
    )
    perspective_body, perspective_receipts, perspective_items = _perspective(
        bundle, list(signals.motifs)
    )
    sections.append(
        _section(
            "perspective",
            layer="more",
            title="Cùng một lần gặp, mỗi người có thể để tâm chuyện khác",
            body=perspective_body,
            perspectives=perspective_items,
            evidence=perspective_receipts,
        )
    )
    actions, action_receipts, voice_label = _editorial_actions(
        bundle, motifs=list(signals.motifs), voice=voice
    )
    if actions:
        sections.append(
            _section(
                "practice",
                layer="more",
                title="Nếu muốn thử thêm",
                body="Vài cách nhỏ để hai bạn tự kiểm chứng ngoài đời.",
                highlights=actions,
                evidence=action_receipts,
            )
        )

    all_receipts = [receipt for section in sections for receipt in section["evidence"]]
    evidence_ids = list(dict.fromkeys(str(receipt["evidence_id"]) for receipt in all_receipts))
    tier: dict[str, Any] = {"key": signals.tier, "label": tier_label}
    if SHOW_TIER_SCORE:
        tier["score"] = round(signals.percentile)
    return {
        "version": RESULT_VERSION,
        "headline": headline,
        "summary": summary,
        "pair_signature": {
            "kicker": tier_label,
            "headline": headline,
            "summary": summary,
            "tier": tier,
            "areas": _areas(signals, safe_context),
            "themes": [
                *([{"key": fit.key, "label": fit.label}] if fit else []),
                *([{"key": tension.key, "label": tension.label}] if tension else []),
            ],
        },
        "compatibility_map": [],
        "sections": sections,
        "dimensions": [],
        "strongest_contacts": [
            {
                "body_a": item.contact.body_a.value,
                "body_b": item.contact.body_b.value,
                "kind": item.contact.kind,
                "tone": item.contact.tone.value,
                "orb": round(item.contact.orb, 2),
            }
            for item in signals.motifs[:5]
        ],
        "metadata": _metadata(
            bundle,
            voice=voice,
            voice_label=voice_label,
            evidence_ids=evidence_ids,
            concept_ids=[item["concept_id"] for item in actions],
            signal_bands=_signal_bands(list(signals.motifs)),
        ),
        "disclaimer": CLOSING_LINE,
    }


def pair_signals(bundle: RelationshipBundle) -> PairSignals | None:
    """Rank and classify one directed pair; None when no pair-specific contact survives."""

    motifs = tuple(_motifs(bundle))
    if not motifs:
        return None
    clusters = tuple(_clusters(list(motifs)))
    ease = ease_signal(list(motifs))
    percentile = rank_percentile(ease)
    levels = {cluster.key: _cluster_level(cluster) for cluster in clusters}
    good = [cluster for cluster in clusters if levels[cluster.key] == "good"]
    calm = [cluster for cluster in clusters if levels[cluster.key] != "watch"]
    # Codex r55: a "watch" theme is never the fit, and a good theme wins over a merely balanced
    # one with more coordination, so the positive copy below is only ever chosen for "good".
    fit = max(
        good or calm,
        key=lambda item: (item.coordination, item.resonance, item.key),
        default=None,
    )
    watched = [cluster for cluster in clusters if levels[cluster.key] == "watch"]
    distinct = [cluster for cluster in watched if fit is None or cluster.key != fit.key]
    tension = max(
        distinct or watched,
        key=lambda item: (item.friction, item.resonance, item.key),
        default=None,
    )
    support = max(
        (
            cluster
            for cluster in clusters
            if levels[cluster.key] == "good"
            and cluster.key not in {fit.key if fit else "", tension.key if tension else ""}
        ),
        key=lambda item: (item.coordination, item.resonance, item.key),
        default=None,
    )
    return PairSignals(
        motifs=motifs,
        clusters=clusters,
        ease=ease,
        percentile=percentile,
        tier=tier_for(percentile),
        fit=fit,
        support=support,
        tension=tension,
        levels=levels,
    )


def ease_signal(motifs: list[Motif]) -> float:
    """How easily the two interact: coordination minus weighted friction (unscaled)."""

    return _channel_mean(motifs, "coordination") - EASE_FRICTION_WEIGHT * _channel_mean(
        motifs, "friction"
    )


def rank_percentile(ease: float) -> float:
    """Position (0-100) of ``ease`` in the reference distribution, linear between quantiles."""

    reference = TIER_REFERENCE
    if ease <= reference[0]:
        return 0.0
    if ease >= reference[-1]:
        return 100.0
    step = 100.0 / (len(reference) - 1)
    index = bisect_right(reference, ease) - 1
    low, high = reference[index], reference[index + 1]
    fraction = 0.0 if high <= low else (ease - low) / (high - low)
    return min(100.0, step * (index + fraction))


def tier_for(percentile: float) -> str:
    return next(key for key, floor in TIER_BANDS if percentile >= floor)


def _cluster_level(cluster: ThemeCluster) -> str:
    if cluster.friction >= TENSION_THRESHOLD and cluster.friction > cluster.coordination:
        return "watch"
    if cluster.coordination >= max(cluster.friction, GOOD_MIN_COORDINATION):
        return "good"
    return "balanced"


def _areas(signals: PairSignals, context: str) -> list[dict[str, str]]:
    by_key = {cluster.key: cluster for cluster in signals.clusters}
    areas: list[dict[str, str]] = []
    for key, label, themes in AREAS[context]:
        present = [by_key[theme] for theme in themes if theme in by_key]
        if not present:
            areas.append(
                {
                    "key": key,
                    "label": label,
                    "level": "quiet",
                    "level_label": LEVEL_LABELS["quiet"],
                    "note": f"Chưa đủ dữ kiện cho mảng {label.lower()}.",
                }
            )
            continue
        order = {"watch": 0, "good": 1, "balanced": 2}
        lead = min(
            present,
            key=lambda item: (
                order[signals.levels[item.key]],
                -max(item.coordination, item.friction),
                item.key,
            ),
        )
        level = signals.levels[lead.key]
        areas.append(
            {
                "key": key,
                "label": label,
                "level": level,
                "level_label": LEVEL_LABELS[level],
                "note": FACTOR_COPY[lead.key][level],
            }
        )
    return areas


def _factors(signals: PairSignals) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The "Vì sao?" checklist: up to five clusters, each with its level and chart terms."""

    factors: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for cluster in signals.clusters[:5]:
        level = signals.levels[cluster.key]
        mode = "friction" if level == "watch" else "fit"
        ordered = _ordered_motifs(cluster, mode=mode)
        lead = ordered[0].contact
        note = (
            f"{BODY_LABELS[lead.body_a]} của bạn và {BODY_LABELS[lead.body_b]} của người kia, "
            f"góc {ASPECT_LABELS.get(lead.kind, lead.kind)}"
        )
        if len(ordered) > 1:
            note += f", cùng {len(ordered) - 1} điểm chạm khác"
        factors.append(
            {
                "key": cluster.key,
                "label": THEME_PLAIN[cluster.key][:1].upper() + THEME_PLAIN[cluster.key][1:],
                "level": level,
                "level_label": LEVEL_LABELS[level],
                "technical_note": note + ".",
                "evidence_ids": [item.evidence_id for item in ordered[:3]],
            }
        )
        receipts.extend(_contact_receipt(item) for item in ordered[:3])
    return factors, _dedupe_receipts(receipts)


def _section(
    key: str,
    *,
    body: str,
    layer: str = "main",
    label: str | None = None,
    title: str = "",
    question: str | None = None,
    topics: list[str] | None = None,
    highlights: list[dict[str, Any]] | None = None,
    perspectives: list[dict[str, str]] | None = None,
    factors: list[dict[str, Any]] | None = None,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    receipts = evidence or []
    section: dict[str, Any] = {
        "key": key,
        "layer": layer,
        "label": label or SECTION_LABELS[key],
        "title": title,
        "body": body,
        "topics": topics or [],
        "depth": "layered" if len(receipts) >= 2 else "focused",
        "highlights": highlights or [],
        "scene": None,
        "perspectives": perspectives or [],
        "observation": None,
        "evidence": receipts,
    }
    if question is not None:
        section["question"] = question
    if factors is not None:
        section["factors"] = factors
    return section


def _metadata(
    bundle: RelationshipBundle,
    *,
    voice: RelationshipVoice,
    voice_label: str,
    evidence_ids: list[str],
    concept_ids: list[str],
    signal_bands: dict[str, str],
) -> dict[str, Any]:
    return {
        "knowledge_version": RELATIONSHIP_KNOWLEDGE_VERSION,
        "renderer_version": RENDERER_VERSION,
        "gate_version": GATE_VERSION,
        "tier_calibration_version": TIER_CALIBRATION_VERSION,
        "chart_config_version": bundle.provenance.config_hash,
        "evidence_ids": evidence_ids,
        "concept_ids": concept_ids,
        "voice": voice.value,
        "voice_label": voice_label,
        # Coarse levels for the optional Luna rewrite payload; never shown.
        "signal_bands": signal_bands,
    }


def _signal_bands(motifs: list[Motif]) -> dict[str, str]:
    def band(value: float) -> str:
        scaled = 18 + 78 * value if motifs else 0
        return "low" if scaled < 34 else "medium" if scaled < 67 else "high"

    return {
        "attraction": band(_channel_mean(motifs, "resonance")),
        "coordination": band(_channel_mean(motifs, "coordination")),
        "friction": band(_channel_mean(motifs, "friction")),
    }


def _editorial_actions(
    bundle: RelationshipBundle,
    *,
    motifs: list[Motif],
    voice: RelationshipVoice,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    """Render only prompts whose source evidence survives the Radar filter."""

    plan = build_editorial_plan(bundle.dimensions, voice=voice, limit=3)
    motif_by_fact = {_dimension_evidence_id(item.contact): item for item in motifs}
    actions: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for index, prompt in enumerate(plan.prompts):
        supporting = [
            motif_by_fact[evidence_id]
            for evidence_id in prompt.evidence_ids
            if evidence_id in motif_by_fact
        ]
        if not supporting:
            continue
        prompt_receipts = [_contact_receipt(item) for item in supporting]
        receipts.extend(prompt_receipts)
        actions.append(
            {
                "key": f"action:{prompt.concept_id}",
                "concept_id": prompt.concept_id,
                "label": f"Thử ngoài đời · {_dimension_label(prompt)}",
                "title": prompt.label,
                "body": _render_prompt(prompt, voice, index=index),
                "evidence_ids": [item.evidence_id for item in supporting],
            }
        )
    return actions, _dedupe_receipts(receipts), plan.voice_profile.label


def _dimension_label(prompt: RelationshipPrompt) -> str:
    return {
        "communication": "cách nói chuyện",
        "emotional": "cảm xúc",
        "relating": "cách kết nối",
        "drive": "nhịp chủ động",
        "growth": "đường dài",
        "friction": "lúc dễ cấn",
    }[prompt.dimension.value]


def _render_prompt(
    prompt: RelationshipPrompt,
    voice: RelationshipVoice,
    *,
    index: int,
) -> str:
    base = prompt.prompt_pattern[0].lower() + prompt.prompt_pattern[1:]
    if voice is RelationshipVoice.GENTLE_SPECIFIC:
        prefixes = (
            "Nếu thấy đủ thoải mái, ",
            "Một cách nhẹ hơn: ",
            "Bạn có thể bắt đầu bằng việc ",
        )
        return f"{prefixes[index % len(prefixes)]}{base}"
    if voice is RelationshipVoice.PLAYFUL_GROUNDED:
        prefixes = (
            "Mini test, khỏi chơi trò đoán ý: ",
            "Thử bản đời thường: ",
            "Check nhẹ một nhịp: ",
        )
        return f"{prefixes[index % len(prefixes)]}{base}"
    if voice is RelationshipVoice.DEEP_DIVE:
        prefixes = (
            "Từ điểm chạm đang nổi bật, ",
            "Để kiểm chứng điều này ngoài đời, ",
            "Thay vì kết luận từ lá số, ",
        )
        return (
            f"{prefixes[index % len(prefixes)]}{base} Sau đó đối chiếu phản hồi thật: "
            "hai người có nói rõ hơn, tôn trọng ranh giới hơn hay vẫn phải đoán nhau?"
        )
    return prompt.prompt_pattern


def _dimension_evidence_id(contact: SynastryContact) -> str:
    return f"synastry:{contact.body_a.value}:{contact.body_b.value}:{contact.kind}"


def _low_signal_reading(
    bundle: RelationshipBundle,
    *,
    context: str,
    voice: RelationshipVoice,
) -> dict[str, Any]:
    """An honest short reading when no pair-specific contact survives filtering."""

    perspective_body, perspective_receipts, perspective_items = _perspective(bundle, [])
    action, question = LOW_SIGNAL_SUGGESTIONS[context]
    tier_label = TIER_LABELS[context]["unclear"]
    sections = [
        _section("fit", body=LOW_SIGNAL_COPY["fit"]),
        _section("check", body=action, question=question),
        _section(
            "why",
            layer="more",
            title="Những điểm chạm Lá đã dùng",
            body=LOW_SIGNAL_COPY["why"],
            factors=[],
        ),
        _section(
            "perspective",
            layer="more",
            title="Cùng một lần gặp, mỗi người có thể để tâm chuyện khác",
            body=perspective_body,
            perspectives=perspective_items,
            evidence=perspective_receipts,
        ),
    ]
    headline = LOW_SIGNAL_COPY["headline"]
    summary = LOW_SIGNAL_COPY["summary"]
    return {
        "version": RESULT_VERSION,
        "headline": headline,
        "summary": summary,
        "pair_signature": {
            "kicker": tier_label,
            "headline": headline,
            "summary": summary,
            "tier": {"key": "unclear", "label": tier_label},
            "areas": [
                {
                    "key": key,
                    "label": label,
                    "level": "quiet",
                    "level_label": LEVEL_LABELS["quiet"],
                    "note": f"Chưa đủ dữ kiện cho mảng {label.lower()}.",
                }
                for key, label, _ in AREAS[context]
            ],
            "themes": [],
        },
        "compatibility_map": [],
        "sections": sections,
        "dimensions": [],
        "strongest_contacts": [],
        "metadata": _metadata(
            bundle,
            voice=voice,
            voice_label=voice_profile(voice).label,
            evidence_ids=[str(item["evidence_id"]) for item in perspective_receipts],
            concept_ids=[],
            signal_bands=_signal_bands([]),
        ),
        "disclaimer": CLOSING_LINE,
    }


def _motifs(bundle: RelationshipBundle) -> list[Motif]:
    motifs: list[Motif] = []
    for contact in bundle.synastry.contacts:
        aspect = ASPECT_CHANNELS.get(contact.kind)
        if aspect is None:
            continue
        low_personalization = (
            contact.body_a in LOW_PERSONALIZATION_BODIES
            and contact.body_b in LOW_PERSONALIZATION_BODIES
        )
        if low_personalization:
            continue
        theme = _theme(contact)
        relevance = (BODY_WEIGHT[contact.body_a] + BODY_WEIGHT[contact.body_b]) / 2
        resonance, coordination, friction = (
            contact.strength * relevance * contribution for contribution in aspect
        )
        motifs.append(
            Motif(
                key=theme,
                label=_theme_label(theme),
                contact=contact,
                evidence_id=_contact_evidence_id(contact),
                resonance=resonance,
                coordination=coordination,
                friction=friction,
            )
        )
    return sorted(
        motifs,
        key=lambda item: (max(item.resonance, item.coordination, item.friction), item.key),
        reverse=True,
    )


def _clusters(motifs: list[Motif]) -> list[ThemeCluster]:
    grouped: dict[str, list[Motif]] = {}
    for motif in motifs:
        grouped.setdefault(motif.key, []).append(motif)

    clusters: list[ThemeCluster] = []
    for key, items in grouped.items():
        ordered = tuple(
            sorted(
                items,
                key=lambda item: (
                    max(item.resonance, item.coordination, item.friction),
                    item.contact.strength,
                    item.evidence_id,
                ),
                reverse=True,
            )[:4]
        )
        clusters.append(
            ThemeCluster(
                key=key,
                label=_theme_label(key),
                motifs=ordered,
                resonance=_cluster_channel(ordered, "resonance"),
                coordination=_cluster_channel(ordered, "coordination"),
                friction=_cluster_channel(ordered, "friction"),
            )
        )
    return sorted(
        clusters,
        key=lambda item: (max(item.resonance, item.coordination, item.friction), item.key),
        reverse=True,
    )


def _cluster_channel(motifs: tuple[Motif, ...], channel: str) -> float:
    values = sorted((float(getattr(item, channel)) for item in motifs), reverse=True)
    weighted = sum(value * (1 - index * 0.12) for index, value in enumerate(values))
    divisor = sum(1 - index * 0.12 for index in range(len(values)))
    reinforcement = min(0.12, max(0, len(values) - 1) * 0.04)
    return min(1.2, weighted / divisor + reinforcement)


def _channel_strongest(motifs: list[Motif], channel: str) -> list[Motif]:
    return sorted(
        motifs,
        key=lambda item: (float(getattr(item, channel)), item.evidence_id),
        reverse=True,
    )[:6]


def _channel_mean(motifs: list[Motif], channel: str) -> float:
    strongest = _channel_strongest(motifs, channel)
    if not strongest:
        return 0.0
    weighted = sum(
        float(getattr(item, channel)) * (1 - index * 0.08) for index, item in enumerate(strongest)
    )
    return weighted / sum(1 - index * 0.08 for index in range(len(strongest)))


def _tier_receipts(motifs: list[Motif]) -> list[dict[str, Any]]:
    """Every contact the ease signal read (top six per channel), so the tier is traceable."""

    used = [
        item
        for channel in ("coordination", "friction")
        for item in _channel_strongest(motifs, channel)
    ]
    return _dedupe_receipts([_contact_receipt(item) for item in used])


def _cluster_receipts(cluster: ThemeCluster, *, mode: str) -> list[dict[str, Any]]:
    return _dedupe_receipts(
        [_contact_receipt(item) for item in _ordered_motifs(cluster, mode=mode)[:3]]
    )


def _dedupe_receipts(receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return list({str(item["evidence_id"]): item for item in receipts}.values())


def _ordered_motifs(cluster: ThemeCluster, *, mode: str) -> tuple[Motif, ...]:
    channel = "coordination" if mode == "fit" else "friction"
    return tuple(
        sorted(
            cluster.motifs,
            key=lambda item: (
                float(getattr(item, channel)),
                item.resonance,
                item.contact.strength,
                item.evidence_id,
            ),
            reverse=True,
        )
    )


def _theme(contact: SynastryContact) -> str:
    bodies = {contact.body_a, contact.body_b}
    if BodyName.MERCURY in bodies:
        return "communication"
    if BodyName.MOON in bodies:
        return "emotional"
    if BodyName.VENUS in bodies or BodyName.MARS in bodies:
        return "attraction"
    if BodyName.SATURN in bodies:
        return "pace"
    if BodyName.NEPTUNE in bodies:
        return "clarity"
    if BodyName.URANUS in bodies:
        return "freedom"
    if BodyName.PLUTO in bodies:
        return "intensity"
    return "visibility"


def _theme_label(theme: str) -> str:
    return THEME_PLAIN[theme]


def _contact_evidence_id(contact: SynastryContact) -> str:
    return f"syn:{contact.body_a.value}:{contact.kind}:{contact.body_b.value}:{contact.orb:.2f}"


def _contact_receipt(motif: Motif) -> dict[str, Any]:
    contact = motif.contact
    return {
        "evidence_id": motif.evidence_id,
        "source": "synastry",
        "plain": (
            f"{BODY_LABELS[contact.body_a]} của bạn tạo góc "
            f"{ASPECT_LABELS.get(contact.kind, contact.kind)} với "
            f"{BODY_LABELS[contact.body_b]} của người kia; Lá dùng góc này để đọc "
            f"{motif.label}."
        ),
        "technical": {
            "body_a": contact.body_a.value,
            "body_b": contact.body_b.value,
            "aspect": contact.kind,
            "orb": round(contact.orb, 2),
            "strength": round(contact.strength, 3),
        },
    }


def _perspective(
    bundle: RelationshipBundle, motifs: list[Motif]
) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    """Two sides of one meeting, without saying what the other person thinks or wants."""

    personal = {BodyName.SUN, BodyName.MOON, BodyName.MERCURY, BodyName.VENUS, BodyName.MARS}
    overlays = [item for item in bundle.synastry.house_overlays if item.body in personal]
    composite = _strongest_composite(bundle.composite.aspects)
    if overlays:
        preferred_bodies = tuple(
            dict.fromkeys(
                body
                for motif in motifs[:4]
                for body in (motif.contact.body_a, motif.contact.body_b)
                if body in personal
            )
        )
        first = next(
            (
                item
                for body in preferred_bodies
                for item in overlays
                if item.body is body and item.body_owner == "a"
            ),
            overlays[0],
        )
        reverse = next(
            (
                item
                for body in preferred_bodies
                for item in overlays
                if item.body is body and item.body_owner == "b"
            ),
            next(
                (item for item in overlays if item.body_owner != first.body_owner),
                overlays[1] if len(overlays) > 1 else first,
            ),
        )
        body = (
            f"Ở cạnh nhau, bạn có thể để ý nhiều tới {HOUSE_AREAS[reverse.house]}. Còn "
            f"{HOUSE_AREAS[first.house]} có quan trọng với phía bên kia hay không thì chỉ họ trả "
            "lời được."
        )
        receipts = [_overlay_receipt(first), _overlay_receipt(reverse)]
        perspectives = [
            {
                "key": "you",
                "label": "Phía bạn",
                "title": f"Bạn có thể để ý nhiều tới {HOUSE_AREAS[reverse.house]}",
                "body": "Cảm nhận thật của bạn khi ở cạnh nhau vẫn là điều đáng tin nhất.",
            },
            {
                "key": "them",
                "label": "Phía bên kia",
                "title": "Điều nên hỏi thay vì đoán",
                "body": (
                    f"Chuyện {HOUSE_AREAS[first.house]} quan trọng thế nào với họ, chỉ họ trả "
                    "lời được. Thử hỏi nhẹ một câu."
                ),
            },
        ]
        if composite is not None:
            receipts.append(_composite_receipt(composite))
            perspectives.append(_composite_perspective(composite))
        return body, _dedupe_receipts(receipts), perspectives
    if composite is not None:
        return (
            _composite_sentence(composite),
            [_composite_receipt(composite)],
            [_composite_perspective(composite)],
        )
    return (
        "Lá chưa có đủ dữ kiện để tách cảm nhận của hai phía. Cách chắc nhất là hỏi nhau.",
        [],
        [],
    )


def _composite_perspective(aspect: CompositeAspect) -> dict[str, str]:
    return {
        "key": "shared",
        "label": "Khi ở cạnh nhau",
        "title": (
            f"{BODY_SHARED_ROLES[aspect.body_a][:1].upper()}{BODY_SHARED_ROLES[aspect.body_a][1:]}"
            f" dễ đi cùng {BODY_SHARED_ROLES[aspect.body_b]}"
        ),
        "body": "Đây là không khí chung hai bạn tạo ra, không phải tính cách của riêng ai.",
    }


def _composite_sentence(aspect: CompositeAspect) -> str:
    return (
        f"Khi ở cạnh nhau, {BODY_SHARED_ROLES[aspect.body_a]} dễ đi cùng "
        f"{BODY_SHARED_ROLES[aspect.body_b]}. Muốn biết mỗi người thấy thế nào, cứ hỏi."
    )


def _overlay_receipt(overlay: HouseOverlay) -> dict[str, Any]:
    evidence_id = (
        f"overlay:{overlay.body_owner}:{overlay.body.value}:{overlay.house_owner}:h{overlay.house}"
    )
    return {
        "evidence_id": evidence_id,
        "source": "house_overlay",
        "plain": (
            f"{BODY_LABELS[overlay.body]} của phía {overlay.body_owner.upper()} nằm trong nhà "
            f"{overlay.house} của phía {overlay.house_owner.upper()}; lớp này chỉ dùng khi giờ và "
            "nơi sinh của cả hai đủ chính xác."
        ),
        "technical": {
            "body_owner": overlay.body_owner,
            "body": overlay.body.value,
            "house_owner": overlay.house_owner,
            "house": overlay.house,
            "house_system": overlay.target_house_system.value,
        },
    }


def _strongest_composite(aspects: tuple[CompositeAspect, ...]) -> CompositeAspect | None:
    eligible = (
        item
        for item in aspects
        if not (
            item.body_a in LOW_PERSONALIZATION_BODIES and item.body_b in LOW_PERSONALIZATION_BODIES
        )
    )
    return max(eligible, key=lambda item: (item.strength, -item.orb), default=None)


def _composite_receipt(aspect: CompositeAspect) -> dict[str, Any]:
    return {
        "evidence_id": (
            f"composite:{aspect.body_a.value}:{aspect.kind}:{aspect.body_b.value}:{aspect.orb:.2f}"
        ),
        "source": "composite_midpoint",
        "plain": (
            f"Trong lá số chung, {BODY_LABELS[aspect.body_a]} tạo góc "
            f"{ASPECT_LABELS.get(aspect.kind, aspect.kind)} với {BODY_LABELS[aspect.body_b]}. "
            "Đây là nhịp chung, không gán cho riêng một người."
        ),
        "technical": {
            "body_a": aspect.body_a.value,
            "body_b": aspect.body_b.value,
            "aspect": aspect.kind,
            "orb": round(aspect.orb, 2),
            "strength": round(aspect.strength, 3),
        },
    }
