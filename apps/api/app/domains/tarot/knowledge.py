from __future__ import annotations

from functools import lru_cache

from app.domains.tarot.minor_readings import MINOR_READINGS
from app.domains.tarot.models import TarotBookSource, TarotCard

KNOWLEDGE_VERSION = "tarot-knowledge-v4"
DECK_VERSION = "tarot-78-v1"

_CONCEPT_SOURCES: dict[str, tuple[str, ...]] = {
    "archetype-depth": ("pollack-78-degrees",),
    "symbolic-tension": ("pollack-78-degrees",),
    "self-reflection": ("greer-tarot-for-yourself",),
    "reader-agency": ("greer-tarot-for-yourself",),
    "position-discipline": ("burger-fiebig-spreads",),
    "spread-intent": ("burger-fiebig-spreads",),
    "card-interaction": ("lipp-interactions",),
    "contrast-and-progression": ("lipp-interactions",),
    "non-determinism": ("wen-holistic-tarot",),
    "ethical-reflection": ("wen-holistic-tarot",),
    "story-coherence": ("bunning-learning-tarot",),
    "everyday-meaning": ("bunning-learning-tarot",),
    "plain-spoken-reading": ("cynova-kitchen-table-tarot",),
    "contextual-practicality": ("cynova-kitchen-table-tarot",),
    "present-focus": ("tishman-mindful-tarot",),
    "reflective-distance": ("tishman-mindful-tarot",),
}

BOOK_SOURCES: tuple[TarotBookSource, ...] = (
    TarotBookSource(
        source_id="pollack-78-degrees",
        title="Seventy-Eight Degrees of Wisdom",
        authors=("Rachel Pollack",),
        official_url="https://redwheelweiser.com/book/seventy-eight-degrees-of-wisdom-9781578636655/",
        concept_ids=("archetype-depth", "symbolic-tension"),
        allowed_uses=("concept-level archetype lens", "symbolic depth as a design method"),
        prohibited_uses=("excerpt", "book-specific metaphor", "chapter structure", "illustration"),
    ),
    TarotBookSource(
        source_id="greer-tarot-for-yourself",
        title="Tarot for Your Self",
        authors=("Mary K. Greer",),
        official_url="https://www.simonandschuster.co.uk/books/Tarot-for-Your-Self/Mary-K-Greer/9781578636792",
        concept_ids=("self-reflection", "reader-agency"),
        allowed_uses=("self-reflection principle", "agency-preserving question design"),
        prohibited_uses=("excerpt", "exercise", "worksheet", "spread", "prompt wording"),
    ),
    TarotBookSource(
        source_id="burger-fiebig-spreads",
        title="The Complete Book of Tarot Spreads",
        authors=("Evelin Bürger", "Johannes Fiebig"),
        official_url="https://www.hachettebookgroup.com/titles/evelin-burger/complete-book-of-tarot-spreads/9781454910794/",
        concept_ids=("position-discipline", "spread-intent"),
        allowed_uses=("position discipline as a method", "spread intent as a method"),
        prohibited_uses=("excerpt", "named spread", "layout", "diagram", "example"),
    ),
    TarotBookSource(
        source_id="lipp-interactions",
        title="Tarot Interactions",
        authors=("Deborah Lipp",),
        official_url="https://www.llewellyn.com/product.php?ean=9780738745206",
        concept_ids=("card-interaction", "contrast-and-progression"),
        allowed_uses=("combination categories", "contrast and progression as methods"),
        prohibited_uses=("excerpt", "pair meaning", "worked example", "layout", "template"),
    ),
    TarotBookSource(
        source_id="wen-holistic-tarot",
        title="Holistic Tarot",
        authors=("Benebell Wen",),
        official_url="https://www.northatlanticbooks.com/shop/holistic-tarot/",
        concept_ids=("non-determinism", "ethical-reflection"),
        allowed_uses=("non-deterministic ethics principle", "personal-development framing"),
        prohibited_uses=("excerpt", "table", "card entry", "case study", "spread"),
    ),
    TarotBookSource(
        source_id="bunning-learning-tarot",
        title="Learning the Tarot",
        authors=("Joan Bunning",),
        official_url="https://redwheelweiser.com/book/learning-the-tarot-9781578630486/",
        concept_ids=("story-coherence", "everyday-meaning"),
        allowed_uses=("story coherence as a synthesis method", "everyday-language principle"),
        prohibited_uses=("excerpt", "lesson", "exercise", "card entry", "spread"),
    ),
    TarotBookSource(
        source_id="cynova-kitchen-table-tarot",
        title="Kitchen Table Tarot",
        authors=("Melissa Cynova",),
        official_url="https://www.llewellyn.com/product.php?ean=9780738750774",
        concept_ids=("plain-spoken-reading", "contextual-practicality"),
        allowed_uses=("plain-spoken tone principle", "practical context framing"),
        prohibited_uses=("excerpt", "anecdote", "exercise", "card entry", "spread"),
    ),
    TarotBookSource(
        source_id="tishman-mindful-tarot",
        title="Mindful Tarot",
        authors=("Lisa Freinkel Tishman",),
        official_url="https://www.llewellyn.com/product.php?ean=9780738758442",
        concept_ids=("present-focus", "reflective-distance"),
        allowed_uses=("present-focused reflection principle", "reflective-distance method"),
        prohibited_uses=("excerpt", "meditation", "exercise", "card entry", "spread"),
    ),
)


