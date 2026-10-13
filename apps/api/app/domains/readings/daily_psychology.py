from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from hashlib import sha256

from app.domains.astro.models import TimePrecision, Tradition
from app.domains.readings.daily_personalization import (
    BODY_DOMAINS,
    CAPACITY_AT_WORK_MEANING,
    HOUSE_ARENAS,
    PAIR_RULES,
    PERSONALIZATION_VERSION,
    PLACEMENT_ISSUES,
    PLACEMENT_MEANINGS,
    REPAIR_REPLY_MEANING,
    SIGN_ELEMENTS,
    SUN_ISSUES,
    SupportedSituation,
    eligible_daily_situations,
)
from app.domains.readings.interpretive_lenses import daily_mixed_radix_slots
from app.domains.readings.knowledge import InterpretationFrame, body_label, semantic_arena
from app.domains.readings.models import (
    DailyMeaningBrief,
    DailySelection,
    DailyTransitRole,
    DerivedFactor,
    FactorKind,
    ReadingPlan,
    ReadingPurpose,
    SemanticArena,
)

DAILY_PSYCHOLOGY_MATRIX_VERSION = "daily-direct-meaning-v7"


@dataclass(frozen=True)
class PsychologySource:
    source_id: str
    title: str
    authors: str
    editorial_use: str
    guardrail: str


PSYCHOLOGY_SOURCES: tuple[PsychologySource, ...] = (
    PsychologySource(
        "kahneman-thinking-fast-slow",
        "Thinking, Fast and Slow",
        "Daniel Kahneman",
        "Tách phản ứng nhanh khỏi dữ kiện đã kiểm tra.",
        "Không dùng lối tắt nhận thức để gắn nhãn trí tuệ hay năng lực.",
    ),
    PsychologySource(
        "cialdini-influence",
        "Influence",
        "Robert B. Cialdini",
        "Nhìn các tín hiệu xã hội có thể kéo một lựa chọn.",
        "Chỉ dùng để nhận biết ảnh hưởng; không tối ưu thao túng người khác.",
    ),
    PsychologySource(
        "dweck-mindset",
        "Mindset",
        "Carol S. Dweck",
        "Phân biệt một lần vấp với kết luận cố định về bản thân.",
        "Không chia người dùng thành hai kiểu người cố định.",
    ),
    PsychologySource(
        "csikszentmihalyi-flow",
        "Flow",
        "Mihaly Csikszentmihalyi",
        "Nhìn độ khó, sự tập trung và phản hồi trong một việc đang làm.",
        "Không hứa năng suất hoặc hạnh phúc nếu làm theo một công thức.",
    ),
    PsychologySource(
        "goleman-emotional-intelligence",
        "Emotional Intelligence",
        "Daniel Goleman",
        "Gọi tên cảm xúc và khoảng dừng trước phản ứng.",
        "Không chấm điểm hoặc chẩn đoán năng lực cảm xúc.",
    ),
    PsychologySource(
        "neff-self-compassion",
        "Self-Compassion",
        "Kristin Neff",
        "Giảm giọng tự trách khi một việc chưa như ý.",
        "Không thay thế hỗ trợ sức khỏe tâm thần chuyên môn.",
    ),
    PsychologySource(
        "harris-happiness-trap",
        "The Happiness Trap",
        "Russ Harris",
        "Xem suy nghĩ là một sự kiện trong đầu thay vì dữ kiện bắt buộc phải theo.",
        "Không biến kỹ thuật ACT thành điều trị trong ứng dụng.",
    ),
    PsychologySource(
        "rosenberg-nonviolent-communication",
        "Nonviolent Communication",
        "Marshall B. Rosenberg",
        "Tách quan sát, cảm xúc, nhu cầu và lời đề nghị.",
        "Không suy đoán nhu cầu hoặc ý định của người khác.",
    ),
    PsychologySource(
        "tavris-aronson-mistakes-were-made",
        "Mistakes Were Made (But Not by Me)",
        "Carol Tavris and Elliot Aronson",
        "Nhìn khoảnh khắc ta bảo vệ lựa chọn cũ dù đã có dữ kiện mới.",
        "Không dùng bất đồng để kết luận ai đang tự lừa dối.",
    ),
    PsychologySource(
        "ross-nisbett-person-situation",
        "The Person and the Situation",
        "Lee Ross and Richard E. Nisbett",
        "Kiểm tra hoàn cảnh trước khi quy mọi hành vi cho tính cách.",
        "Không biến một tình huống thành nhãn tính cách ổn định.",
    ),
)


@dataclass(frozen=True)
class DailyIssuePattern:
    """One situation; wording variants must preserve its meaning and matched action."""

    key: str
    arenas: tuple[SemanticArena, ...]
    headlines: tuple[str, ...]
    scenes: tuple[str, ...]
    advice: tuple[str, ...]
    meaning: str
    takeaway: str
    scene_anchors: tuple[str, ...]
    action_anchors: tuple[str, ...]
    source_ids: tuple[str, ...]
    observation_question: str
    relationship_advice: tuple[str, ...] = ()


