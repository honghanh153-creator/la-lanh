"""Card cores as complete Vietnamese clauses, for framed Tarot readings only (Tarot pass 2).

Owner feedback (29/10/2026, "content tarot vẫn kỳ lắm"): position blocks read "lead + label: card
text" and many card cores start with a bare verb ("muốn học một điều…", "cần nhìn…"), so they do
not stand as a sentence. ``CORE_SENTENCES`` gives, per topic and card, the same meaning as a
clause with a subject, without a final stop. Cores that already read as a natural clause have no
entry and are used as they are.

Rules for every sentence (tests/tarot/test_phrasing.py): at most 18 words (so a 4-word lead and
a 6-word frame stay inside the 28-word sentence limit), the reader is "bạn", no advice words
("hãy", "nên", "đừng", "phải", "khoan"), no fate claim and no claim about what another person
thinks or wants.

The card field tables (knowledge.py, context_readings.py, relationship_readings.py) are not
edited: legacy readings (renderer v6) keep their text byte for byte. Only the framed renderer
(roles, stance summary and reasons) reads this overlay. New copy here needs the owner's reading
before release (docs/reviews/2026-10-29-tarot-pass2.md).
"""

from __future__ import annotations

from app.domains.tarot.models import TarotContext

PHRASING_VERSION = "tarot-core-sentences-v1"