_MAJOR: tuple[tuple[str, str, str, str, str, str], ...] = (
    (
        "fool",
        "Kẻ Khờ",
        "The Fool",
        "cho phép mình bắt đầu khi chưa có đủ mọi câu trả lời",
        "lao đi chỉ để thoát cảm giác mắc kẹt",
        "thử một bước nhỏ còn đường quay lại",
    ),
    (
        "magician",
        "Pháp Sư",
        "The Magician",
        "dùng kỹ năng và những thứ bạn đã có để bắt đầu làm",
        "cố kiểm soát hình ảnh thay vì làm việc thật",
        "chọn một việc bạn đã biết cách làm và bắt đầu từ đó",
    ),
    (
        "high-priestess",
        "Nữ Tư Tế",
        "The High Priestess",
        "để ý cảm giác của mình nhưng vẫn cần kiểm tra thông tin",
        "coi linh cảm là bằng chứng đã đủ",
        "tách điều cảm thấy khỏi điều đã kiểm chứng",
    ),
    (
        "empress",
        "Hoàng Hậu",
        "The Empress",
        "dành thời gian chăm sóc một người, một việc hoặc chính mình",
        "cho quá nhiều rồi âm thầm mong được hiểu",
        "ghi thêm một việc bạn cần cho mình vào lịch hôm nay",
    ),
    (
        "emperor",
        "Hoàng Đế",
        "The Emperor",
        "cần có kế hoạch và giới hạn rõ trước khi làm tiếp",
        "siết mọi thứ vì sợ mất thế chủ động",
        "nói một giới hạn cụ thể và lý do thực tế",
    ),
    (
        "hierophant",
        "Người Giữ Nếp",
        "The Hierophant",
        "xem lại điều mình làm theo vì gia đình, trường học hoặc thói quen",
        "làm đúng khuôn dù khuôn không còn hợp",
        "hỏi vì sao cần làm theo một quy tắc bạn chưa hiểu",
    ),
    (
        "lovers",
        "Người Tình",
        "The Lovers",
        "cần chọn điều phù hợp với mình, kể cả khi rất thích một người",
        "nghĩ thích nhau là đủ mà chưa nói rõ hai người muốn gì",
        "nói rõ một điều quan trọng với bạn trong mối quan hệ này",
    ),
    (
        "chariot",
        "Cỗ Xe",
        "The Chariot",
        "cần quyết định mình muốn đi tới đâu trước khi cố làm nhanh hơn",
        "tăng tốc để khỏi phải xử lý mâu thuẫn bên trong",
        "viết mục tiêu của việc đang làm trong một câu",
    ),
    (
        "strength",
        "Sức Mạnh",
        "Strength",
        "giữ bình tĩnh và nói rõ điều mình muốn, thay vì cố ép người khác",
        "gồng lên để không ai thấy mình đang quá tải",
        "nói bình tĩnh một việc bạn không thể nhận thêm",
    ),
    (
        "hermit",
        "Ẩn Sĩ",
        "The Hermit",
        "dành một khoảng riêng để nghĩ rõ mình muốn gì",
        "tránh nói chuyện quá lâu vì chưa biết mở lời thế nào",
        "xin một khoảng riêng có thời hạn và quay lại đối thoại",
    ),
    (
        "wheel-of-fortune",
        "Bánh Xe",
        "Wheel of Fortune",
        "nhận ra tình hình đang đổi và phần mình có thể điều chỉnh",
        "chờ vận may làm hộ một quyết định",
        "chọn một việc có thể đổi khi kế hoạch không còn như trước",
    ),
    (
        "justice",
        "Công Lý",
        "Justice",
        "đối chiếu lựa chọn với dữ kiện và hệ quả thật",
        "dùng lý lẽ để né phần cảm xúc liên quan",
        "viết ra dữ kiện, giả định và trách nhiệm của mình",
    ),
    (
        "hanged-man",
        "Người Treo Ngược",
        "The Hanged Man",
        "đổi góc nhìn trước khi tiếp tục dùng cách cũ",
        "trì hoãn vô hạn rồi gọi đó là chờ đúng lúc",
        "đặt giờ quay lại xử lý việc bạn đang tạm hoãn",
    ),
    (
        "death",
        "Chuyển Mùa",
        "Death",
        "cần chấp nhận một việc đã kết thúc để bắt đầu việc khác",
        "cắt quá nhanh vì không muốn chịu cảm giác chia tay",
        "kết thúc một phần cụ thể thay vì phủ nhận toàn bộ",
    ),
    (
        "temperance",
        "Tiết Chế",
        "Temperance",
        "tìm cách vừa làm việc cần làm, vừa không bỏ qua nhu cầu của mình",
        "cố làm vừa lòng mọi người rồi không nói điều mình cần",
        "chọn phần bạn có thể làm thay vì nhận hết hoặc bỏ hết",
    ),
    (
        "devil",
        "Sợi Ràng",
        "The Devil",
        "nhận ra một thói quen khiến mình khó dừng dù không còn thấy vui",
        "nghĩ mình không có lựa chọn nên tiếp tục một việc không còn muốn",
        "chọn một thói quen bạn muốn giảm và thử bớt một lần hôm nay",
    ),
    (
        "tower",
        "Tòa Tháp",
        "The Tower",
        "cần xem lại một kế hoạch khi có điều mới làm nó không còn phù hợp",
        "bỏ cả kế hoạch chỉ vì một việc không diễn ra như mong đợi",
        "giữ phần vẫn còn ổn và sửa đúng chỗ đang có vấn đề",
    ),
    (
        "star",
        "Ngôi Sao",
        "The Star",
        "lấy lại hy vọng từ một việc nhỏ đang tiến triển tốt",
        "dùng hy vọng để bỏ qua giới hạn hiện tại",
        "ghi lại một việc đã tốt hơn và tiếp tục làm điều giúp nó tốt lên",
    ),
    (
        "moon",
        "Mặt Trăng",
        "The Moon",
        "đi chậm khi cảm giác, ký ức và dữ kiện đang lẫn vào nhau",
        "lấy nỗi lo để điền vào chỗ còn thiếu thông tin",
        "hoãn kết luận và kiểm tra một điều cụ thể",
    ),
    (
        "sun",
        "Mặt Trời",
        "The Sun",
        "nhìn nhận điều đang tốt và chia sẻ niềm vui mà không phải giả vờ",
        "đòi mình phải vui để chứng minh mọi thứ ổn",
        "ghi nhận điều tốt mà không xóa phần còn khó",
    ),
    (
        "judgement",
        "Tiếng Gọi",
        "Judgement",
        "nhìn lại một chuyện cũ để biết lần tới mình muốn làm khác điều gì",
        "biến một lỗi cũ thành bản án lâu dài",
        "viết một điều bạn đã học và một việc muốn làm khác lần tới",
    ),
    (
        "world",
        "Thế Giới",
        "The World",
        "nhận ra một việc đã hoàn thành và cho phép mình dừng sửa",
        "níu thêm việc chỉ vì chưa quen với khoảng trống",
        "đánh dấu điều đã xong trước khi bắt đầu việc mới",
    ),
)