DAILY_ISSUES: tuple[DailyIssuePattern, ...] = (
    DailyIssuePattern(
        "missing-context",
        (SemanticArena.RELATIONSHIPS, SemanticArena.COMMUNICATION, SemanticArena.WORK),
        (
            "Bạn đọc lại tin nhắn vì chưa hiểu ý.",
            "Tin nhắn ngắn, bạn lại nghĩ thêm nhiều chuyện.",
            "Bạn đang đoán ý từ một tin nhắn.",
            "Một tin nhắn chưa rõ làm bạn nghĩ mãi.",
        ),
        (
            (
                "Khi nhận một tin nhắn ngắn, bạn có thể đọc lại nhiều lần vì chưa hiểu người "
                "kia muốn nói gì."
            ),
            (
                "Khi tin nhắn chỉ có vài chữ, bạn có thể tự nghĩ thêm lý do dù người kia chưa "
                "giải thích."
            ),
            "Khi đọc một tin nhắn chưa rõ ý, bạn có thể mất nhiều thời gian đoán hơn là hỏi lại.",
        ),
        (
            "Hỏi lại phần chưa rõ: Bạn muốn nói gì ở chỗ này?",
            "Nhắn một câu hỏi về đúng chỗ bạn chưa hiểu.",
            "Viết câu hỏi của bạn rồi hỏi lại người gửi tin nhắn.",
            "Đọc lại tin nhắn một lần, rồi hỏi phần còn chưa rõ.",
        ),
        "Tin nhắn chưa đủ rõ; cách mình hiểu có thể khác điều người gửi muốn nói.",
        "Tin nhắn ngắn không có nghĩa là người kia đang khó chịu với bạn.",
        ("tin nhắn", "nhắn"),
        ("chưa rõ", "chưa hiểu", "tin nhắn", "người gửi"),
        ("ross-nisbett-person-situation", "harris-happiness-trap"),
        "Sau khi hỏi lại, bạn đã biết người kia muốn nói gì chưa?",
    ),
    DailyIssuePattern(
        "too-many-open-loops",
        (SemanticArena.WORK, SemanticArena.ENERGY, SemanticArena.SELF_CARE),
        (
            "Bạn bắt đầu nhiều việc, chưa xong việc nào.",
            "Bạn đổi việc liên tục, việc cũ vẫn còn.",
            "Việc đang làm dở lại bị bỏ sang bên.",
            "Bạn bận cả buổi, việc vẫn chưa xong.",
        ),
        (
            (
                "Khi đang làm một việc, bạn có thể chuyển sang việc khác vừa được nhắc. Việc "
                "trước vẫn chưa xong."
            ),
            (
                "Khi nhiều việc đến cùng lúc, bạn có thể làm mỗi việc một chút rồi quên mình "
                "đang dở ở đâu."
            ),
            (
                "Khi danh sách việc dài ra, bạn có thể đổi việc liên tục mà chưa hoàn thành "
                "được việc nào."
            ),
        ),
        (
            "Chọn một việc để làm trong 20 phút, chưa chuyển sang việc khác.",
            "Viết các việc còn dở, rồi chọn một việc làm trước.",
            "Chọn việc cần xong trước. Để các việc khác sang một danh sách riêng.",
            "Đặt 20 phút cho một việc. Hết giờ mới xem việc tiếp theo.",
        ),
        "Chuyển việc liên tục khiến nhiều việc cùng dang dở, dù mình đã dành thời gian làm.",
        "Mỗi lần chuyển việc, bạn mất thêm thời gian để nhớ lại mình đang làm tới đâu.",
        ("việc", "dở"),
        ("chọn", "một việc", "20 phút"),
        ("csikszentmihalyi-flow", "kahneman-thinking-fast-slow"),
        "Bạn đã chọn được việc làm trước và biết việc nào để sau chưa?",
    ),
    DailyIssuePattern(
        "changed-plan",
        (SemanticArena.RELATIONSHIPS, SemanticArena.WORK, SemanticArena.COMMUNICATION),
        (
            "Một cuộc hẹn đổi giờ làm bạn phải sắp lại.",
            "Lịch đã xếp xong, giờ hẹn lại đổi.",
            "Bạn đang phải xếp lại một cuộc hẹn.",
            "Giờ hẹn đổi, kế hoạch của bạn cũng đổi.",
        ),
        (
            (
                "Khi một cuộc hẹn đổi giờ sát lúc gặp, bạn có thể phải bỏ hoặc dời việc đã "
                "xếp trước đó."
            ),
            (
                "Khi người kia báo đổi giờ hẹn, bạn có thể thấy khó chịu vì lịch của mình "
                "phải sắp lại."
            ),
            (
                "Khi giờ hẹn thay đổi vào phút cuối, bạn có thể chưa biết nên giữ hay dời "
                "những việc còn lại."
            ),
        ),
        (
            "Xác nhận giờ hẹn mới trước khi đổi những việc khác.",
            "Hỏi giờ hẹn mới đã chắc chưa, rồi mới sắp lại lịch.",
            "Nhắn giờ bạn còn có thể gặp, để hai bên chốt lại.",
            "Nói rõ giờ nào không tiện và đề nghị một giờ hẹn khác.",
        ),
        "Giờ hẹn thay đổi ảnh hưởng đến lịch của mình, không chỉ đến cuộc hẹn.",
        "Một lịch hẹn bị đổi thường kéo theo cả ngày của bạn, không chỉ một buổi gặp.",
        ("hẹn", "lịch"),
        ("giờ", "lịch", "hẹn"),
        ("goleman-emotional-intelligence", "rosenberg-nonviolent-communication"),
        "Hai bên đã thống nhất giờ mới mà bạn sắp xếp được chưa?",
    ),
    DailyIssuePattern(
        "comparison-loop",
        (SemanticArena.WORK, SemanticArena.SELF_CARE, SemanticArena.ENERGY),
        (
            "Thấy người khác làm tốt, bạn chê việc mình.",
            "Bạn so việc của mình với thành quả người khác.",
            "Xem thành quả người khác, bạn lại thấy mình chậm.",
            "Việc mình vừa làm bỗng thấy chưa đủ tốt.",
        ),
        (
            (
                "Khi thấy người khác khoe kết quả, bạn có thể thấy việc mình vừa làm không "
                "còn đáng kể."
            ),
            "Khi xem thành quả của người khác, bạn có thể quên mất phần việc mình đã làm xong.",
            (
                "Khi thấy người khác được khen, bạn có thể so lại tiến độ của mình rồi thấy "
                "mình chậm hơn."
            ),
        ),
        (
            "Ghi một việc mình đã làm xong trước khi xem tiếp.",
            "Viết phần việc của mình đã tiến triển so với hôm trước.",
            "Chọn một việc của mình để làm xong trước khi xem tiếp.",
            "Đặt bài đăng sang bên và ghi việc tiếp theo của mình.",
        ),
        "Nhìn thành quả của người khác có thể khiến mình bỏ qua tiến triển của chính mình.",
        "Thứ người khác đăng lên thường là khoảnh khắc đẹp nhất, không phải cả quá trình.",
        ("người khác", "thành quả", "kết quả"),
        ("mình", "của mình"),
        ("dweck-mindset", "neff-self-compassion"),
        "Bạn đang nhìn việc của mình hay chỉ nhìn kết quả người khác?",
    ),
    DailyIssuePattern(
        "automatic-caretaking",
        (SemanticArena.RELATIONSHIPS, SemanticArena.ENERGY, SemanticArena.SELF_CARE),
        (
            "Bạn nhận lời giúp trước khi xem mình còn sức.",
            "Bạn đang mệt, vẫn nhận thêm việc giúp người khác.",
            "Muốn giúp người khác, bạn quên lịch của mình.",
            "Bạn giúp thêm một việc dù đã khá mệt.",
        ),
        (
            (
                "Khi ai đó nhờ giúp, bạn có thể nhận lời ngay dù hôm nay mình đã mệt và còn "
                "việc riêng."
            ),
            (
                "Khi người kia cần bạn, bạn có thể gác việc riêng để giúp rồi mới nhận ra "
                "mình không còn sức."
            ),
            (
                "Khi được nhờ thêm một việc, bạn có thể đồng ý trước rồi mới xem lịch của "
                "mình còn chỗ không."
            ),
        ),
        (
            "Nói rõ bạn giúp được phần nào và trong bao lâu.",
            "Kiểm tra lịch, rồi nói rõ phần mình còn giúp được.",
            "Nói bạn chưa giúp ngay được và hẹn lúc khác nếu đang mệt.",
            "Chọn phần bạn đủ sức giúp, chưa nhận hết việc.",
        ),
        "Muốn giúp không có nghĩa là mình có thời gian và sức để nhận hết.",
        "Giúp quá sức thường khiến việc của chính bạn bị dồn lại sau.",
        ("giúp", "nhờ", "cần bạn"),
        ("giúp", "nhận", "lịch"),
        ("goleman-emotional-intelligence", "neff-self-compassion"),
        "Phần bạn nhận giúp có vừa với thời gian và sức mình không?",
    ),
    DailyIssuePattern(
        "decision-fatigue",
        (SemanticArena.WORK, SemanticArena.ENERGY, SemanticArena.SELF_CARE),
        (
            "Bạn chọn mãi vẫn chưa biết chọn cái nào.",
            "Càng xem nhiều lựa chọn, bạn càng khó chọn.",
            "Bạn đang mệt mà vẫn cố chọn cho đúng.",
            "Một lựa chọn nhỏ cũng làm bạn nghĩ lâu.",
        ),
        (
            (
                "Khi đã mệt mà vẫn phải chọn giữa nhiều phương án, bạn có thể xem đi xem lại "
                "nhưng chưa chốt được."
            ),
            "Khi danh sách lựa chọn quá dài, bạn có thể tìm thêm thông tin dù đã khá mệt.",
            (
                "Khi phải chọn vào lúc mệt, bạn có thể mất nhiều thời gian cho một quyết định "
                "vốn không lớn."
            ),
        ),
        (
            "Giảm còn hai lựa chọn phù hợp nhất rồi so một điểm quan trọng.",
            "Chọn một tiêu chí quan trọng và bỏ các phương án không đáp ứng.",
            "Đặt giờ xem lại lựa chọn sau khi nghỉ nếu chưa cần chốt ngay.",
            "Viết điều bạn cần nhất, rồi chọn phương án đáp ứng điều đó.",
        ),
        "Mệt và quá nhiều lựa chọn có thể làm việc chọn mất thêm thời gian.",
        "Khó chọn lúc mệt không có nghĩa là bạn thiếu quyết đoán.",
        ("chọn", "phương án", "quyết định"),
        ("chọn", "phương án", "tiêu chí"),
        ("kahneman-thinking-fast-slow", "harris-happiness-trap"),
        "Bạn đã biết điều gì quan trọng nhất với lựa chọn này chưa?",
    ),
    DailyIssuePattern(
        "perfect-before-start",
        (SemanticArena.WORK, SemanticArena.COMMUNICATION),
        (
            "Bạn định gửi rồi, nhưng lại sửa thêm.",
            "Bạn có thể sửa mãi một việc đã đủ dùng.",
            "Bản nháp xong rồi, bạn vẫn chưa gửi.",
            "Bạn sửa thêm vài chữ rồi lại chưa gửi.",
        ),
        (
            "Khi bản nháp đã đủ ý, bạn có thể vẫn sửa vài chữ vì lo người khác đánh giá.",
            "Khi định gửi một bản nháp, bạn có thể đọc lại rồi sửa thêm dù nội dung đã đủ.",
            (
                "Khi đã làm xong bản nháp, bạn có thể tiếp tục chỉnh câu chữ và chưa gửi cho "
                "người cần xem."
            ),
        ),
        (
            "Gửi bản nháp và nói rõ phần nào còn cần góp ý.",
            "Chọn một chỗ cần góp ý, rồi gửi bản nháp để hỏi.",
            "Đặt giờ gửi bản nháp. Trước đó chỉ sửa lỗi làm người đọc hiểu sai.",
            "Gửi bản nháp cho người cần xem và hỏi một câu cụ thể.",
        ),
        "Bản nháp đã đủ để người khác đọc, nhưng mình trì hoãn gửi vì còn lo bị đánh giá.",
        "Người đọc cần một bản nháp, không cần một bản hoàn hảo.",
        ("bản nháp", "sửa", "gửi"),
        ("gửi", "góp ý"),
        ("dweck-mindset", "csikszentmihalyi-flow"),
        "Bạn đã gửi bản nháp hoặc hẹn được giờ gửi chưa?",
    ),
    DailyIssuePattern(
        "group-pressure",
        (SemanticArena.COMMUNICATION, SemanticArena.WORK, SemanticArena.RELATIONSHIPS),
        (
            "Bạn gật đầu, nhưng vẫn chưa hiểu hết.",
            "Cả nhóm chốt rồi, bạn vẫn muốn hỏi thêm.",
            "Bạn đồng ý theo dù còn một chỗ chưa rõ.",
            "Mọi người đồng ý, bạn vẫn chưa hiểu vì sao.",
        ),
        (
            "Khi cả nhóm chốt rất nhanh, bạn có thể đồng ý theo dù vẫn còn một chỗ muốn hỏi lại.",
            "Khi cả nhóm đã đồng ý, bạn có thể ngại hỏi lại phần mình chưa hiểu.",
            (
                "Khi cả nhóm chuyển sang việc tiếp theo, bạn có thể đã gật đầu dù chưa hiểu "
                "rõ điều vừa chốt."
            ),
        ),
        (
            "Hỏi ngay chỗ đó: Mình chưa rõ phần này, giải thích thêm được không?",
            "Nói phần bạn chưa hiểu để cả nhóm giải thích lại.",
            "Hỏi cả nhóm vì sao chọn cách đó nếu bạn còn chưa rõ.",
            "Xin cả nhóm giải thích lại đúng chỗ bạn còn chưa rõ.",
        ),
        "Mọi người đồng ý rất nhanh nhưng mình vẫn chưa hiểu đủ để đồng ý.",
        "Chỗ chưa hiểu hôm nay thường quay lại thành việc phải làm lại sau.",
        ("nhóm", "mọi người"),
        ("nhóm", "giải thích", "chưa hiểu"),
        ("cialdini-influence", "ross-nisbett-person-situation"),
        "Bạn đã hiểu chỗ mình vừa hỏi lại chưa?",
    ),
    DailyIssuePattern(
        "avoid-small-conflict",
        (SemanticArena.RELATIONSHIPS, SemanticArena.COMMUNICATION, SemanticArena.WORK),
        (
            "Bạn chưa đồng ý, nhưng vẫn nói là được.",
            "Bạn nói được rồi mới thấy không muốn làm.",
            "Bạn nhận lời dù việc đó không tiện.",
            "Bạn muốn từ chối, nhưng lại nhận lời.",
        ),
        (
            (
                "Khi được nhờ một việc không tiện, bạn có thể nói được cho nhanh rồi mới thấy "
                "mình không muốn nhận."
            ),
            "Khi người kia nhờ thêm việc, bạn có thể nhận lời vì ngại từ chối dù lịch mình đã đầy.",
            "Khi chưa muốn nhận một việc, bạn có thể vẫn đồng ý để cuộc nói chuyện kết thúc nhanh.",
        ),
        (
            "Nói rõ bạn không nhận được việc đó, không cần giải thích quá dài.",
            "Nhắn lại bạn chưa nhận được việc này để người kia sắp xếp.",
            "Nói rõ phần bạn có thể nhận nếu chỉ làm được một phần.",
            "Nói lại giờ nào mình có thể làm được việc đã nhận.",
        ),
        "Mình nói đồng ý để tránh từ chối, dù việc đó không phù hợp với thời gian hoặc mong muốn.",
        "Một câu đồng ý cho xong dễ làm người kia hiểu sai điều bạn muốn.",
        ("nhờ", "nhận", "việc"),
        ("nhận", "làm được", "không tiện"),
        ("rosenberg-nonviolent-communication", "goleman-emotional-intelligence"),
        "Người kia đã biết rõ phần bạn có thể và không thể nhận chưa?",
    ),
    DailyIssuePattern(
        "defend-old-choice",
        (SemanticArena.WORK, SemanticArena.COMMUNICATION, SemanticArena.RELATIONSHIPS),
        (
            "Cách cũ chưa hiệu quả, bạn vẫn làm tiếp.",
            "Bạn đã làm nhiều nhưng kết quả chưa khá hơn.",
            "Bạn làm thêm dù cách đó chưa có kết quả.",
            "Bạn chưa muốn đổi cách đã làm lâu.",
        ),
        (
            (
                "Khi một cách làm chưa cho kết quả, bạn có thể tiếp tục làm thêm vì đã bỏ "
                "nhiều công vào đó."
            ),
            (
                "Khi kết quả chưa khá hơn, bạn có thể làm tiếp theo cách cũ trước khi xem có "
                "cần đổi không."
            ),
            (
                "Khi đã dành nhiều thời gian cho một cách làm, bạn có thể thấy khó đổi dù kết "
                "quả vẫn chưa tốt."
            ),
        ),
        (
            "Kiểm tra kết quả gần nhất trước khi bỏ thêm công.",
            "Viết kết quả bạn cần, rồi so với kết quả cách cũ đang cho.",
            "Chọn một phần nhỏ để thử cách khác và so kết quả.",
            "Hỏi điều gì cần thay đổi để cách làm này có kết quả.",
        ),
        "Công sức đã bỏ ra có thể khiến mình giữ một cách làm chưa hiệu quả.",
        "Đã tốn nhiều công sức không phải lý do để giữ một cách chưa ổn.",
        ("kết quả", "cách", "làm"),
        ("kết quả", "cách", "thay đổi"),
        ("tavris-aronson-mistakes-were-made", "dweck-mindset"),
        "Bạn đã biết cách làm hiện tại có hiệu quả ở chỗ nào chưa?",
    ),
)