_GENERAL: dict[str, str] = {
    "major-fool": "bạn có thể cho phép mình bắt đầu khi chưa có đủ mọi câu trả lời",
    "major-magician": "bạn có thể bắt đầu bằng kỹ năng và những thứ mình đã có",
    "major-high-priestess": (
        "cảm giác của bạn đáng được để ý, nhưng thông tin vẫn cần được kiểm tra"
    ),
    "major-empress": "bạn đang cần dành thời gian chăm sóc một người, một việc hoặc chính mình",
    "major-emperor": "bạn đang cần một kế hoạch và giới hạn rõ trước khi làm tiếp",
    "major-hierophant": (
        "điều bạn làm theo vì gia đình, trường học hay thói quen đáng được xem lại"
    ),
    "major-lovers": "bạn cần chọn điều hợp với mình, kể cả khi rất thích một người",
    "major-chariot": "bạn cần quyết định mình muốn đi tới đâu trước khi cố làm nhanh hơn",
    "major-strength": (
        "bạn có thể giữ bình tĩnh và nói rõ điều mình muốn, thay vì cố ép người khác"
    ),
    "major-hermit": "bạn cần một khoảng riêng để nghĩ rõ mình muốn gì",
    "major-wheel-of-fortune": "tình hình đang đổi, và vẫn có phần bạn có thể điều chỉnh",
    "major-justice": "lựa chọn này cần được đối chiếu với dữ kiện và hệ quả thật",
    "major-hanged-man": "bạn có thể cần đổi góc nhìn trước khi tiếp tục dùng cách cũ",
    "major-death": ("có một việc đã kết thúc, và chấp nhận điều đó giúp bạn bắt đầu việc khác"),
    "major-temperance": (
        "bạn đang tìm cách vừa làm việc cần làm, vừa không bỏ qua nhu cầu của mình"
    ),
    "major-devil": "có một thói quen khiến bạn khó dừng dù không còn thấy vui",
    "major-tower": "một điều mới khiến kế hoạch cũ không còn phù hợp và cần được xem lại",
    "major-star": "một việc nhỏ đang tiến triển tốt có thể giúp bạn lấy lại hy vọng",
    "major-moon": "khi cảm giác, ký ức và dữ kiện đang lẫn vào nhau, bạn cần đi chậm lại",
    "major-sun": ("có những điều đang tốt, và bạn có thể chia sẻ niềm vui mà không cần giả vờ"),
    "major-judgement": ("nhìn lại một chuyện cũ giúp bạn biết lần tới mình muốn làm khác điều gì"),
    "major-world": "một việc đã hoàn thành, và bạn có thể cho phép mình dừng sửa",
    "wands-ace": "bạn đang có hứng bắt đầu một việc mới",
    "wands-2": "bạn muốn đi xa hơn nhưng vẫn đang cân nhắc bước đầu",
    "wands-3": "bạn đã bắt đầu và đang chờ xem kế hoạch đi được đến đâu",
    "wands-4": "bạn có một cột mốc đáng vui cùng những người đã giúp mình",
    "wands-6": "bạn muốn công sức của mình được nhìn nhận",
    "wands-7": "bạn cần bảo vệ một lựa chọn khi có người không đồng ý",
    "wands-9": "bạn đã cố gắng lâu, giờ vừa muốn tiếp tục vừa thấy mệt",
    "wands-10": "bạn đang ôm nhiều trách nhiệm hơn mức mình xử lý nổi",
    "wands-page": "bạn tò mò và muốn thử một ý tưởng mới",
    "wands-knight": "bạn muốn hành động nhanh khi đang rất hào hứng",
    "wands-queen": "bạn muốn tự tin thể hiện điều mình thích",
    "wands-king": "bạn có hướng đi rõ và muốn đưa mọi người cùng tiến tới",
    "cups-ace": "bạn đang bắt đầu đón nhận một cảm xúc mới",
    "cups-3": "bạn thấy vui và được đón nhận khi ở cùng bạn bè",
    "cups-4": "bạn chưa thấy hứng thú với điều đang được đề nghị",
    "cups-5": "bạn buồn vì điều đã mất và khó nhìn thấy điều vẫn còn",
    "cups-6": "bạn nhớ cảm giác thân thuộc từ một người hoặc chuyện cũ",
    "cups-7": "bạn có nhiều điều muốn nhưng chưa biết điều nào thực tế",
    "cups-8": "bạn nhận ra một chuyện quen thuộc không còn làm mình hài lòng",
    "cups-9": "bạn biết điều gì làm mình vui và thế nào là đủ với mình",
    "cups-10": "bạn muốn có một mối quan hệ khiến mình yên tâm và được là mình",
    "cups-page": "bạn muốn nói một lời dễ thương nhưng còn ngại",
    "cups-knight": "bạn muốn thể hiện tình cảm bằng lời nói hoặc một lời mời",
    "cups-queen": "bạn lắng nghe cảm xúc của mình và quan tâm đến người khác",
    "cups-king": "bạn có thể giữ bình tĩnh khi nói về một chuyện khiến mình xúc động",
    "swords-ace": "hỏi đúng câu hỏi giúp bạn nhìn rõ một điều",
    "swords-2": "bạn đang kẹt giữa hai lựa chọn và chưa muốn quyết định",
    "swords-3": "một lời nói hoặc một sự thật đang làm bạn buồn",
    "swords-4": "đầu óc bạn cần nghỉ sau nhiều suy nghĩ hoặc tranh luận",
    "swords-6": "bạn muốn bớt căng thẳng và xử lý chuyện theo cách bình tĩnh hơn",
    "swords-7": "có điều bạn đang giấu hoặc tránh nói rõ, và nó đáng được xem lại",
    "swords-8": "bạn thấy như không có lựa chọn, dù vẫn còn một phần mình quyết được",
    "swords-9": "nỗi lo khiến một chuyện cứ chạy đi chạy lại trong đầu bạn",
    "swords-page": "bạn muốn hỏi và tìm hiểu trước khi tin một điều",
    "swords-knight": "bạn muốn giải quyết nhanh bằng một câu nói thẳng",
    "swords-queen": "bạn muốn nói rõ giới hạn mà không vòng vo",
    "swords-king": "bạn cần quyết định dựa trên thông tin thay vì tranh cãi",
    "pentacles-2": "bạn đang chia thời gian giữa nhiều việc cùng cần mình",
    "pentacles-4": "bạn muốn giữ chặt thời gian hoặc những gì mình đang có",
    "pentacles-5": "bạn thấy mình thiếu sự hỗ trợ khi đang gặp khó",
    "pentacles-6": "bạn cần nhìn xem hai bên đang cho và nhận có cân bằng không",
    "pentacles-7": "bạn đã bỏ công và cần xem cách làm có đáng tiếp tục không",
    "pentacles-8": "bạn tiến bộ nhờ luyện một kỹ năng đều đặn",
    "pentacles-9": "bạn muốn tự chủ và tận hưởng điều mình đã làm được",
    "pentacles-10": "bạn muốn xây một nền ổn định có thể chia sẻ với người thân",
    "pentacles-page": "bạn muốn học một điều có thể dùng được trong thực tế",
    "pentacles-knight": "bạn làm chậm nhưng đều và giữ được điều đã hứa",
    "pentacles-queen": "bạn quan tâm bằng những việc thiết thực hằng ngày",
    "pentacles-king": "bạn muốn dùng kinh nghiệm để làm một việc ổn định và lâu dài",
}

