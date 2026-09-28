from __future__ import annotations

from dataclasses import dataclass

from app.domains.astro.models import Tradition
from app.domains.readings.interpretive_lenses import (
    CURRENT_FORCES,
    METHODOLOGY_VERSION,
    PLANET_PERSPECTIVES,
    EditorialMode,
    ElementMeaning,
    InterpretiveLens,
    ModalityMeaning,
    PlanetPerspective,
    daily_mixed_radix_slots,
    house_mode,
    resolve_daily_editorial_variant,
    sign_structure,
)
from app.domains.readings.models import (
    INTERPRETATION_KNOWLEDGE_VERSION,
    BackgroundLens,
    DerivedFactor,
    FactorKind,
    ReadingPlan,
    ReadingPurpose,
    SemanticArena,
)

KNOWLEDGE_VERSION = INTERPRETATION_KNOWLEDGE_VERSION

BODY_LABELS = {
    "sun": "Mặt Trời",
    "moon": "Mặt Trăng",
    "mercury": "Sao Thủy",
    "venus": "Sao Kim",
    "mars": "Sao Hỏa",
    "jupiter": "Sao Mộc",
    "saturn": "Sao Thổ",
    "uranus": "Thiên Vương",
    "neptune": "Hải Vương",
    "pluto": "Diêm Vương",
    "true_node": "Nút Bắc",
    "mean_node": "Nút Bắc trung bình",
    "south_node": "Nút Nam",
    "chiron": "Chiron",
}


def body_label(value: str) -> str:
    return BODY_LABELS.get(value, value.replace("_", " ").title())


@dataclass(frozen=True)
class PlanetMeaning:
    drive: str
    stress: str
    action: str


@dataclass(frozen=True)
class SignMeaning:
    style: str
    stress: str
    manifestation: str
    practices: tuple[str, str, str]
    hooks: tuple[str, str, str]


@dataclass(frozen=True)
class HouseMeaning:
    arena: str
    manifestation: str


@dataclass(frozen=True)
class AspectMeaning:
    bridge: str
    watch: str


@dataclass(frozen=True)
class InterpretationFrame:
    hook: str
    thesis: str
    manifestation: str
    micro_action: str
    evidence_factor_refs: tuple[str, ...]
    knowledge_refs: tuple[str, ...]
    arena: SemanticArena = SemanticArena.GENERAL
    mechanism_key: str = "general"
    scene_key: str = "general"
    action_key: str = "observe"


PLANETS: dict[str, PlanetMeaning] = {
    "sun": PlanetMeaning(
        "được tự quyết và thấy việc mình làm có ý nghĩa",
        "cố chứng minh mình ổn bằng cách làm thêm",
        "chọn một việc thật sự mang dấu tay của bạn và bỏ bớt một việc chỉ để ghi điểm",
    ),
    "moon": PlanetMeaning(
        "được an toàn trước khi mở lòng",
        "nuốt nhu cầu xuống rồi mong người khác tự hiểu",
        "viết riêng một câu “mình đang cảm thấy…” và một câu “mình đang cần…”",
    ),
    "mercury": PlanetMeaning(
        "hiểu cho rõ rồi mới nói",
        "nghĩ thêm năm vòng nhưng vẫn chưa nói câu chính",
        "viết câu quan trọng nhất trước, phần giải thích để sau",
    ),
    "venus": PlanetMeaning(
        "biết mình được trân trọng theo cách nào",
        "biến sự im lặng thành một bài test ngầm",
        "nói thẳng một điều khiến bạn thấy được trân trọng, dưới dạng đề nghị",
    ),
    "mars": PlanetMeaning(
        "được hành động thẳng và giữ ranh giới",
        "bật chế độ xử lý trước khi biết mình đang bực điều gì",
        "chọn một bước bắt đầu và một giới hạn bạn sẽ không vượt qua hôm nay",
    ),
    "jupiter": PlanetMeaning(
        "được thử một khả năng rộng hơn",
        "hào hứng với viễn cảnh trước khi kiểm tra nguồn lực",
        "ghi một khả năng muốn thử và một bằng chứng nhỏ cần có trước khi đi xa",
    ),
    "saturn": PlanetMeaning(
        "có cấu trúc đủ chắc để yên tâm tiến tiếp",
        "coi chịu đựng là bằng chứng duy nhất của trưởng thành",
        "đặt một tiêu chuẩn đủ dùng và một mốc dừng rõ ràng",
    ),
    "uranus": PlanetMeaning(
        "được đổi cách làm mà vẫn giữ quyền tự chủ",
        "phá nhịp quá sớm chỉ để thoát cảm giác bị bó",
        "đổi đúng một biến nhỏ thay vì lật cả bàn",
    ),
    "neptune": PlanetMeaning(
        "có khoảng mềm để tưởng tượng và cảm nhận",
        "để mong muốn lấp chỗ của dữ kiện",
        "tách điều bạn biết, điều bạn đoán và điều bạn đang hy vọng thành ba dòng",
    ),
    "pluto": PlanetMeaning(
        "được đi tới lõi và lấy lại quyền chủ động",
        "giữ quá chặt vì sợ mất thế kiểm soát",
        "chọn một điều có thể buông quyền kiểm soát mà không bỏ rơi chính mình",
    ),
    "chiron": PlanetMeaning(
        "được đối xử tử tế với điểm còn nhạy",
        "dùng một lần hụt trước đây để kết luận về hiện tại",
        "gọi đúng điều đang chạm vào mình trước khi phản ứng với người đối diện",
    ),
    "true_node": PlanetMeaning(
        "được tập một cách phản ứng mới",
        "ép mình phải tiến bộ thật nhanh",
        "thử một lựa chọn mới ở quy mô đủ nhỏ để còn quay lại quan sát",
    ),
    "mean_node": PlanetMeaning(
        "được tập một cách phản ứng mới",
        "ép mình phải tiến bộ thật nhanh",
        "thử một lựa chọn mới ở quy mô đủ nhỏ để còn quay lại quan sát",
    ),
    "south_node": PlanetMeaning(
        "được dùng kỹ năng quen mà không mắc kẹt trong nó",
        "quay về phản xạ cũ chỉ vì nó dễ đoán",
        "giữ phần kỹ năng còn hữu ích và thử bỏ một phản xạ đã quá hạn",
    ),
}