def _supported_issue(
    key: str,
    arenas: tuple[SemanticArena, ...],
    title: str,
    scene: str,
    action: str,
    meaning: str,
    takeaway: str,
    scene_anchors: tuple[str, ...],
    action_anchors: tuple[str, ...],
    question: str,
) -> DailyIssuePattern:
    return DailyIssuePattern(
        key,
        arenas,
        (title,) * 4,
        (scene,) * 3,
        (action,) * 4,
        meaning,
        takeaway,
        scene_anchors,
        action_anchors,
        ("rosenberg-nonviolent-communication", "goleman-emotional-intelligence"),
        question,
    )


DAILY_ISSUES += (
    _supported_issue(
        "capacity-before-agreement",
        (
            SemanticArena.WORK,
            SemanticArena.RELATIONSHIPS,
            SemanticArena.ENERGY,
            SemanticArena.SELF_CARE,
            SemanticArena.COMMUNICATION,
        ),
        "Bạn muốn giúp, nhưng chưa biết làm lúc nào.",
        "Khi có người nhờ thêm việc, bạn có thể muốn nhận dù chưa biết lịch còn chỗ nào.",
        "Kiểm tra lịch rồi nói rõ phần bạn làm được và thời gian cần.",
        "Muốn nhận việc và có thời gian làm việc đó là hai điều khác nhau.",
        "Nhận thêm khi lịch đã kín thường khiến việc nào cũng bị làm vội.",
        ("nhờ", "lịch"),
        ("lịch", "thời gian"),
        "Bạn đã tìm được thời gian cho phần việc mình nhận chưa?",
    ),
    _supported_issue(
        "quick-reply",
        (SemanticArena.COMMUNICATION, SemanticArena.RELATIONSHIPS, SemanticArena.WORK),
        "Bạn định trả lời khi chưa đọc hết.",
        "Khi một tin nhắn làm bạn khó chịu, bạn có thể gõ câu trả lời ngay dù chưa đọc hết.",
        "Đọc hết tin nhắn rồi viết câu trả lời về đúng điều người kia hỏi.",
        "Phản ứng nhanh có thể đi trước việc hiểu đầy đủ tin nhắn.",
        "Câu bật ra đầu tiên chưa chắc là điều bạn thật sự muốn nói.",
        ("tin nhắn", "chưa đọc hết"),
        ("đọc hết", "câu trả lời"),
        "Câu trả lời của bạn đã đúng điều người kia hỏi chưa?",
    ),
    _supported_issue(
        "repair-reply",
        (SemanticArena.COMMUNICATION, SemanticArena.RELATIONSHIPS, SemanticArena.WORK),
        "Bạn gửi rồi mới thấy câu mình hơi gắt.",
        "Khi đọc lại tin nhắn vừa gửi, bạn có thể thấy cách mình trả lời gắt hơn điều muốn nói.",
        "Nhắn lại ý bạn muốn nói bằng một câu rõ, không trách người kia.",
        "Sau một câu trả lời vội, có thể sửa cách nói thay vì tiếp tục tranh cãi.",
        "Lỡ nói gắt một câu không có nghĩa là cả cuộc trò chuyện đã hỏng.",
        ("vừa gửi", "đã gửi", "đọc lại"),
        ("nhắn lại", "nói lại", "muốn nói"),
        "Bạn đã nói lại đúng ý mình muốn người kia hiểu chưa?",
    ),
    _supported_issue(
        "specific-feedback",
        (SemanticArena.WORK, SemanticArena.COMMUNICATION, SemanticArena.RELATIONSHIPS),
        "Bạn có bản nháp, nhưng câu hỏi còn chung.",
        "Khi gửi bản nháp để xin góp ý, bạn có thể chỉ hỏi ổn chưa mà chưa nói phần cần xem.",
        "Chọn một phần trong bản nháp và hỏi người đọc góp ý đúng phần đó.",
        "Bản nháp giúp trao đổi rõ hơn khi câu hỏi chỉ đúng phần cần góp ý.",
        "Người đọc thường góp ý theo điều họ thấy, không theo điều bạn đang lo.",
        ("bản nháp", "góp ý"),
        ("một phần", "đúng phần", "phần còn", "góp ý riêng"),
        "Bạn đã nhận được góp ý cho đúng phần mình cần chưa?",
    ),
    _supported_issue(
        "name-the-need",
        (
            SemanticArena.RELATIONSHIPS,
            SemanticArena.COMMUNICATION,
            SemanticArena.ENERGY,
            SemanticArena.SELF_CARE,
        ),
        "Bạn muốn được giúp nhưng chưa nói cần gì.",
        "Khi thấy quá tải, bạn có thể nói mình mệt nhưng chưa nói việc nào cần người kia giúp.",
        "Nói một việc cụ thể bạn cần giúp và hỏi người kia có làm được không.",
        "Nói mình mệt chưa cho người kia biết việc cụ thể mình cần giúp.",
        "Lời than mệt thường chỉ nhận lại lời an ủi, chưa phải sự giúp đỡ.",
        ("quá tải", "giúp"),
        ("cụ thể", "cần giúp", "nhờ giúp"),
        "Người kia đã biết bạn cần giúp việc cụ thể nào chưa?",
    ),
)


