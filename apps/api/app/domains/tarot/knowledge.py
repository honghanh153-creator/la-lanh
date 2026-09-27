from __future__ import annotations

from functools import lru_cache

from app.domains.tarot.models import TarotBookSource, TarotCard

KNOWLEDGE_VERSION = "tarot-knowledge-v1"
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
        "gom thứ đang có thành một hành động có chủ đích",
        "cố kiểm soát hình ảnh thay vì làm việc thật",
        "chọn đúng một công cụ và dùng nó đến nơi",
    ),
    (
        "high-priestess",
        "Nữ Tư Tế",
        "The High Priestess",
        "nghe phần mình đã nhận ra nhưng chưa gọi thành lời",
        "coi linh cảm là bằng chứng đã đủ",
        "tách điều cảm thấy khỏi điều đã kiểm chứng",
    ),
    (
        "empress",
        "Hoàng Hậu",
        "The Empress",
        "nuôi điều có khả năng lớn lên bằng sự chăm sóc đều",
        "cho quá nhiều rồi âm thầm mong được hiểu",
        "đặt nhu cầu của mình vào cùng danh sách cần chăm",
    ),
    (
        "emperor",
        "Hoàng Đế",
        "The Emperor",
        "tạo cấu trúc và ranh giới đủ rõ để yên tâm",
        "siết mọi thứ vì sợ mất thế chủ động",
        "nói một giới hạn cụ thể và lý do thực tế",
    ),
    (
        "hierophant",
        "Người Giữ Nếp",
        "The Hierophant",
        "xem lại quy tắc mình đang tin và nơi nó đến từ",
        "làm đúng khuôn dù khuôn không còn hợp",
        "giữ phần có ích và hỏi lại phần chỉ vì thói quen",
    ),
    (
        "lovers",
        "Người Tình",
        "The Lovers",
        "chọn điều đồng thuận với giá trị chứ không chỉ với cảm xúc tức thời",
        "để độ hút thay cho một cuộc nói chuyện rõ ràng",
        "gọi tên điều mình thật sự đang chọn",
    ),
    (
        "chariot",
        "Cỗ Xe",
        "The Chariot",
        "đưa hai lực kéo khác nhau về cùng một hướng",
        "tăng tốc để khỏi phải xử lý mâu thuẫn bên trong",
        "chốt hướng trước khi thêm tốc độ",
    ),
    (
        "strength",
        "Sức Mạnh",
        "Strength",
        "dùng sự vững vàng thay vì ép buộc",
        "gồng lên để không ai thấy mình đang quá tải",
        "giảm lực nhưng giữ ranh giới",
    ),
    (
        "hermit",
        "Ẩn Sĩ",
        "The Hermit",
        "lùi khỏi tiếng ồn để nghe câu trả lời của chính mình",
        "cô lập quá lâu rồi gọi đó là bình yên",
        "xin một khoảng riêng có thời hạn và quay lại đối thoại",
    ),
    (
        "wheel-of-fortune",
        "Bánh Xe",
        "Wheel of Fortune",
        "nhận ra nhịp đang đổi và phần mình có thể điều chỉnh",
        "chờ vận may làm hộ một quyết định",
        "đổi một biến nhỏ trong tầm tay",
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
        "tạm dừng có mốc kết thúc và câu hỏi cần trả lời",
    ),
    (
        "death",
        "Chuyển Mùa",
        "Death",
        "thừa nhận một nhịp đã hết để chừa chỗ cho nhịp khác",
        "cắt quá nhanh vì không muốn chịu cảm giác chia tay",
        "kết thúc một phần cụ thể thay vì phủ nhận toàn bộ",
    ),
    (
        "temperance",
        "Tiết Chế",
        "Temperance",
        "pha hai nhu cầu theo liều lượng có thể sống cùng",
        "cố làm vừa lòng mọi phía đến mức mất vị của mình",
        "điều chỉnh một mức độ thay vì chọn tất cả hoặc không gì",
    ),
    (
        "devil",
        "Sợi Ràng",
        "The Devil",
        "nhìn thẳng điều đang giữ mình bằng ham muốn, sợ hãi hoặc thói quen",
        "gọi sự lệ thuộc là không còn lựa chọn",
        "tìm một mắt xích có thể tháo mà không tự phạt mình",
    ),
    (
        "tower",
        "Tòa Tháp",
        "The Tower",
        "nhận ra cấu trúc nào đã không còn đứng vững",
        "phá hết chỉ vì một phần vừa nứt",
        "giữ điều còn thật và sửa đúng chỗ đã lộ vấn đề",
    ),
    (
        "star",
        "Ngôi Sao",
        "The Star",
        "khôi phục một niềm tin có bằng chứng nhỏ để bám vào",
        "dùng hy vọng để bỏ qua giới hạn hiện tại",
        "chọn một dấu hiệu sống được và chăm nó đều",
    ),
    (
        "moon",
        "Mặt Trăng",
        "The Moon",
        "đi chậm khi cảm giác, ký ức và dữ kiện đang lẫn vào nhau",
        "để nỗi lo viết nốt phần thông tin còn thiếu",
        "hoãn kết luận và kiểm tra một điều cụ thể",
    ),
    (
        "sun",
        "Mặt Trời",
        "The Sun",
        "đưa điều đang có sức sống ra chỗ sáng rõ",
        "đòi mình phải vui để chứng minh mọi thứ ổn",
        "ghi nhận điều tốt mà không xóa phần còn khó",
    ),
    (
        "judgement",
        "Tiếng Gọi",
        "Judgement",
        "nhìn lại đủ thật để chọn cách đáp lại khác đi",
        "biến một lỗi cũ thành bản án lâu dài",
        "rút một bài học cụ thể rồi trả phần còn lại về quá khứ",
    ),
    (
        "world",
        "Thế Giới",
        "The World",
        "nhận ra một vòng đã đủ đầy để khép lại",
        "níu thêm việc chỉ vì chưa quen với khoảng trống",
        "đánh dấu điều đã xong trước khi mở vòng mới",
    ),
)