SIGNS: dict[str, SignMeaning] = {
    "aries": SignMeaning(
        "nhanh, thẳng và thích có điểm bắt đầu rõ",
        "đi trước cảm giác của chính mình",
        "khi một tin nhắn tới đúng lúc bạn đang bực hoặc một đầu việc bị chặn giữa đường",
        (
            "đợi mười nhịp thở rồi mới trả lời",
            "bắt đầu bằng bước nhỏ nhất",
            "hỏi xem việc này có thật sự gấp",
        ),
        (
            "Bạn có thể sắp trả lời nhanh hơn mức mình thật sự chắc.",
            "Một việc đang khiến bạn muốn xử lý ngay cho xong.",
            "Năng lượng khởi động có rồi; hướng đi mới là phần cần chọn.",
        ),
    ),
    "taurus": SignMeaning(
        "chậm, chắc và cần cảm giác đủ tin cậy",
        "giữ nhịp quen lâu hơn mức nó còn dễ chịu",
        "khi lịch quen bị đổi, một cam kết cần sửa hoặc bạn phải quyết định có tiếp tục chờ",
        (
            "đổi một chi tiết, không đổi cả hệ",
            "kiểm tra cơ thể trước khi đồng ý",
            "đặt hạn chót cho việc chờ thêm",
        ),
        (
            "Có thứ bạn chưa muốn đổi chỉ vì nó vẫn còn quen.",
            "Chậm lại là hợp lý; đứng yên mãi thì chưa chắc.",
            "Cơ thể có thể đang biết câu trả lời trước lịch làm việc.",
        ),
    ),
    "gemini": SignMeaning(
        "tò mò, linh hoạt và cần trao đổi để hiểu",
        "gom thêm thông tin để né một câu trả lời đơn giản",
        "khi bạn soạn đi sửa lại một tin nhắn hoặc mở thêm tài liệu dù câu chính đã khá rõ",
        (
            "chốt ý chính trong một câu",
            "hỏi một câu thật thay vì ba câu vòng",
            "tắt bớt một luồng thông tin",
        ),
        (
            "Đầu óc đang mở quá nhiều tab cho một chuyện.",
            "Bạn có đủ dữ kiện; thứ thiếu có thể là một câu chốt.",
            "Một cuộc trò chuyện ngắn có thể gỡ nút nhanh hơn tự đoán.",
        ),
    ),
    "cancer": SignMeaning(
        "nhạy với bầu không khí và cần nơi đủ an toàn",
        "ôm luôn phần cảm xúc của người khác",
        "khi ai đó xuống mood và bạn lập tức đổi lịch, đổi giọng hoặc nhận luôn phần chăm sóc",
        (
            "hỏi phần nào thật sự là của mình",
            "nói nhu cầu trước khi chăm người khác",
            "rời khỏi không khí căng vài phút",
        ),
        (
            "Bạn có thể đang giữ hộ một cảm xúc không hẳn là của mình.",
            "Không khí xung quanh hơi ồn; nhu cầu của bạn thì nói nhỏ.",
            "Chăm người khác rất tự nhiên, nhưng hôm nay đừng bỏ sót mình.",
        ),
    ),
    "leo": SignMeaning(
        "ấm, biểu đạt rõ và cần được nhìn thấy đúng chỗ",
        "đọc sự im lặng thành việc mình không đủ quan trọng",
        "khi một điều bạn làm rất có tâm chỉ nhận lại phản hồi ngắn hoặc không đúng lúc",
        ("làm vì mình thấy đáng", "xin phản hồi cụ thể", "đặt niềm vui trở lại lịch hôm nay"),
        (
            "Có điều bạn muốn được công nhận nhưng chưa muốn nói thẳng.",
            "Đừng để một phản hồi nhạt làm nhỏ đi thứ bạn đang thích.",
            "Hôm nay hợp để cho một điều mình tự hào được lên tiếng.",
        ),
    ),
    "virgo": SignMeaning(
        "cụ thể, quan sát kỹ và thích biến rối thành việc làm được",
        "sửa chi tiết trong khi cơ thể đã hết pin",
        "khi việc đã đủ gửi nhưng bạn vẫn căn lại chữ, format hoặc checklist thêm một vòng",
        ("chọn chuẩn đủ dùng", "xử lý một điểm gây kẹt nhất", "dành mười lăm phút không tối ưu gì"),
        (
            "Bạn đang sửa thêm một chi tiết mà chưa chắc ai cần.",
            "Việc này có thể cần một tiêu chuẩn đủ tốt, không cần hoàn hảo.",
            "Danh sách dài không đồng nghĩa với ngày hôm nay phải dài theo.",
        ),
    ),
    "libra": SignMeaning(
        "đối thoại, cân nhắc và cần sự có qua có lại",
        "giữ hòa khí bằng cách làm mờ câu trả lời của mình",
        "khi hai người muốn khác nhau và bạn tự động chọn câu dễ nghe hơn câu mình thật sự muốn",
        (
            "nói lựa chọn riêng trước",
            "đề nghị một trao đổi công bằng",
            "đừng nhận vai hòa giải tự động",
        ),
        (
            "Bạn đang cân cả phòng nhưng quên cân phần của mình.",
            "Một câu trả lời lịch sự vẫn có thể rất rõ.",
            "Sự dễ chịu chung không nên được mua bằng im lặng riêng.",
        ),
    ),
    "scorpio": SignMeaning(
        "sâu, kín và cần niềm tin đã được kiểm chứng",
        "giữ kín đến lúc áp lực nói thay mình",
        "khi bạn đã nhận ra điều không ổn nhưng vẫn im để xem người kia có tự hiểu hay không",
        (
            "chia sẻ mười phần trăm sự thật trước",
            "hỏi thay vì thử lòng",
            "tách riêng tư khỏi im lặng trừng phạt",
        ),
        (
            "Có chuyện bạn nhìn ra khá rõ nhưng vẫn chưa muốn nói.",
            "Bạn không cần kể hết; nhưng giấu hết cũng đang tốn sức.",
            "Một câu hỏi thẳng có thể đỡ mệt hơn một bài test ngầm.",
        ),
    ),
    "sagittarius": SignMeaning(
        "rộng, ham thử và cần thấy ý nghĩa phía trước",
        "đổi hướng trước khi chuyện cũ kịp được xử lý",
        "khi một kế hoạch mới xuất hiện đúng lúc cuộc trò chuyện cũ vẫn còn dang dở",
        (
            "chọn một thử nghiệm có mốc kiểm tra",
            "đi xa vừa đủ để có góc nhìn mới",
            "quay lại hoàn tất một cuộc nói chuyện",
        ),
        (
            "Một hướng mới rất hấp dẫn, nhưng chuyện cũ vẫn còn một dấu phẩy.",
            "Bạn cần khoảng rộng; chưa chắc cần biến mất.",
            "Ý tưởng lớn sẽ đáng tin hơn sau một bước kiểm tra nhỏ.",
        ),
    ),
    "capricorn": SignMeaning(
        "có cấu trúc, thực tế và cần thấy tiến bộ",
        "xử lý cảm xúc như một việc có thể hoãn vô hạn",
        (
            "khi lịch vẫn chạy rất gọn nhưng bạn bắt đầu cáu với những việc bình thường "
            "vốn không đáng kể"
        ),
        (
            "đặt giờ dừng",
            "chia tiến bộ thành bước nhìn thấy được",
            "đưa một nhu cầu mềm vào kế hoạch cứng",
        ),
        (
            "Bạn đang gánh khá gọn, đến mức người khác tưởng là không nặng.",
            "Có việc cần kỷ luật; cũng có việc cần được bớt đi.",
            "Tiến bộ hôm nay có thể là dừng đúng giờ.",
        ),
    ),
    "aquarius": SignMeaning(
        "độc lập, quan sát tốt và cần khoảng thở để nghĩ khác",
        "đứng ngoài cảm xúc lâu đến mức bị hiểu là không cần ai",
        (
            "khi bạn giải thích chuyện rất logic nhưng người đối diện vẫn chưa biết "
            "bạn đang buồn hay cần gì"
        ),
        (
            "nói phần cảm xúc trước phần phân tích",
            "tìm một người hiểu ngữ cảnh",
            "đổi cách làm nhưng giữ mục tiêu",
        ),
        (
            "Bạn hiểu chuyện này bằng đầu rồi; tim có thể chưa theo kịp.",
            "Khoảng cách giúp bạn nhìn rõ, nhưng đừng để nó thành mất kết nối.",
            "Một ý tưởng khác thường đang cần một người để thử cùng.",
        ),
    ),
    "pisces": SignMeaning(
        "mềm, giàu tưởng tượng và bắt bầu không khí rất nhanh",
        "hòa vào cảm giác chung rồi khó tìm lại phần của mình",
        (
            "khi một tin nhắn đổi giọng hoặc căn phòng bỗng im, rồi bạn tự nối thêm "
            "ý nghĩa trước khi biết chuyện gì thật sự xảy ra"
        ),
        (
            "tách điều đã xảy ra khỏi phần bạn đang tự nối thêm",
            "viết tên cảm xúc trước khi đoán nguyên nhân",
            "hỏi một câu rõ thay vì tự hoàn thành phần còn thiếu",
        ),
        (
            "Một tin nhắn ngắn có thể kéo theo cả phần bạn tự nối thêm.",
            "Bạn bắt mood rất nhanh; phần khó là biết cảm giác nào thực sự thuộc về mình.",
            "Cảm giác đầu tiên đáng nghe, nhưng chưa cần biến thành kết luận.",
        ),
    ),
}