# Six headlines, eight hypothetical illustrations and eight compatible actions
# give 384 day cards WITHIN each supported meaning, including the neutral fallback.
# All actions remain possible in every illustration of their own issue.
_DAILY_VARIATIONS = {
    "missing-context": (
        ("Bạn chưa rõ người kia đang hỏi điều gì.", "Bạn đọc được câu chữ, chưa hiểu yêu cầu."),
        (
            "Khi một tin nhắn chỉ ghi được thôi, bạn có thể chưa biết người kia đồng ý phần nào.",
            "Khi tin nhắn nói để sau nhé, bạn có thể đoán lý do mà chưa hỏi rõ.",
            "Khi nhóm gửi một tin nhắn cụt, bạn có thể chưa biết câu đó trả lời ai.",
            "Khi tin nhắn nhắc làm như cũ, bạn có thể chưa rõ người gửi đang nói cách nào.",
            "Khi nhận tin nhắn thiếu phần giải thích, bạn có thể hiểu theo một ý khác người gửi.",
        ),
        (
            "Hỏi người gửi tin nhắn xem câu đó đang nói về phần nào.",
            "Viết lại ý bạn hiểu từ tin nhắn và hỏi người gửi có đúng không.",
            "Chọn một chữ chưa rõ trong tin nhắn rồi hỏi người gửi giải thích.",
            "Nói điều bạn còn chưa hiểu, chưa thêm lý do thay người gửi.",
        ),
    ),
    "too-many-open-loops": (
        ("Việc mới đến, bạn bỏ dở việc đang làm.", "Bạn mở thêm việc khi việc cũ chưa xong."),
        (
            "Khi đang viết một đoạn, bạn có thể mở thêm tài liệu rồi để đoạn đó còn dở.",
            "Khi đang dọn một chỗ, bạn có thể chuyển sang việc khác dù chỗ đầu chưa xong.",
            "Khi đang đọc tài liệu, bạn có thể mở việc mới từ một thông báo vừa đến.",
            "Khi thấy một ý tưởng mới, bạn có thể bắt đầu ngay dù việc đang làm còn dở.",
            "Khi đang hoàn thành một danh sách, bạn có thể thêm việc mới trước khi xong việc cũ.",
        ),
        (
            "Chọn một việc còn dở và viết điều cần làm để kết thúc nó.",
            "Chọn một việc đang làm để hoàn thành rồi đóng các mục không dùng.",
            "Ghi việc mới ra giấy rồi chọn một việc cũ để làm xong.",
            "Chọn một việc có thể xong trong mười phút và làm riêng việc đó.",
        ),
    ),
    "changed-plan": (
        ("Giờ hẹn mới chưa rõ, lịch bạn đã đổi.", "Bạn phải chọn lại giờ cho cuộc hẹn."),
        (
            "Khi cuộc hẹn bị dời sang buổi khác, bạn có thể phải xếp lại việc đã dành giờ làm.",
            "Khi giờ hẹn mới trùng một việc khác, bạn có thể chưa biết nên giữ lịch nào.",
            "Khi người kia đổi giờ nhưng chưa chốt, bạn có thể sửa lịch của mình quá sớm.",
            "Khi cuộc hẹn bắt đầu muộn hơn dự tính, bạn có thể không còn đủ giờ cho việc sau.",
            "Khi được đề nghị đổi ngày hẹn, bạn có thể quên kiểm tra việc mình đã xếp.",
        ),
        (
            "Kiểm tra một việc đã xếp trước khi xác nhận giờ hẹn mới.",
            "Viết hai giờ bạn còn trống rồi đề nghị người kia chọn một giờ.",
            "Nói giờ bạn cần kết thúc cuộc hẹn để giữ việc tiếp theo.",
            "Hỏi lại ngày và giờ hẹn trước khi ghi vào lịch.",
        ),
    ),
    "comparison-loop": (
        ("Bạn quên phần đã xong khi xem người khác.", "Một lời khen người khác khiến bạn tự chê."),
        (
            "Khi xem người khác hoàn thành sớm, bạn có thể quên phần khó mình vừa giải quyết.",
            "Khi thấy kết quả đẹp của người khác, bạn có thể chê bản nháp mình đang làm.",
            "Khi nghe người khác được khen, bạn có thể bỏ qua một việc mình vừa làm xong.",
            "Khi nhìn danh sách thành quả của người khác, bạn có thể chỉ đếm việc mình còn thiếu.",
            "Khi xem tiến độ người khác, bạn có thể thấy phần mình đã làm không còn đáng kể.",
        ),
        (
            "Ghi một chỗ việc của mình đã tốt hơn bản trước.",
            "Chọn một phần mình đã hoàn thành và ghi kết quả của phần đó.",
            "Đặt kết quả người khác sang bên rồi viết bước tiếp theo của mình.",
            "Viết một điều mình đã học được từ việc vừa làm.",
        ),
    ),
    "automatic-caretaking": (
        ("Bạn giúp người khác rồi thiếu giờ cho mình.", "Bạn nhận giúp khi phần mình vẫn còn dở."),
        (
            "Khi có người nhờ xem hộ một việc, bạn có thể nhận ngay dù việc riêng vẫn còn dở.",
            "Khi người kia nhờ thêm một phần, bạn có thể nhận hết dù đã dành giờ nghỉ.",
            "Khi được nhờ làm thay, bạn có thể bỏ việc của mình sang bên dù đang khá mệt.",
            "Khi người kia cần bạn hỗ trợ, bạn có thể kéo dài giờ giúp dù việc riêng chưa xong.",
            "Khi ai đó nhờ thêm lần nữa, bạn có thể nhận lời dù thời gian còn lại không nhiều.",
        ),
        (
            "Viết phần mình còn đủ sức giúp và nói rõ phần chưa nhận được.",
            "Chọn một phần nhỏ để giúp, rồi giữ giờ nghỉ đã định.",
            "Kiểm tra việc riêng còn dở và nói giờ mình có thể giúp.",
            "Nói giới hạn thời gian mình dành để giúp, chưa nhận thêm phần khác.",
        ),
    ),
    "decision-fatigue": (
        ("Bạn đã mệt, danh sách lựa chọn còn dài.", "Bạn tìm thêm phương án khi chưa chọn xong."),
        (
            "Khi đã mệt mà còn so nhiều phương án, bạn có thể đọc lại cùng một thông tin.",
            "Khi cần chọn một việc nhỏ lúc mệt, bạn có thể mở thêm lựa chọn thay vì chốt.",
            "Khi các phương án gần giống nhau, bạn có thể so mãi dù sức mình đã giảm.",
            "Khi phải chọn vào cuối buổi, bạn có thể xem thêm phương án dù đã biết điều cần nhất.",
            "Khi danh sách phương án cứ dài thêm, bạn có thể chưa chọn được dù đã khá mệt.",
        ),
        (
            "Chọn hai phương án đáp ứng điều cần nhất rồi dừng tìm thêm.",
            "Ghi một tiêu chí bắt buộc và so các phương án theo tiêu chí đó.",
            "Đặt giờ nghỉ trước khi xem lại lựa chọn chưa cần chốt.",
            "Bỏ các phương án không phù hợp rồi so hai lựa chọn còn lại.",
        ),
    ),
    "perfect-before-start": (
        ("Bạn đã đủ ý, vẫn chờ thêm để gửi.", "Bạn chỉnh bản nháp thay vì xin góp ý."),
        (
            "Khi bản nháp đã có đủ phần chính, bạn có thể sửa cách mở đầu rồi chưa gửi.",
            "Khi người cần xem đang chờ bản nháp, bạn có thể chỉnh thêm dù ý đã rõ.",
            "Khi bản nháp chỉ còn vài chỗ nhỏ, bạn có thể sửa mãi vì lo người đọc chê.",
            "Khi định gửi bản nháp để hỏi, bạn có thể đổi vài chữ rồi lại để đó.",
            "Khi bản nháp đã đủ để trao đổi, bạn có thể chờ chỉnh đẹp hơn rồi mới gửi.",
        ),
        (
            "Gửi bản nháp với một câu hỏi về phần bạn chưa chắc.",
            "Viết giờ gửi bản nháp và giữ đúng giờ đó.",
            "Gửi phần đã đủ ý để người đọc góp ý, đánh dấu phần còn thiếu.",
            "Chọn người cần xem rồi gửi bản nháp, chưa chỉnh thêm cách trình bày.",
        ),
    ),
    "group-pressure": (
        ("Nhóm đã chốt, câu hỏi của bạn còn đó.", "Bạn theo ý nhóm khi chưa rõ một phần."),
        (
            "Khi nhóm chọn một cách làm rất nhanh, bạn có thể nói được dù chưa hiểu một bước.",
            "Khi nhóm chuyển sang phần mới, bạn có thể vẫn chưa rõ điều vừa được thống nhất.",
            "Khi mọi người đều gật đầu, bạn có thể ngại hỏi lại phần mình nghe chưa rõ.",
            "Khi nhóm chốt việc qua chat, bạn có thể đồng ý dù còn muốn hỏi ai làm phần nào.",
            "Khi nhóm đã chọn xong, bạn có thể giữ lại câu hỏi vì thấy mọi người đều hiểu.",
        ),
        (
            "Chọn một phần chưa hiểu và xin nhóm giải thích lại phần đó.",
            "Nhắn câu hỏi còn lại vào nhóm để mọi người trả lời rõ.",
            "Nói lại ý mình hiểu và hỏi nhóm xem có đúng không.",
            "Hỏi nhóm bước đầu tiên cần làm nếu phần vừa chốt còn chưa rõ.",
        ),
    ),
    "avoid-small-conflict": (
        ("Bạn nhận việc để khỏi phải nói không.", "Bạn muốn nói không, câu trả lời lại khác."),
        (
            "Khi được nhờ làm thêm một phần, bạn có thể nhận lời dù phần đó không tiện.",
            "Khi người kia chờ câu trả lời, bạn có thể nói được dù không muốn nhận việc.",
            "Khi việc được nhờ trùng giờ nghỉ, bạn có thể vẫn nhận vì ngại nói không.",
            "Khi chưa muốn nhận việc, bạn có thể nói để mình làm rồi mới nghĩ lại.",
            "Khi được nhờ thêm lần nữa, bạn có thể nhận việc chỉ để khỏi phải từ chối.",
        ),
        (
            "Nói lại việc mình không nhận được để người kia tìm cách khác.",
            "Viết rõ phần việc không tiện rồi nhắn lại người đã nhờ.",
            "Nói một giới hạn cụ thể cho việc mình đã nhận.",
            "Nhắn lại phần bạn nhận được và phần cần người kia tự sắp xếp.",
        ),
    ),
    "defend-old-choice": (
        ("Bạn giữ cách cũ vì đã bỏ nhiều công.", "Kết quả chưa tốt, bạn vẫn ngại đổi cách."),
        (
            "Khi cách cũ vẫn cho kết quả thấp, bạn có thể làm thêm vì không muốn bỏ công đã dành.",
            "Khi đã thử một cách nhiều lần, bạn có thể ngại đổi dù kết quả chưa tốt.",
            "Khi sửa thêm theo cách cũ, bạn có thể chưa kiểm tra phần nào thật sự có kết quả.",
            "Khi kết quả không đổi sau vài lần làm, bạn có thể tiếp tục vì cách đó đã quen.",
            "Khi được gợi ý cách khác, bạn có thể giữ cách cũ dù kết quả vẫn chưa khá hơn.",
        ),
        (
            "Chọn một kết quả cần cải thiện và thử đổi một bước nhỏ.",
            "Viết phần cách cũ có kết quả, rồi chọn phần cần thử khác.",
            "Kiểm tra một lần làm gần nhất trước khi tiếp tục cách cũ.",
            "Ghi kết quả của một lần thử cách khác rồi so với cách cũ.",
        ),
    ),
    "capacity-before-agreement": (
        (
            "Bạn muốn nhận việc, lịch chưa có chỗ.",
            "Bạn chưa biết dành giờ nào để giúp.",
            "Bạn muốn giúp thêm dù giờ trống còn ít.",
            "Bạn nhận thêm việc khi chưa xem lịch.",
            "Việc được nhờ chưa có giờ trong lịch bạn.",
        ),
        (
            "Khi người kia nhờ xem hộ một việc, bạn có thể muốn giúp dù chưa kiểm tra giờ trống.",
            "Khi có thêm việc được nhờ, bạn có thể định nhận mà chưa biết sẽ làm vào lúc nào.",
            "Khi được nhờ thêm một phần, bạn có thể quên so thời gian cần với giờ mình còn trống.",
            "Khi người kia cần bạn giúp, bạn có thể muốn nhận dù lịch đã có nhiều việc.",
            "Khi một việc được nhờ cần làm lâu, bạn có thể định nhận trước khi xem lịch.",
            "Khi có người nhờ giúp, bạn có thể chưa biết lịch còn giờ nào trống.",
            "Khi được nhờ hỗ trợ, bạn có thể chỉ nghĩ đến việc giúp mà chưa tính giờ để làm.",
        ),
        (
            "Viết thời gian cần cho việc được nhờ rồi so với lịch còn trống.",
            "Chọn một phần làm được trong thời gian trống và nói rõ phần đó.",
            "Kiểm tra lịch rồi nói giờ sớm nhất bạn có thể giúp.",
            "Ghi thời gian bắt đầu và dừng trước khi nhận phần việc giúp.",
            "Nói mình cần xem lịch rồi mới trả lời phần có thể giúp.",
            "Chọn một khoảng thời gian trống và hỏi việc cần giúp có vừa khoảng đó không.",
            "Nói rõ bạn cần bao nhiêu thời gian để làm phần được nhờ.",
        ),
    ),
    "quick-reply": (
        (
            "Bạn gõ câu trả lời khi tin nhắn còn dài.",
            "Bạn định gửi trước khi hiểu hết câu hỏi.",
            "Bạn muốn trả lời ngay một tin nhắn khó chịu.",
            "Bạn đọc nửa tin nhắn rồi bắt đầu đáp.",
            "Bạn chưa đọc hết, câu trả lời đã có.",
        ),
        (
            "Khi một tin nhắn hỏi nhiều ý, bạn có thể gõ câu trả lời ngay từ ý đầu.",
            "Khi tin nhắn mở đầu khó nghe, bạn có thể muốn trả lời trước khi đọc phần còn lại.",
            "Khi đang bực vì một câu trong tin nhắn, bạn có thể gõ ngay dù còn đoạn chưa đọc.",
            "Khi tin nhắn có phần giải thích ở cuối, bạn có thể đã soạn câu trả lời từ đầu.",
            "Khi thấy một chữ làm mình khó chịu, bạn có thể chuẩn bị đáp mà chưa đọc hết tin nhắn.",
            "Khi tin nhắn dài hơn dự tính, bạn có thể trả lời ý đầu rồi bỏ sót câu hỏi sau.",
            "Khi tin nhắn có thêm phần giải thích, bạn có thể đang gõ câu trả lời cho phần trước.",
        ),
        (
            "Đọc hết tin nhắn và ghi câu hỏi chính trước khi soạn câu trả lời.",
            "Đọc hết phần giải thích rồi viết lại câu trả lời chưa gửi.",
            "Viết câu trả lời ở bản nháp, đọc hết tin nhắn rồi mới gửi.",
            "Đọc hết tin nhắn rồi hỏi lại một chỗ chưa rõ trước khi trả lời.",
            "Chọn câu hỏi cần trả lời sau khi đọc hết tin nhắn.",
            "Đọc hết tin nhắn rồi bỏ câu trả lời không liên quan đến điều được hỏi.",
            "Ghi một ý muốn trả lời, đọc hết tin nhắn rồi kiểm tra lại ý đó.",
        ),
    ),
    "repair-reply": (
        (
            "Bạn đọc lại câu đã gửi và muốn sửa.",
            "Ý bạn muốn nói khác câu vừa gửi.",
            "Câu trả lời đã gửi nghe gắt hơn dự tính.",
            "Bạn muốn nói lại ý trong tin đã gửi.",
            "Tin nhắn vừa gửi chưa đúng cách bạn muốn nói.",
        ),
        (
            (
                "Khi đọc lại câu vừa gửi, bạn có thể thấy mình trách người kia "
                "nhiều hơn điều muốn hỏi."
            ),
            "Khi xem tin nhắn đã gửi, bạn có thể thấy câu trả lời ngắn nghe gắt hơn ý định.",
            "Khi đọc lại đoạn chat, bạn có thể muốn nói rõ hơn điều mình vừa trả lời.",
            "Khi xem câu vừa gửi lúc bực, bạn có thể thấy ý chính chưa được nói rõ.",
            (
                "Khi đọc lại tin nhắn sau lúc vội, bạn có thể thấy cách trả lời "
                "chưa đúng điều muốn nói."
            ),
            "Khi nhìn câu trả lời đã gửi, bạn có thể nhận ra mình cần hỏi thay vì trách.",
            "Khi đọc lại tin nhắn của mình, bạn có thể thấy một câu làm ý muốn nói bị lệch.",
        ),
        (
            "Nhắn lại một câu làm rõ điều bạn muốn hỏi, không đoán ý người kia.",
            "Viết ý muốn nói bằng một câu rồi nhắn lại để làm rõ.",
            "Nói lại phần mình muốn hỏi thay cho câu trách vừa gửi.",
            "Nhắn lại rằng cách nói vừa rồi hơi gắt, rồi ghi rõ ý muốn nói.",
            "Chọn một câu chưa đúng ý và nhắn lại cách nói rõ hơn.",
            "Nói lại điều mình cần trao đổi, chưa thêm lời trách người kia.",
            "Nhắn lại câu hỏi chính để người kia biết bạn muốn nói gì.",
        ),
    ),
    "specific-feedback": (
        (
            "Bạn xin góp ý mà chưa chỉ phần cần xem.",
            "Câu hỏi về bản nháp chưa đủ cụ thể.",
            "Bạn gửi bản nháp nhưng chưa nói cần góp ý gì.",
            "Người đọc chưa biết phần nào bạn muốn hỏi.",
            "Bạn hỏi ổn chưa thay vì hỏi đúng phần.",
        ),
        (
            "Khi gửi bản nháp có nhiều phần, bạn có thể xin góp ý mà chưa chỉ phần muốn hỏi.",
            "Khi cần góp ý cho đoạn mở đầu, bạn có thể gửi cả bản nháp rồi chỉ hỏi ổn chưa.",
            "Khi nhờ người kia xem bản nháp, bạn có thể chưa nói mình cần góp ý về ý hay câu chữ.",
            "Khi gửi bản nháp lần đầu, bạn có thể quên ghi câu hỏi về phần còn chưa rõ.",
            "Khi muốn người đọc xem một đoạn, bạn có thể gửi bản nháp mà chưa đánh dấu đoạn đó.",
            "Khi cần biết bản nháp có dễ hiểu không, bạn có thể chỉ hỏi người đọc thấy thế nào.",
            "Khi nhờ góp ý bản nháp, bạn có thể chưa nói chỗ nào mình đang phân vân.",
        ),
        (
            "Ghi dấu một phần trong bản nháp và hỏi phần đó có dễ hiểu không.",
            "Viết một câu hỏi về đúng phần cần góp ý rồi gửi cùng bản nháp.",
            "Chọn một phần trong bản nháp và hỏi người đọc hiểu ý gì từ phần đó.",
            "Nói rõ mình cần góp ý về ý hay câu chữ ở một phần của bản nháp.",
            "Ghi một chỗ cần người đọc xem kỹ rồi xin góp ý riêng chỗ đó.",
            "Hỏi người đọc góp ý một phần trước, chưa yêu cầu xem hết bản nháp.",
            "Chọn phần còn phân vân và hỏi một câu cụ thể về phần đó.",
        ),
    ),
    "name-the-need": (
        (
            "Bạn nói mệt, chưa nói muốn được giúp gì.",
            "Bạn cần giúp một việc nhưng nói chưa rõ.",
            "Bạn muốn người kia hiểu điều mình cần giúp.",
            "Bạn than việc nhiều mà chưa nhờ việc cụ thể.",
            "Bạn chưa nói việc nào cần người kia giúp.",
        ),
        (
            "Khi việc dồn lại, bạn có thể nói mình quá tải mà chưa nhờ ai giúp một phần cụ thể.",
            "Khi cần người kia giúp, bạn có thể chỉ nói mệt quá mà chưa nói cần làm việc gì.",
            "Khi thấy mình không làm xuể, bạn có thể kể các việc mà chưa đề nghị giúp phần nào.",
            "Khi muốn bớt một việc, bạn có thể nói mình bận mà chưa nhờ người kia làm giúp.",
            "Khi đang quá tải, bạn có thể muốn được giúp nhưng chưa chọn việc để nhờ.",
            "Khi có nhiều việc còn dở, bạn có thể than mệt mà chưa nói việc nào cần giúp.",
            "Khi người kia hỏi có cần giúp không, bạn có thể chưa nói được một việc cụ thể.",
        ),
        (
            "Chọn một việc cần giúp và nói rõ phần mình muốn người kia làm.",
            "Viết một đề nghị cụ thể cho việc cần giúp, rồi hỏi người kia.",
            "Nói việc cần giúp và thời gian cần xong, rồi hỏi người kia có tiện không.",
            "Chọn một phần có thể nhờ giúp thay vì kể lại toàn bộ việc đang dở.",
            "Hỏi người kia có giúp một việc cụ thể được không, chưa coi đó là điều bắt buộc.",
            "Nói rõ mình cần giúp việc nào, không yêu cầu người kia tự đoán.",
            "Ghi một việc cụ thể cần giúp rồi nói đề nghị bằng một câu.",
        ),
    ),
}


