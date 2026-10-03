from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256

from app.domains.astro.models import Tradition
from app.domains.readings.interpretive_lenses import daily_mixed_radix_slots
from app.domains.readings.knowledge import InterpretationFrame, semantic_arena
from app.domains.readings.models import ReadingPlan, ReadingPurpose, SemanticArena

DAILY_PSYCHOLOGY_MATRIX_VERSION = "daily-psychology-scene-advice-v2"


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
    key: str
    arenas: tuple[SemanticArena, ...]
    headlines: tuple[str, str, str]
    scenes: tuple[str, str, str]
    observations: tuple[str, str, str]
    advice: tuple[str, str, str, str]
    source_ids: tuple[str, ...]


DAILY_ISSUES: tuple[DailyIssuePattern, ...] = (
    DailyIssuePattern(
        "missing-context",
        (SemanticArena.RELATIONSHIPS, SemanticArena.COMMUNICATION, SemanticArena.WORK),
        (
            "Một chi tiết nhỏ dễ bị đầu óc viết tiếp thành cả câu chuyện.",
            "Khoảng trống thông tin hôm nay dễ được lấp bằng suy đoán.",
            "Một câu trả lời chưa rõ có thể chiếm nhiều chỗ hơn chính sự việc.",
        ),
        (
            "khi một tin nhắn ngắn hơn thường lệ xuất hiện, bạn dễ đọc lại nó nhiều lần",
            "khi câu trả lời đến muộn, bạn dễ tự nối thêm lý do trước khi người kia nói rõ",
            "khi một yêu cầu còn mơ hồ, bạn dễ bắt tay làm theo cách mình đoán là đúng",
        ),
        (
            "Điều đã xảy ra chỉ là một dấu hiệu; phần còn lại vẫn chưa có dữ kiện.",
            "Bạn có thể phản ứng với phần mình tự điền thêm nhiều hơn với câu chữ thật.",
            "Việc chờ thêm thông tin có thể khó chịu hơn chính câu trả lời.",
        ),
        (
            "Nhắn một câu hỏi thẳng vào chỗ bạn chưa hiểu.",
            "Viết hai dòng: một dòng là điều bạn biết, một dòng là điều bạn đang đoán.",
            "Chờ mười phút rồi mới quyết định có nhắn thêm hay không.",
            "Đọc lại đúng tin nhắn. Đừng tự đoán người kia đang nghĩ gì.",
        ),
        (
            "kahneman-thinking-fast-slow",
            "harris-happiness-trap",
            "rosenberg-nonviolent-communication",
        ),
    ),
    DailyIssuePattern(
        "too-many-open-loops",
        (SemanticArena.WORK, SemanticArena.ENERGY, SemanticArena.SELF_CARE),
        (
            "Nhiều việc nhỏ dễ cùng đòi làm trước.",
            "Một ngày bận có thể bắt đầu bằng quá nhiều việc đều mang nhãn gấp.",
            "Đầu óc dễ giữ tất cả cửa sổ mở cùng lúc.",
        ),
        (
            "khi ba đầu việc cùng báo đến, bạn dễ chuyển qua lại mà chưa khép việc nào",
            "khi lịch có một khoảng trống, bạn dễ lấp ngay bằng việc tiếp theo",
            "khi cơ thể đã mệt, bạn vẫn dễ mở thêm một việc chỉ để thấy mình đang tiến lên",
        ),
        (
            "Mỗi lần đổi việc tạo cảm giác đang bận, nhưng phần quan trọng vẫn đứng yên.",
            "Việc nhỏ và việc quan trọng có thể đang dùng cùng một mức chú ý.",
            "Mệt dễ bị hiểu nhầm thành thiếu cố gắng, nên danh sách tiếp tục dài ra.",
        ),
        (
            "Chọn một việc làm trong hai mươi phút. Tạm cất các việc còn lại.",
            "Viết ra ba việc rồi khoanh việc cần xong trước.",
            "Chọn giờ dừng trước khi bắt đầu.",
            "Tắt một loại thông báo cho đến khi xong việc đang làm.",
        ),
        ("csikszentmihalyi-flow", "goleman-emotional-intelligence"),
    ),
    DailyIssuePattern(
        "changed-plan",
        (SemanticArena.WORK, SemanticArena.ENERGY, SemanticArena.SELF_CARE),
        (
            "Một thay đổi nhỏ trong lịch dễ kéo theo phản ứng lớn hơn dự kiến.",
            "Kế hoạch đổi phút chót có thể làm cả ngày mất điểm tựa.",
            "Điều gây khó chịu có thể là cách thay đổi xảy ra, không chỉ là việc bị đổi.",
        ),
        (
            "khi một cuộc hẹn hoặc đầu việc đổi giờ, bạn dễ cố giữ nguyên mọi phần còn lại",
            "khi người khác đổi kế hoạch sát giờ, cơ thể dễ căng trước khi bạn kịp trả lời",
            "khi lịch bị chen ngang, bạn dễ coi cả ngày như đã hỏng",
        ),
        (
            "Một thay đổi đang bị tính như nhiều thay đổi cùng lúc.",
            "Cảm giác mất quyền chủ động có thể lớn hơn phần việc thật sự phải sửa.",
            "Bạn có thể đang bảo vệ kế hoạch cũ vì nó từng tạo cảm giác ổn định.",
        ),
        (
            "Chỉ đổi phần bắt buộc phải đổi. Những phần khác cứ giữ nguyên.",
            "Hỏi lại giờ mới và ai cần làm gì.",
            "Dành hai phút viết lại kế hoạch ngắn nhất có thể.",
            "Nói rõ lần sau bạn cần được báo sớm hơn.",
        ),
        ("ross-nisbett-person-situation", "goleman-emotional-intelligence"),
    ),
    DailyIssuePattern(
        "comparison-loop",
        (SemanticArena.WORK, SemanticArena.RELATIONSHIPS, SemanticArena.SELF_CARE),
        (
            "Một thành tích của người khác dễ làm việc của bạn bỗng trông nhỏ lại.",
            "So sánh có thể xuất hiện trước khi bạn nhớ hai người đang ở hai chặng khác nhau.",
            "Một con số đẹp trên màn hình dễ đổi cách bạn nhìn ngày của mình.",
        ),
        (
            (
                "khi thấy người khác khoe kết quả, bạn dễ xem lại tiến độ của mình "
                "bằng tiêu chuẩn của họ"
            ),
            "khi một người được khen, bạn dễ nhớ ngay phần mình còn thiếu",
            "khi lướt qua một cập nhật đẹp, bạn dễ quên những phần không được đăng lên",
        ),
        (
            "Một khoảnh khắc của người khác đang được đặt cạnh toàn bộ quá trình của bạn.",
            "Sự chú ý chuyển từ việc đang làm sang vị trí của mình trong mắt người khác.",
            "Cảm giác tụt lại có thể đến trước khi bạn kiểm tra mục tiêu ban đầu.",
        ),
        (
            "Chọn một việc hôm nay mà bạn tự làm được, không cần so với ai.",
            "Rời màn hình năm phút rồi quay lại việc của mình.",
            "Ghi ra một việc bạn đã làm xong hôm nay.",
            "Ẩn bài đăng khiến bạn liên tục so sánh trong hôm nay.",
        ),
        ("cialdini-influence", "dweck-mindset"),
    ),
    DailyIssuePattern(
        "automatic-caretaking",
        (SemanticArena.RELATIONSHIPS, SemanticArena.ENERGY, SemanticArena.SELF_CARE),
        (
            "Cảm xúc của người khác dễ trở thành việc bạn phải xử lý.",
            "Một người xuống mood có thể làm lịch của bạn đổi theo.",
            "Phản xạ chăm người khác dễ chạy trước câu hỏi bạn còn sức hay không.",
        ),
        (
            "khi ai đó buồn, bạn dễ đổi lịch, đổi giọng hoặc nhận luôn phần chăm sóc",
            "khi người kia im hơn thường lệ, bạn dễ đặt nhu cầu của mình sang một bên",
            "khi không khí căng lên, bạn dễ nhận trách nhiệm làm mọi người dễ chịu lại",
        ),
        (
            "Sự quan tâm đang đi cùng một phần trách nhiệm chưa chắc thuộc về bạn.",
            "Bạn có thể giúp rất nhanh nhưng chỉ nhận ra mình mệt sau đó.",
            "Nhu cầu của bạn dễ biến mất khỏi cuộc trò chuyện dù chưa hề được giải quyết.",
        ),
        (
            "Hỏi thẳng: bạn muốn mình nghe, giúp, hay chỉ ngồi cạnh?",
            "Nói trước bạn có thể dành bao nhiêu thời gian.",
            "Tự hỏi: mình còn đủ sức để giúp việc này không?",
            "Giữ lại ít nhất một việc của mình, đừng hủy cả lịch.",
        ),
        ("goleman-emotional-intelligence", "neff-self-compassion"),
    ),
    DailyIssuePattern(
        "decision-fatigue",
        (SemanticArena.WORK, SemanticArena.ENERGY, SemanticArena.SELF_CARE),
        (
            "Một lựa chọn nhỏ có thể thấy nặng vì đã có quá nhiều lựa chọn trước đó.",
            "Cuối ngày, việc đơn giản cũng dễ bị nghĩ thành một bài toán lớn.",
            "Mệt có thể đội lốt phân vân.",
        ),
        (
            (
                "khi phải chọn thêm một việc, bạn dễ mở nhiều phương án nhưng không muốn "
                "chốt phương án nào"
            ),
            (
                "khi cơ thể xuống pin, bạn dễ tiếp tục tìm lựa chọn tốt nhất cho một việc "
                "không quá quan trọng"
            ),
            "khi danh sách đã dài, bạn dễ trì hoãn cả quyết định nhỏ như trả lời hay đặt lịch",
        ),
        (
            "Năng lượng dùng để cân nhắc có thể đã nhiều hơn giá trị khác biệt giữa các phương án.",
            "Bạn đang cố giảm mọi rủi ro trong lúc khả năng chú ý đã giảm.",
            "Việc chưa chốt tiếp tục chiếm chỗ dù bản thân nó không lớn.",
        ),
        (
            "Chỉ giữ hai lựa chọn rồi chọn một.",
            "Việc nào chưa gấp, hẹn giờ mai mới quyết.",
            "Chọn cách dễ đổi lại nhất và thử nhỏ trước.",
            "Chọn một điều quan trọng nhất. Bỏ qua phần phụ lần này.",
        ),
        ("kahneman-thinking-fast-slow", "csikszentmihalyi-flow"),
    ),
    DailyIssuePattern(
        "perfect-before-start",
        (SemanticArena.WORK, SemanticArena.COMMUNICATION, SemanticArena.SELF_CARE),
        (
            "Chuẩn bị kỹ dễ biến thành cách chưa phải bắt đầu.",
            "Một việc chưa hoàn hảo có thể nằm yên lâu hơn một việc còn thiếu.",
            "Sợ làm chưa đẹp dễ xuất hiện dưới dạng cần thêm một vòng chỉnh sửa.",
        ),
        (
            "khi sắp gửi một bài hoặc tin nhắn, bạn dễ sửa thêm dù ý chính đã rõ",
            "khi bắt đầu việc mới, bạn dễ tìm thêm tài liệu trước khi làm bản đầu tiên",
            "khi thấy một lỗi nhỏ, bạn dễ quay lại làm lại cả phần đã đủ dùng",
        ),
        (
            "Tiêu chuẩn đang tăng nhanh hơn chất lượng thật sự cần có.",
            "Bạn có thể đang bảo vệ mình khỏi cảm giác bị đánh giá bằng cách chưa đưa gì ra ngoài.",
            "Phần chuẩn bị tạo cảm giác an toàn nhưng chưa tạo phản hồi mới.",
        ),
        (
            "Gửi bản nháp và ghi rõ phần còn thiếu.",
            "Làm bản đầu trong mười lăm phút. Chưa cần sửa câu chữ.",
            "Chọn mức đủ dùng cho lần này rồi dừng.",
            "Nhờ một người trả lời đúng một câu hỏi.",
        ),
        ("dweck-mindset", "neff-self-compassion"),
    ),
    DailyIssuePattern(
        "group-pressure",
        (SemanticArena.RELATIONSHIPS, SemanticArena.COMMUNICATION, SemanticArena.WORK),
        (
            "Ý kiến đông người dễ nghe giống ý kiến đúng.",
            "Một cái gật đầu nhanh có thể đến trước suy nghĩ thật của bạn.",
            "Không khí đồng thuận dễ làm phần còn lăn tăn im đi.",
        ),
        (
            "khi cả nhóm đồng ý nhanh, bạn dễ gật theo dù vẫn còn một câu hỏi",
            "khi một người có tiếng nói mạnh chốt ý, bạn dễ bỏ qua dữ kiện mình vừa nhận ra",
            "khi bạn bè cùng chọn một hướng, bạn dễ thấy phương án khác kém hợp lý hơn trước",
        ),
        (
            "Cảm giác thuộc về nhóm đang đứng cạnh chất lượng thật của lựa chọn.",
            "Sự tự tin của người nói có thể đang được nghe như bằng chứng.",
            "Điều chưa rõ vẫn còn đó dù căn phòng đã chuyển sang chuyện khác.",
        ),
        (
            "Nói câu bạn còn chưa rõ trước khi đồng ý.",
            "Xin một phút xem lại rồi mới trả lời.",
            "Viết lựa chọn của bạn trước khi nghe cả nhóm.",
            "Hỏi cả nhóm đang dựa vào điều gì để chốt.",
        ),
        ("cialdini-influence", "ross-nisbett-person-situation"),
    ),
    DailyIssuePattern(
        "avoid-small-conflict",
        (SemanticArena.RELATIONSHIPS, SemanticArena.COMMUNICATION, SemanticArena.WORK),
        (
            "Một điều khó nói dễ được đổi thành thêm nhiều việc phải làm.",
            "Giữ hòa khí hôm nay có thể khiến một nhu cầu biến mất khỏi câu chuyện.",
            "Một câu đồng ý nhanh dễ để lại phần khó chịu đến sau.",
        ),
        (
            "khi được nhờ thêm việc, bạn dễ nhận lời trước rồi mới tính mình còn sức hay không",
            "khi người kia hiểu khác ý, bạn dễ im để cuộc trò chuyện kết thúc êm",
            "khi cần từ chối, bạn dễ giải thích rất dài để tránh một câu không ngắn gọn",
        ),
        (
            "Sự yên ổn trước mắt đang được đổi bằng một cuộc nói chuyện khó hơn về sau.",
            "Người kia có thể không biết có vấn đề vì bạn chưa để lại dấu hiệu nào.",
            "Phần bực dễ quay lại ở một việc nhỏ khác không liên quan.",
        ),
        (
            "Nói câu trả lời trước, rồi giải thích bằng một câu.",
            "Nếu không làm hết được, đề nghị một phần bạn có thể làm.",
            "Viết câu bạn muốn nói trong hai dòng. Đọc lại rồi gửi.",
            "Hỏi hai bên đang hiểu khác nhau ở chỗ nào.",
        ),
        ("rosenberg-nonviolent-communication", "goleman-emotional-intelligence"),
    ),
    DailyIssuePattern(
        "defend-old-choice",
        (SemanticArena.WORK, SemanticArena.COMMUNICATION, SemanticArena.RELATIONSHIPS),
        (
            "Dữ kiện mới dễ bị xem nhẹ khi bạn đã bỏ nhiều công vào lựa chọn cũ.",
            "Một quyết định từng hợp lý có thể đang được bảo vệ lâu hơn chính lý do ban đầu.",
            "Càng giải thích một lựa chọn, việc đổi ý càng dễ thấy như thua cuộc.",
        ),
        (
            "khi ai đó chỉ ra một điểm chưa ổn, bạn dễ kể lại vì sao mình đã chọn như vậy",
            (
                "khi kế hoạch không cho kết quả như mong đợi, bạn dễ thêm công sức trước "
                "khi xem lại hướng đi"
            ),
            "khi cuộc trò chuyện có dữ kiện mới, bạn dễ tìm phần bảo vệ kết luận cũ trước",
        ),
        (
            (
                "Việc bảo vệ công sức đã bỏ ra có thể che mất câu hỏi phương án còn hiệu quả "
                "hay không."
            ),
            "Đổi ý đang bị hiểu như phủ nhận toàn bộ lựa chọn trước đây.",
            "Một lời giải thích hợp lý vẫn có thể đi cùng một quyết định cần sửa.",
        ),
        (
            "Viết một lý do để giữ và một lý do để đổi.",
            "Tự hỏi: nếu hôm nay mới bắt đầu, mình còn chọn cách này không?",
            "Sửa một phần nhỏ trước, chưa cần bỏ hết.",
            "Nói điều gì đã đổi, thay vì cố chứng minh ai đúng.",
        ),
        ("tavris-aronson-mistakes-were-made", "dweck-mindset"),
    ),
)


