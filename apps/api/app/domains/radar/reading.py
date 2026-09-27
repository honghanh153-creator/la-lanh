"""Deterministic, evidence-bound relationship readings for Radar.

The projector intentionally receives chart facts rather than raw birth inputs. It
creates reflection prompts, not a verdict about either person or the relationship.
"""

from __future__ import annotations

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

RENDERER_VERSION = "radar-living-dossier-v1"
GATE_VERSION = "conditional-reflection-v3"


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

HOUSE_AREAS = {
    1: "cách xuất hiện và phản ứng ngay lúc gặp nhau",
    2: "cảm giác an tâm, giá trị và chuyện cho - nhận",
    3: "cách nói chuyện, nhắn tin và xử lý chuyện hằng ngày",
    4: "vùng riêng tư, gia đình và cảm giác được ở nhà",
    5: "sự vui, flirt, sáng tạo và cách thể hiện mình thích ai đó",
    6: "nếp sinh hoạt, việc nhỏ và cách hỗ trợ nhau",
    7: "cách hai người định nghĩa quan hệ và sự công bằng",
    8: "niềm tin, ranh giới thân mật và chuyện khó nói",
    9: "niềm tin sống, học hỏi và trải nghiệm mới",
    10: "mục tiêu, hình ảnh bên ngoài và cách cùng tiến lên",
    11: "tình bạn, nhóm chung và những kế hoạch phía trước",
    12: "điều nhạy cảm, khó gọi tên hoặc cần thêm thời gian mới rõ",
}

BODY_FUNCTIONS = {
    BodyName.SUN: "cách thể hiện mình và nhu cầu được nhìn nhận",
    BodyName.MOON: "cảm xúc và cảm giác an tâm",
    BodyName.MERCURY: "cách nói, hỏi và xử lý thông tin",
    BodyName.VENUS: "cách cho - nhận sự quan tâm",
    BodyName.MARS: "cách chủ động, phản ứng và đặt ranh giới",
    BodyName.JUPITER: "cách mở rộng góc nhìn và tạo hy vọng",
    BodyName.SATURN: "nhịp cam kết, giới hạn và trách nhiệm",
    BodyName.URANUS: "nhu cầu tự do và cách phản ứng với thay đổi",
    BodyName.NEPTUNE: "trực giác, tưởng tượng và điều chưa nói rõ",
    BodyName.PLUTO: "cường độ, quyền lực và điều khó làm ngơ",
    BodyName.TRUE_NODE: "hướng phát triển còn mới",
    BodyName.MEAN_NODE: "hướng phát triển còn mới",
    BodyName.SOUTH_NODE: "phản xạ đã quen",
    BodyName.CHIRON: "điểm nhạy và cách học từ điều dễ đau",
}

BODY_ACTIONS = {
    BodyName.SUN: "cách bạn xuất hiện và thể hiện mình",
    BodyName.MOON: "mood và phản xạ cảm xúc của bạn",
    BodyName.MERCURY: "cách bạn nhắn, hỏi và giải thích",
    BodyName.VENUS: "cách bạn thể hiện thích và quan tâm",
    BodyName.MARS: "cách bạn chủ động, phản ứng và đặt giới hạn",
    BodyName.JUPITER: "cách bạn khích lệ và mở rộng câu chuyện",
    BodyName.SATURN: "cách bạn giữ lời, đặt giới hạn và nhắc trách nhiệm",
    BodyName.URANUS: "những thay đổi bất ngờ và nhu cầu tự do của bạn",
    BodyName.NEPTUNE: "cách bạn bắt mood, tưởng tượng và để ngỏ",
    BodyName.PLUTO: "độ tập trung, im lặng và sức nặng bạn mang vào tương tác",
    BodyName.TRUE_NODE: "những lựa chọn còn mới với bạn",
    BodyName.MEAN_NODE: "những lựa chọn còn mới với bạn",
    BodyName.SOUTH_NODE: "phản xạ quen thuộc của bạn",
    BodyName.CHIRON: "cách bạn phản ứng quanh một điểm nhạy",
}

BODY_RECEPTIONS = {
    BodyName.SUN: "cảm giác được nhìn thấy của người kia",
    BodyName.MOON: "cảm giác an tâm và được thấu hiểu của người kia",
    BodyName.MERCURY: "cách người kia nghe, hiểu và trả lời",
    BodyName.VENUS: "cách người kia nhận sự quan tâm và đánh giá điều mình thích",
    BodyName.MARS: "cách người kia hành động và bảo vệ ranh giới",
    BodyName.JUPITER: "niềm tin và cảm giác còn nhiều khả năng của người kia",
    BodyName.SATURN: "cách người kia nhìn cam kết, giới hạn và trách nhiệm",
    BodyName.URANUS: "nhu cầu tự do và phản ứng với thay đổi của người kia",
    BodyName.NEPTUNE: "trực giác, kỳ vọng và phần người kia chưa gọi tên",
    BodyName.PLUTO: "điều người kia khó làm ngơ hoặc chỉ nói khi đủ tin",
    BodyName.TRUE_NODE: "hướng phát triển còn mới với người kia",
    BodyName.MEAN_NODE: "hướng phát triển còn mới với người kia",
    BodyName.SOUTH_NODE: "phản xạ quen thuộc của người kia",
    BodyName.CHIRON: "điểm nhạy và cách người kia tự bảo vệ",
}