_RELATIONSHIP_ACTIONS = {
    "missing-context": (
        "Nói với người kia cách mình hiểu tin nhắn rồi hỏi có đúng không.",
        "Hỏi người kia câu trong tin nhắn đang trả lời phần nào của cuộc nói chuyện.",
        "Nhắn người kia một câu hỏi về chỗ chưa rõ, chưa đoán lý do họ viết vậy.",
        "Hỏi lại ý người kia trong tin nhắn rồi nói phần mình cần hiểu thêm.",
        "Chọn một chỗ chưa hiểu trong tin nhắn và hỏi người kia giải thích lại.",
        "Nói với người kia mình chưa rõ yêu cầu nào trong tin nhắn.",
        "Nhắn lại ý mình hiểu từ tin nhắn và xin người kia sửa phần chưa đúng.",
        "Hỏi người kia cần mình trả lời điều gì ở chỗ tin nhắn chưa rõ.",
    ),
    "changed-plan": (
        "Hỏi người kia giờ hẹn mới và nói giờ nào mình còn gặp được.",
        "Nói với người kia giờ mình cần kết thúc cuộc hẹn rồi cùng chốt lại.",
        "Nói hai giờ hẹn mình còn trống rồi hỏi người kia chọn giờ nào.",
        "Nhắn người kia phần lịch mình không đổi được rồi hỏi giờ hẹn khác.",
        "Hỏi lại giờ hẹn người kia đã chắc chưa trước khi hai bên đổi lịch.",
        "Nói giờ hẹn mới ảnh hưởng việc nào của mình và đề nghị một giờ phù hợp.",
        "Chọn một giờ cả hai còn gặp được rồi xác nhận lại cuộc hẹn.",
        "Hỏi người kia cuộc hẹn cần bao lâu để hai bên xếp giờ phù hợp.",
    ),
    "automatic-caretaking": (
        "Hỏi người kia phần nào cần bạn giúp, rồi nhận phần vừa sức.",
        "Nói với người kia mình giúp được đến giờ nào và hỏi phần nào cần trước.",
        "Hỏi người kia một phần cần giúp nhất rồi nói phần mình còn đủ sức làm.",
        "Nói với người kia việc riêng mình còn dở rồi cùng chọn phần giúp được.",
        "Hỏi người kia có thể tự làm phần nào, rồi nhận một phần còn lại.",
        "Nói mình cần giữ giờ nghỉ và hỏi người kia có thể nhận giúp lúc khác không.",
        "Chọn một phần giúp vừa sức rồi hỏi người kia phần đó có phù hợp không.",
        "Nhắn người kia phần mình chưa giúp được và phần có thể cùng làm.",
    ),
    "group-pressure": (
        "Nói với nhóm phần mình chưa hiểu và hỏi ai có thể giải thích lại.",
        "Hỏi nhóm điều vừa chốt có đúng ý mình hiểu không, rồi nêu chỗ còn chưa rõ.",
        "Nhắn nhóm một câu hỏi còn lại và xin giải thích trước khi làm tiếp.",
        "Hỏi nhóm vì sao chọn cách đó rồi nói phần mình còn chưa hiểu.",
        "Xin một người trong nhóm giải thích lại chỗ mình chưa rõ.",
        "Nói với nhóm mình đã đồng ý nhưng còn cần hiểu một bước.",
        "Hỏi nhóm ai làm phần mình chưa rõ để trao đổi đúng người.",
        "Nói lại ý mình hiểu và nhờ nhóm kiểm tra một chỗ còn chưa chắc.",
    ),
    "avoid-small-conflict": (
        "Nói với người kia phần mình không nhận được và hỏi họ có cách sắp xếp khác không.",
        "Nhắn người kia việc mình nhận được và việc cần họ tìm người khác.",
        "Nói lại với người kia mình không tiện nhận việc đó, chưa hứa thêm phần khác.",
        "Hỏi người kia có thể đổi phần việc đã nhờ không rồi nói giới hạn mình nhận được.",
        "Nói với người kia giờ nào mình làm được việc đã nhận để cùng sắp lại.",
        "Nhắn rõ phần mình không muốn nhận để người kia không phải đoán.",
        "Nói với người kia phần việc mình đã nhận cần thu lại ở mức nào.",
        "Nói một giới hạn cho việc đã nhận và hỏi người kia có sắp xếp được không.",
    ),
    "defend-old-choice": (
        "Hỏi người cùng làm cách cũ đang cho kết quả gì rồi cùng chọn một bước thử khác.",
        "Nói với người kia kết quả mình cần và hỏi cách cũ có đáp ứng không.",
        "Chọn một phần thử cách khác và hỏi người cùng làm sẽ so kết quả thế nào.",
        "Hỏi người kia phần nào của cách cũ còn hiệu quả trước khi cùng bỏ thêm công.",
        "Nói kết quả chưa tốt của cách cũ rồi đề nghị hai bên đổi một bước nhỏ.",
        "Viết kết quả cách cũ đang cho và hỏi người kia có cách kiểm tra khác không.",
        "Hỏi người cùng làm một thay đổi có thể thử mà chưa bỏ hết cách cũ.",
        "Nói phần công đã bỏ ra và phần kết quả cần sửa để hai bên cùng xem lại.",
    ),
    "capacity-before-agreement": (
        "Nói với người kia thời gian bạn cần và hỏi họ cần xong lúc nào.",
        "Hỏi người kia thời gian cần cho việc đó rồi cùng so với lịch bạn còn trống.",
        "Nói thời gian bạn có thể bắt đầu và hỏi người kia có chờ được không.",
        "Chọn phần vừa thời gian mình có và hỏi người kia phần đó có giúp được không.",
        "Nói với người kia mình cần xem lịch rồi mới chốt thời gian giúp.",
        "Hỏi người kia phần nào cần trước rồi nói thời gian mình dành được.",
        "Nói thời gian mình cần dừng và hỏi người kia có chia việc theo đó được không.",
        "Nhắn người kia thời gian còn trống và hỏi việc cần giúp có vừa khoảng đó không.",
    ),
    "quick-reply": (
        "Đọc hết tin nhắn rồi hỏi người kia có đúng điều mình vừa hiểu không.",
        "Đọc hết phần giải thích rồi nói với người kia câu hỏi mình cần làm rõ.",
        "Viết câu trả lời chưa gửi rồi đọc hết tin nhắn để kiểm tra ý người kia.",
        "Đọc hết tin nhắn rồi hỏi người kia chỗ làm mình khó chịu đang có ý gì.",
        "Đọc hết tin nhắn rồi trả lời câu người kia hỏi, chưa đoán lý do họ hỏi.",
        "Hỏi người kia một chỗ chưa hiểu sau khi đọc hết tin nhắn.",
        "Đọc hết tin nhắn rồi viết một câu trả lời rõ về điều mình muốn trao đổi.",
        "Đọc hết tin nhắn rồi xác nhận điều người kia cần trước khi gửi câu trả lời.",
    ),
    "repair-reply": (
        "Nhắn lại ý mình muốn nói và hỏi người kia câu vừa gửi có chỗ nào chưa rõ.",
        "Nói lại câu hỏi chính và hỏi người kia có hiểu đúng ý mình muốn nói không.",
        "Nhắn lại rằng câu vừa rồi hơi gắt rồi nói rõ điều mình muốn trao đổi.",
        "Nói lại phần mình muốn hỏi và để người kia trả lời đúng phần đó.",
        "Nhắn lại cách nói rõ hơn rồi hỏi người kia có cần mình giải thích thêm không.",
        "Nói ý mình muốn nói bằng một câu và hỏi người kia hiểu câu đó thế nào.",
        "Nhắn lại điều mình cần trao đổi, chưa thêm lời trách về ý người kia.",
        "Nói lại ý chính rồi hỏi người kia câu nào trong tin vừa gửi còn chưa rõ.",
    ),
    "specific-feedback": (
        "Hỏi người kia hiểu ý gì từ một phần bản nháp, rồi nghe họ góp ý phần đó.",
        "Nói với người kia một phần cần góp ý và hỏi họ có tiện xem không.",
        "Chọn một phần bản nháp rồi hỏi người kia muốn mình làm rõ chỗ nào.",
        "Hỏi người kia một câu về phần còn phân vân, chưa yêu cầu họ đoán mình cần gì.",
        "Chọn một phần cần góp ý và hỏi người kia có hiểu cách mình trình bày không.",
        "Ghi dấu một phần bản nháp rồi nhờ người kia nói ý họ hiểu từ phần đó.",
        "Hỏi người kia góp ý một phần cụ thể và nói mình sẽ xem lại phần ấy.",
        "Nói với người kia điều muốn hỏi ở một phần bản nháp rồi xin góp ý.",
    ),
    "name-the-need": (
        "Nói một việc cụ thể mình cần giúp và hỏi người kia có tiện nhận phần đó không.",
        "Hỏi người kia có giúp được một phần cụ thể không, rồi nói phần mình tự làm.",
        "Nói việc cần giúp và hỏi người kia cần thêm thông tin gì để nhận việc đó.",
        "Chọn một việc cần giúp rồi hỏi người kia có đủ giờ cho việc ấy không.",
        "Nói một đề nghị cụ thể và nghe người kia trả lời phần họ giúp được.",
        "Hỏi người kia có thể giúp việc cụ thể nào trong phần mình đang cần.",
        "Nói rõ việc cần giúp rồi hỏi người kia muốn cùng làm hay làm riêng một phần.",
        "Ghi một việc cụ thể cần giúp rồi trao đổi với người kia về giờ làm.",
    ),
}