_ARENA_LEADS = {
    SemanticArena.RELATIONSHIPS: "Trong một mối quan hệ bạn đang để tâm,",
    SemanticArena.COMMUNICATION: "Trong một cuộc nói chuyện hoặc đoạn chat hôm nay,",
    SemanticArena.WORK: "Ở công việc hoặc chuyện học hôm nay,",
    SemanticArena.ENERGY: "Khi cơ thể bắt đầu quá tải hôm nay,",
    SemanticArena.SELF_CARE: "Trong lúc chăm mình hoặc nghỉ ngơi hôm nay,",
}

_REFLECTIONS = (
    "Chỉ thử một lần hôm nay là đủ.",
    "Làm xong, xem tình hình có dễ hơn không.",
    "Nếu không giúp ích, bạn không cần làm tiếp.",
)

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
    issue_slot, headline_slot, scene_slot, observation_slot, advice_slot, reflection_slot = (
        daily_mixed_radix_slots(
            plan.editorial_seed,
            (len(pool), 3, 3, 3, 4, len(_REFLECTIONS)),
        )
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
        _SIGN_ORDER.index(date_only_sign)
        if date_only_sign in _SIGN_ORDER
        else int.from_bytes(sha256(chart_signature.encode()).digest()[:4], "big")
    )
    issue_slot = (issue_slot + chart_shift) % len(pool)
    headline_slot = (headline_slot + chart_shift // len(pool)) % 3
    issue = pool[issue_slot]
    lead = _ARENA_LEADS.get(arena)
    scene = issue.scenes[scene_slot]
    if lead is not None:
        scene = f"{lead} {scene[0].lower()}{scene[1:]}"
    else:
        scene = f"Hôm nay, {scene}"
    manifestation = f"{scene}. {issue.observations[observation_slot]}"
    action = f"{issue.advice[advice_slot]} {_REFLECTIONS[reflection_slot]}"
    source_refs = tuple(f"psychology-source:{source_id}" for source_id in issue.source_ids)

    return replace(
        frame,
        hook=issue.headlines[headline_slot],
        manifestation=manifestation,
        micro_action=action,
        knowledge_refs=(
            *frame.knowledge_refs,
            f"psychology-matrix:{DAILY_PSYCHOLOGY_MATRIX_VERSION}",
            *source_refs,
        ),
        arena=arena,
        scene_key=(f"psychology:{issue.key}:scene-{scene_slot}:observation-{observation_slot}"),
        action_key=f"psychology:{issue.key}:advice-{advice_slot}:reflection-{reflection_slot}",
    )


def source_ids() -> frozenset[str]:
    return frozenset(source.source_id for source in PSYCHOLOGY_SOURCES)


def issue_source_ids() -> frozenset[str]:
    return frozenset(source_id for issue in DAILY_ISSUES for source_id in issue.source_ids)