HOUSES: dict[int, HouseMeaning] = {
    1: HouseMeaning(
        "cách bạn bước vào tình huống",
        "khi vừa xuất hiện ở một nhóm mới hoặc phải tự giới thiệu mình",
    ),
    2: HouseMeaning(
        "tiền bạc, nguồn lực và cảm giác đủ",
        "khi định giá công sức, mua sắm hoặc quyết định giữ lại điều gì",
    ),
    3: HouseMeaning(
        "giao tiếp và nhịp học hằng ngày",
        "khi nhắn một câu quan trọng, học điều mới hoặc xử lý quá nhiều thông tin",
    ),
    4: HouseMeaning(
        "đời sống riêng và nơi bạn hạ cảnh giác",
        "khi về nhà, ở cạnh người thân hoặc cần một chỗ thật sự được thả lỏng",
    ),
    5: HouseMeaning(
        "niềm vui, sáng tạo và hẹn hò", "khi muốn làm điều vui chỉ vì nó vui, không vì thành tích"
    ),
    6: HouseMeaning(
        "công việc thường ngày và cách chăm cơ thể",
        "khi lịch kín, việc vụn tăng hoặc cơ thể bắt đầu báo hết sức chứa",
    ),
    7: HouseMeaning(
        "quan hệ một-một và cách thương lượng",
        "khi hai người cần nói rõ kỳ vọng thay vì chờ nhau tự hiểu",
    ),
    8: HouseMeaning(
        "tin cậy, thân mật và nguồn lực chung",
        "khi phải chia sẻ điều riêng, vay-mượn hoặc bàn về ranh giới sâu hơn",
    ),
    9: HouseMeaning(
        "niềm tin, học xa và góc nhìn lớn",
        "khi một trải nghiệm mới làm bạn xem lại điều mình từng tin chắc",
    ),
    10: HouseMeaning(
        "hướng nghề nghiệp và vai trò công khai",
        "khi nhận trách nhiệm, trình bày năng lực hoặc chọn thứ muốn xây lâu dài",
    ),
    11: HouseMeaning(
        "quan hệ bạn bè, cộng đồng và kế hoạch tương lai",
        "trong quan hệ với một nhóm, khi muốn thuộc về mà vẫn giữ tiếng nói riêng",
    ),
    12: HouseMeaning(
        "đời sống bên trong và khoảng nghỉ",
        "khi cần rút bớt kích thích để nghe xem mình đang mệt, buồn hay chỉ quá tải",
    ),
}