def _expand_daily_issue(issue: DailyIssuePattern) -> DailyIssuePattern:
    titles, scenes, actions = _DAILY_VARIATIONS[issue.key]
    expanded = replace(
        issue,
        headlines=tuple(dict.fromkeys((*issue.headlines, *titles))),
        scenes=tuple(dict.fromkeys((*issue.scenes, *scenes))),
        advice=tuple(dict.fromkeys((*issue.advice, *actions))),
        relationship_advice=_RELATIONSHIP_ACTIONS.get(issue.key, ()),
    )
    if (len(expanded.headlines), len(expanded.scenes), len(expanded.advice)) != (6, 8, 8):
        raise ValueError(f"Daily issue {issue.key} requires 384 distinct bounded variants")
    if SemanticArena.RELATIONSHIPS in issue.arenas and len(set(expanded.relationship_advice)) != 8:
        raise ValueError(f"Daily issue {issue.key} requires eight matched relationship actions")
    return expanded


DAILY_ISSUES = tuple(_expand_daily_issue(issue) for issue in DAILY_ISSUES)

# Plain-language name of each situation's mechanism, used only when a transit
# legitimately explains today's note (B1b). At most 12 words, no advice.
WHY_TODAY_GISTS: dict[str, str] = {
    "missing-context": "chuyện bạn đoán ý khi thông tin còn thiếu",
    "too-many-open-loops": "chuyện bạn mở thêm việc khi việc cũ còn dở",
    "changed-plan": "chuyện bạn xoay lại lịch khi kế hoạch đổi",
    "comparison-loop": "chuyện bạn tự so mình với người khác",
    "automatic-caretaking": "chuyện bạn nhận giúp người khác trước khi tính sức mình",
    "decision-fatigue": "chuyện bạn khó chọn khi đang mệt",
    "perfect-before-start": "chuyện bạn sửa mãi trước khi dám gửi",
    "group-pressure": "chuyện bạn gật theo nhóm khi chưa hiểu hết",
    "avoid-small-conflict": "chuyện bạn nói đồng ý để khỏi phải từ chối",
    "defend-old-choice": "chuyện bạn giữ cách cũ vì đã bỏ nhiều công",
    "capacity-before-agreement": "chuyện bạn nhận lời khi lịch đã kín",
    "quick-reply": "chuyện bạn trả lời trước khi kịp hiểu rõ",
    "repair-reply": "chuyện bạn trả lời vội rồi mới thấy gắt",
    "specific-feedback": "chuyện bạn muốn nhận góp ý thật cụ thể",
    "name-the-need": "chuyện bạn nói ra điều mình thật sự cần",
}
if set(WHY_TODAY_GISTS) != {issue.key for issue in DAILY_ISSUES}:
    raise ValueError("Every Daily issue needs exactly one why-today gist")

