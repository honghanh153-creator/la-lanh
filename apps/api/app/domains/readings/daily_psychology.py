from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from hashlib import sha256

from app.domains.astro.models import Tradition
from app.domains.readings.interpretive_lenses import daily_mixed_radix_slots
from app.domains.readings.knowledge import InterpretationFrame, semantic_arena
from app.domains.readings.models import (
    DailyMeaningBrief,
    ReadingPlan,
    ReadingPurpose,
    SemanticArena,
)

DAILY_PSYCHOLOGY_MATRIX_VERSION = "daily-direct-meaning-v4"


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
    headlines: tuple[str, str, str, str]
    scenes: tuple[str, str, str]
    advice: tuple[str, str, str, str]
    meaning: str
    takeaway: str
    scene_anchors: tuple[str, ...]
    action_anchors: tuple[str, ...]
    source_ids: tuple[str, ...]
    observation_question: str


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
        "Chưa hiểu một tin nhắn không có nghĩa là người kia đang khó chịu.",
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
        "Bận nhiều không đồng nghĩa với hoàn thành nhiều.",
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
        "Có thể nói rõ giờ nào còn phù hợp thay vì tự đổi hết lịch.",
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
        "So với việc mình làm trước đó giúp nhìn rõ tiến triển hơn một bài đăng của người khác.",
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
        "Có thể giúp một phần và nói rõ giới hạn của mình.",
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
        "Ít lựa chọn hơn hoặc nghỉ trước khi chọn có thể giúp mình so sánh rõ hơn.",
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
        "Có thể gửi để nhận góp ý mà chưa cần chỉnh mọi câu thật hoàn hảo.",
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
        "Cả nhóm đã chốt không có nghĩa là câu hỏi của mình đã được giải đáp.",
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
        "Người kia khó biết mình không tiện nếu mình chỉ nói đồng ý.",
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
        "Việc đã làm nhiều và việc đang có hiệu quả là hai điều khác nhau.",
        ("kết quả", "cách", "làm"),
        ("kết quả", "cách", "thay đổi"),
        ("tavris-aronson-mistakes-were-made", "dweck-mindset"),
        "Bạn đã biết cách làm hiện tại có hiệu quả ở chỗ nào chưa?",
    ),
)


DAILY_PSYCHOLOGY_CONTENT_FINGERPRINT = sha256(
    json.dumps(
        {
            "version": DAILY_PSYCHOLOGY_MATRIX_VERSION,
            "situations": [asdict(issue) for issue in DAILY_ISSUES],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
).hexdigest()[:8]


_ARENA_LEADS = {
    SemanticArena.RELATIONSHIPS: "Với người kia,",
    SemanticArena.COMMUNICATION: "Trong cuộc nói chuyện,",
    SemanticArena.WORK: "Ở công việc hoặc chuyện học,",
    SemanticArena.ENERGY: "Với cơ thể đang mệt,",
    SemanticArena.SELF_CARE: "Trong giờ nghỉ ngơi,",
}

_SIGN_ORDER = (
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
)


def apply_daily_psychology(
    plan: ReadingPlan,
    frame: InterpretationFrame,
) -> InterpretationFrame:
    """Compile one observable daily scene and one compatible bounded action."""

    if plan.purpose is not ReadingPurpose.DAILY_NOTE or plan.tradition is not Tradition.WESTERN:
        return frame

    arena = semantic_arena(plan.background_lens)
    pool = (
        DAILY_ISSUES
        if arena is SemanticArena.GENERAL
        else tuple(issue for issue in DAILY_ISSUES if arena in issue.arenas)
    )
    issue_slot, headline_slot, scene_slot, advice_slot = daily_mixed_radix_slots(
        plan.editorial_seed,
        (len(pool), 4, 3, 4),
    )
    chart_signature = "|".join(factor.id for factor in plan.factors) or plan.mode.value
    date_only_sign = next(
        (
            factor.id.rsplit(":", 1)[1]
            for factor in plan.factors
            if factor.id.startswith("date_only:sun:vibe:certain:")
        ),
        None,
    )
    chart_shift = (
        _SIGN_ORDER.index(date_only_sign) * 37
        if date_only_sign in _SIGN_ORDER
        else int.from_bytes(sha256(chart_signature.encode()).digest()[:4], "big")
    )
    issue_slot = (issue_slot + chart_shift) % len(pool)
    headline_slot = (headline_slot + chart_shift // len(pool)) % 4
    scene_slot = (scene_slot + chart_shift // (len(pool) * 4)) % 3
    advice_slot = (advice_slot + chart_shift // (len(pool) * 12)) % 4
    issue = pool[issue_slot]
    lead = _ARENA_LEADS.get(arena)
    manifestation = issue.scenes[scene_slot]
    if lead is not None:
        manifestation = f"{lead} {manifestation[0].lower()}{manifestation[1:]}"
    action = issue.advice[advice_slot]
    source_refs = tuple(f"psychology-source:{source_id}" for source_id in issue.source_ids)

    return replace(
        frame,
        hook=issue.headlines[headline_slot],
        thesis=f"{issue.meaning} {issue.takeaway}",
        manifestation=manifestation,
        micro_action=action,
        knowledge_refs=(
            *frame.knowledge_refs,
            f"psychology-matrix:{DAILY_PSYCHOLOGY_MATRIX_VERSION}",
            *source_refs,
        ),
        arena=arena,
        mechanism_key=f"psychology:{issue.key}",
        scene_key=f"psychology:{issue.key}:scene-{scene_slot}",
        action_key=f"psychology:{issue.key}:advice-{advice_slot}",
        daily_meaning=DailyMeaningBrief(
            core_meaning=issue.meaning,
            reader_takeaway=issue.takeaway,
            scene_anchors=issue.scene_anchors,
            action_anchors=issue.action_anchors,
            observation_question=issue.observation_question,
        ),
    )


def source_ids() -> frozenset[str]:
    return frozenset(source.source_id for source in PSYCHOLOGY_SOURCES)


def issue_source_ids() -> frozenset[str]:
    return frozenset(source_id for issue in DAILY_ISSUES for source_id in issue.source_ids)