ASPECTS: dict[str, AspectMeaning] = {
    "conjunction": AspectMeaning(
        "thường được kích hoạt cùng lúc",
        "phản ứng theo cảm giác đầu tiên trước khi gọi tên mình đang cần gì",
    ),
    "opposition": AspectMeaning(
        "kéo sự chú ý về hai phía khác nhau",
        "đẩy một phía sang người khác rồi chỉ giữ phía còn lại",
    ),
    "square": AspectMeaning(
        "tạo ma sát khiến cả hai khó bị bỏ qua",
        "giải quyết một nhu cầu bằng cách nén nhu cầu còn lại",
    ),
    "trine": AspectMeaning(
        "hỗ trợ nhau khá tự nhiên", "dùng điều vốn thuận tay mà quên kiểm tra thực tế"
    ),
    "sextile": AspectMeaning(
        "có thể phối hợp khi bạn chủ động", "đợi hoàn cảnh tự làm phần còn lại"
    ),
    "quincunx": AspectMeaning(
        "cần được điều chỉnh liên tục để cùng tồn tại",
        "cố tìm một cách xử lý dùng được cho mọi tình huống",
    ),
}

ELEMENT_PROCESS_COPY = {
    "fire": "muốn bắt đầu hoặc hành động để biết điều gì thật sự có năng lượng",
    "earth": "cần một dữ kiện hoặc bước cụ thể rồi mới yên tâm",
    "air": "cần nói hoặc nghĩ thành lời để hiểu chuyện gì đang xảy ra",
    "water": "cần đủ an toàn rồi mới nói rõ điều mình cảm",
}


LENS_MANIFESTATIONS: dict[BackgroundLens, str] = {
    BackgroundLens.RELATIONSHIPS: (
        "trong một cuộc trò chuyện thân thiết, khi kỳ vọng chưa được nói rõ"
    ),
    BackgroundLens.COMMUNICATION: (
        "khi câu cần nói rất ngắn nhưng phần giải thích trong đầu lại quá dài"
    ),
    BackgroundLens.WORK: ("trong công việc, khi nhận thêm việc hoặc phải chốt ưu tiên"),
    BackgroundLens.ENERGY: "khi đầu óc còn muốn chạy nhưng cơ thể đã giảm tốc",
    BackgroundLens.SELF_CARE: "khi cả nghỉ ngơi cũng bắt đầu giống một mục tiêu phải hoàn thành",
}

LENS_HOOKS: dict[BackgroundLens, str] = {
    BackgroundLens.RELATIONSHIPS: "Trong một mối quan hệ đang khiến bạn để tâm",
    BackgroundLens.COMMUNICATION: "Trong cuộc nói chuyện bạn đang nghĩ tới",
    BackgroundLens.WORK: "Ở công việc hôm nay",
    BackgroundLens.ENERGY: "Khi sức chứa đang xuống",
    BackgroundLens.SELF_CARE: "Trong cách bạn chăm mình hôm nay",
}

LENS_ACTIONS: dict[BackgroundLens, str] = {
    BackgroundLens.RELATIONSHIPS: (
        "chọn một điều bạn đang đoán về người kia, rồi đổi nó thành một câu hỏi "
        "có thể trả lời thẳng"
    ),
    BackgroundLens.COMMUNICATION: (
        "viết ba dòng: điều đã xảy ra, điều bạn đang cảm và điều bạn muốn hỏi"
    ),
    BackgroundLens.WORK: (
        "chọn một đầu việc, viết tiêu chuẩn hoàn thành của nó và để phần còn lại chờ"
    ),
    BackgroundLens.ENERGY: (
        "giảm một kích thích trong mười phút rồi kiểm tra xem sức chứa có đổi không"
    ),
    BackgroundLens.SELF_CARE: (
        "chọn một việc chăm mình đủ nhỏ để làm mà không cần biến nó thành thành tích"
    ),
}


def semantic_arena(background_lens: BackgroundLens | None) -> SemanticArena:
    if background_lens is None or background_lens is BackgroundLens.AUTO:
        return SemanticArena.GENERAL
    return SemanticArena(background_lens.value)


def _apply_background_lens(
    plan: ReadingPlan,
    *,
    hook: str,
    manifestation: str,
    micro_action: str,
) -> tuple[str, str, str]:
    lens = plan.background_lens
    if lens is None or lens is BackgroundLens.AUTO:
        return hook, manifestation, micro_action
    contextual_hook = f"{LENS_HOOKS[lens]}, {hook[0].lower()}{hook[1:]}"
    contextual_manifestation = (
        f"Cụ thể, pattern này dễ lộ ra {LENS_MANIFESTATIONS[lens]}. {manifestation}"
    )
    contextual_action = (
        f"Thử {LENS_ACTIONS[lens]}. Sau đó ghi lại điều gì thực sự xảy ra; "
        "đừng dùng cảm giác ban đầu để chốt hộ kết quả."
    )
    return contextual_hook, contextual_manifestation, contextual_action


def _parts(factor: DerivedFactor) -> list[str]:
    return factor.id.split(":")


def _placement_sign(factor: DerivedFactor) -> str | None:
    parts = _parts(factor)
    return parts[3] if factor.kind is FactorKind.PLANET_PLACEMENT and len(parts) > 3 else None


def _aspect_phase(factor: DerivedFactor) -> str | None:
    ref = next((item for item in factor.evidence_refs if ":phase:" in item), None)
    return ref.rsplit(":", 1)[1] if ref is not None else None


def _natal_phase_copy(phase: str | None) -> str:
    if phase == "applying":
        return "Hai phần này thường gọi nhau khá nhanh."
    if phase == "separating":
        return "Bạn thường nhận ra cơ chế này rõ hơn sau khi nó đã xảy ra."
    return ""


def _orb_weight(orb: float) -> str:
    if orb <= 1:
        return "Góc khá sát nên chủ đề này thường dễ lộ rõ."
    if orb <= 3:
        return "Góc khá gần, đáng chú ý."
    return "Góc rộng: chỉ xem là nét phụ; đối chiếu với trải nghiệm thật."


def _contrast_copy(
    *,
    lens: InterpretiveLens,
    body_a: str,
    body_b: str,
    planet_a: PlanetMeaning,
    planet_b: PlanetMeaning,
    element_a_key: str,
    element_b_key: str,
) -> str:
    label_a = body_label(body_a)
    label_b = body_label(body_b)
    if planet_a.drive == planet_b.drive:
        needs = f"Cả {label_a} và {label_b} cùng nhấn mạnh nhu cầu {planet_a.drive}."
    else:
        needs = f"{label_a} cần {planet_a.drive}; {label_b} cần {planet_b.drive}."

    if lens not in {InterpretiveLens.RELATIONSHIPS, InterpretiveLens.REGULATION}:
        return needs
    if element_a_key != element_b_key:
        return needs
    process = f"Cả hai đều {ELEMENT_PROCESS_COPY[element_a_key]}."
    return f"{needs} {process}"