_RELATIONSHIPS: dict[str, str] = {
    "major-fool": "bạn muốn thử làm quen dù chưa biết chuyện sẽ đi đến đâu",
    "major-magician": "bạn có thể chủ động nói rõ điều mình muốn trong mối quan hệ",
    "major-empress": "bạn muốn được quan tâm bằng những việc nhỏ, đều đặn",
    "major-emperor": "bạn muốn hai người có lời hẹn và giới hạn rõ ràng",
    "major-hierophant": "bạn cần biết hai người có cùng cách nhìn về sự cam kết không",
    "major-lovers": "bạn muốn tình cảm đi cùng những lựa chọn mà mình thấy đúng",
    "major-chariot": "bạn muốn mối quan hệ tiến thêm một bước thay vì cứ chờ",
    "major-strength": "bạn có thể nói điều khó chịu mà không làm người kia tổn thương",
    "major-hermit": "bạn cần thời gian riêng để biết mình muốn gì trước khi nhắn lại",
    "major-justice": "bạn cần nhìn cả điều mình làm lẫn điều mình mong người kia làm",
    "major-hanged-man": "nghe hết phía còn lại có thể giúp bạn hiểu cuộc cãi nhau khác đi",
    "major-star": "bạn muốn tin rằng mình vẫn có thể được lắng nghe sau một lần thất vọng",
    "major-moon": "bạn chưa rõ người kia muốn gì, vì vậy dễ tự nghĩ thêm lý do",
    "major-sun": "bạn muốn được nói thật và thoải mái khi ở cạnh người kia",
    "major-judgement": "bạn cần nhìn lại cách hai người từng giải quyết những chuyện tương tự",
    "major-world": "bạn muốn biết hai người đã đi đến đâu và có muốn bước tiếp không",
    "wands-ace": "bạn có hứng chủ động rủ người kia làm một việc mới",
    "wands-2": "bạn muốn tiến thêm nhưng còn phân vân có chủ động hay không",
    "wands-3": "bạn đã chủ động và đang chờ xem người kia có đáp lại không",
    "wands-4": "bạn muốn có những cuộc gặp khiến cả hai thoải mái và được chào đón",
    "wands-6": "bạn muốn công sức mình dành cho kết nối này được nhìn thấy",
    "wands-7": "bạn cần giữ điều mình muốn dù người kia không đồng ý ngay",
    "wands-8": "bạn muốn cuộc trò chuyện tiến nhanh và có câu trả lời rõ",
    "wands-9": "bạn muốn bảo vệ mình sau một trải nghiệm không vui",
    "wands-10": "bạn có thể đang nhận quá nhiều phần giữ liên lạc và sắp xếp gặp gỡ",
    "wands-page": "bạn muốn làm quen và xem hai người có vui khi trò chuyện không",
    "wands-knight": "bạn muốn tiến nhanh vì đang thấy người kia rất cuốn hút",
    "wands-queen": "bạn muốn tự tin thể hiện điều mình thích mà không cần diễn khác đi",
    "wands-king": "bạn muốn chủ động nói hướng mình muốn hai người tiến tới",
    "cups-ace": "bạn bắt đầu có cảm tình và muốn cho người kia biết",
    "cups-2": "bạn muốn việc lắng nghe và đáp lại đến từ cả hai phía",
    "cups-3": "bạn muốn kết nối qua những cuộc gặp vui và bạn bè chung",
    "cups-4": "bạn chưa thấy hứng thú với cách hai người đang tìm hiểu nhau",
    "cups-5": "bạn còn buồn về một việc giữa hai người và khó nhìn ra ngoài chuyện đó",
    "cups-6": "bạn nhớ cảm giác thân thuộc từ một người hoặc chuyện cũ",
    "cups-7": "bạn có nhiều điều mong từ người kia nhưng chưa biết điều nào thực tế",
    "cups-8": "bạn nhận ra cách hai người đang ở cạnh nhau chưa làm mình hài lòng",
    "cups-9": "bạn biết điều gì khiến mình vui khi ở trong một mối quan hệ",
    "cups-10": "bạn muốn được là mình và thấy yên tâm khi ở cạnh người kia",
    "cups-page": "bạn muốn nói một lời dễ thương nhưng còn ngại",
    "cups-knight": "bạn muốn thể hiện tình cảm bằng một lời nói hoặc lời mời",
    "cups-queen": "bạn muốn nghe và hiểu cảm xúc của người kia",
    "cups-king": "bạn muốn nói rõ cảm xúc mà vẫn giữ bình tĩnh",
    "swords-ace": "hai người cần một câu nói rõ để bớt hiểu lầm",
    "swords-2": "bạn chưa biết nói tiếp hay dừng lại để nghĩ thêm",
    "swords-4": "bạn cần nghỉ khỏi cuộc cãi nhau trước khi có thể nói tiếp",
    "swords-5": "bạn cần xem cuộc tranh luận đang giúp hiểu nhau hay chỉ để thắng",
    "swords-6": "bạn muốn hai người thoát khỏi cách cãi nhau đã làm cả hai mệt",
    "swords-8": "bạn sợ phản ứng của người kia đến mức thấy mình không có lựa chọn",
    "swords-9": "bạn lo về kết nối này đến mức nghĩ đi nghĩ lại một chi tiết",
    "swords-page": "bạn muốn biết thêm trước khi tin vào điều người kia nói",
    "swords-knight": "bạn muốn nói ngay điều mình thấy không đúng",
    "swords-queen": "bạn muốn nói thẳng điều mình cần và không muốn trong mối quan hệ",
    "swords-king": "hai người cần thống nhất điều cụ thể thay vì tranh luận theo cảm xúc lúc đó",
    "pentacles-ace": "bạn muốn biến lời hẹn thành thời gian gặp nhau thật",
    "pentacles-2": "bạn cần sắp xếp thời gian cho người kia mà vẫn giữ việc riêng",
    "pentacles-3": "bạn muốn hai người cùng góp sức vào chuyện đã thống nhất",
    "pentacles-4": "bạn muốn biết mối quan hệ có ổn định trước khi thay đổi cách gần gũi",
    "pentacles-5": "bạn có thể thấy mình bị bỏ ngoài một chuyện cần có sự quan tâm",
    "pentacles-6": "bạn cần nhìn xem việc cho và nhận có thoải mái với cả hai không",
    "pentacles-7": "bạn cần xem công sức dành cho kết nối này có đem lại điều mình muốn không",
    "pentacles-8": "bạn muốn cải thiện cách hai người nói chuyện qua những việc nhỏ lặp lại",
    "pentacles-9": "bạn muốn gần gũi mà vẫn có thời gian và cuộc sống riêng",
    "pentacles-10": (
        "bạn muốn biết chuyện gia đình và kế hoạch lâu dài ảnh hưởng hai người ra sao"
    ),
    "pentacles-page": "bạn muốn tìm hiểu người kia qua việc họ làm chứ không chỉ lời nói",
    "pentacles-knight": "bạn muốn sự quan tâm đều đặn và có thể tin cậy",
    "pentacles-queen": "bạn muốn thể hiện sự quan tâm bằng việc chăm sóc thiết thực",
    "pentacles-king": "bạn muốn lời hứa được thể hiện qua việc làm ổn định",
}