_SUITS: dict[str, tuple[str, str, str, str, str]] = {
    "wands": (
        "Gậy",
        "động lực và quyền bắt đầu",
        "nôn nóng biến hứng thú thành cam kết",
        "một ý tưởng vừa làm bạn muốn đứng dậy làm ngay",
        "chuyển năng lượng thành một bước có giới hạn",
    ),
    "cups": (
        "Cốc",
        "cảm xúc và cách mình đón nhận kết nối",
        "đọc cảm giác như một kết luận đã chắc",
        "một khoảnh khắc làm mood đổi dù chưa ai nói hết câu",
        "gọi tên cảm xúc trước khi đoán nguyên nhân",
    ),
    "swords": (
        "Kiếm",
        "suy nghĩ, ngôn ngữ và quyết định",
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
        "đứng giữa quá lâu vì sợ mất một bên",
        "chọn tiêu chí để so thay vì đoán",
    ),
    "3": (
        "Ba",
        "một nhịp cần người hoặc nguồn lực phối hợp",
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
        "loại một phương án không qua tiêu chí thật",
    ),
    "8": (
        "Tám",
        "nhịp lặp đang tạo quán tính",
        "bận liên tục nhưng không biết việc nào đang đưa mình đi đâu",
        "giữ một nhịp có ích và bỏ một nhịp chỉ gây nhiễu",
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
        "kết thúc, chia bớt hoặc đặt lại sức chứa",
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
        "chọn nhịp đủ nhanh nhưng còn kịp quan sát",
    ),
    "queen": (
        "Nữ Hoàng",
        "khả năng giữ một không gian đủ sâu",
        "ôm luôn phần của người khác",
        "giữ sự tinh tế mà không nhận hộ trách nhiệm",
    ),
    "king": (
        "Nhà Vua",
        "khả năng dẫn nhịp và chịu trách nhiệm",
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
    for suit, (suit_vi, domain, suit_tension, _scene, suit_resource) in _SUITS.items():
        for rank, (rank_vi, motion, rank_tension, rank_resource) in _RANKS.items():
            minors.append(
                TarotCard(
                    id=f"{suit}-{rank}",
                    title_vi=f"{rank_vi} {suit_vi}",
                    title_en=f"{rank.title()} of {suit.title()}",
                    arcana="minor",
                    suit=suit,
                    rank=rank,
                    core=f"{motion} trong vùng {domain}",
                    tension=f"{rank_tension}; đồng thời dễ {suit_tension}",
                    resource=f"{rank_resource}, rồi {suit_resource}",
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