def _context_house(
    plan: ReadingPlan, body_refs: tuple[str, ...]
) -> tuple[DerivedFactor, HouseMeaning] | None:
    for factor in plan.factors:
        if factor.kind is not FactorKind.HOUSE_PLACEMENT:
            continue
        if not set(factor.child_refs).intersection(body_refs):
            continue
        house = int(_parts(factor)[3])
        return factor, HOUSES[house]
    return None


def _fallback_context(plan: ReadingPlan) -> str:
    if plan.background_lens is not None:
        return LENS_MANIFESTATIONS[plan.background_lens]
    return "khi bạn phải phản hồi một việc quan trọng trong lúc sức chứa không còn nhiều"


def vibe_frame(plan: ReadingPlan) -> InterpretationFrame:
    factor = plan.factors[0]
    raw_signs = _parts(factor)[4].split(",")
    if len(raw_signs) != 1 or _parts(factor)[3] != "certain":
        hooks = (
            "Ngày sinh của bạn đang đứng đúng một vùng chuyển tiếp.",
            "Hôm nay Lá giữ lại một dấu hỏi thay vì chọn bừa một cung.",
            "Có một chi tiết trong ngày sinh chưa đủ chắc để gọi tên.",
            "Bản đọc này bắt đầu bằng điều thật nhất: dữ kiện còn mở.",
            "Chưa chốt cung cũng là một kết quả có ích.",
        )
        manifestations = (
            "Vì thế những mô tả tổng quan trước đây có thể lúc đúng lúc trượt.",
            (
                "Điều này giải thích vì sao một nhãn cung đơn lẻ có thể chưa giống "
                "trải nghiệm của bạn."
            ),
            "Khoảng chưa xác định này đáng được giữ nguyên hơn là lấp bằng một lời đoán đẹp tai.",
        )
        actions = (
            "Nếu nhớ được khoảng giờ sinh, hãy bổ sung để thu hẹp kết quả.",
            "Thử hỏi lại người thân hoặc xem giấy tờ cũ; không tìm được cũng không sao.",
            "Tạm dùng note như một câu hỏi quan sát, chưa dùng nó để kết luận về mình.",
        )
        closings = (
            "Lá sẽ chỉ mở thêm khi có dữ kiện đáng tin hơn.",
            "Bạn không cần ép mình nhớ ngay để tiếp tục dùng app.",
        )
        reflections = (
            "Để ý điều gì khiến bạn muốn chốt vội.",
            "Để ý phản xạ đầu tiên, chưa cần tin nó ngay.",
            "Để ý lúc cơ thể biết trước phần lý trí.",
            "Để ý điều bạn đang né gọi tên.",
            "Để ý chuyện gì đổi khi chậm một nhịp.",
        )
        (
            hook_slot,
            manifestation_slot,
            action_slot,
            closing_slot,
            reflection_slot,
        ) = daily_mixed_radix_slots(
            plan.editorial_seed,
            (
                len(hooks),
                len(manifestations),
                len(actions),
                len(closings),
                len(reflections),
            ),
        )
        hook = hooks[hook_slot]
        manifestation = (
            f"{manifestations[manifestation_slot]} "
            "Dữ kiện đầu vào vẫn còn một khoảng chưa xác định."
        )
        micro_action = (
            f"{actions[action_slot]} {closings[closing_slot]} {reflections[reflection_slot]}"
        )
        hook, manifestation, micro_action = _apply_background_lens(
            plan,
            hook=hook,
            manifestation=manifestation,
            micro_action=micro_action,
        )
        return InterpretationFrame(
            hook=hook,
            thesis=(
                "Khi chưa có giờ sinh, Lá chưa thể biết chắc Mặt Trời thuộc phía nào. "
                "Vì vậy bản này không mượn đặc điểm của một cung để đoán bạn."
            ),
            manifestation=manifestation,
            micro_action=micro_action,
            evidence_factor_refs=(factor.id,),
            knowledge_refs=(
                "mode:date-only-ambiguous",
                (
                    "daily-variant:"
                    f"{hook_slot}-{manifestation_slot}-{action_slot}-{closing_slot}-"
                    f"{reflection_slot}"
                ),
            ),
            arena=semantic_arena(plan.background_lens),
            mechanism_key="date-only-ambiguous",
            scene_key=f"{semantic_arena(plan.background_lens).value}:uncertain-sign",
            action_key=f"clarify-data:{action_slot}",
        )
    sign = raw_signs[0] if raw_signs and raw_signs[0] in SIGNS else "pisces"
    meaning = SIGNS[sign]
    modes = tuple(EditorialMode)
    reflections = (
        "Để ý phản xạ đầu tiên.",
        "Để ý chuyện gì xảy ra ngay sau đó.",
        "Để ý lúc cơ thể lên tiếng trước.",
        "Để ý điều bạn đang né gọi tên.",
        "Để ý điều đổi khi chậm một nhịp.",
    )
    hook_slot, practice_slot, mode_slot, close_slot, reflection_slot = daily_mixed_radix_slots(
        plan.editorial_seed,
        (len(meaning.hooks), len(meaning.practices), len(modes), 2, len(reflections)),
    )
    hook = meaning.hooks[hook_slot]
    practice = meaning.practices[practice_slot]
    mode = modes[mode_slot]
    mode_copy = {
        EditorialMode.MECHANISM: f"Khi có áp lực, {meaning.stress} có thể là cách giữ nhịp quen.",
        EditorialMode.FRICTION: f"Điểm dễ trượt hôm nay: {meaning.stress}.",
        EditorialMode.RESOURCE: f"Phần dùng được hôm nay là khả năng {meaning.style}.",
        EditorialMode.CONTRAST: (
            f"Đừng gom hai thứ làm một: {meaning.style} là nguồn lực; "
            f"{meaning.stress} là chỗ cần canh."
        ),
        EditorialMode.EXPERIMENT: (
            "Đây là một giả thuyết để soi vào tình huống thật, không phải nhãn tính cách."
        ),
    }[mode]
    close = (
        "Ghi lại điều gì thật sự đổi sau đó."
        if close_slot == 0
        else "Nếu không thấy khác, bỏ thử nghiệm này và giữ lại dữ kiện thật."
    )
    manifestation = (
        f"Trong đời thường, pattern này có thể lộ ra {meaning.manifestation}. {mode_copy} "
        "Không khớp việc thật thì bỏ qua."
    )
    micro_action = (
        f"Thử {practice}. {reflections[reflection_slot]} {close} "
        "Có giờ sinh chính xác và nơi sinh, Lá mới đọc thêm cảm xúc và bối cảnh."
    )
    hook, manifestation, micro_action = _apply_background_lens(
        plan,
        hook=hook,
        manifestation=manifestation,
        micro_action=micro_action,
    )
    return InterpretationFrame(
        hook=hook,
        thesis=(
            f"Đây là góc đọc từ một yếu tố trong ngày sinh: bạn thường vào nhịp theo kiểu "
            f"{meaning.style}. Điểm dễ vấp là {meaning.stress}; chưa đủ để kết luận về toàn bộ bạn."
        ),
        manifestation=manifestation,
        micro_action=micro_action,
        evidence_factor_refs=(factor.id,),
        knowledge_refs=(
            f"sign:{sign}",
            "mode:date-only",
            f"editorial-mode:{mode.value}",
            (
                "daily-variant:"
                f"{hook_slot}-{practice_slot}-{mode_slot}-{close_slot}-{reflection_slot}"
            ),
        ),
        arena=semantic_arena(plan.background_lens),
        mechanism_key=f"sun-sign:{sign}:{mode.value}",
        scene_key=f"{semantic_arena(plan.background_lens).value}:{sign}",
        action_key=f"{sign}:{practice_slot}",
    )