_WORK: dict[str, str] = {
    "major-fool": "bạn có thể thử một hướng làm mới trước khi cam kết lâu dài",
    "wands-2": "bạn cần chọn một hướng phát triển thay vì giữ mọi kế hoạch trên giấy",
    "wands-3": "điều đã khởi động đáng được theo dõi trước khi bạn cân nhắc mở rộng",
    "wands-7": "bạn cần bảo vệ ưu tiên đã chọn trước các yêu cầu phát sinh",
    "wands-king": "việc dẫn dắt cần một hướng rõ và quyền chủ động cho người cùng làm",
    "cups-8": "bạn cần xem công việc hiện tại còn đáp ứng điều mình mong muốn không",
    "swords-6": "việc chuyển sang cách làm bớt vướng cần một bước bàn giao rõ",
    "pentacles-4": (
        "để giữ nguồn lực ổn định, bạn cần phân biệt khoản dự phòng với việc giữ quá chặt"
    ),
    "pentacles-page": "việc học một kỹ năng thực tế có thể bắt đầu từ bài tập vừa sức",
    "pentacles-king": "để quản lý nguồn lực tốt, bạn cần mức cam kết ổn định và giới hạn rõ",
}

_COMMUNICATION: dict[str, str] = {
    "major-fool": "bạn có thể mở lời dù chưa biết cuộc trao đổi sẽ diễn ra thế nào",
    "major-devil": "bạn cần nhận ra lúc mình nói chỉ để giữ sự đồng ý của người khác",
    "wands-3": "sau khi nói rõ lời đề nghị, bạn cần dành thời gian chờ phản hồi",
    "cups-queen": ("khi lắng nghe cảm xúc, người kể cần có chỗ để tự gọi tên điều họ trải qua"),
    "cups-4": "khi chưa muốn trò chuyện, bạn có thể nói ra thay vì miễn cưỡng đáp",
    "cups-8": "bạn có thể rời một cuộc trao đổi không còn giúp hai bên hiểu nhau",
    "swords-2": "dù chưa có câu trả lời, bạn vẫn có thể nói rõ mình đang cân nhắc gì",
    "swords-3": "lời làm bạn buồn cần được nhắc lại đúng câu và đúng tác động của nó",
    "swords-5": "bạn cần xem lời đáp đang giải quyết vấn đề hay chỉ giành phần thắng",
    "swords-7": "chuyện riêng tư và thông tin người khác cần biết là hai điều khác nhau",
    "pentacles-4": "muốn giữ riêng chuyện cá nhân, bạn cần nói rõ ranh giới",
    "pentacles-7": "một thỏa thuận cần có thời gian để thấy cách trao đổi có thay đổi không",
    "pentacles-king": (
        "lời cam kết cần nói rõ mức thực hiện để người nghe biết có thể trông cậy gì"
    ),
}