# The aspect is described by what it does, never as a forecast or a mood level.
_WHY_TODAY_VERBS = {
    "conjunction": "đang đi sát",
    "sextile": "đang hỗ trợ",
    "trine": "đang hỗ trợ",
    "square": "đang tạo góc căng với",
    "opposition": "đang tạo góc căng với",
}


def render_why_today(plan: ReadingPlan) -> str | None:
    """One closed-template sentence linking today's transit to the frozen situation."""

    selection = plan.daily_selection
    if selection is None or selection.transit_ref is None:
        return None
    transit = next(factor for factor in plan.factors if factor.id == selection.transit_ref)
    transit_body, natal_body = transit.subjects
    aspect = transit.id.split(":")[2]
    return (
        f"Hôm nay {body_label(transit_body)} {_WHY_TODAY_VERBS[aspect]} "
        f"{body_label(natal_body)} của bạn, phần trong lá số gắn với "
        f"{WHY_TODAY_GISTS[selection.issue_key]}."
    )


DAILY_PSYCHOLOGY_CONTENT_FINGERPRINT = sha256(
    json.dumps(
        {
            "version": DAILY_PSYCHOLOGY_MATRIX_VERSION,
            "situations": [asdict(issue) for issue in DAILY_ISSUES],
            "personalization": PERSONALIZATION_VERSION,
            "placements": PLACEMENT_ISSUES,
            "placement_meanings": PLACEMENT_MEANINGS,
            "sign_elements": SIGN_ELEMENTS,
            "sun_issues": SUN_ISSUES,
            "body_domains": BODY_DOMAINS,
            "house_arenas": HOUSE_ARENAS,
            "pairs": [{**asdict(rule), "bodies": sorted(rule.bodies)} for rule in PAIR_RULES],
            "why_today": WHY_TODAY_GISTS,
            "context_meanings": [CAPACITY_AT_WORK_MEANING, REPAIR_REPLY_MEANING],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
).hexdigest()[:8]


NO_PERSONAL_MEANING = "Lá chưa đủ dữ kiện để nói riêng về bạn ở góc này."

# A lead opens the scene sentence ("Với người kia, khi …") so the context reads
# as one sentence, not a fragment. Every scene starts with "Khi".
_ARENA_LEADS = {
    SemanticArena.RELATIONSHIPS: "Với người kia,",
    SemanticArena.COMMUNICATION: "Trong một cuộc nói chuyện,",
    SemanticArena.WORK: "Trong công việc hoặc chuyện học,",
    SemanticArena.ENERGY: "Về năng lượng của cơ thể,",
    SemanticArena.SELF_CARE: "Trong giờ nghỉ ngơi,",
}
# v6 notes stored a separate fragment before the scene; saved notes keep it.
LEGACY_ARENA_LEADS = {
    SemanticArena.RELATIONSHIPS: "Ví dụ với người kia.",
    SemanticArena.COMMUNICATION: "Ví dụ trong cuộc nói chuyện.",
    SemanticArena.WORK: "Ví dụ trong công việc hoặc chuyện học.",
    SemanticArena.ENERGY: "Ví dụ khi chăm cơ thể.",
    SemanticArena.SELF_CARE: "Ví dụ trong giờ nghỉ ngơi.",
}


def lead_scene(lead: str, scene: str) -> str:
    return f"{lead} {scene[:1].lower()}{scene[1:]}"


def current_scene_lead(manifestation: str) -> str | None:
    """The v7 context clause opening a scene ("Với người kia,"), if any."""

    return next(
        (lead for lead in _ARENA_LEADS.values() if manifestation.startswith(f"{lead} ")),
        None,
    )


def split_scene_lead(manifestation: str) -> tuple[SemanticArena | None, str]:
    """Return the scene's arena lead and the direct scene text, current or legacy."""

    for arena, lead in _ARENA_LEADS.items():
        if manifestation.startswith(f"{lead} "):
            rest = manifestation[len(lead) + 1 :]
            return arena, f"{rest[:1].upper()}{rest[1:]}"
    for arena, lead in LEGACY_ARENA_LEADS.items():
        if manifestation.startswith(f"{lead} "):
            return arena, manifestation[len(lead) + 1 :]
    return None, manifestation


class StaleDailySelection(ValueError):
    """A stored Daily plan's frozen situation no longer exists under current rules."""


INSUFFICIENT_CONTEXT_RULE = "insufficient-context"
FALLBACK_ISSUE_KEY = "capacity-before-agreement"


def _situation_pool(
    plan: ReadingPlan, situations: tuple[SupportedSituation, ...]
) -> list[SupportedSituation]:
    arena = semantic_arena(plan.background_lens)
    issues = {issue.key: issue for issue in DAILY_ISSUES}
    eligible = tuple(
        situation
        for situation in situations
        if arena is SemanticArena.GENERAL or arena in issues[situation.issue_key].arenas
    )
    if not eligible:
        return []

    # A known house refines context, not personality. User's explicit lens wins.
    def rank(situation: SupportedSituation) -> tuple[int, int, int, int]:
        return (*situation.rank, int(situation.arena is arena))

    best_rank = max(rank(situation) for situation in eligible)
    return sorted(
        (situation for situation in eligible if rank(situation) == best_rank),
        key=lambda situation: (situation.issue_key, situation.rule_key),
    )


def _pick(plan: ReadingPlan, pool: list[SupportedSituation]) -> SupportedSituation | None:
    (issue_slot,) = daily_mixed_radix_slots(plan.editorial_seed, (max(1, len(pool)),))
    return pool[issue_slot] if pool else None


def select_daily_situation(
    natal_plan: ReadingPlan,
    transit_plans: tuple[tuple[DerivedFactor, ReadingPlan], ...],
) -> tuple[DailySelection, DerivedFactor | None]:
    """Choose today's situation once, then the only transit allowed to explain it.

    ``transit_plans`` pairs every salient transit with the natal plan plus that
    transit (and its natal dependency). A transit *drives* a situation its own
    pair rule creates; it *supports* a natal situation only when its pair rule
    yields the same issue and it touches a placement the situation rests on.
    Sharing a planet alone is never enough (Codex review of the B1b plan).
    """

    driven: list[tuple[SupportedSituation, DerivedFactor]] = [
        (situation, transit)
        for transit, plan in transit_plans
        for situation in eligible_daily_situations(plan)
        if transit.id in situation.factor_refs
    ]
    pool = _situation_pool(
        natal_plan,
        (*eligible_daily_situations(natal_plan), *(situation for situation, _ in driven)),
    )
    picked = _pick(natal_plan, pool)
    if picked is None:
        return DailySelection(
            issue_key=FALLBACK_ISSUE_KEY, rule_key=INSUFFICIENT_CONTEXT_RULE, support_refs=()
        ), None
    driver = next((transit for situation, transit in driven if situation is picked), None)
    transit: DerivedFactor | None
    if driver is not None:
        role, transit = DailyTransitRole.DRIVES, driver
    else:
        supporters = [
            transit
            for situation, transit in driven
            if situation.issue_key == picked.issue_key
            and set(transit.child_refs) & set(picked.factor_refs)
        ]
        transit = min(supporters, key=lambda item: (-item.salience, item.id), default=None)
        role = DailyTransitRole.SUPPORTS if transit is not None else DailyTransitRole.NONE
    return DailySelection(
        issue_key=picked.issue_key,
        rule_key=picked.rule_key,
        support_refs=picked.factor_refs,
        transit_ref=transit.id if transit is not None else None,
        transit_role=role,
    ), transit


def _frozen_situation(plan: ReadingPlan) -> SupportedSituation | None:
    selection = plan.daily_selection
    if selection is None or selection.rule_key == INSUFFICIENT_CONTEXT_RULE:
        return None
    match = next(
        (
            situation
            for situation in eligible_daily_situations(plan)
            if situation.rule_key == selection.rule_key
            and situation.issue_key == selection.issue_key
            and situation.factor_refs == selection.support_refs
        ),
        None,
    )
    if match is None:
        # Never quietly render a different situation from the one persisted.
        raise StaleDailySelection("frozen daily selection no longer matches the plan")
    return match


def apply_daily_psychology(
    plan: ReadingPlan,
    frame: InterpretationFrame,
) -> InterpretationFrame:
    """Compile one observable daily scene and one compatible bounded action."""

    if plan.purpose is not ReadingPurpose.DAILY_NOTE or plan.tradition is not Tradition.WESTERN:
        return frame

    arena = semantic_arena(plan.background_lens)
    issues = {issue.key: issue for issue in DAILY_ISSUES}
    if plan.daily_selection is not None:
        frozen = _frozen_situation(plan)
        pool = [frozen] if frozen is not None else []
        issue_slot = 0
    else:
        pool = _situation_pool(plan, eligible_daily_situations(plan))
        (issue_slot,) = daily_mixed_radix_slots(plan.editorial_seed, (max(1, len(pool)),))
    # Eligibility ties must not consume the day counter: two factors supporting
    # the same issue would otherwise repeat its card on consecutive days.
    headline_slot, scene_slot, advice_slot = daily_mixed_radix_slots(
        plan.editorial_seed,
        (6, 8, 8),
    )
    selected = pool[issue_slot] if pool else None
    issue = issues[selected.issue_key if selected else FALLBACK_ISSUE_KEY]
    scene_arena = (
        arena
        if arena is not SemanticArena.GENERAL
        else (selected.arena if selected and selected.arena in issue.arenas else arena)
    )
    lead = _ARENA_LEADS.get(scene_arena)
    manifestation = issue.scenes[scene_slot]
    if lead is not None:
        manifestation = lead_scene(lead, manifestation)
    actions = issue.relationship_advice if arena is SemanticArena.RELATIONSHIPS else issue.advice
    action = actions[advice_slot]
    source_refs = tuple(f"psychology-source:{source_id}" for source_id in issue.source_ids)
    personal_meaning = selected.meaning if selected else NO_PERSONAL_MEANING
    # The rewrite brief keeps the situation's meaning; the reader sees two
    # sentences: what tends to happen for you, then what you can take from it.
    # Limits (example scene, date-only reading) live in the evidence and the one
    # page disclaimer, never inside the main text.
    core_meaning = f"{personal_meaning} {issue.meaning}"
    takeaway = issue.takeaway
    allowed_refs = {
        factor.id
        for factor in plan.factors
        if plan.precision is TimePrecision.EXACT
        or factor.kind not in {FactorKind.HOUSE_PLACEMENT, FactorKind.ANGLE}
    }
    selected_refs = tuple(
        dict.fromkeys(
            ref
            for ref in (
                *(selected.factor_refs if selected else ()),
                *plan.hero_factor_refs,
                *frame.evidence_factor_refs,
            )
            if ref in allowed_refs
        )
    )[:12]
    # Disclosure order is canonical, not editorial priority. A changed lens may
    # change true supporting facts, but never merely reorder the same facts.
    evidence_refs = (
        *tuple(ref for ref in plan.hero_factor_refs if ref in selected_refs),
        *tuple(sorted(set(selected_refs) - set(plan.hero_factor_refs))),
    )

    return replace(
        frame,
        hook=issue.headlines[headline_slot],
        thesis=f"{personal_meaning} {takeaway}",
        manifestation=manifestation,
        micro_action=action,
        knowledge_refs=(
            *frame.knowledge_refs,
            f"psychology-matrix:{DAILY_PSYCHOLOGY_MATRIX_VERSION}",
            f"personalization:{PERSONALIZATION_VERSION}",
            f"daily-rule:{selected.rule_key if selected else INSUFFICIENT_CONTEXT_RULE}",
            *source_refs,
        ),
        arena=arena,
        evidence_factor_refs=evidence_refs,
        mechanism_key=f"psychology:{issue.key}",
        scene_key=f"psychology:{issue.key}:scene-{scene_slot}",
        action_key=f"psychology:{issue.key}:{arena.value}-advice-{advice_slot}",
        daily_meaning=DailyMeaningBrief(
            core_meaning=core_meaning,
            reader_takeaway=takeaway,
            scene_anchors=issue.scene_anchors,
            action_anchors=issue.action_anchors,
            observation_question=issue.observation_question,
        ),
    )


def source_ids() -> frozenset[str]:
    return frozenset(source.source_id for source in PSYCHOLOGY_SOURCES)


def issue_source_ids() -> frozenset[str]:
    return frozenset(source_id for issue in DAILY_ISSUES for source_id in issue.source_ids)