def full_frame(plan: ReadingPlan) -> InterpretationFrame:
    if plan.tradition is Tradition.JYOTISH:
        return _jyotish_structural_frame(plan)

    by_id = {factor.id: factor for factor in plan.factors}
    hero = next((by_id[ref] for ref in plan.hero_factor_refs if ref in by_id), plan.factors[0])
    body_refs = hero.child_refs or tuple(
        factor.id
        for factor in plan.factors
        if factor.kind is FactorKind.PLANET_PLACEMENT
        and set(factor.subjects).intersection(hero.subjects)
    )
    placements = [
        by_id[ref]
        for ref in body_refs
        if ref in by_id and by_id[ref].kind is FactorKind.PLANET_PLACEMENT
    ]
    if not placements:
        placements = [
            factor for factor in plan.factors if factor.kind is FactorKind.PLANET_PLACEMENT
        ][:2]
    primary = placements[0] if placements else hero
    secondary = placements[1] if len(placements) > 1 else primary
    body_a = primary.subjects[0]
    body_b = secondary.subjects[0]
    planet_a = PLANETS.get(body_a, PLANETS["sun"])
    planet_b = PLANETS.get(body_b, PLANETS["moon"])
    perspective_a = PLANET_PERSPECTIVES.get(body_a, PLANET_PERSPECTIVES["sun"])
    perspective_b = PLANET_PERSPECTIVES.get(body_b, PLANET_PERSPECTIVES["moon"])
    sign_a_key = _placement_sign(primary) or "pisces"
    sign_b_key = _placement_sign(secondary) or "pisces"
    sign_a = SIGNS.get(sign_a_key, SIGNS["pisces"])
    sign_b = SIGNS.get(sign_b_key, SIGNS["pisces"])
    element_a, modality_a, element_a_key, modality_a_key = sign_structure(sign_a_key)
    _element_b, _modality_b, element_b_key, modality_b_key = sign_structure(sign_b_key)
    editorial_variant = resolve_daily_editorial_variant(
        plan.editorial_seed,
        plan.background_lens,
    )
    lens = editorial_variant.lens
    context = _context_house(plan, tuple(item.id for item in placements))
    context_phrase = _context_phrase(plan, context)
    evidence_refs = [hero.id, *(item.id for item in placements)]
    knowledge_refs = [
        f"methodology:{METHODOLOGY_VERSION}",
        f"planet:{body_a}",
        f"planet:{body_b}",
        f"lens:{lens.value}",
        f"editorial-mode:{editorial_variant.mode.value}",
        editorial_variant.signature,
    ]

    contrast = _contrast_copy(
        lens=lens,
        body_a=body_a,
        body_b=body_b,
        planet_a=planet_a,
        planet_b=planet_b,
        element_a_key=element_a_key,
        element_b_key=element_b_key,
    )
    if lens in {InterpretiveLens.RELATIONSHIPS, InterpretiveLens.REGULATION}:
        knowledge_refs.extend((f"element:{element_a_key}", f"element:{element_b_key}"))
    elif lens in {InterpretiveLens.WORK, InterpretiveLens.GROWTH}:
        knowledge_refs.extend((f"modality:{modality_a_key}", f"modality:{modality_b_key}"))

    if hero.kind is FactorKind.NATAL_ASPECT:
        parts = _parts(hero)
        aspect_name = parts[3]
        orb = float(parts[6])
        aspect = ASPECTS.get(aspect_name, ASPECTS["conjunction"])
        aspect_core = (
            f"{body_label(body_a)} và {body_label(body_b)} {aspect.bridge}. {contrast} "
            f"Điểm dễ kẹt: {aspect.watch}. {_orb_weight(orb)}"
        )
        phase = _aspect_phase(hero)
        phase_copy = (
            _natal_phase_copy(phase)
            if lens in {InterpretiveLens.RELATIONSHIPS, InterpretiveLens.COMMUNICATION}
            else ""
        )
        knowledge_refs.extend((f"aspect:{aspect_name}", f"aspect-phase:{phase or 'unknown'}"))
    else:
        phase_copy = ""
        aspect_core = (
            f"Một phần vận hành {sign_a.style}; phần còn lại {sign_b.style}. "
            f"Điểm cần canh là {planet_a.stress}, nhất là khi {planet_b.stress}."
        )

    thesis = aspect_core
    if context is not None:
        evidence_refs.append(context[0].id)
        house_number = int(_parts(context[0])[3])
        _, mode_key = house_mode(house_number)
        knowledge_refs.extend((f"house:{house_number}", f"house-mode:{mode_key}"))
    if phase_copy:
        thesis = f"{thesis} {phase_copy}"

    pattern_sign = (
        "cố giải quyết thật nhanh để khỏi phải giữ hai nhu cầu cùng lúc"
        if hero.role.value == "tension"
        else "làm theo điều vốn thuận tay mà quên kiểm tra nhu cầu còn lại"
    )
    hook, manifestation, action = _lens_copy(
        lens=lens,
        planet_a=planet_a,
        planet_b=planet_b,
        perspective_a=perspective_a,
        perspective_b=perspective_b,
        element_a=element_a,
        modality_a=modality_a,
        context_phrase=context_phrase,
        context=context,
        background_lens=plan.background_lens,
        pattern_sign=pattern_sign,
        editorial_mode=editorial_variant.mode,
        action_slot=editorial_variant.action_slot,
        reflection_slot=editorial_variant.reflection_slot,
        dynamic=plan.purpose is ReadingPurpose.DAILY_NOTE,
    )
    return InterpretationFrame(
        hook=hook,
        thesis=thesis,
        manifestation=manifestation,
        micro_action=action,
        evidence_factor_refs=tuple(dict.fromkeys(evidence_refs)),
        knowledge_refs=tuple(dict.fromkeys(knowledge_refs)),
        arena=semantic_arena(plan.background_lens),
        mechanism_key=f"{hero.kind.value}:{hero.role.value}:{lens.value}",
        scene_key=f"{semantic_arena(plan.background_lens).value}:{context_phrase}",
        action_key=f"{lens.value}:{editorial_variant.action_slot}",
    )