_ENERGY: dict[str, str] = {
    "major-moon": ("khi chưa rõ mình mệt vì đâu, bạn có thể bắt đầu từ lịch sinh hoạt thực tế"),
    "wands-2": "chốt một lựa chọn rõ giúp bạn đỡ tốn sức cân nhắc cả ngày",
    "wands-knight": "khi một lúc có nhiều hứng, bạn cần điểm dừng để không nhận quá sức",
    "wands-king": "để dành sức cho hướng chính, bạn cần biết phần nào không cần tự mình làm",
    "cups-queen": ("khi nghe chuyện của người khác, bạn cũng cần tính đến sức chú ý mình còn lại"),
    "swords-4": "đầu óc đã làm việc nhiều cần một lúc nghỉ, không nạp thêm thông tin",
    "pentacles-2": ("khi đổi qua lại giữa nhiều việc, công sức chuyển sự chú ý cũng cần được tính"),
}

_SELF_CARE: dict[str, str] = {
    "major-hierophant": (
        "cách chăm mình hợp nhất là cách theo nhu cầu, không chỉ theo lời truyền nhau"
    ),
    "major-death": "bạn có thể bỏ một yêu cầu với bản thân không còn hợp giai đoạn này",
    "wands-king": (
        "tự quyết cuộc sống riêng là đi theo hướng bạn muốn, không chỉ theo kỳ vọng bên ngoài"
    ),
    "cups-10": ("thuộc về một nơi cũng cần chỗ cho nhu cầu của bạn, không chỉ hòa thuận bề ngoài"),
    "swords-page": ("để hiểu nhu cầu của mình, câu hỏi thật giúp nhiều hơn việc soi lỗi liên tục"),
    "swords-knight": ("dù muốn sửa mình nhanh, bạn vẫn cần chọn thay đổi không làm mình quá sức"),
    "pentacles-4": (
        "để giữ đồ, tiền và thời gian riêng, bạn cần ranh giới hợp với nhu cầu của mình"
    ),
    "pentacles-7": (
        "một thói quen chăm mình đáng được nhìn bằng ích lợi thật, không chỉ số ngày đã giữ"
    ),
}

CORE_SENTENCES: dict[str, dict[str, str]] = {
    TarotContext.GENERAL.value: _GENERAL,
    TarotContext.RELATIONSHIPS.value: _RELATIONSHIPS,
    TarotContext.WORK.value: _WORK,
    TarotContext.COMMUNICATION.value: _COMMUNICATION,
    TarotContext.ENERGY.value: _ENERGY,
    TarotContext.SELF_CARE.value: _SELF_CARE,
}


def core_sentence(card_id: str, topic: TarotContext | str, core: str) -> str:
    """The card's core for ``topic`` as a complete clause (no final stop): the overlay when
    there is one, otherwise the authored core, which already reads as a clause."""

    key = topic.value if isinstance(topic, TarotContext) else topic
    return CORE_SENTENCES.get(key, {}).get(card_id, core)


def capitalized(text: str) -> str:
    return text[:1].upper() + text[1:]


def contains_clause(prose: str, clause: str) -> bool:
    """``clause`` appears in ``prose`` as written or with its first letter capitalized (it may
    open a sentence)."""

    return clause in prose or capitalized(clause) in prose