BODY_SHARED_ROLES = {
    BodyName.SUN: "nhu cầu được nhìn thấy",
    BodyName.MOON: "mood và cảm giác an tâm",
    BodyName.MERCURY: "cách hai người nói và hiểu",
    BodyName.VENUS: "cách tạo sự dễ chịu và quan tâm",
    BodyName.MARS: "nhịp chủ động, phản ứng và đặt giới hạn",
    BodyName.JUPITER: "cảm giác lạc quan và muốn thử thêm",
    BodyName.SATURN: "nhịp cam kết, giới hạn và trách nhiệm",
    BodyName.URANUS: "nhu cầu tự do và đổi mới",
    BodyName.NEPTUNE: "mood, tưởng tượng và điều còn để ngỏ",
    BodyName.PLUTO: "độ sâu và sức nặng của tương tác",
    BodyName.TRUE_NODE: "một hướng phát triển còn mới",
    BodyName.MEAN_NODE: "một hướng phát triển còn mới",
    BodyName.SOUTH_NODE: "phản xạ chung đã thành quen",
    BodyName.CHIRON: "điểm nhạy và khả năng học từ va chạm",
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

SCENE_COPY = {
    "communication": {
        "title": "Một đoạn chat đang trôi, rồi một câu ngắn làm nhịp đổi",
        "fit": (
            "Hai người có thể bắt được ý hoặc nối câu khá nhanh. Lúc này, câu chuyện dễ đi xa "
            "hơn xã giao vì mỗi người đều cảm thấy người kia đang thật sự theo kịp."
        ),
        "friction": (
            "Chỉ một câu trả lời cụt, một từ dùng khác ý hoặc việc trả lời quá nhanh cũng có thể "
            "làm hai người phản ứng với giọng điệu trước khi nghe hết nội dung."
        ),
    },
    "emotional": {
        "title": "Một người xuống mood; người kia nhận ra nhưng chưa chắc biết nên làm gì",
        "fit": (
            "Tín hiệu cảm xúc có thể được nhận ra khá sớm, kể cả trước khi được gọi tên. Khi hỏi "
            "nhẹ và chờ câu trả lời thật, hai người có cửa hiểu nhau sâu hơn."
        ),
        "friction": (
            "Một người có thể muốn được hỏi ngay, trong khi người kia nghĩ cho khoảng riêng mới là "
            "quan tâm. Không nói rõ nhu cầu khiến cả hai cùng cố đúng nhưng vẫn hụt nhau."
        ),
    },
    "attraction": {
        "title": "Sự chú ý lộ ra qua cách chủ động, flirt hoặc dành thời gian",
        "fit": (
            "Hai người dễ nhận ra mình đang được để ý qua hành động nhỏ, ánh nhìn hoặc cách "
            "ưu tiên thời gian. Đây là lực hút để quan sát thêm, không phải bằng chứng về ý định."
        ),
        "friction": (
            "Một người có thể xem sự chủ động là hứng thú rõ ràng; người kia chỉ đang thoải mái ở "
            "khoảnh khắc đó. Nếu không hỏi, chemistry rất dễ bị dùng để điền vào chỗ chưa biết."
        ),
    },
    "pace": {
        "title": "Chuyện hẹn gặp, phản hồi hoặc định nghĩa mối quan hệ bắt đầu cần một nhịp rõ",
        "fit": (
            "Có khả năng tạo được sự đều đặn: nhớ việc đã hẹn, quay lại chuyện còn dang dở và cho "
            "nhau biết điều gì đang xảy ra. Những việc nhỏ này làm kết nối bớt mơ hồ."
        ),
        "friction": (
            "Một người có thể muốn chắc rồi mới tiến; người kia lại thấy việc phải chốt sớm "
            "làm mất tự nhiên. Cấn nằm ở tốc độ, không tự động có nghĩa là thiếu quan tâm."
        ),
    },
    "clarity": {
        "title": "Một khoảng trống thông tin xuất hiện sau câu nói mơ hồ hoặc lời hẹn chưa chốt",
        "fit": (
            "Hai người có thể cùng bắt được mood, ẩn ý hoặc một thế giới riêng rất nhanh. Khi phần "
            "thực tế cũng được nói rõ, sự đồng điệu này làm cuộc trò chuyện có chiều sâu."
        ),
        "friction": (
            "Điều chưa nói rất dễ được trí tưởng tượng hoàn thiện hộ. Cả hai có thể phản ứng "
            "với câu chuyện mình tự nối thêm thay vì điều người kia thật sự đã nói."
        ),
    },
    "freedom": {
        "title": "Kế hoạch đổi phút chót hoặc một người cần biến mất một lúc",
        "fit": (
            "Mỗi người có thể kéo người kia thử cách làm mới, bớt đóng khung và có thêm không gian "
            "cho sự bất ngờ. Kết nối vì thế khó bị nhàm."
        ),
        "friction": (
            "Điều từng tạo cảm giác thú vị có thể thành thất thường nếu thay đổi không được báo "
            "trước. Một phía cần tự do; phía kia cần biết mình đang đứng ở đâu."
        ),
    },
    "intensity": {
        "title": "Một chuyện nhỏ chạm đúng điều cả hai thật sự để tâm",
        "fit": (
            "Hai người khó chỉ dừng ở chuyện bề mặt khi đã mở lòng. Có khả năng nhìn thấy phần "
            "người kia thường giấu và tạo cảm giác kết nối này có trọng lượng."
        ),
        "friction": (
            "Độ sâu cũng làm phản ứng mạnh hơn: một lần lảng tránh, giữ bí mật hoặc tranh quyền "
            "chủ động có thể nặng hơn chính sự việc."
        ),
    },
    "visibility": {
        "title": "Một người cần được ghi nhận; người kia thể hiện chú ý theo cách khác",
        "fit": (
            "Hai người có thể làm nhau thấy mình nổi bật hơn, được khích lệ hoặc có thêm tự tin để "
            "thể hiện. Sự chú ý nhất quán là phần có giá trị nhất ở đây."
        ),
        "friction": (
            "Cả hai có thể đều muốn được nhìn thấy nhưng không nhận ra tín hiệu của nhau. Khen sai "
            "điều hoặc chỉ chú ý lúc cao trào dễ để lại cảm giác mình không thật sự được hiểu."
        ),
    },
}

CONTEXT_CHECKS = {
    "crush": {
        "title": "Thử một lần nói rõ, đừng thử lòng",
        "body": (
            "Trong lần nhắn tin hoặc gặp tiếp theo, hỏi một câu có thể trả lời thẳng. "
            "Sau đó nhìn vào cách hai người phản hồi thật, thay vì dùng độ hút để đoán ý nhau."
        ),
    },
    "friend": {
        "title": "Thử chốt một kế hoạch thật cụ thể",
        "body": (
            "Chọn một việc nhỏ hai bạn cùng muốn làm, thống nhất thời gian và cách đổi kế hoạch. "
            "Nhịp phối hợp ngoài đời sẽ nói nhiều hơn một khoảnh khắc hợp mood."
        ),
    },
    "partner": {
        "title": "Thử đổi một va chạm thành yêu cầu rõ",
        "body": (
            "Khi một chuyện quen thuộc nóng lên, mỗi người nói điều mình quan sát được và một "
            "đề nghị có thể nhận hoặc từ chối. Xem hai bạn có quay lại được với nhau không."
        ),
    },
    "someone": {
        "title": "Thử một tương tác nhỏ rồi xem thật",
        "body": (
            "Chọn một câu hỏi hoặc một việc chung ít áp lực. Để ý xem cuộc nói chuyện có qua lại, "
            "có tôn trọng khoảng riêng và có dễ làm rõ khi hiểu nhầm không."
        ),
    },
}


def build_radar_reading(
    bundle: RelationshipBundle,
    *,
    context: str,
    voice: RelationshipVoice = RelationshipVoice.STRAIGHT_WARM,
) -> dict[str, Any]:
    """Project relationship facts into a layered, traceable public dossier."""

    safe_context = context if context in CONTEXT_CHECKS else "someone"
    motifs = _motifs(bundle)
    if not motifs:
        return _low_signal_reading(bundle, context=safe_context, voice=voice)

    clusters = _clusters(motifs)

    resonance, resonance_receipts = _index(motifs, "resonance")
    coordination, coordination_receipts = _index(motifs, "coordination")
    friction, friction_receipts = _index(motifs, "friction")
    fit = max(clusters, key=lambda item: (item.coordination, item.resonance, item.key))
    tension = max(clusters, key=lambda item: (item.friction, item.resonance, item.key))
    if tension.key == fit.key and len(clusters) > 1:
        tension = max(
            (item for item in clusters if item.key != fit.key),
            key=lambda item: (item.friction, item.resonance, item.key),
        )

    fit_support = _support_cluster(clusters, fit, channel="coordination")
    tension_support = _support_cluster(clusters, tension, channel="friction")

    has_distinct_tension = tension.key != fit.key or tension.friction >= 0.35
    active_tension = tension if has_distinct_tension else None
    headline = _headline(fit, tension) if active_tension else _headline_without_tension(fit)
    summary = _summary(fit, tension) if active_tension else _summary_without_tension(fit)
    perspective_body, perspective_receipts, perspective_items = _perspective(bundle, motifs)
    fit_receipts = _chapter_receipts(fit, fit_support, mode="fit")
    tension_receipts = (
        _chapter_receipts(tension, tension_support, mode="friction") if active_tension else []
    )
    check = CONTEXT_CHECKS[safe_context]
    editorial_actions, editorial_receipts, voice_label = _editorial_actions(
        bundle, motifs=motifs, voice=voice
    )
    sections: list[dict[str, Any]] = [
        {
            "key": "fit",
            "label": "Điểm hợp",
            "title": _fit_title(_primary_motif(fit, mode="fit")),
            "body": _chapter_intro(fit, fit_support, mode="fit"),
            "topics": _topic_labels(fit, fit_support),
            "depth": _depth(fit_receipts),
            "highlights": _chapter_highlights(fit, fit_support, mode="fit"),
            "scene": _scene_card(fit.key, mode="fit"),
            "perspectives": [],
            "observation": None,
            "evidence": fit_receipts,
        },
        {
            "key": "friction",
            "label": "Điểm dễ cấn",
            "title": (
                _friction_title(_primary_motif(tension, mode="friction"))
                if active_tension
                else "Chưa thấy một điểm cấn đủ mạnh để gọi tên"
            ),
            "body": (
                _chapter_intro(tension, tension_support, mode="friction")
                if active_tension
                else (
                    "Các tín hiệu hiện có chưa tạo thành một pattern lệch nhịp riêng. "
                    "Đừng biến khoảng trống này thành kết luận rằng hai người sẽ luôn dễ dàng; "
                    "hãy nhìn cách cả hai xử lý lần hiểu nhầm thật đầu tiên."
                )
            ),
            "topics": _topic_labels(tension, tension_support) if active_tension else [],
            "depth": _depth(tension_receipts),
            "highlights": (
                _chapter_highlights(tension, tension_support, mode="friction")
                if active_tension
                else []
            ),
            "scene": _scene_card(tension.key, mode="friction") if active_tension else None,
            "perspectives": [],
            "observation": None,
            "evidence": tension_receipts,
        },
        {
            "key": "perspective",
            "label": "Hai phía có thể thấy khác nhau",
            "title": "Cùng một kết nối, chưa chắc cùng một trải nghiệm",
            "body": perspective_body,
            "topics": list(dict.fromkeys([fit.label, tension.label])),
            "depth": _depth(perspective_receipts),
            "highlights": [],
            "scene": None,
            "perspectives": perspective_items,
            "observation": {
                "label": "Điều đáng đối chiếu",
                "title": "Đừng dùng trải nghiệm của mình để đo hộ phía còn lại",
                "body": (
                    "Cùng một lần nhắn tin, gặp gỡ hoặc im lặng có thể mang trọng lượng khác nhau "
                    "với mỗi người. Hỏi về trải nghiệm thật sẽ chính xác hơn suy từ chart."
                ),
            },
            "evidence": perspective_receipts,
        },
        {
            "key": "check",
            "label": "Đem ra đời thật",
            "title": check["title"],
            "body": check["body"],
            "topics": list(
                dict.fromkeys([fit.label, *([tension.label] if active_tension else [])])
            ),
            "depth": "focused",
            "highlights": editorial_actions,
            "scene": None,
            "perspectives": [],
            "observation": {
                "label": "Một lần thử là đủ",
                "title": "Quan sát cách hai người quay lại sau một nhịp lệch",
                "body": _observation_body(fit, active_tension, safe_context),
            },
            "evidence": _dedupe_receipts(
                [
                    fit_receipts[0],
                    *([tension_receipts[0]] if tension_receipts else []),
                    *editorial_receipts,
                ]
            ),
        },
    ]
    all_receipts = [
        *(receipt for section in sections for receipt in section["evidence"]),
        *resonance_receipts,
        *coordination_receipts,
        *friction_receipts,
    ]
    all_evidence_ids = list(dict.fromkeys(str(receipt["evidence_id"]) for receipt in all_receipts))

    return {
        "version": "radar-result-v2",
        "headline": headline,
        "summary": summary,
        "pair_signature": {
            "kicker": _kicker(resonance, coordination, friction),
            "headline": headline,
            "summary": summary,
            "themes": [
                {"key": fit.key, "label": fit.label},
                *([{"key": tension.key, "label": tension.label}] if active_tension else []),
            ],
        },
        "compatibility_map": [
            {
                "key": "resonance",
                "label": "Bắt sóng",
                "value": resonance,
                "meaning": "Độ hai người dễ làm nhau chú ý hoặc thấy có tín hiệu qua lại.",
                "evidence": resonance_receipts,
            },
            {
                "key": "coordination",
                "label": "Dễ phối hợp",
                "value": coordination,
                "meaning": "Độ hai nhịp có sẵn đường để nói, làm và điều chỉnh cùng nhau.",
                "evidence": coordination_receipts,
            },
            {
                "key": "friction",
                "label": "Lực cấn",
                "value": friction,
                "meaning": "Độ tương tác dễ kích hoạt khác biệt hoặc cần làm rõ nhiều hơn.",
                "evidence": friction_receipts,
            },
        ],
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
            for item in motifs[:5]
        ],
        "metadata": {
            "knowledge_version": RELATIONSHIP_KNOWLEDGE_VERSION,
            "renderer_version": RENDERER_VERSION,
            "gate_version": GATE_VERSION,
            "chart_config_version": bundle.provenance.config_hash,
            "evidence_ids": all_evidence_ids,
            "concept_ids": [item["concept_id"] for item in editorial_actions],
            "voice": voice.value,
            "voice_label": voice_label,
        },
        "disclaimer": (
            "Ba chỉ báo là bản đồ tương tác từ hai chart, không phải xác suất thành công. "
            "Điều hai người thực sự nói và làm vẫn là dữ liệu quan trọng nhất."
        ),
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
            "Từ tín hiệu đang nổi bật trong chart, ",
            "Để kiểm chứng lớp này ngoài đời, ",
            "Thay vì kết luận từ chart, ",
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
    """Return an honest short report when no pair-specific contact survives filtering."""

    perspective_body, perspective_receipts, perspective_items = _perspective(bundle, [])
    check = CONTEXT_CHECKS[context]
    evidence_ids = [str(item["evidence_id"]) for item in perspective_receipts]
    compatibility_map = [
        {
            "key": key,
            "label": label,
            "value": 0,
            "meaning": "Chưa đủ tín hiệu riêng của cặp để đọc chỉ báo này.",
            "evidence": [],
        }
        for key, label in (
            ("resonance", "Bắt sóng"),
            ("coordination", "Dễ phối hợp"),
            ("friction", "Lực cấn"),
        )
    ]
    sections = [
        {
            "key": "fit",
            "label": "Điểm hợp",
            "title": "Chưa có điểm hợp đủ riêng để gọi tên",
            "body": (
                "Những tín hiệu còn lại quá chung để nói đây là pattern riêng của hai người. "
                "Radar dừng ở đây thay vì bù bằng một lời hợp gu nghe hay nhưng khó kiểm chứng."
            ),
            "topics": [],
            "depth": "focused",
            "highlights": [],
            "scene": None,
            "perspectives": [],
            "observation": None,
            "evidence": [],
        },
        {
            "key": "friction",
            "label": "Điểm dễ cấn",
            "title": "Chưa có điểm cấn đủ riêng để gọi tên",
            "body": (
                "Không có đủ bằng chứng để gắn một kiểu lệch nhịp cho cặp này. "
                "Một lần hai người bất đồng thật sẽ cho nhiều dữ liệu hơn một câu đoán từ chart."
            ),
            "topics": [],
            "depth": "focused",
            "highlights": [],
            "scene": None,
            "perspectives": [],
            "observation": None,
            "evidence": [],
        },
        {
            "key": "perspective",
            "label": "Hai phía có thể thấy khác nhau",
            "title": "Cùng một kết nối, chưa chắc cùng một trải nghiệm",
            "body": perspective_body,
            "topics": [],
            "depth": _depth(perspective_receipts),
            "highlights": [],
            "scene": None,
            "perspectives": perspective_items,
            "observation": None,
            "evidence": perspective_receipts,
        },
        {
            "key": "check",
            "label": "Đem ra đời thật",
            "title": check["title"],
            "body": check["body"],
            "topics": [],
            "depth": "focused",
            "highlights": [],
            "scene": None,
            "perspectives": [],
            "observation": {
                "label": "Một lần thử là đủ",
                "title": "Ưu tiên điều hai người thật sự làm",
                "body": (
                    "Khi chart chưa cho đủ tín hiệu riêng, cách hai người hỏi, trả lời và sửa một "
                    "hiểu nhầm nhỏ là dữ liệu hữu ích nhất."
                ),
            },
            "evidence": [],
        },
    ]
    headline = "Chart chưa cho đủ tín hiệu riêng để kể thay câu chuyện của hai người."
    summary = (
        "Radar chỉ giữ phần có thể truy ngược. Lần này dữ liệu phù hợp còn mỏng, nên bản đọc "
        "ngắn và nhường chỗ cho tương tác thật."
    )
    return {
        "version": "radar-result-v2",
        "headline": headline,
        "summary": summary,
        "pair_signature": {
            "kicker": "Tín hiệu mỏng · chưa nên đoán xa",
            "headline": headline,
            "summary": summary,
            "themes": [],
        },
        "compatibility_map": compatibility_map,
        "sections": sections,
        "dimensions": [],
        "strongest_contacts": [],
        "metadata": {
            "knowledge_version": RELATIONSHIP_KNOWLEDGE_VERSION,
            "renderer_version": RENDERER_VERSION,
            "gate_version": GATE_VERSION,
            "chart_config_version": bundle.provenance.config_hash,
            "evidence_ids": evidence_ids,
            "concept_ids": [],
            "voice": voice.value,
            "voice_label": voice_profile(voice).label,
        },
        "disclaimer": (
            "Bản đọc ngắn vì Radar chưa có đủ bằng chứng riêng của cặp. "
            "Điều hai người thực sự nói và làm vẫn là dữ liệu quan trọng nhất."
        ),
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


def _support_cluster(
    clusters: list[ThemeCluster], primary: ThemeCluster, *, channel: str
) -> ThemeCluster | None:
    candidates = [item for item in clusters if item.key != primary.key]
    if not candidates:
        return None
    support = max(
        candidates,
        key=lambda item: (float(getattr(item, channel)), item.resonance, item.key),
    )
    return support if float(getattr(support, channel)) >= 0.35 else None


def _topic_labels(primary: ThemeCluster, support: ThemeCluster | None) -> list[str]:
    return [primary.label] if support is None else [primary.label, support.label]


def _chapter_receipts(
    primary: ThemeCluster, support: ThemeCluster | None, *, mode: str
) -> list[dict[str, Any]]:
    motifs = [*_ordered_motifs(primary, mode=mode)[:3]]
    if support is not None:
        motifs.extend(_ordered_motifs(support, mode=mode)[:3])
    return _dedupe_receipts([_contact_receipt(item) for item in motifs])


def _dedupe_receipts(receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return list({str(item["evidence_id"]): item for item in receipts}.values())


def _depth(receipts: list[dict[str, Any]]) -> str:
    return "layered" if len(receipts) >= 2 else "focused"


def _chapter_highlights(
    primary: ThemeCluster,
    support: ThemeCluster | None,
    *,
    mode: str,
) -> list[dict[str, Any]]:
    highlights = [_cluster_highlight(primary, mode=mode, role="Tín hiệu chính")]
    if len(primary.motifs) > 1:
        highlights.append(_reinforcement_highlight(primary, mode=mode))
    elif support is not None:
        highlights.append(_cluster_highlight(support, mode=mode, role="Lớp đi kèm"))
    return highlights


def _cluster_highlight(
    cluster: ThemeCluster,
    *,
    mode: str,
    role: str,
) -> dict[str, Any]:
    primary = _primary_motif(cluster, mode=mode)
    ordered = _ordered_motifs(cluster, mode=mode)
    return {
        "key": f"{mode}:{cluster.key}:primary",
        "label": role,
        "title": _fit_title(primary) if mode == "fit" else _friction_title(primary),
        "body": _cluster_body(cluster, mode=mode),
        "evidence_ids": [item.evidence_id for item in ordered[:3]],
    }


def _reinforcement_highlight(cluster: ThemeCluster, *, mode: str) -> dict[str, Any]:
    first, second = _ordered_motifs(cluster, mode=mode)[:2]
    scene = _first_sentence(SCENE_COPY[cluster.key][mode])
    return {
        "key": f"{mode}:{cluster.key}:reinforced",
        "label": "Điểm lặp lại trong chart",
        "title": "Đây không phải tín hiệu đến từ một góc đơn lẻ",
        "body": (
            f"{scene} Hai góc khác nhau cùng quay về {cluster.label}; vì vậy Radar giữ "
            "chủ đề này để bạn kiểm chứng qua nhiều lần tương tác, không phải chỉ một khoảnh khắc."
        ),
        "evidence_ids": [first.evidence_id, second.evidence_id],
    }


def _chapter_intro(
    cluster: ThemeCluster,
    support: ThemeCluster | None,
    *,
    mode: str,
) -> str:
    lead = "Điểm dễ đi cùng nhất" if mode == "fit" else "Điểm dễ lệch nhất"
    next_step = (
        "Phần dưới chỉ ra lúc nó giúp hai người vào nhịp và cách kiểm chứng trong đời thường."
        if mode == "fit"
        else "Phần dưới chỉ ra lúc nó dễ làm hai người lệch nhịp và cách nhận biết sớm."
    )
    if support is None:
        return f"{lead} nằm ở {cluster.label}. {next_step}"
    return (
        f"{lead} nằm ở {cluster.label}. {next_step} Một lớp khác cũng xuất hiện ở "
        f"{support.label}; mở phần dưới để xem hai lớp này đi cùng nhau thế nào."
    )


def _cluster_body(cluster: ThemeCluster, *, mode: str) -> str:
    ordered = _ordered_motifs(cluster, mode=mode)
    primary = ordered[0]
    body = _fit_body(primary) if mode == "fit" else _friction_body(primary)
    if len(ordered) > 1:
        support = ordered[1]
        return (
            f"{body} Ở lớp đi kèm, {_contact_bridge(support.contact)}. "
            f"{_aspect_dynamic(support.contact.kind).capitalize()}."
        )
    return body


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


def _primary_motif(cluster: ThemeCluster, *, mode: str) -> Motif:
    return _ordered_motifs(cluster, mode=mode)[0]


def _contact_bridge(contact: SynastryContact) -> str:
    return f"{BODY_ACTIONS[contact.body_a]} chạm vào {BODY_RECEPTIONS[contact.body_b]}"


def _aspect_dynamic(kind: str) -> str:
    return {
        "conjunction": "hai nhịp dễ bật lên cùng lúc và làm tín hiệu mạnh hơn",
        "trine": "hai nhịp có sẵn đường để đi cùng mà không cần cố quá nhiều",
        "sextile": "hai nhịp có cửa phối hợp khi một trong hai chủ động mở lời",
        "square": "khác biệt khó bị lờ đi và thường đòi hỏi nói rõ hơn",
        "opposition": "hai phía dễ hút nhau vào cùng một vấn đề nhưng đứng ở hai đầu khác nhau",
    }.get(kind, "hai nhịp tạo ra một điểm chạm đáng để quan sát")


def _scene_card(theme: str, *, mode: str) -> dict[str, str]:
    scene = SCENE_COPY[theme]
    return {
        "label": "Cảnh dễ gặp",
        "title": scene["title"],
        "body": scene[mode],
    }


def _observation_body(fit: ThemeCluster, tension: ThemeCluster | None, context: str) -> str:
    context_line = {
        "crush": "Sau một lần nhắn hoặc gặp, để ý xem câu hỏi rõ có được trả lời rõ không.",
        "friend": (
            "Sau một kế hoạch chung, để ý xem hai người có báo thay đổi và chốt lại dễ không."
        ),
        "partner": (
            "Sau một va chạm nhỏ, để ý xem hai người có quay lại để làm rõ điều vừa xảy ra không."
        ),
        "someone": (
            "Sau một tương tác ít áp lực, để ý xem cuộc nói chuyện có qua lại và tôn trọng "
            "khoảng riêng không."
        ),
    }[context]
    if tension is None:
        return (
            f"{context_line} Đừng chỉ đo bằng lúc {fit.label} đang rất vào; hãy chờ thêm một "
            "lần hai người phải làm rõ điều chưa hiểu nhau."
        )
    return (
        f"{context_line} Đừng chỉ đo bằng lúc {fit.label} đang rất vào; hãy nhìn thêm cách "
        f"hai người xử lý {tension.label} khi nhịp bắt đầu lệch."
    )


def _index(motifs: list[Motif], channel: str) -> tuple[int, list[dict[str, Any]]]:
    strongest = sorted(
        motifs,
        key=lambda item: (float(getattr(item, channel)), item.evidence_id),
        reverse=True,
    )[:6]
    if not strongest:
        return 0, []
    weighted = sum(
        float(getattr(item, channel)) * (1 - index * 0.08) for index, item in enumerate(strongest)
    )
    divisor = sum(1 - index * 0.08 for index in range(len(strongest)))
    value = round(max(8, min(96, 18 + 78 * weighted / divisor)))
    return value, [_contact_receipt(item) for item in strongest]


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
    return {
        "communication": "cách nói và hiểu nhau",
        "emotional": "nhịp cảm xúc",
        "attraction": "sức hút và cách thể hiện sự thích",
        "pace": "nhịp tiến gần và ranh giới",
        "clarity": "kỳ vọng và độ rõ ràng",
        "freedom": "khoảng riêng và sự bất ngờ",
        "intensity": "độ gắn sâu và cường độ",
        "visibility": "cảm giác được nhìn thấy",
    }[theme]


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
            f"{BODY_LABELS[contact.body_b]} của người kia; Radar dùng góc này để đọc "
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


def _headline(
    fit: ThemeCluster,
    tension: ThemeCluster,
) -> str:
    resource = {
        "communication": "Nói chuyện có thể vào rất nhanh",
        "emotional": "Hai người dễ nhận ra mood của nhau",
        "attraction": "Sự chú ý qua lại khó bị xem là vô tình",
        "pace": "Kết nối này có cửa tạo được một nhịp đều",
        "clarity": "Hai người dễ cùng bước vào một thế giới riêng",
        "freedom": "Mỗi người kéo người kia ra khỏi lối quen",
        "intensity": "Kết nối này khó dừng ở chuyện bề mặt",
        "visibility": "Hai người dễ làm nhau thấy mình nổi bật",
    }[fit.key]
    negotiation = {
        "communication": "một câu thiếu ngữ cảnh cũng đủ làm lệch sóng",
        "emotional": "cách cần được trấn an lại chưa chắc giống nhau",
        "attraction": "chemistry không tự nói hộ ý định",
        "pace": "tốc độ tiến gần cần được nói rõ",
        "clarity": "khoảng trống thông tin rất dễ bị suy diễn lấp đầy",
        "freedom": "sự bất ngờ cần đi cùng báo trước",
        "intensity": "độ sâu cũng khiến phản ứng dễ nặng hơn sự việc",
        "visibility": "hai người có thể cần được ghi nhận theo hai cách khác nhau",
    }[tension.key]
    return f"{resource}; nhưng {negotiation}."


def _headline_without_tension(fit: ThemeCluster) -> str:
    resource = {
        "communication": "Nói chuyện có thể vào rất nhanh",
        "emotional": "Hai người dễ nhận ra mood của nhau",
        "attraction": "Sự chú ý qua lại khó bị xem là vô tình",
        "pace": "Kết nối này có cửa tạo được một nhịp đều",
        "clarity": "Hai người dễ cùng bước vào một thế giới riêng",
        "freedom": "Mỗi người kéo người kia ra khỏi lối quen",
        "intensity": "Kết nối này khó dừng ở chuyện bề mặt",
        "visibility": "Hai người dễ làm nhau thấy mình nổi bật",
    }[fit.key]
    return f"{resource}; phần dễ lệch chưa đủ rõ để Radar nói hộ."


def _summary(fit: ThemeCluster, tension: ThemeCluster) -> str:
    if fit.key == tension.key:
        return (
            f'Điểm hút và điểm cấn cùng nằm ở {fit.label}: rất dễ có cảm giác "đúng sóng", '
            "nhưng cũng dễ hiểu quá nhiều từ một tín hiệu nhỏ."
        )
    return (
        f"Chỗ dễ đi cùng nằm ở {fit.label}: {_first_sentence(SCENE_COPY[fit.key]['fit'])} "
        f"Chỗ cần thương lượng nằm ở {tension.label}: "
        f"{_first_sentence(SCENE_COPY[tension.key]['friction'])}"
    )


def _summary_without_tension(fit: ThemeCluster) -> str:
    return (
        f"Tín hiệu rõ nhất hiện nằm ở {fit.label}: "
        f"{_first_sentence(SCENE_COPY[fit.key]['fit'])} "
        "Radar chưa có một cụm bằng chứng khác đủ mạnh để gắn nhãn điểm cấn."
    )


def _first_sentence(value: str) -> str:
    first, _, _ = value.partition(". ")
    return first.rstrip(".") + "."


def _kicker(resonance: int, coordination: int, friction: int) -> str:
    if resonance >= 70 and friction >= 65:
        return "Hút rõ · cấn cũng rõ"
    if coordination >= 68:
        return "Dễ vào nhịp · vẫn cần nói thật"
    if friction >= 70:
        return "Có tín hiệu · cần nhiều phiên dịch"
    return "Có điểm chạm · nên xem bằng tương tác thật"


def _fit_title(motif: Motif) -> str:
    pair_title = {
        (BodyName.PLUTO, BodyName.SUN): "Sự chú ý của bạn dễ có sức nặng với người kia",
        (BodyName.SUN, BodyName.PLUTO): "Cách bạn hiện diện có thể chạm sâu hơn vẻ ngoài",
        (BodyName.MERCURY, BodyName.MOON): "Một câu nói có thể chạm tới mood trước lời giải thích",
        (BodyName.MOON, BodyName.MERCURY): "Mood của bạn dễ đổi cách người kia nghe và trả lời",
        (BodyName.VENUS, BodyName.MARS): "Sự quan tâm của bạn dễ gặp lại một phản ứng rõ",
        (BodyName.MARS, BodyName.VENUS): "Sự chủ động của bạn dễ làm người kia chú ý",
    }.get((motif.contact.body_a, motif.contact.body_b))
    if pair_title is not None:
        return pair_title
    return {
        "communication": "Nói đúng nhịp là bắt được ý khá nhanh",
        "emotional": "Có cửa để nhận ra mood của nhau",
        "attraction": "Sự chú ý giữa hai người không quá khó thấy",
        "pace": "Có khả năng tạo cảm giác nghiêm túc và có mặt",
        "clarity": "Trí tưởng tượng chung có thể làm cuộc trò chuyện cuốn",
        "freedom": "Hai người dễ kéo nhau ra khỏi lối quen",
        "intensity": "Kết nối này khó bị xem là nhạt",
        "visibility": "Có tín hiệu khiến mỗi người thấy mình được để ý",
    }[motif.key]


def _fit_body(motif: Motif) -> str:
    flow = motif.contact.kind in {"trine", "sextile"}
    bridge = _contact_bridge(motif.contact).capitalize() + ". "
    if motif.key == "communication":
        return bridge + (
            "Cuộc nói chuyện thường dễ nối tiếp."
            if flow
            else "Khác biệt đủ rõ để hai người khó chỉ nói chuyện cho có."
        )
    if motif.key == "emotional":
        return bridge + (
            "Hai người có thể bắt được thay đổi cảm xúc sớm hơn bình thường, "
            "nhất là khi cả hai nói nhu cầu thay vì bắt nhau đoán."
        )
    if motif.key == "attraction":
        return bridge + (
            "Sự chủ động, quan tâm hoặc flirt dễ nhận được phản ứng. "
            "Độ hút có thật; ý định vẫn cần hỏi bằng lời."
        )
    if motif.key == "pace":
        return bridge + (
            "Tương tác có thể có nhịp và ranh giới rõ hơn. Khi không biến "
            "sự nghiêm túc thành kiểm soát, đây là điểm giữ kết nối khỏi trôi."
        )
    if motif.key == "clarity":
        return bridge + (
            "Hai người có thể cùng bắt được một mood, một câu đùa hoặc một hình dung rất "
            "nhanh. Viết rõ điều mình muốn sẽ giúp phần đẹp này không biến thành suy diễn."
        )
    if motif.key == "freedom":
        return bridge + (
            "Sự khác nhau dễ tạo tò mò và kéo hai người thử một cách tương tác mới. Cho nhau "
            "quyền đổi ý giúp sự mới mẻ này bớt thất thường."
        )
    if motif.key == "intensity":
        return bridge + (
            "Một lời khen, ánh nhìn hoặc lần nhớ đúng chi tiết nhỏ có thể được cảm nhận mạnh hơn "
            "bình thường. Sự nhất quán sẽ nói nhiều hơn một khoảnh khắc quá cuốn."
        )
    return bridge + (
        "Một người có thể khiến người kia thấy mình nổi bật hơn trong cuộc trò chuyện. "
        "Tín hiệu này mạnh nhất khi sự chú ý đi kèm hành động nhất quán."
    )


def _friction_title(motif: Motif) -> str:
    pair_title = {
        (BodyName.SATURN, BodyName.MOON): "Lúc một người cần mềm, người kia có thể chuyển sang sửa",
        (BodyName.MOON, BodyName.SATURN): "Mood của bạn có thể gặp lại sự dè chừng từ người kia",
        (BodyName.MERCURY, BodyName.MOON): "Một câu nói dễ bị nghe bằng mood hiện tại",
        (BodyName.MOON, BodyName.MERCURY): "Cảm xúc có thể đi nhanh hơn phần giải thích",
        (BodyName.MARS, BodyName.VENUS): "Sự chủ động và cảm giác được thích chưa chắc cùng nhịp",
    }.get((motif.contact.body_a, motif.contact.body_b))
    if pair_title is not None:
        return pair_title
    return {
        "communication": "Dễ phản ứng với cách nói trước khi nghe hết ý",
        "emotional": "Cùng có cảm xúc nhưng chưa chắc cần cùng một cách được dỗ",
        "attraction": "Độ hút mạnh không đồng nghĩa hai người muốn cùng một nhịp",
        "pace": "Một người muốn chắc, người kia có thể thấy mình bị chậm lại",
        "clarity": "Khoảng trống thông tin rất dễ bị trí tưởng tượng lấp đầy",
        "freedom": "Sự bất ngờ vui lúc đầu có thể thành thiếu ổn định về sau",
        "intensity": "Một chuyện nhỏ có thể chạm đúng nút nhạy của cả hai",
        "visibility": "Cả hai có thể cùng muốn được công nhận theo cách khác nhau",
    }[motif.key]


def _friction_body(motif: Motif) -> str:
    bridge = _contact_bridge(motif.contact).capitalize() + ". "
    if motif.contact.kind in {"square", "opposition"}:
        lead = "Góc này tạo lực kéo đủ mạnh để khác biệt khó bị lờ đi."
    elif motif.contact.kind == "conjunction":
        lead = "Hai chức năng đứng rất gần nhau nên tín hiệu dễ bị khuếch đại."
    else:
        lead = "Đường kết nối khá trơn nên chỗ lệch có thể bị bỏ qua lúc đầu."
    follow = {
        "communication": (
            " Khi câu chữ bắt đầu sắc, hỏi lại một ý cụ thể sẽ hữu ích hơn đoán thái độ."
        ),
        "emotional": " Một người cần gần chưa chắc người kia cũng sẵn sàng gần ngay lúc đó.",
        "attraction": " Nên tách điều mình thấy hấp dẫn khỏi điều người kia thực sự đã đồng ý.",
        "pace": " Nói rõ tốc độ và giới hạn giúp sự chắc chắn không biến thành sức ép.",
        "clarity": " Điều chưa được nói nên được giữ là dấu hỏi, không nâng thành sự thật.",
        "freedom": (" Báo trước thay đổi và tôn trọng khoảng riêng sẽ giảm cảm giác bị kéo - đẩy."),
        "intensity": " Dừng đúng lúc và quay lại sau giúp tránh biến quan tâm thành cuộc giằng co.",
        "visibility": " Đừng dùng sự chú ý như bằng chứng rằng hai người đang muốn cùng một điều.",
    }[motif.key]
    return bridge + lead + follow


def _perspective(
    bundle: RelationshipBundle, motifs: list[Motif]
) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    personal = {BodyName.SUN, BodyName.MOON, BodyName.MERCURY, BodyName.VENUS, BodyName.MARS}
    overlays = [item for item in bundle.synastry.house_overlays if item.body in personal]
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
            f"Bạn có thể làm vùng {HOUSE_AREAS[first.house]} nổi lên ở phía người kia, trong khi "
            f"người kia có thể chạm vào {HOUSE_AREAS[reverse.house]} ở bạn. Vì vậy cùng một "
            "tương tác có thể quan trọng theo hai cách khác nhau."
        )
        receipts = [_overlay_receipt(first), _overlay_receipt(reverse)]
        perspectives = [
            _overlay_perspective(first, key="you"),
            _overlay_perspective(reverse, key="them"),
        ]
        composite = _strongest_composite(bundle.composite.aspects)
        if composite is not None:
            body += " " + _composite_sentence(composite)
            receipts.append(_composite_receipt(composite))
            perspectives.append(_composite_perspective(composite))
        return body, _dedupe_receipts(receipts), perspectives

    composite = _strongest_composite(bundle.composite.aspects)
    if composite is not None:
        return (
            _composite_sentence(composite),
            [_composite_receipt(composite)],
            [_composite_perspective(composite)],
        )
    if not motifs:
        return (
            "Chưa có lớp nhà hoặc nhịp chung đủ tin cậy để tách trải nghiệm của hai phía.",
            [],
            [],
        )
    return (
        "Chưa có lớp nhà đủ tin cậy để nói hai phía cảm nhận ở vùng đời sống nào. Radar chỉ "
        "giữ lại khác biệt đã thấy trong các contact giữa hai chart.",
        [_contact_receipt(motifs[0])],
        [],
    )


def _overlay_perspective(overlay: HouseOverlay, *, key: str) -> dict[str, str]:
    if key == "you":
        return {
            "key": "you",
            "label": "Bạn có thể tạo tín hiệu này",
            "title": f"Bạn chạm vào {HOUSE_AREAS[overlay.house]} ở phía người kia",
            "body": (
                f"Khi {BODY_FUNCTIONS[overlay.body]} của bạn lộ ra, người kia có thể chú ý "
                f"nhiều hơn tới {HOUSE_AREAS[overlay.house]}. Đây là vùng được kích hoạt, "
                "không phải điều "
                "chart có thể dùng để nói hộ suy nghĩ hoặc ý muốn của họ."
            ),
        }
    return {
        "key": "them",
        "label": "Người kia có thể tạo tín hiệu này",
        "title": f"Họ chạm vào {HOUSE_AREAS[overlay.house]} ở bạn",
        "body": (
            f"Khi {BODY_FUNCTIONS[overlay.body]} của người kia lộ ra, bạn có thể để ý nhiều "
            f"hơn tới {HOUSE_AREAS[overlay.house]}. Cảm giác thật của bạn vẫn là dữ liệu "
            "cần ưu tiên."
        ),
    }


def _composite_perspective(aspect: CompositeAspect) -> dict[str, str]:
    return {
        "key": "shared",
        "label": "Nhịp chung khi ở cạnh nhau",
        "title": (
            f"{BODY_SHARED_ROLES[aspect.body_a].capitalize()} dễ kéo theo "
            f"{BODY_SHARED_ROLES[aspect.body_b]}"
        ),
        "body": (
            f"Khi hai người ở cạnh nhau, {BODY_SHARED_ROLES[aspect.body_a]} có thể đi cùng "
            f"{BODY_SHARED_ROLES[aspect.body_b]}. {_aspect_dynamic(aspect.kind).capitalize()}. "
            "Đây là không khí chung của tương tác, không phải tính cách riêng của một người."
        ),
    }


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


def _composite_sentence(aspect: CompositeAspect) -> str:
    return (
        f"Nhịp chung cũng cho thấy {BODY_SHARED_ROLES[aspect.body_a]} có thể đi cùng "
        f"{BODY_SHARED_ROLES[aspect.body_b]}. Đây là không khí hai người tạo ra khi ở cạnh nhau, "
        "không phải tính cách của riêng ai."
    )


def _composite_receipt(aspect: CompositeAspect) -> dict[str, Any]:
    return {
        "evidence_id": (
            f"composite:{aspect.body_a.value}:{aspect.kind}:{aspect.body_b.value}:{aspect.orb:.2f}"
        ),
        "source": "composite_midpoint",
        "plain": (
            f"Trong chart chung, {BODY_LABELS[aspect.body_a]} tạo góc "
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