def _lens_copy(
    *,
    lens: InterpretiveLens,
    planet_a: PlanetMeaning,
    planet_b: PlanetMeaning,
    perspective_a: PlanetPerspective,
    perspective_b: PlanetPerspective,
    element_a: ElementMeaning,
    modality_a: ModalityMeaning,
    context_phrase: str,
    context: tuple[DerivedFactor, HouseMeaning] | None,
    background_lens: BackgroundLens | None,
    pattern_sign: str,
    editorial_mode: EditorialMode,
    action_slot: int,
    reflection_slot: int,
    dynamic: bool,
) -> tuple[str, str, str]:
    # These objects come from the immutable interpretation catalog. Keeping this
    # assembly here makes the semantic frame auditable before any prose renderer.
    arena = context[1].arena if context else "tình huống này"
    if lens is InterpretiveLens.RELATIONSHIPS:
        hook = f"Trong quan hệ, một phần muốn {planet_a.drive}; phần kia muốn {planet_b.drive}."
        manifestation = (
            f"Bạn có thể {perspective_a.relationships}, trong khi phần kia "
            f"{perspective_b.relationships}. Dễ bắt gặp {context_phrase}, rồi {pattern_sign}."
        )
        action = (
            "Thử nói một nhu cầu của bạn dưới dạng đề nghị, rồi hỏi phần còn lại của người kia. "
            "Đừng dùng chart để đoán hộ câu trả lời của họ."
        )
    elif lens is InterpretiveLens.WORK:
        hook = f"Ở công việc, bạn có thể vừa muốn {planet_a.drive}, vừa muốn {planet_b.drive}."
        manifestation = (
            f"Một bên {perspective_a.work}; bên kia {perspective_b.work}. "
            f"Cơ chế này dễ hiện ra {context_phrase}, nhất là khi bạn {pattern_sign}."
        )
        action = (
            f"Chọn một ưu tiên có tiêu chuẩn hoàn thành rõ, rồi {planet_a.action}. "
            "Xem đây là thử nghiệm cho hôm nay, không phải công thức nghề nghiệp."
        )
    elif lens is InterpretiveLens.REGULATION:
        hook = f"Lúc quá tải, nhu cầu {planet_a.drive} có thể va vào nhu cầu {planet_b.drive}."
        manifestation = (
            f"Dễ thấy {context_phrase}. Phản xạ bảo vệ có thể là "
            f"{perspective_a.protection}; đồng thời phần kia "
            f"{perspective_b.protection}. Với nhịp {element_a.rhythm}, bạn dễ {element_a.overload}."
        )
        action = (
            f"Trước khi xử lý chuyện ở {context[1].arena if context else 'tình huống này'}, "
            f"thử {perspective_a.regulation}. Chỉ cần xem sức chứa có đổi không."
        )
    elif lens is InterpretiveLens.COMMUNICATION:
        hook = f"Có lúc câu nói ra muốn {planet_a.drive}; điều chưa nói lại muốn {planet_b.drive}."
        manifestation = (
            f"Nó dễ lộ ra {context_phrase}. Bạn có thể {perspective_a.protection}, "
            f"rồi {pattern_sign}; thế mạnh thật sự là {modality_a.strength}."
        )
        action = (
            f"Viết ba dòng: điều đã biết, điều đang cảm và điều muốn đề nghị; sau đó "
            f"{element_a.missing_move}."
        )
    elif lens is InterpretiveLens.GROWTH:
        hook = (
            f"Bài tập không phải chọn giữa {planet_a.drive} và {planet_b.drive}; "
            "là để hai phần cùng có tiếng."
        )
        manifestation = (
            f"Trong vùng {arena}, bạn có thể {pattern_sign}. Điểm mắc: {modality_a.stuck_pattern}."
        )
        action = (
            f"Mang theo câu hỏi này hôm nay: “{perspective_a.growth_question}” "
            "Không cần trả lời ngay; tìm một tình huống thật để kiểm tra."
        )
    else:
        hook = f"Một phần muốn {planet_a.drive}; phần kia muốn {planet_b.drive}."
        manifestation = (
            f"Nó thường lộ ra {context_phrase}. Bạn có thể {pattern_sign}; "
            f"bên dưới thường là phản xạ {perspective_a.protection}."
        )
        action = f"Thử thế này: {planet_a.action}. Chỉ quan sát phản ứng, không chấm điểm mình."
    if not dynamic:
        return hook, manifestation, action

    mode_hook = {
        EditorialMode.MECHANISM: "Điều đang chạy bên dưới:",
        EditorialMode.FRICTION: "Điểm dễ kẹt hôm nay:",
        EditorialMode.RESOURCE: "Phần bạn có thể dùng:",
        EditorialMode.CONTRAST: "Hai nhu cầu đang cùng lên tiếng:",
        EditorialMode.EXPERIMENT: "Một cách khác để thử:",
    }[editorial_mode]
    if background_lens is not None and background_lens is not BackgroundLens.AUTO:
        contextual_action = LENS_ACTIONS[background_lens]
        action_variants = (
            f"Thử {contextual_action}. Ghi lại phản hồi thật thay vì đoán kết quả.",
            f"Một thử nghiệm nhỏ: {contextual_action}. Chỉ quan sát điều gì đổi.",
            f"Thử {contextual_action}. Sau đó trả lời: “{perspective_a.growth_question}”",
        )
    else:
        action_variants = (
            action,
            (
                f"Một thử nghiệm nhỏ: {perspective_a.regulation}. "
                "Quan sát điều gì đổi, không ép kết quả."
            ),
            (f"“{perspective_a.growth_question}” Tìm một tình huống thật để trả lời."),
        )
    reflection = (
        "Để ý phản xạ đầu tiên.",
        "Để ý chuyện gì xảy ra ngay sau đó.",
        "Để ý lúc cơ thể lên tiếng trước lời nói.",
        "Để ý lúc bạn muốn sửa mình cho vừa tình huống.",
        "Để ý điều đang bị né gọi tên.",
        "Để ý phần bạn đang gánh hộ.",
        "Để ý điều đổi khi chậm một nhịp.",
    )[reflection_slot]
    return (
        f"{mode_hook} {hook}",
        manifestation,
        f"{action_variants[action_slot]} {reflection}",
    )


