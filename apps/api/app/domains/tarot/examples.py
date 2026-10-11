"""Original hypothetical examples; never events inferred about the reader."""

from app.domains.tarot.relationship_readings import RELATIONSHIP_EXAMPLES

CARD_EXAMPLES: dict[str, str] = {
    "major-fool": "Bạn muốn thử một hoạt động mới nhưng cứ đợi đến khi mình biết hết mọi thứ.",
    "major-magician": (
        "Bạn đã biết làm bản thử, nhưng dành cả buổi chọn tên và màu thay vì bắt đầu."
    ),
    "major-high-priestess": (
        "Bạn thấy một câu trả lời hơi lạ và nghĩ ngay người kia có chuyện giấu mình."
    ),
    "major-empress": (
        "Bạn giúp người khác chuẩn bị mọi thứ, còn việc ăn uống và nghỉ của mình thì để sau."
    ),
    "major-emperor": (
        "Cả nhóm làm cùng một việc nhưng chưa ai nói rõ ai phụ trách và khi nào cần xong."
    ),
    "major-hierophant": (
        "Bạn làm theo cách quen của gia đình dù chưa biết cách ấy còn phù hợp với mình không."
    ),
    "major-lovers": (
        "Bạn thích một lựa chọn, nhưng nhận ra nó đòi mình chấp nhận điều mình không muốn."
    ),
    "major-chariot": "Bạn rất muốn việc tiến nhanh nên chốt luôn lịch mà chưa hỏi người cùng làm.",
    "major-strength": (
        "Bạn đang bực và đã soạn một câu khá gắt, nhưng vẫn có thể chọn chưa gửi ngay."
    ),
    "major-hermit": (
        "Bạn muốn nghĩ cho rõ nên chưa trả lời tin nhắn, nhưng chưa báo người kia mình cần "
        "thời gian."
    ),
    "major-wheel-of-fortune": (
        "Lịch bỗng đổi vì một việc ngoài dự tính, trong khi bạn đã chuẩn bị cho kế hoạch cũ."
    ),
    "major-justice": (
        "Bạn nhớ mình đã cố nhiều, nhưng cuộc trao đổi còn có một phần trách nhiệm mình chưa nhận."
    ),
    "major-hanged-man": (
        "Bạn đã thử cùng một cách nhiều lần mà không được, nhưng chưa hỏi có cách khác không."
    ),
    "major-death": (
        "Một kế hoạch đã kết thúc, nhưng bạn vẫn giữ lịch và thói quen như thể nó còn tiếp tục."
    ),
    "major-temperance": (
        "Bạn vừa muốn làm cho xong, vừa đang thiếu sức; chọn ít việc hơn có thể hợp lý lúc này."
    ),
    "major-devil": (
        "Bạn không còn thích một thói quen, nhưng vẫn làm tiếp vì ngại cảm giác khó chịu khi dừng."
    ),
    "major-tower": (
        "Bạn biết một thông tin mới khiến kế hoạch cũ không còn dùng được và cần xem lại từ đầu."
    ),
    "major-star": (
        "Sau một lần thất vọng, bạn vẫn thấy có một việc nhỏ mình muốn thử lại mà chưa cần hứa gì."
    ),
    "major-moon": (
        "Người kia trả lời ngắn hơn thường lệ, nhưng bạn chưa biết họ bận hay đang không vui."
    ),
    "major-sun": (
        "Một việc đã làm được khiến bạn vui, rồi bạn lại thấy ngại khi người khác khen mình."
    ),
    "major-judgement": (
        "Bạn nhận ra mình cứ gặp một kiểu rắc rối và muốn xem lần này mình có thể làm khác gì."
    ),
    "major-world": (
        "Bạn đã xong một chặng việc, nhưng chưa dừng để nhìn lại điều đã học và điều còn muốn làm."
    ),
    "cups-ace": (
        "Bạn thấy vui khi nói chuyện với một người mới, nhưng chưa biết cả hai muốn tìm hiểu "
        "đến đâu."
    ),
    "cups-2": (
        "Hai người đều chủ động hỏi han và nhớ điều người kia đã kể, không chỉ một bên cố "
        "bắt chuyện."
    ),
    "cups-3": (
        "Bạn vui khi gặp nhóm bạn, nhưng có một chuyện riêng mình chưa muốn nói trước tất cả."
    ),
    "cups-4": (
        "Bạn được rủ đi chơi nhưng chưa muốn đi, rồi lại thấy áy náy vì người rủ rất nhiệt tình."
    ),
    "cups-5": (
        "Một buổi hẹn không như mong đợi khiến bạn quên rằng vẫn có những người khác sẵn "
        "lòng gặp mình."
    ),
    "cups-6": (
        "Bạn nhớ một người cũ qua một bài hát, rồi chỉ nhớ lúc vui mà quên những lần không "
        "hiểu nhau."
    ),
    "cups-7": (
        "Bạn có nhiều kế hoạch hấp dẫn, nhưng chưa xem mình có đủ thời gian và nguồn lực cho "
        "kế hoạch nào."
    ),
    "cups-8": (
        "Bạn vẫn tham gia một việc quen, nhưng lần nào xong cũng thấy mình không còn muốn làm tiếp."
    ),
    "cups-9": (
        "Bạn muốn dành buổi tối cho một việc mình thích, nhưng cứ đợi xem người khác có cho "
        "là đáng không."
    ),
    "cups-10": (
        "Mọi người trông có vẻ hòa thuận, nhưng bạn vẫn chưa nói điều mình cần để sống cùng "
        "thoải mái hơn."
    ),
    "cups-page": (
        "Bạn muốn nhắn một lời quan tâm, rồi sửa đi sửa lại vì sợ người kia nghĩ mình thích họ quá."
    ),
    "cups-knight": (
        "Bạn muốn rủ một người đi chơi và đang hào hứng nói đến nhiều kế hoạch mình chưa "
        "chắc sắp xếp được."
    ),
    "cups-queen": (
        "Một người kể chuyện buồn, bạn lập tức tìm cách giúp dù họ có thể chỉ đang cần được nghe."
    ),
    "cups-king": (
        "Bạn nói mình không sao trong một cuộc trao đổi quan trọng, dù thật ra có điều khiến "
        "mình buồn."
    ),
    "wands-ace": (
        "Một ý tưởng làm bạn hào hứng đến mức muốn nhận thêm việc ngay trước khi thử xem nó "
        "có phù hợp không."
    ),
    "wands-2": (
        "Bạn đã có bản kế hoạch khá rõ, nhưng chưa chọn được việc đầu tiên mình sẽ làm trong "
        "tuần này."
    ),
    "wands-3": (
        "Bạn đã gửi một đề xuất và đang chờ phản hồi, nhưng hai bên chưa hẹn lúc nào sẽ nói tiếp."
    ),
    "wands-4": (
        "Nhóm vừa hoàn thành một việc khó, nhưng cuộc trò chuyện lập tức chuyển sang việc "
        "tiếp theo."
    ),
    "wands-5": (
        "Trong cuộc trao đổi, ai cũng có ý kiến và nói cùng lúc nên vấn đề chính vẫn chưa "
        "được giải quyết."
    ),
    "wands-6": (
        "Bạn làm tốt một phần việc, nhưng thấy hụt hẫng chỉ vì chưa ai nhắc tới công sức ấy."
    ),
    "wands-7": (
        "Có người hỏi lý do lựa chọn của bạn, và bạn nghe câu hỏi như thể họ đang phủ nhận mình."
    ),
    "wands-8": "Nhiều tin nhắn đến cùng lúc khiến bạn nhận lời nhanh trước khi đọc hết yêu cầu.",
    "wands-9": (
        "Bạn đã cố nhiều ngày và khá mệt, nhưng vẫn muốn nhận thêm để không bị xem là thiếu "
        "cố gắng."
    ),
    "wands-10": (
        "Bạn đang giữ cả việc của mình lẫn phần người khác bỏ sót, trong khi thời hạn vẫn như cũ."
    ),
    "wands-page": (
        "Bạn muốn thử một sở thích mới nhưng dành nhiều thời gian kể về nó hơn là làm lần đầu."
    ),
    "wands-knight": (
        "Bạn muốn chốt một kế hoạch ngay, còn người cùng làm vẫn đang hỏi những điều cần "
        "biết trước."
    ),
    "wands-queen": (
        "Bạn có một ý tưởng muốn chia sẻ, rồi ngại vì thấy người khác nói chuyện tự tin hơn mình."
    ),
    "wands-king": (
        "Bạn nhìn rõ hướng muốn đi, nhưng chưa hỏi người cùng làm có thời gian và muốn nhận "
        "phần nào."
    ),
    "swords-ace": (
        "Bạn hỏi thẳng một câu và nhận ra điều gây hiểu nhầm trước đó chỉ là thiếu một thông tin."
    ),
    "swords-2": "Bạn cứ hoãn chọn giữa hai cách vì cả hai đều có điểm khó chấp nhận.",
    "swords-3": (
        "Một câu nói làm bạn buồn, nhưng bạn chưa kể rõ câu nào và vì sao nó khiến mình đau."
    ),
    "swords-4": (
        "Bạn đã nghĩ về một việc cả ngày mà chưa rõ hơn; đầu đang mệt nhưng vẫn cố tìm thêm "
        "câu trả lời."
    ),
    "swords-5": (
        "Bạn có thể đáp lại để thắng một cuộc tranh luận, nhưng biết câu ấy sẽ làm cuộc nói "
        "chuyện khó tiếp tục."
    ),
    "swords-6": "Bạn đang thử một cách làm bớt căng hơn, dù vẫn còn lưu luyến cách cũ đã quen.",
    "swords-7": (
        "Bạn chưa muốn nói hết một chuyện vì ngại bị hỏi thêm, nhưng người liên quan đang "
        "cần biết phần quan trọng."
    ),
    "swords-8": (
        "Bạn nghĩ mình không có lựa chọn, rồi nhận ra chưa từng hỏi xem thời hạn có thể đổi không."
    ),
    "swords-9": (
        "Bạn đọc lại một tin nhắn nhiều lần vào tối muộn và càng nghĩ càng thấy những khả "
        "năng đáng lo."
    ),
    "swords-10": (
        "Một việc đã không thể tiếp tục như cũ, nhưng bạn vẫn cố thêm chỉ vì đã bỏ quá nhiều công."
    ),
    "swords-page": (
        "Bạn muốn hỏi cho rõ nhưng hỏi liên tiếp nhiều câu, khiến người kia có cảm giác bị "
        "kiểm tra."
    ),
    "swords-knight": (
        "Bạn thấy một điểm sai và nói ngay, trước khi nghe hết lý do người kia đưa ra."
    ),
    "swords-queen": (
        "Bạn biết mình không muốn nhận thêm, nhưng đang tìm cách nói rõ mà không phải xin "
        "lỗi quá nhiều."
    ),
    "swords-king": (
        "Cả nhóm cần một quyết định rõ, nhưng vẫn chưa thống nhất sẽ dựa vào thông tin nào để chọn."
    ),
    "pentacles-ace": (
        "Bạn có cơ hội thử một việc thật, nhưng cần xem lịch và nguồn lực trước khi nhận lời."
    ),
    "pentacles-2": "Bạn đổi qua lại giữa hai việc cả buổi, nhưng chưa chọn việc nào cần làm trước.",
    "pentacles-3": (
        "Mỗi người đều cố làm tốt phần mình, nhưng chưa hỏi sản phẩm chung cần đạt điều gì."
    ),
    "pentacles-4": "Bạn giữ một cách làm quen vì thấy an toàn, dù có một thay đổi nhỏ đáng thử.",
    "pentacles-5": "Bạn đang thiếu sức hoặc thiếu người giúp, nhưng chưa nói ra vì sợ làm phiền.",
    "pentacles-6": (
        "Bạn thường là người sắp xếp và giúp đỡ, rồi thấy buồn khi không nhận lại sự quan "
        "tâm tương tự."
    ),
    "pentacles-7": (
        "Bạn đã bỏ công một thời gian nhưng chưa xem kết quả có đủ để tiếp tục theo cách cũ không."
    ),
    "pentacles-8": (
        "Bạn đang luyện một kỹ năng và sửa từng lỗi nhỏ, dù kết quả chưa đủ nổi bật để được khen."
    ),
    "pentacles-9": (
        "Bạn đã tự lo được một phần cuộc sống, nhưng thấy ngại khi dành thời gian tận hưởng "
        "điều mình làm được."
    ),
    "pentacles-10": (
        "Một lựa chọn ảnh hưởng cả sinh hoạt lâu dài, nên bạn cần nghe thêm ý kiến người "
        "cùng chịu trách nhiệm."
    ),
    "pentacles-page": (
        "Bạn muốn học một việc mới và đang tìm bài tập đầu tiên vừa sức, thay vì chỉ xem "
        "người khác làm."
    ),
    "pentacles-knight": (
        "Bạn giữ lịch làm đều đặn, nhưng cần xem cách làm ấy còn có ích hay chỉ đang thành "
        "thói quen."
    ),
    "pentacles-queen": (
        "Bạn lo để mọi người có đủ điều cần dùng, nhưng phần thời gian nghỉ của mình lại "
        "thường bị cắt."
    ),
    "pentacles-king": (
        "Bạn có nguồn lực để giúp một kế hoạch đi tiếp, nhưng chưa nói rõ mức đóng góp mình "
        "thấy thoải mái."
    ),
}

CONTEXT_EXAMPLES: dict[tuple[str, str], str] = {
    ("cups-king", "work"): (
        "Bạn không đồng ý với cách chia việc trong nhóm, nhưng cứ nói mình ổn để tránh căng thẳng."
    ),
    ("cups-queen", "work"): (
        "Một đồng nghiệp đang quá tải, bạn nhận luôn việc của họ dù lịch của mình cũng đã kín."
    ),
    ("cups-2", "work"): (
        "Hai người cùng làm một việc và đều hỏi phần mình có thể hỗ trợ, thay vì chờ người "
        "kia tự xoay xở."
    ),
}


def example_for(card_id: str, context: str) -> str:
    example = (
        RELATIONSHIP_EXAMPLES[card_id]
        if context == "relationships"
        else CONTEXT_EXAMPLES.get((card_id, context), CARD_EXAMPLES[card_id])
    )
    return "Ví dụ: Có lần " + example[:1].lower() + example[1:]