_SUITS: dict[str, tuple[str, str, str, str, str]] = {
    "wands": (
        "Gậy",
        "một việc bạn muốn bắt đầu hoặc theo đuổi",
        "nôn nóng biến hứng thú thành cam kết",
        "một ý tưởng vừa làm bạn muốn đứng dậy làm ngay",
        "biến hứng thú thành một việc nhỏ có thể làm hôm nay",
    ),
    "cups": (
        "Cốc",
        "cảm xúc và cách bạn đón nhận sự gần gũi",
        "đọc cảm giác như một kết luận đã chắc",
        "một câu trả lời ngắn làm cảm xúc đổi dù chưa ai nói hết ý",
        "gọi tên cảm xúc trước khi đoán nguyên nhân",
    ),
    "swords": (
        "Kiếm",
        "suy nghĩ, lời nói và quyết định",
        "nghĩ thêm vòng nữa để tránh câu cần nói",
        "một tin nhắn được soạn rồi xóa hoặc một câu cứ chạy lại trong đầu",
        "viết câu chính ngắn hơn phần giải thích",
    ),
    "pentacles": (
        "Tiền",
        "thời gian, công sức và điều có thể kiểm chứng",
        "bám vào thứ đã bỏ công dù nó không còn đáng",
        "một lịch hẹn, khoản công sức hoặc việc thực tế đang cần được chốt",
        "đặt một mốc, con số hoặc hành động nhìn thấy được",
    ),
}