def _short_arena(context: tuple[DerivedFactor, HouseMeaning] | None) -> str:
    if context is None:
        return "chuyện hôm nay"
    house = int(_parts(context[0])[3])
    return {
        1: "cách bạn xuất hiện",
        2: "nguồn lực",
        3: "giao tiếp",
        4: "đời sống riêng",
        5: "hẹn hò",
        6: "công việc",
        7: "quan hệ",
        8: "ranh giới",
        9: "niềm tin",
        10: "công việc",
        11: "quan hệ",
        12: "đời sống riêng",
    }[house]


def _context_phrase(
    plan: ReadingPlan,
    context: tuple[DerivedFactor, HouseMeaning] | None,
) -> str:
    if plan.background_lens is not None:
        return LENS_MANIFESTATIONS[plan.background_lens]
    if context is not None:
        return context[1].manifestation
    return _fallback_context(plan)


def _jyotish_structural_frame(plan: ReadingPlan) -> InterpretationFrame:
    by_id = {factor.id: factor for factor in plan.factors}
    hero = next((by_id[ref] for ref in plan.hero_factor_refs if ref in by_id), plan.factors[0])
    evidence_refs = [hero.id, *hero.child_refs]

    if hero.kind is FactorKind.GRAHA_DRISHTI:
        parts = _parts(hero)
        body_a, body_b, houses_apart, kind = parts[2], parts[3], parts[5], parts[6]
        hook = (
            "Hai điểm đang liên hệ trực tiếp trong bản đồ Jyotish: "
            f"{body_label(body_a)} và {body_label(body_b)}."
        )
        thesis = (
            f"Engine ghi nhận drishti loại {kind}, cách nhau {houses_apart} nhà. "
            "Bản này giữ ở mức mô tả cấu trúc thay vì gán một kết luận tính cách chưa được duyệt."
        )
    elif hero.kind is FactorKind.NAKSHATRA:
        name_ref = next(
            (ref for ref in hero.evidence_refs if ref.startswith("jyotish:nakshatra:name:")),
            "jyotish:nakshatra:name:chưa xác định",
        )
        nakshatra = name_ref.removeprefix("jyotish:nakshatra:name:")
        hook = f"Bản đồ Jyotish đang đặt trọng tâm vào Nakshatra {nakshatra}."
        thesis = (
            "Vị trí đã được tính theo cấu hình sidereal/ayanamsa bạn chọn. "
            "Lá chưa biến tên này thành một phán quyết khi corpus Jyotish riêng "
            "chưa qua chuyên gia."
        )
    else:
        hook = "Bản đồ Jyotish đã tính xong; phần diễn giải sâu đang được giữ thận trọng."
        thesis = (
            "Lá chỉ hiển thị dữ kiện đủ căn cứ trong lần đọc này, thay vì mượn copy Western "
            "để lấp chỗ trống."
        )

    return InterpretationFrame(
        hook=hook,
        thesis=thesis,
        manifestation=(
            "Bạn có thể mở phần căn cứ để xem đúng factor nào đang được dùng trong hệ Jyotish."
        ),
        micro_action=(
            "Tạm xem đây là bản đọc cấu trúc; đừng dùng nó để chốt một quyết định quan trọng."
        ),
        evidence_factor_refs=tuple(dict.fromkeys(evidence_refs)),
        knowledge_refs=("tradition:jyotish", "mode:structural"),
        arena=SemanticArena.STRUCTURAL,
        mechanism_key=f"jyotish:{hero.kind.value}",
        scene_key="jyotish:evidence-disclosure",
        action_key="jyotish:inspect-evidence",
    )


def transit_copy(factor: DerivedFactor) -> str:
    parts = _parts(factor)
    transit_body = parts[1]
    aspect_name = parts[2]
    natal_body = parts[4]
    phase = parts[8]
    aspect = ASPECTS.get(aspect_name, ASPECTS["conjunction"])
    phase_copy = {
        "approaching": "Mức độ đang tăng dần",
        "exact": "Mức độ đang rõ nhất ở hiện tại",
        "separating": "Mức độ đang hạ dần",
    }.get(phase, "Mức độ đang thay đổi")
    current_force = CURRENT_FORCES.get(transit_body, "một lực muốn mở rộng")
    natal_target = CURRENT_FORCES.get(natal_body, "một nhu cầu nền")
    return (
        f"Hiện tại, {current_force} chạm {natal_target}. {phase_copy}; hai phần "
        f"{aspect.bridge}. Đây là bối cảnh quan sát, không phải dự báo hay lý do quyết định."
    )