_RANKS: dict[str, tuple[str, str, str, str]] = {
    "ace": ("Át", "một khả năng vừa mở", "vội gọi mầm mới là kết quả", "cho nó một lần thử nhỏ"),
    "2": (
        "Hai",
        "hai hướng cần được đặt cạnh nhau",
        "đứng giữa quá lâu vì sợ mất một lựa chọn",
        "chọn tiêu chí để so thay vì đoán",
    ),
    "3": (
        "Ba",
        "một việc cần thêm người hoặc nguồn lực phối hợp",
        "mong mọi người tự hiểu phần việc",
        "nói rõ ai cần làm gì tiếp",
    ),
    "4": (
        "Bốn",
        "nhu cầu giữ ổn định và bảo toàn",
        "giữ chặt đến mức không còn chỗ thở",
        "xác định điều thật sự cần giữ",
    ),
    "5": (
        "Năm",
        "một va chạm làm lộ phần chưa khớp",
        "chỉ nhìn phần hụt rồi bỏ sót thứ còn dùng được",
        "gọi đúng điều đã lệch và phần còn có thể sửa",
    ),
    "6": (
        "Sáu",
        "sự điều chỉnh để dòng trao đổi cân hơn",
        "cho hoặc nhận theo cách tạo món nợ ngầm",
        "làm rõ điều gì đang được trao và có tự nguyện không",
    ),
    "7": (
        "Bảy",
        "một bài kiểm tra về lựa chọn và kiên nhẫn",
        "giữ quá nhiều phương án để khỏi chịu trách nhiệm chọn",
        "loại một phương án không đạt tiêu chí bạn đã chọn",
    ),
    "8": (
        "Tám",
        "một việc lặp lại đang thành thói quen",
        "bận liên tục nhưng không biết việc nào đang đưa mình đi đâu",
        "giữ việc có ích và bỏ một việc chỉ gây nhiễu",
    ),
    "9": (
        "Chín",
        "điểm gần đủ nhưng hệ thần kinh vẫn còn cảnh giác",
        "co lại trước khi biết nguy cơ có thật không",
        "kiểm tra mức an toàn hiện tại thay vì dùng ký ức cũ",
    ),
    "10": (
        "Mười",
        "một chu kỳ đã đầy tải",
        "ôm nốt phần cuối vì nghĩ bỏ xuống là thất bại",
        "kết thúc một việc hoặc chia bớt phần đang ôm",
    ),
    "page": (
        "Tiểu Đồng",
        "sự tò mò đang học cách thành tiếng",
        "hỏi để được trấn an thay vì để hiểu",
        "đặt một câu hỏi thật và nghe hết câu trả lời",
    ),
    "knight": (
        "Kỵ Sĩ",
        "động lực muốn đưa chuyện tiến lên",
        "để tốc độ đi trước độ rõ",
        "đi đủ nhanh nhưng vẫn còn kịp quan sát",
    ),
    "queen": (
        "Nữ Hoàng",
        "khả năng giữ một không gian đủ sâu",
        "ôm luôn phần của người khác",
        "giữ sự tinh tế mà không nhận hộ trách nhiệm",
    ),
    "king": (
        "Nhà Vua",
        "khả năng dẫn dắt và chịu trách nhiệm",
        "dùng quyền kiểm soát thay cho đối thoại",
        "đưa ra một quyết định có ranh giới và lý do",
    ),
}


@lru_cache(maxsize=1)
def all_cards() -> tuple[TarotCard, ...]:
    majors = tuple(
        TarotCard(
            id=f"major-{slug}",
            title_vi=title_vi,
            title_en=title_en,
            arcana="major",
            core=core,
            tension=tension,
            resource=resource,
            source_concept_ids=("archetype-depth", "self-reflection", "non-determinism"),
        )
        for slug, title_vi, title_en, core, tension, resource in _MAJOR
    )
    minors: list[TarotCard] = []
    for suit, suit_data in _SUITS.items():
        suit_vi = suit_data[0]
        for rank, rank_data in _RANKS.items():
            rank_vi = rank_data[0]
            core, tension, resource = MINOR_READINGS[f"{suit}-{rank}"]
            minors.append(
                TarotCard(
                    id=f"{suit}-{rank}",
                    title_vi=f"{rank_vi} {suit_vi}",
                    title_en=f"{rank.title()} of {suit.title()}",
                    arcana="minor",
                    suit=suit,
                    rank=rank,
                    core=core,
                    tension=tension,
                    resource=resource,
                    source_concept_ids=(
                        "symbolic-tension",
                        "card-interaction",
                        "ethical-reflection",
                    ),
                )
            )
    return majors + tuple(minors)


def card_by_id(card_id: str) -> TarotCard:
    try:
        return next(card for card in all_cards() if card.id == card_id)
    except StopIteration as exc:
        raise KeyError(card_id) from exc


def minor_scene(card: TarotCard) -> str | None:
    if card.suit is None:
        return None
    return _SUITS[card.suit][3]


def source_ids_for_concepts(concept_ids: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                source_id
                for concept_id in concept_ids
                for source_id in _CONCEPT_SOURCES.get(concept_id, ())
            }
        )
    )
