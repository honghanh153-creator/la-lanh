"""The 120 planet-by-house cells (Daily v2 plan, section 1.1, rules N-2…N-5 and A-6).

DRAFT FOR OWNER APPROVAL (C3a-2). Not wired into any reading yet.

A cell is a kind of energy (the planet) meeting an area of life (the house), written as an
invitation, never as a forecast. Each cell has:

* ``theme``: one plain sentence;
* ``ways``: three or four ways it often shows up ("many doors", rule N-3). Every way is drawn
  from one meaning of that house in ``house_meanings.HOUSE_MEANINGS`` and carries that meaning's
  key, so the source of every door is traceable;
* ``suggestion``: one "Nếu…, thì…" sentence.

Rules the data keeps (checked in ``tests/readings/test_planet_house_cells.py``):

* The first way comes from a meaning a classical source stands behind (Lilly, BPHS or
  Phaladeepika) and is never ⚠. A MODERN-only meaning is only ever a later door ("source rule
  outranks N-4").
* A ⚠ meaning is never first and never alone: a cell that uses one has at least three ways and
  at least two that are not ⚠. Meanings that must never reach a daily reading are not used.
* Fast planets (Moon, Sun, Mercury, Venus, Mars) speak only of mood and small things: no ⚠
  meaning and no life theme (children, marriage, moving home, changing jobs…). Life themes only
  come from Jupiter outward (N-5), and only as one door.
* Saturn or Mars with house 5 never mention children (A-6). This draft goes further: children
  appear only with Jupiter in house 5, the plan's own example.
* No sentence predicts an event, assumes the reader's situation (single, partnered, has
  children, gender) or names a house, sign, planet or aspect.

How long a planet stays is not written into the sentences; the reading that uses a cell adds the
time words ("hôm nay", "mấy tuần này", "giai đoạn này").
"""

from __future__ import annotations

from dataclasses import dataclass

PLANET_HOUSE_CELLS_VERSION = "planet-house-cells-2026-11-04-draft1"

PLANETS: tuple[str, ...] = (
    "moon",
    "sun",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
)
# N-5: these change house within days or weeks; they speak of mood and small things only.
FAST_PLANETS = frozenset({"moon", "sun", "mercury", "venus", "mars"})
SLOW_PLANETS = frozenset(PLANETS) - FAST_PLANETS


@dataclass(frozen=True)
class Way:
    """One door of a cell: the plain words and the house meaning they come from."""

    meaning: str
    text: str


@dataclass(frozen=True)
class PlanetHouseCell:
    planet: str
    house: int
    theme: str
    ways: tuple[Way, ...]
    suggestion: str

    @property
    def sources(self) -> tuple[str, ...]:
        """Keys of the house meanings this cell uses, in the order the reader meets them."""

        return tuple(dict.fromkeys(way.meaning for way in self.ways))

    def sentences(self) -> tuple[str, ...]:
        return (self.theme, *(way.text for way in self.ways), self.suggestion)


_RAW: dict[str, dict[int, tuple[str, tuple[tuple[str, str], ...], str]]] = {
    "moon": {
        1: (
            "Cảm xúc hiện rõ trên nét mặt, vui buồn gì cũng khó giấu.",
            (
                ("temperament", "phản ứng theo cảm xúc nhanh hơn thường lệ"),
                ("body_appearance", "muốn chăm cho vẻ ngoài một chút"),
                ("vitality", "sức lực lên xuống theo tâm trạng"),
                ("inner_joy_sorrow", "một chuyện nhỏ cũng làm lòng vui hay chùng xuống"),
            ),
            "Nếu thấy mình nhạy hơn mọi khi, thì cho mình thêm một khoảng nghỉ giữa các việc.",
        ),
        2: (
            "Lòng yên hơn khi thấy mình có đủ những thứ cần dùng.",
            (
                ("money_wealth", "để ý từng khoản chi nhỏ trong ngày"),
                ("family_table", "thèm một bữa cơm ấm cúng"),
                ("belongings", "muốn sắp lại đồ đạc cho gọn"),
                ("self_worth", "cần nghe một lời ghi nhận"),
            ),
            "Nếu thấy lòng bồn chồn, thì nấu một món quen hoặc lau lại một món đồ mình quý.",
        ),
        3: (
            "Đầu óc muốn trò chuyện, muốn hỏi han và nghe ngóng.",
            (
                ("messages_news", "tin nhắn qua lại nhiều hơn mọi ngày"),
                ("neighbours_kin", "vài câu chào hỏi với hàng xóm"),
                ("short_trips", "một quãng đi bộ hay chạy việc gần nhà"),
                ("everyday_learning", "đọc vài trang sách cho vui"),
            ),
            "Nếu muốn nói chuyện, thì nhắn hỏi thăm một người lâu rồi chưa liên lạc.",
        ),
        4: (
            "Lòng muốn ở gần những gì quen thuộc và ấm áp.",
            (
                ("home_dwelling", "muốn ở nhà, dọn một góc cho gọn"),
                ("home_contentment", "một buổi tối yên ả trong nhà"),
                ("roots", "nhớ món ăn hay mùi vị ngày nhỏ"),
                ("how_things_close", "muốn khép lại một việc còn dở"),
            ),
            "Nếu thấy mệt, thì về sớm một chút và pha cho mình một cốc trà ấm.",
        ),
        5: (
            "Lòng muốn chơi và muốn làm gì đó bằng tay.",
            (
                ("pleasure_feasts", "một buổi ăn uống vui với người quen"),
                ("creativity", "vẽ vời, hát hò, nấu một món mới"),
                ("sport_play", "một trò chơi nhỏ cho đầu óc nhẹ đi"),
                ("learning_intelligence", "tò mò học một điều lạ"),
            ),
            "Nếu có mười lăm phút rảnh, thì dành nó cho một việc chỉ để vui.",
        ),
        6: (
            "Cảm xúc gắn với những việc nhỏ trong ngày.",
            (
                ("small_animals", "thấy dịu lại khi ở cạnh một con vật nhỏ"),
                ("daily_work", "muốn làm xong từng việc vặt cho nhẹ đầu"),
                ("body_care_habits", "để ý hơn tới giấc ngủ và bữa ăn"),
                ("helpers", "cảm kích một người giúp mình việc lặt vặt"),
            ),
            "Nếu thấy rối, thì viết ra ba việc nhỏ và làm xong việc nhẹ nhất trước.",
        ),
        7: (
            "Lòng hướng về người khác, muốn có ai đó cùng chia sẻ.",
            (
                ("love", "muốn ở gần người mình thương hơn"),
                ("business_partners", "làm việc thấy hợp hơn khi có người cùng làm"),
                ("agreements", "muốn hai bên nói rõ điều mình mong"),
                ("open_opponents", "một câu nói thẳng làm lòng gợn lên"),
            ),
            "Nếu thấy chạnh lòng vì một người, thì nói ra điều mình cần bằng một câu nhẹ nhàng.",
        ),
        8: (
            "Cảm xúc đi sâu hơn, những điều thường giấu kín muốn nổi lên.",
            (
                ("deep_fears", "một nỗi lo cũ quay lại trong đầu"),
                ("shared_money", "để ý tới khoản tiền chung với người khác"),
                ("intimacy", "muốn được tin cậy và gần gũi thật lòng"),
                ("inner_change", "muốn buông một thói quen cảm xúc cũ"),
            ),
            "Nếu lòng thấy nặng, thì viết điều đang lo ra giấy rồi đặt nó sang một bên.",
        ),
        9: (
            "Lòng muốn đi xa một chút, dù chỉ trong ý nghĩ.",
            (
                ("long_journeys", "mơ về một chuyến đi tới nơi lạ"),
                ("higher_learning", "muốn đọc một cuốn sách mở rộng tầm nhìn"),
                ("dreams", "giấc mơ đêm rõ hơn thường ngày"),
                ("faith", "thấy yên khi nghĩ về điều mình tin"),
            ),
            "Nếu thấy ngột ngạt, thì đổi đường đi quen hoặc ghé một chỗ chưa từng tới.",
        ),
        10: (
            "Cảm xúc hiện ra cả ở nơi đông người, chỗ mình làm việc hay học tập.",
            (
                ("reputation", "để tâm hơn tới cách người khác nhìn mình"),
                ("career", "muốn việc mình làm được thấy và ghi nhận"),
                ("authority", "nhạy hơn với lời nói của người có tiếng nói"),
            ),
            "Nếu một lời góp ý làm bạn chùng xuống, thì đợi qua một đêm rồi hãy trả lời.",
        ),
        11: (
            "Lòng muốn ở giữa bạn bè, nơi mình được là chính mình.",
            (
                ("friends", "nhớ một người bạn và muốn gặp"),
                ("trust", "cần một chỗ dựa để kể chuyện"),
                ("groups", "thấy vui khi được góp mặt trong một nhóm"),
                ("hopes_wishes", "một mong ước nhỏ trở lại trong đầu"),
            ),
            "Nếu thấy cô đơn, thì gửi một tin nhắn ngắn cho người bạn mình tin.",
        ),
        12: (
            "Lòng cần yên tĩnh, muốn rút vào trong một chút.",
            (
                ("rest_sleep", "buồn ngủ sớm, muốn đi nằm hơn đi chơi"),
                ("solitude", "thích ở một mình hơn thường ngày"),
                ("quiet_sorrow", "một nỗi buồn nhỏ không rõ từ đâu"),
                ("spiritual_life", "muốn ngồi lặng một lúc, thở chậm lại"),
            ),
            "Nếu lòng chùng xuống mà không rõ vì sao, thì cho mình ngủ sớm hơn mọi hôm.",
        ),
    },
    "sun": {
        1: (
            "Bạn muốn được là mình rõ hơn, và để người khác thấy điều đó.",
            (
                ("temperament", "dám nói ý mình hơn thường lệ"),
                ("vitality", "sức lực khá dồi dào"),
                ("body_appearance", "muốn đổi kiểu tóc hay cách ăn mặc"),
                ("new_beginnings", "hăng hái bắt đầu một việc nhỏ cho riêng mình"),
            ),
            "Nếu có một việc bạn muốn tự làm theo ý mình, thì đây là lúc bắt tay vào.",
        ),
        2: (
            "Sự chú ý dồn về những gì mình có và cách mình tự lo cho mình.",
            (
                ("money_wealth", "nghĩ nhiều về chuyện thu chi"),
                ("gain_loss", "cân nhắc kỹ trước một khoản chi"),
                ("self_worth", "muốn thấy công sức mình được trả đúng"),
                ("precious_things", "để mắt tới một món đồ quý"),
            ),
            (
                "Nếu muốn yên tâm hơn, "
                "thì ghi lại các khoản chi trong một tuần để thấy mình đang ở đâu."
            ),
        ),
        3: (
            "Đầu óc sáng ra, muốn hỏi, muốn học và muốn nói.",
            (
                ("everyday_learning", "thích học thêm một kỹ năng nhỏ"),
                ("messages_news", "trao đổi nhiều qua tin nhắn và thư"),
                ("siblings", "chuyện trò nhiều hơn với anh chị em"),
                ("short_trips", "vài chuyến đi ngắn quanh nơi mình sống"),
            ),
            "Nếu có điều muốn biết, thì ghi câu hỏi ra rồi hỏi người hiểu chuyện.",
        ),
        4: (
            "Sự chú ý quay về nhà, về chỗ mình thuộc về.",
            (
                ("home_dwelling", "muốn sửa sang hay sắp lại chỗ ở"),
                ("home_contentment", "thích ở nhà hơn ra ngoài"),
                ("roots", "nghĩ về nơi mình lớn lên"),
                ("how_things_close", "muốn làm cho xong một việc kéo dài"),
            ),
            "Nếu nhà có một góc làm bạn khó chịu, thì dọn nó trong cuối tuần này.",
        ),
        5: (
            "Bạn muốn được vui và được thể hiện mình.",
            (
                ("pleasure_feasts", "hứng thú với những buổi vui chơi, tụ tập"),
                ("creativity", "muốn làm ra một thứ mang dấu ấn riêng"),
                ("sport_play", "thích vận động hay chơi một môn thể thao"),
                ("romance", "lòng dễ rung trước một người"),
            ),
            "Nếu có một sở thích đang bỏ dở, thì dành cho nó một buổi trong tuần.",
        ),
        6: (
            "Sức lực dồn vào việc hằng ngày và cách mình chăm cơ thể.",
            (
                ("helpers", "cần tới người giúp một tay cho việc nhà, việc vặt"),
                ("daily_work", "muốn làm việc gọn gàng, đúng giờ hơn"),
                ("body_care_habits", "muốn sửa một thói quen ăn ngủ"),
                ("service", "thấy vui khi giúp được ai đó"),
            ),
            "Nếu muốn đổi một thói quen, thì chọn một việc nhỏ và giữ nó trong bảy ngày.",
        ),
        7: (
            "Sự chú ý dồn vào những người đi cùng mình.",
            (
                ("business_partners", "làm việc theo cặp, cần người cùng gánh"),
                ("love", "muốn dành thời gian cho người mình thương"),
                ("agreements", "muốn hai bên thống nhất rõ hơn"),
                ("open_opponents", "thấy rõ hơn ai không cùng ý với mình"),
            ),
            "Nếu đang làm chung với ai đó, thì hỏi người ấy cần gì ở bạn.",
        ),
        8: (
            "Bạn muốn nhìn thẳng vào điều sâu kín hơn trong lòng.",
            (
                ("deep_fears", "gọi tên được một nỗi sợ lâu nay"),
                ("shared_money", "sắp lại chuyện tiền chung cho rõ"),
                ("inner_change", "muốn đổi một điều từ bên trong"),
                ("intimacy", "cần sự tin cậy hơn là lời nói xã giao"),
            ),
            "Nếu có một chuyện bạn hay né, thì thử nghĩ về nó mười phút khi lòng đang yên.",
        ),
        9: (
            "Tầm mắt muốn mở rộng, ra khỏi những gì quen thuộc.",
            (
                ("higher_learning", "muốn học một điều sâu hơn, một khóa học mới"),
                ("long_journeys", "lên kế hoạch cho một chuyến đi xa"),
                ("faith", "nghĩ nhiều về điều mình tin"),
                ("life_philosophy", "muốn hiểu vì sao mình sống như hiện nay"),
            ),
            "Nếu thấy mọi thứ quá quen, thì đọc hay xem một thứ về một nơi bạn chưa biết.",
        ),
        10: (
            "Việc bạn làm muốn được nhìn thấy.",
            (
                ("reputation", "để tâm tới tiếng nói và hình ảnh của mình"),
                ("career", "muốn đẩy việc chính lên một bước"),
                ("authority", "có dịp trao đổi với người có quyền quyết định"),
            ),
            "Nếu có một việc làm tốt mà chưa ai biết, thì nói về nó một cách đơn giản.",
        ),
        11: (
            "Bạn muốn tỏa sáng cùng bạn bè và những người cùng chí hướng.",
            (
                ("friends", "dành thời gian gặp bạn bè"),
                ("hopes_wishes", "nghĩ lại một mong ước còn để đó"),
                ("groups", "góp sức vào một nhóm hay một việc chung"),
                ("gains_income", "nghĩ cách có thêm một nguồn thu nhỏ"),
            ),
            "Nếu có một mong ước, thì kể nó với một người bạn để nó rõ ràng hơn.",
        ),
        12: (
            "Sức lực hướng vào trong, cần nghỉ để nạp lại.",
            (
                ("rest_sleep", "cần ngủ nhiều hơn mọi khi"),
                ("expenses", "để ý những khoản tiền lặng lẽ đi ra"),
                ("solitude", "thích làm việc một mình, ít ồn ào"),
                ("spiritual_life", "muốn có thời gian tĩnh tâm"),
            ),
            "Nếu thấy mình hụt sức, thì bớt một cuộc hẹn để có một buổi tối cho riêng mình.",
        ),
    },
    "mercury": {
        1: (
            "Đầu óc nhanh nhạy, muốn nói ra điều mình nghĩ.",
            (
                ("mind_intellect", "suy nghĩ chạy nhanh hơn thường ngày"),
                ("temperament", "nói nhiều hơn và hay đùa hơn"),
                ("new_beginnings", "nhiều ý tưởng cho việc mới"),
                ("body_appearance", "muốn chỉnh lại cách mình trình bày, ăn mặc"),
            ),
            "Nếu ý nghĩ chạy nhanh quá, thì ghi vội vào sổ rồi chọn một ý để làm.",
        ),
        2: (
            "Đầu óc bận tính toán chuyện tiền và đồ dùng.",
            (
                ("gain_loss", "so giá, tính toán trước khi mua"),
                ("money_wealth", "muốn ghi sổ thu chi cho rõ"),
                ("belongings", "sắp xếp hay bán bớt đồ không dùng"),
                ("self_worth", "nghĩ về giá trị công sức của mình"),
            ),
            "Nếu định mua một món lớn, thì đợi hai ngày rồi hẵng quyết.",
        ),
        3: (
            "Tin nhắn, câu chuyện và việc vặt kéo đến nhiều.",
            (
                ("messages_news", "điện thoại báo tin liên tục"),
                ("short_trips", "chạy qua chạy lại vài việc gần"),
                ("everyday_learning", "học nhanh một điều mới"),
                ("neighbours_kin", "trò chuyện với hàng xóm, họ hàng gần"),
            ),
            "Nếu tin nhắn dồn tới, thì trả lời theo từng đợt thay vì giữ máy cả ngày.",
        ),
        4: (
            "Suy nghĩ quay về nhà và chuyện trong nhà.",
            (
                ("home_dwelling", "lên danh sách việc cần sửa trong nhà"),
                ("how_things_close", "nghĩ cách khép lại một việc dở dang"),
                ("roots", "nhắc lại chuyện cũ của gia đình"),
                ("vehicles", "lo sửa sang chiếc xe hay đồ đi lại"),
            ),
            "Nếu nhà có việc cần bàn, thì nói ngắn gọn từng việc một.",
        ),
        5: (
            "Đầu óc thích chơi chữ, chơi trò và nghĩ ra điều mới.",
            (
                ("learning_intelligence", "thích đố vui, giải câu đố"),
                ("pleasure_feasts", "những cuộc nói chuyện vui bên bàn ăn"),
                ("creativity", "viết vài dòng, vẽ phác một ý"),
                ("sport_play", "rủ nhau chơi một trò cần suy nghĩ"),
            ),
            "Nếu có một ý tưởng vui, thì ghi lại ngay khi nó còn mới.",
        ),
        6: (
            "Đầu óc giỏi sắp xếp việc nhỏ hằng ngày.",
            (
                ("helpers", "dặn dò, trao đổi với người phụ mình một tay"),
                ("daily_work", "lập danh sách và gạch dần từng việc"),
                ("body_care_habits", "đọc về cách ăn uống, ngủ nghỉ"),
                ("small_animals", "tìm hiểu cách chăm một con vật nhỏ"),
            ),
            "Nếu việc vặt chất đống, thì làm những việc dưới năm phút trước.",
        ),
        7: (
            "Những cuộc trò chuyện giữa hai người trở nên quan trọng.",
            (
                ("business_partners", "bàn bạc với người cùng làm"),
                ("love", "muốn nói chuyện lâu hơn với người mình thương"),
                ("open_opponents", "một cuộc tranh luận thẳng thắn"),
                ("agreements", "chốt lại một thỏa thuận nhỏ"),
            ),
            "Nếu sắp nói chuyện quan trọng, thì nghe hết ý người kia trước khi đáp.",
        ),
        8: (
            "Đầu óc muốn đào sâu, tìm hiểu điều nằm bên dưới.",
            (
                ("shared_money", "xem lại giấy tờ về tiền chung"),
                ("deep_fears", "tự hỏi vì sao mình lo một điều"),
                ("intimacy", "một cuộc trò chuyện thật lòng, ít người biết"),
                ("inner_change", "đọc hay nghe về cách con người thay đổi"),
            ),
            "Nếu có một câu hỏi cứ quay lại, thì viết nó ra và tìm một câu trả lời nhỏ.",
        ),
        9: (
            "Đầu óc ham học và muốn hiểu điều rộng hơn.",
            (
                ("higher_learning", "đọc sâu một chủ đề mình thích"),
                ("long_journeys", "tìm hiểu đường đi cho một chuyến xa"),
                ("faith", "trò chuyện về niềm tin và cách nghĩ"),
                ("life_philosophy", "thích những câu hỏi lớn về cuộc sống"),
            ),
            "Nếu muốn học một điều, thì chọn một cuốn sách và đọc mỗi ngày vài trang.",
        ),
        10: (
            "Lời nói và giấy tờ ở chỗ làm cần được chăm chút.",
            (
                ("career", "viết, trình bày, báo cáo việc mình làm"),
                ("authority", "trao đổi với cấp trên hay người có quyền"),
                ("reputation", "cân nhắc lời mình nói trước đông người"),
            ),
            "Nếu sắp gửi một tin quan trọng ở chỗ làm, thì đọc lại một lần trước khi bấm gửi.",
        ),
        11: (
            "Bạn bè và các nhóm trò chuyện sôi nổi hơn.",
            (
                ("friends", "nhắn tin qua lại với bạn bè"),
                ("trust", "nghe một lời khuyên từ người mình tin"),
                ("groups", "góp ý trong một nhóm chung"),
                ("hopes_wishes", "bàn về dự định với người cùng chí hướng"),
            ),
            "Nếu nhóm chung ồn ào quá, thì tắt thông báo một lúc để đầu nhẹ lại.",
        ),
        12: (
            "Suy nghĩ quay vào trong, nói ít mà nghĩ nhiều.",
            (
                ("rest_sleep", "đầu còn nghĩ ngợi khi đi ngủ"),
                ("quiet_sorrow", "một ý nghĩ buồn cứ lởn vởn"),
                ("solitude", "thích viết nhật ký hay ngồi một mình"),
                ("spiritual_life", "đọc một trang sách về tâm hồn"),
            ),
            "Nếu khó dỗ giấc, thì viết ba dòng ra giấy rồi gấp sổ lại.",
        ),
    },
    "venus": {
        1: (
            "Bạn muốn trông tươi tắn hơn và thấy thoải mái với chính mình.",
            (
                ("body_appearance", "chăm chút da, tóc, quần áo"),
                ("temperament", "cư xử mềm mỏng, dịu dàng hơn"),
                ("inner_joy_sorrow", "lòng vui vì những điều nhỏ"),
                ("vitality", "thấy khỏe khoắn khi được nghỉ ngơi đủ"),
            ),
            "Nếu muốn, thì tặng mình một món nhỏ làm mình thấy đẹp hơn.",
        ),
        2: (
            "Lòng thích những thứ đẹp, những thứ có giá trị lâu.",
            (
                ("precious_things", "để mắt tới một món đồ đẹp, đồ quý"),
                ("family_table", "một bữa ăn ngon cùng người nhà"),
                ("money_wealth", "chi tiền cho thứ làm mình vui"),
                ("self_worth", "thấy mình xứng đáng được đối xử tốt"),
            ),
            "Nếu muốn mua một món đẹp, thì chọn thứ bạn dùng được lâu.",
        ),
        3: (
            "Lời nói mềm hơn, chuyện trò nhẹ nhàng hơn.",
            (
                ("messages_news", "những tin nhắn vui, những lời khen"),
                ("siblings", "gần gũi hơn với anh chị em"),
                ("short_trips", "một chuyến đi chơi gần cho đổi gió"),
                ("ways_of_speaking", "nói khéo hơn, biết chọn lời"),
            ),
            "Nếu quý ai đó, thì nhắn cho họ một lời cảm ơn cụ thể.",
        ),
        4: (
            "Bạn muốn nhà mình đẹp và ấm hơn.",
            (
                ("home_dwelling", "mua một chậu cây hay đổi chỗ đồ đạc"),
                ("home_contentment", "những buổi tối êm ở nhà"),
                ("roots", "nhớ hương vị món ăn quen"),
            ),
            "Nếu có một góc nhà bạn thích, thì làm nó đẹp thêm bằng một thứ nhỏ.",
        ),
        5: (
            "Mắt thấy đẹp và lòng muốn vui.",
            (
                ("pleasure_feasts", "một bữa ngon, một buổi đi chơi"),
                ("creativity", "làm đẹp một thứ bằng tay mình"),
                ("romance", "tim rung trước một ánh nhìn"),
                ("sport_play", "những trò vui nhẹ nhàng với người quen"),
            ),
            "Nếu có một buổi rảnh, thì đi tới một nơi bạn thấy đẹp.",
        ),
        6: (
            "Việc hằng ngày nhẹ hơn khi có chút niềm vui đi kèm.",
            (
                ("small_animals", "vuốt ve một con vật nhỏ cho lòng dịu"),
                ("helpers", "quý người giúp mình một tay"),
                ("daily_work", "trang trí chỗ làm cho vui mắt"),
                ("body_care_habits", "chăm cơ thể nhẹ nhàng, như ngâm chân, xoa bóp"),
            ),
            "Nếu ngày dài và mệt, thì kèm vào đó một thú vui nhỏ, như một bản nhạc.",
        ),
        7: (
            "Giữa bạn và người khác, mọi chuyện êm hơn.",
            (
                ("love", "thân thiết hơn với người mình thương"),
                ("business_partners", "hợp tác vui vẻ với người cùng làm"),
                ("agreements", "hai bên nhường nhau một chút để đi tới thống nhất"),
                ("open_opponents", "làm hòa với một người từng không hợp"),
            ),
            "Nếu có một người bạn quý, thì cho họ biết điều đó bằng một việc nhỏ.",
        ),
        8: (
            "Lòng cần sự gần gũi thật, không chỉ bề ngoài.",
            (
                ("shared_money", "chia tiền bạc với người khác cho công bằng"),
                ("deep_fears", "muốn được an ủi về một nỗi lo"),
                ("intimacy", "khao khát một mối thân thiết sâu"),
                ("inner_change", "thấy mình đổi khác qua một mối quan hệ"),
            ),
            "Nếu muốn gần ai đó hơn, thì kể với họ một điều thật về mình.",
        ),
        9: (
            "Lòng thích cái đẹp ở nơi xa và ở những điều mới lạ.",
            (
                ("long_journeys", "ngắm ảnh một nơi muốn đến"),
                ("higher_learning", "học về nghệ thuật, ngôn ngữ, văn hóa"),
                ("faith", "thấy bình yên trong niềm tin của mình"),
                ("blessings", "biết ơn những điều lành đang có"),
            ),
            "Nếu chưa đi xa được, thì nấu một món ăn của một nơi bạn muốn tới.",
        ),
        10: (
            "Ở chỗ làm, sự mềm mỏng và tinh tế là thế mạnh của bạn.",
            (
                ("reputation", "được khen về cách cư xử"),
                ("career", "làm việc trong không khí vui vẻ hơn"),
                ("authority", "trò chuyện êm với cấp trên"),
            ),
            "Nếu cần nhờ một người ở chỗ làm, thì mở lời bằng một câu khen thật lòng.",
        ),
        11: (
            "Bạn bè mang lại niềm vui nhẹ nhàng.",
            (
                ("friends", "một buổi cà phê với bạn"),
                ("trust", "thấy ấm lòng vì có người để dựa"),
                ("groups", "vui khi góp mặt trong một hội nhóm"),
                ("hopes_wishes", "một mong ước nhỏ về cái đẹp"),
            ),
            "Nếu lâu rồi chưa gặp bạn, thì rủ một người đi ăn món cả hai cùng thích.",
        ),
        12: (
            "Niềm vui tìm đến trong những lúc yên lặng.",
            (
                ("rest_sleep", "một giấc ngủ ngon, một buổi sáng thong thả"),
                ("solitude", "thích tự thưởng cho mình khi ở một mình"),
                ("expenses", "chi tiêu lặng lẽ cho những thú vui riêng"),
                ("spiritual_life", "thấy bình an khi nghe nhạc, ngồi thiền"),
            ),
            "Nếu thấy cần dịu lại, thì tắt điện thoại sớm và nghe một bản nhạc êm.",
        ),
    },
    "mars": {
        1: (
            "Bạn có nhiều sức, muốn làm ngay và làm nhanh.",
            (
                ("vitality", "cơ thể muốn vận động nhiều hơn"),
                ("temperament", "nóng tính, ít kiên nhẫn hơn thường lệ"),
                ("new_beginnings", "hăng hái lao vào một việc mới"),
                ("body_appearance", "muốn rèn cho mình khỏe và gọn hơn"),
            ),
            "Nếu thấy bứt rứt, thì đi bộ nhanh hay tập một bài trước khi nói chuyện khó.",
        ),
        2: (
            "Sức lực dồn vào chuyện kiếm và giữ những gì của mình.",
            (
                ("money_wealth", "làm thêm để có thêm tiền"),
                ("gain_loss", "chi nhanh theo cảm hứng"),
                ("belongings", "muốn giữ chặt đồ của mình"),
                ("self_worth", "muốn chứng tỏ mình làm được"),
            ),
            "Nếu muốn chi một khoản vì nóng lòng, thì đợi tới hôm sau rồi quyết.",
        ),
        3: (
            "Lời nói nhanh và thẳng hơn thường ngày.",
            (
                ("messages_news", "trả lời tin nhắn ngay, ít cân nhắc"),
                ("courage", "dám nói điều mình nghĩ"),
                ("short_trips", "chạy việc liên tục, đi lại nhiều"),
                ("siblings", "tranh luận với anh chị em"),
            ),
            "Nếu một tin nhắn làm bạn bực, thì đợi mười phút rồi mới trả lời.",
        ),
        4: (
            "Sức lực dồn về nhà, muốn sửa và dọn.",
            (
                ("home_dwelling", "khuân vác, sửa sang trong nhà"),
                ("how_things_close", "dứt điểm một việc kéo dài"),
                ("vehicles", "sửa chiếc xe hay đồ đi lại"),
            ),
            "Nếu nóng lòng muốn sửa nhà, thì làm từng góc một cho khỏi mệt.",
        ),
        5: (
            "Bạn sôi nổi, muốn chơi hết mình.",
            (
                ("pleasure_feasts", "hăng hái tụ tập, vui chơi"),
                ("sport_play", "muốn thi đấu, chơi thể thao"),
                ("creativity", "lao vào một dự án mình thích"),
                ("romance", "rung động mạnh và nhanh"),
            ),
            "Nếu muốn thử sức, thì chọn một môn chơi có luật rõ để vui mà không quá sức.",
        ),
        6: (
            "Bạn muốn làm thật nhiều việc trong ngày.",
            (
                ("helpers", "sốt ruột khi người phụ mình làm chậm"),
                ("daily_work", "làm việc dồn dập, muốn xong nhanh"),
                ("body_care_habits", "muốn tập luyện đều hơn"),
                ("service", "xắn tay giúp người khác"),
            ),
            "Nếu thấy việc dồn quá, thì nghỉ năm phút sau mỗi giờ làm.",
        ),
        7: (
            "Những người quanh bạn khiến bạn muốn hành động.",
            (
                ("business_partners", "cùng người khác đẩy nhanh một việc chung"),
                ("open_opponents", "tranh cãi thẳng thắn với một người không cùng ý"),
                ("desire_passion", "đam mê, ham muốn mạnh hơn"),
                ("love", "muốn chủ động hơn với người mình thương"),
            ),
            "Nếu sắp cãi nhau, thì nói về việc, đừng nói về con người.",
        ),
        8: (
            "Sức lực đi sâu vào những điều khó nói.",
            (
                ("shared_money", "quyết liệt sắp lại chuyện tiền chung"),
                ("deep_fears", "đối mặt với một nỗi sợ"),
                ("intimacy", "khao khát gần gũi mạnh mẽ"),
                ("inner_change", "muốn cắt bỏ một thói quen cũ"),
            ),
            "Nếu có một chuyện cần nói thẳng, thì chọn lúc cả hai đều bình tĩnh.",
        ),
        9: (
            "Bạn hăng hái đi xa hơn, học nhiều hơn.",
            (
                ("long_journeys", "muốn xách ba lô lên và đi"),
                ("higher_learning", "học dồn một môn mới"),
                ("faith", "bảo vệ điều mình tin rất hăng"),
                ("life_philosophy", "tranh luận về quan điểm sống"),
            ),
            "Nếu muốn đi đâu đó, thì chọn một chuyến ngắn có kế hoạch rõ.",
        ),
        10: (
            "Bạn muốn đẩy mạnh việc đang làm và được ghi nhận.",
            (
                ("career", "làm việc hăng, nhận thêm phần khó"),
                ("authority", "va chạm với người có quyền"),
                ("reputation", "muốn chứng tỏ mình trước mọi người"),
            ),
            "Nếu bất đồng với người phụ trách, thì nói bằng số liệu và giữ giọng bình tĩnh.",
        ),
        11: (
            "Bạn hăng hái góp sức cho bạn bè và việc chung.",
            (
                ("friends", "rủ bạn bè cùng làm một việc"),
                ("trust", "thất vọng khi ai đó không giữ lời"),
                ("groups", "đứng ra dẫn dắt một nhóm"),
                ("hopes_wishes", "đẩy nhanh một mong ước"),
            ),
            "Nếu nhóm chung chậm quá, thì nhận phần việc của mình và làm xong trước.",
        ),
        12: (
            "Sức lực đi vào trong, làm việc lặng lẽ.",
            (
                ("rest_sleep", "ngủ không yên vì còn nhiều việc trong đầu"),
                ("quiet_sorrow", "giận mà không nói ra"),
                ("solitude", "thích làm việc một mình cho nhanh"),
                ("expenses", "chi tiền vội cho những việc không tính trước"),
            ),
            "Nếu có cơn giận giữ trong lòng, thì đi bộ hay viết ra để nó có chỗ thoát.",
        ),
    },
    "jupiter": {
        1: (
            "Bạn muốn lớn thêm, cởi mở và tin vào mình hơn.",
            (
                ("temperament", "rộng lượng, lạc quan hơn"),
                ("vitality", "thấy sức sống trở lại"),
                ("body_appearance", "muốn chăm cơ thể theo cách mới"),
                ("new_beginnings", "bắt đầu một hướng đi mới cho mình"),
            ),
            "Nếu có một điều bạn từng nghĩ là quá sức, thì thử bước một bước nhỏ về phía nó.",
        ),
        2: (
            "Những gì bạn có muốn được mở rộng và dùng cho tốt.",
            (
                ("money_wealth", "nghĩ về cách tăng thu nhập lâu dài"),
                ("family_table", "những bữa ăn đông vui hơn"),
                ("gain_loss", "rộng tay chi cho người khác"),
                ("self_worth", "tin hơn vào giá trị của mình"),
            ),
            "Nếu muốn rộng rãi với người khác, thì đặt trước một mức chi mà bạn thấy thoải mái.",
        ),
        3: (
            "Việc học và những cuộc trò chuyện hằng ngày mở ra thêm.",
            (
                ("everyday_learning", "học thêm một kỹ năng, một ngôn ngữ"),
                ("messages_news", "nhận nhiều tin tức và lời mời"),
                ("siblings", "gần lại với anh chị em"),
                ("short_trips", "những chuyến đi gần mà vui"),
            ),
            "Nếu có một khóa học ngắn bạn để ý, thì đăng ký thử một buổi.",
        ),
        4: (
            "Nhà và cảm giác thuộc về muốn rộng ra.",
            (
                ("home_dwelling", "muốn có chỗ ở rộng rãi hay thoáng hơn"),
                ("home_contentment", "nhà đông vui, ấm cúng hơn"),
                ("parents_home", "chuyện với cha mẹ hay người lớn trong nhà"),
                ("roots", "tìm hiểu gốc gác gia đình"),
            ),
            "Nếu muốn nhà ấm hơn, thì mời vài người thân quý tới ăn một bữa.",
        ),
        5: (
            "Điều bạn yêu muốn lớn thêm.",
            (
                ("pleasure_feasts", "một sở thích, một thú vui đang bỏ quên"),
                ("creativity", "thứ bạn tự tay làm ra"),
                ("romance", "một mối tình cảm"),
                ("children", "chuyện con cái"),
            ),
            "Nếu có một niềm vui bạn đã gác lại, thì đây là lúc mở nó ra.",
        ),
        6: (
            "Việc hằng ngày có thêm chỗ cho điều tốt.",
            (
                ("helpers", "có thêm người phụ giúp một tay"),
                ("daily_work", "công việc hằng ngày nhiều hơn, rộng hơn"),
                ("body_care_habits", "xây một thói quen tốt cho cơ thể"),
                ("service", "giúp người khác một cách rộng lượng"),
            ),
            "Nếu việc nhiều lên, thì nhận việc vừa sức thay vì nhận hết.",
        ),
        7: (
            "Những mối quan hệ giữa hai người có chỗ để lớn lên.",
            (
                ("business_partners", "một người cùng làm ăn hay cùng làm việc hợp ý"),
                ("love", "tình cảm với người mình thương rộng mở hơn"),
                ("agreements", "những thỏa thuận có lợi cho cả hai"),
                ("marriage", "một lời hứa gắn bó lâu dài"),
            ),
            "Nếu có một người bạn tin để cùng làm một việc, thì mở lời mời họ.",
        ),
        8: (
            "Bạn có dịp hiểu sâu và tin người hơn.",
            (
                ("shared_money", "chuyện tiền chung rộng rãi, rõ ràng hơn"),
                ("deep_fears", "nhìn một nỗi sợ với lòng bao dung"),
                ("intimacy", "sự gần gũi sâu sắc hơn"),
                ("inner_change", "một đổi thay bên trong làm bạn lớn hơn"),
            ),
            "Nếu có một nỗi sợ cũ, thì thử nói về nó với một người bạn tin.",
        ),
        9: (
            "Thế giới của bạn muốn rộng ra, gần cũng như xa.",
            (
                ("long_journeys", "một chuyến đi xa đáng nhớ"),
                ("higher_learning", "học cao hơn, đọc sâu hơn"),
                ("faith", "niềm tin vững thêm"),
                ("blessings", "thấy mình được nhiều điều lành"),
            ),
            "Nếu có một chuyến đi hay một khóa học bạn ấp ủ, thì bắt đầu tìm hiểu từ bây giờ.",
        ),
        10: (
            "Công việc của bạn có thêm cửa để vươn xa.",
            (
                ("career", "nghề nghiệp mở ra hướng mới"),
                ("reputation", "được biết tới nhiều hơn"),
                ("position", "nhận thêm trách nhiệm"),
                ("lifelong_goal", "nghĩ về điều muốn xây lâu dài"),
            ),
            "Nếu gặp một cơ hội đúng điều bạn muốn, thì chuẩn bị kỹ và nói ra mong muốn của mình.",
        ),
        11: (
            "Bạn bè và mong ước có thêm chỗ đứng trong đời bạn.",
            (
                ("friends", "có thêm bạn mới hợp ý"),
                ("hopes_wishes", "một mong ước lớn rõ dần"),
                ("groups", "tham gia một cộng đồng"),
                ("gains_income", "nghĩ tới một nguồn thu thêm"),
            ),
            "Nếu có điều bạn mong từ lâu, thì viết nó ra và chọn một bước làm trong tháng này.",
        ),
        12: (
            "Bạn có thêm chỗ cho nghỉ ngơi và đời sống bên trong.",
            (
                ("rest_sleep", "biết nghỉ ngơi đúng lúc hơn"),
                ("quiet_sorrow", "nhẹ dần một nỗi buồn cũ"),
                ("spiritual_life", "đời sống tâm linh sâu hơn"),
                ("solitude", "thích những khoảng lặng một mình"),
            ),
            "Nếu thấy cần dừng lại, thì cho mình một ngày không lịch hẹn.",
        ),
    },
    "saturn": {
        1: (
            "Bạn muốn nghiêm túc hơn với chính mình.",
            (
                ("temperament", "chín chắn, kiệm lời hơn"),
                ("vitality", "cần giữ sức cẩn thận hơn"),
                ("body_appearance", "muốn chăm cơ thể đều đặn, kỷ luật"),
                ("new_beginnings", "bắt đầu chậm mà chắc"),
            ),
            (
                "Nếu thấy mình gánh nhiều, "
                "thì chọn ra một việc thật quan trọng và bỏ bớt phần còn lại."
            ),
        ),
        2: (
            "Chuyện tiền bạc cần được xây chậm và chắc.",
            (
                ("money_wealth", "lập kế hoạch để dành lâu dài"),
                ("gain_loss", "cân nhắc kỹ chuyện được mất"),
                ("belongings", "giữ lại đồ thật cần, bỏ bớt đồ thừa"),
                ("self_worth", "học cách định giá công sức mình"),
            ),
            "Nếu tiền làm bạn lo, thì bắt đầu bằng một khoản để dành nhỏ mỗi tháng.",
        ),
        3: (
            "Lời nói và việc học cần sự cẩn thận.",
            (
                ("everyday_learning", "học một kỹ năng khó, từng chút một"),
                ("messages_news", "viết, trả lời cẩn thận hơn"),
                ("neighbours_kin", "giữ gìn quan hệ với hàng xóm, họ hàng gần"),
                ("siblings", "nhận thêm phần lo cho anh chị em"),
            ),
            "Nếu đang học một điều khó, thì đặt giờ cố định mỗi ngày, dù chỉ hai mươi phút.",
        ),
        4: (
            "Nhà và nền móng của bạn cần được xây lại cho vững.",
            (
                ("home_dwelling", "sửa sang chỗ ở cho bền"),
                ("how_things_close", "khép lại một chuyện cũ trong nhà"),
                ("land", "tính chuyện lâu dài về đất, về nhà"),
                ("roots", "nhìn lại nơi mình lớn lên bằng con mắt người lớn"),
            ),
            "Nếu có việc nhà cứ hoãn mãi, thì chia nó thành từng bước nhỏ, mỗi tuần một bước.",
        ),
        5: (
            "Điều bạn yêu muốn bạn nghiêm túc hơn.",
            (
                ("pleasure_feasts", "một niềm vui cần giờ cố định"),
                ("creativity", "một dự án cần kỷ luật"),
                ("romance", "một mối tình cảm cần lời hứa rõ hơn"),
                ("learning_intelligence", "một môn học cần kiên nhẫn"),
            ),
            "Nếu thấy chơi mà mệt, thì thử ít mà đều.",
        ),
        6: (
            "Việc hằng ngày cần nề nếp hơn.",
            (
                ("helpers", "sắp xếp lại việc với người phụ giúp"),
                ("daily_work", "nhận thêm trách nhiệm ở việc hằng ngày"),
                ("body_care_habits", "xây thói quen chăm cơ thể đều đặn"),
                ("service", "giúp người khác một cách bền bỉ"),
            ),
            "Nếu ngày nào cũng rối, thì giữ một giờ dậy và một giờ ngủ cố định.",
        ),
        7: (
            "Những gì bạn hứa với người khác cần rõ ràng và bền hơn.",
            (
                ("business_partners", "một mối hợp tác cần nói rõ phần việc"),
                ("agreements", "một thỏa thuận cần ghi lại cho chắc"),
                ("marriage", "một mối gắn bó cần cam kết rõ hơn"),
                ("love", "thử thách sự kiên nhẫn trong tình cảm"),
            ),
            "Nếu một mối quan hệ làm bạn mệt, thì nói rõ điều bạn làm được và chưa làm được.",
        ),
        8: (
            "Bạn được mời nhìn thẳng vào điều nặng lòng, chậm rãi.",
            (
                ("shared_money", "sắp xếp lại chuyện tiền chung cho minh bạch"),
                ("deep_fears", "đối diện một nỗi sợ lâu năm"),
                ("inner_change", "thay đổi chậm mà sâu"),
                ("intimacy", "học cách tin người từng bước"),
            ),
            "Nếu thấy nặng lòng, thì đi chậm, mỗi lần chỉ nhìn một chuyện.",
        ),
        9: (
            "Niềm tin và việc học cần được kiểm lại cho vững.",
            (
                ("higher_learning", "theo đuổi một việc học dài hơi"),
                ("faith", "tự hỏi lại điều mình tin"),
                ("long_journeys", "một chuyến đi xa cần chuẩn bị kỹ"),
                ("life_philosophy", "xây một cách nhìn đời chín chắn hơn"),
            ),
            "Nếu đang học điều gì lâu dài, thì đặt mốc nhỏ để thấy mình đi được bao xa.",
        ),
        10: (
            "Con đường nghề nghiệp cần được xây từng bậc.",
            (
                ("career", "nhận việc khó hơn, trách nhiệm hơn"),
                ("authority", "làm việc dưới một người đòi hỏi cao"),
                ("position", "giữ một vị trí cần nhiều kiên nhẫn"),
                ("lifelong_goal", "nghĩ lại điều mình muốn xây lâu dài"),
            ),
            "Nếu thấy mình đi chậm, thì ghi lại mỗi tuần một việc làm xong.",
        ),
        11: (
            "Bạn bè và mong ước được lọc lại, giữ cái bền.",
            (
                ("friends", "ít bạn hơn nhưng thân hơn"),
                ("trust", "biết rõ ai là chỗ dựa thật"),
                ("groups", "nhận trách nhiệm trong một nhóm"),
                ("hopes_wishes", "một mong ước cần nhiều năm mới thành"),
            ),
            "Nếu thấy một mối quen biết làm mình mệt, thì cho phép mình gặp ít đi.",
        ),
        12: (
            "Bạn cần thời gian lặng lẽ để sắp xếp lại bên trong.",
            (
                ("rest_sleep", "cần ngủ đủ và nghỉ đúng giờ"),
                ("quiet_sorrow", "một nỗi buồn cũ cần được nhìn nhận"),
                ("solitude", "chọn ở một mình để nghĩ cho rõ"),
                ("expenses", "giữ lại những khoản chi thật cần"),
            ),
            "Nếu ngày nào cũng ồn, thì giữ cho mình một giờ yên tĩnh trước khi ngủ.",
        ),
    },
    "uranus": {
        1: (
            "Bạn muốn sống đúng là mình, kể cả khi điều đó lạ với người khác.",
            (
                ("temperament", "muốn tự do hơn, ít theo khuôn"),
                ("mind_intellect", "nảy ra những ý nghĩ bất ngờ"),
                ("body_appearance", "đổi hẳn cách ăn mặc hay kiểu tóc"),
                ("new_beginnings", "bắt đầu điều chưa ai đoán trước"),
            ),
            "Nếu muốn đổi mới mình, thì thử một thay đổi nhỏ trước khi đổi lớn.",
        ),
        2: (
            "Cách bạn kiếm và giữ tiền muốn đổi khác.",
            (
                ("money_wealth", "tìm một cách kiếm tiền mới"),
                ("gain_loss", "thấy cần một khoản dự phòng cho điều bất ngờ"),
                ("belongings", "muốn bỏ bớt đồ để nhẹ người"),
                ("self_worth", "nhìn lại giá trị của mình theo cách mới"),
            ),
            (
                "Nếu thấy chi tiêu thất thường, "
                "thì để riêng một khoản nhỏ cho những việc không tính trước."
            ),
        ),
        3: (
            "Cách bạn nghĩ và nói muốn đổi mới.",
            (
                ("everyday_learning", "học một thứ mới lạ, khác thường"),
                ("messages_news", "tin tức bất ngờ tới dồn dập"),
                ("short_trips", "những chuyến đi gần không định trước"),
                ("ways_of_speaking", "nói thẳng ý tưởng khác người"),
            ),
            "Nếu một ý nghĩ mới đến bất chợt, thì ghi lại và để nó một tuần rồi xem lại.",
        ),
        4: (
            "Nhà và nề nếp gia đình muốn có điều mới.",
            (
                ("home_dwelling", "đổi cách bày biện, hay đổi chỗ ở"),
                ("home_contentment", "cần thêm khoảng tự do ngay trong nhà"),
                ("roots", "nhìn lại nếp nhà theo cách khác"),
                ("how_things_close", "một nếp cũ trong nhà khép lại"),
            ),
            "Nếu thấy nhà ngột ngạt, thì đổi một thứ trong cách sắp đặt trước khi tính chuyện lớn.",
        ),
        5: (
            "Niềm vui của bạn muốn đi theo lối mới.",
            (
                ("pleasure_feasts", "thử một kiểu vui chơi chưa từng thử"),
                ("creativity", "sáng tạo theo cách riêng, khác lạ"),
                ("sport_play", "mê một môn chơi mới"),
                ("romance", "rung động bất ngờ"),
            ),
            "Nếu có một sở thích lạ mà bạn tò mò, thì thử nó một lần cho biết.",
        ),
        6: (
            "Việc hằng ngày muốn thoát khỏi lối mòn.",
            (
                ("helpers", "đổi cách chia việc với người phụ giúp"),
                ("daily_work", "đổi giờ làm, đổi cách làm"),
                ("body_care_habits", "thử một cách chăm cơ thể mới"),
            ),
            "Nếu thấy ngày nào cũng như ngày nào, thì đổi thứ tự một việc quen trong buổi sáng.",
        ),
        7: (
            "Bạn cần thêm khoảng tự do ngay cả khi ở bên người khác.",
            (
                ("business_partners", "đổi cách làm việc với người cùng làm"),
                ("love", "cần khoảng riêng ngay trong tình cảm"),
                ("agreements", "viết lại một thỏa thuận cho hợp với bây giờ"),
                ("open_opponents", "một người bất ngờ phản đối"),
            ),
            "Nếu thấy bị bó buộc, thì nói rõ điều bạn cần mà không đổ lỗi.",
        ),
        8: (
            "Những điều sâu kín được nhìn theo cách mới.",
            (
                ("shared_money", "đổi cách chia tiền chung"),
                ("deep_fears", "một nỗi sợ bỗng được nhìn thấu"),
                ("inner_change", "một đổi thay bên trong đến nhanh"),
                ("intimacy", "cần sự tự do ngay cả khi thân thiết"),
            ),
            "Nếu một điều sâu trong lòng bỗng rõ ra, thì cho mình thời gian trước khi làm gì đó.",
        ),
        9: (
            "Cách bạn nhìn đời muốn mở sang hướng khác.",
            (
                ("higher_learning", "học một môn mới lạ"),
                ("long_journeys", "muốn tới một nơi rất khác nơi mình sống"),
                ("faith", "đổi khác trong điều mình tin"),
                ("life_philosophy", "tìm ra một cách nghĩ mới về cuộc sống"),
            ),
            "Nếu một ý tưởng lạ làm bạn tò mò, thì tìm đọc về nó trước khi tin hay bỏ.",
        ),
        10: (
            "Chuyện nghề nghiệp muốn rẽ sang lối riêng.",
            (
                ("career", "muốn làm việc theo cách tự do hơn"),
                ("authority", "khó chịu với cách quản lý cứng nhắc"),
                ("reputation", "được biết tới vì điều khác người"),
                ("lifelong_goal", "nghĩ lại hẳn điều mình muốn xây"),
            ),
            "Nếu muốn đổi hướng, thì thử trước bằng một việc nhỏ bên cạnh việc chính.",
        ),
        11: (
            "Bạn bè và mong ước thay đổi theo cách bất ngờ.",
            (
                ("friends", "gặp những người bạn rất khác mình"),
                ("trust", "nhìn lại ai thật sự hợp với mình"),
                ("groups", "tìm tới một nhóm mới"),
                ("hopes_wishes", "một mong ước mới thay cho mong ước cũ"),
            ),
            "Nếu thấy lạc lõng trong nhóm quen, thì thử ghé một nhóm có cùng sở thích mới.",
        ),
        12: (
            "Đời sống bên trong muốn được giải tỏa.",
            (
                ("rest_sleep", "giấc ngủ thất thường, giấc mơ lạ"),
                ("quiet_sorrow", "một nỗi buồn cũ bỗng được buông ra"),
                ("solitude", "cần ở một mình bất chợt"),
                ("spiritual_life", "tò mò về một cách tĩnh tâm mới"),
            ),
            "Nếu ngủ không đều, thì giữ cố định giờ tắt đèn trong vài tuần.",
        ),
    },
    "neptune": {
        1: (
            "Bạn mềm hơn và nhạy hơn với mọi thứ quanh mình.",
            (
                ("temperament", "hay xúc động, thương người hơn"),
                ("inner_joy_sorrow", "vui buồn lẫn vào nhau, khó gọi tên"),
                ("body_appearance", "vẻ ngoài mơ màng, dịu dàng"),
                ("vitality", "sức lực lúc lên lúc xuống"),
            ),
            "Nếu thấy mình mông lung, thì chọn một việc cụ thể để làm trong ngày.",
        ),
        2: (
            "Chuyện tiền và đồ đạc cần được nhìn cho rõ.",
            (
                ("money_wealth", "khoản thu chi mờ nhạt, khó theo dõi"),
                ("gain_loss", "dễ chi theo cảm xúc"),
                ("precious_things", "thích những món đồ đẹp mang ý nghĩa"),
                ("self_worth", "hay nghi ngờ giá trị của mình"),
            ),
            "Nếu một khoản chi nghe quá hay, thì hỏi thêm một người tỉnh táo trước khi quyết.",
        ),
        3: (
            "Lời nói và suy nghĩ thêm chất thơ.",
            (
                ("everyday_learning", "thích đọc thơ, nghe nhạc"),
                ("messages_news", "tin nhắn dễ bị hiểu lầm"),
                ("ways_of_speaking", "nói bằng hình ảnh hơn là con số"),
                ("siblings", "thương anh chị em theo cách lặng lẽ"),
            ),
            "Nếu một tin nhắn làm bạn băn khoăn, thì hỏi lại cho rõ thay vì tự đoán.",
        ),
        4: (
            "Bạn mơ về một mái nhà yên bình.",
            (
                ("home_dwelling", "muốn nhà là nơi trú ẩn"),
                ("home_contentment", "những buổi tối êm đềm, mơ màng"),
                ("roots", "nhớ nhung nơi mình lớn lên"),
                ("how_things_close", "một chuyện cũ trong nhà nhòe dần"),
            ),
            "Nếu nhà thấy bề bộn, thì giữ một góc nhỏ thật yên cho riêng mình.",
        ),
        5: (
            "Niềm vui của bạn mang màu mơ mộng.",
            (
                ("pleasure_feasts", "mê phim ảnh, âm nhạc"),
                ("learning_intelligence", "học vẽ, học đàn theo cảm hứng"),
                ("creativity", "cảm hứng nghệ thuật dồi dào"),
                ("romance", "mơ mộng về tình yêu"),
            ),
            "Nếu có cảm hứng, thì ghi lại hay vẽ ra ngay, dù chỉ vài nét.",
        ),
        6: (
            "Bạn cần thương mình hơn giữa những việc hằng ngày.",
            (
                ("helpers", "thương cảm với người phụ giúp mình"),
                ("service", "muốn giúp người khác không tính toán"),
                ("body_care_habits", "cơ thể nhạy hơn, cần ngủ nghỉ đúng giờ"),
                ("daily_work", "việc hằng ngày hay bị lẫn lộn"),
            ),
            "Nếu thấy mình giúp người quá sức, thì giữ lại một buổi trong tuần cho mình.",
        ),
        7: (
            "Bạn nhìn người khác bằng đôi mắt dịu dàng hơn.",
            (
                ("love", "mơ về một tình cảm trọn vẹn"),
                ("business_partners", "tin người cùng làm hơi nhiều"),
                ("agreements", "những lời hứa chưa rõ ràng"),
                ("desire_passion", "khao khát được thấu hiểu"),
            ),
            "Nếu thấy mình hứa vì cả nể, thì xin thêm thời gian trước khi trả lời.",
        ),
        8: (
            "Ranh giới giữa mình và người khác mờ đi.",
            (
                ("shared_money", "tiền chung cần giấy tờ rõ ràng"),
                ("deep_fears", "nỗi lo mơ hồ khó gọi tên"),
                ("intimacy", "khao khát hòa làm một với ai đó"),
                ("inner_change", "một đổi thay âm thầm bên trong"),
            ),
            "Nếu thấy mình gánh cảm xúc của người khác, thì cho mình một lúc ở riêng để lắng lại.",
        ),
        9: (
            "Bạn khao khát một điều lớn hơn để tin.",
            (
                ("faith", "tìm về đời sống tinh thần, niềm tin"),
                ("dreams", "giấc mơ rõ và nhiều ý nghĩa"),
                ("long_journeys", "mơ một chuyến đi tới nơi linh thiêng"),
                ("higher_learning", "học về tôn giáo, nghệ thuật, thơ ca"),
            ),
            "Nếu một lời dạy làm bạn say mê, thì vẫn giữ cho mình quyền hỏi lại.",
        ),
        10: (
            "Chuyện nghề nghiệp có lúc mờ, có lúc đầy cảm hứng.",
            (
                ("career", "muốn làm việc có ý nghĩa hơn là chỉ vì tiền"),
                ("reputation", "hình ảnh của mình trong mắt người khác chưa rõ"),
                ("authority", "khó đọc ý người phụ trách"),
                ("lifelong_goal", "mơ về điều muốn làm cả đời"),
            ),
            "Nếu chưa rõ mình muốn gì, thì ghi lại những việc làm bạn quên giờ giấc.",
        ),
        11: (
            "Bạn mơ về một nhóm bạn tâm giao.",
            (
                ("friends", "thương bạn bè, sẵn lòng giúp"),
                ("hopes_wishes", "mong ước đẹp mà còn xa"),
                ("groups", "gắn với một nhóm cùng lý tưởng"),
                ("trust", "tin người hơn mức cần"),
            ),
            "Nếu một mong ước còn xa, thì chọn một bước nhỏ để nó bớt mơ hồ.",
        ),
        12: (
            "Đời sống bên trong sâu và mềm hơn.",
            (
                ("rest_sleep", "cần ngủ nhiều, mơ nhiều"),
                ("spiritual_life", "tìm về thiền, cầu nguyện hay âm nhạc"),
                ("solitude", "thích những giờ lặng lẽ một mình"),
                ("quiet_sorrow", "thương cảm một nỗi buồn không tên"),
            ),
            "Nếu thấy mình chìm vào mộng tưởng, thì làm một việc bằng tay để về lại với hiện tại.",
        ),
    },
    "pluto": {
        1: (
            "Một phần trong bạn muốn đổi khác từ gốc.",
            (
                ("temperament", "mạnh mẽ, quyết liệt hơn"),
                ("vitality", "sức bền lớn hơn mình nghĩ"),
                ("body_appearance", "muốn đổi hẳn hình ảnh của mình"),
                ("inner_joy_sorrow", "cảm xúc sâu và đậm"),
            ),
            "Nếu thấy mình muốn đổi hẳn, thì bắt đầu từ một thói quen mỗi ngày.",
        ),
        2: (
            "Chuyện tiền và giá trị bản thân được nhìn tận gốc.",
            (
                ("money_wealth", "muốn tự chủ hơn về tiền bạc"),
                ("gain_loss", "nhìn kỹ chuyện được mất về tiền"),
                ("self_worth", "xây lại lòng tự trọng từ bên trong"),
                ("belongings", "dọn bỏ nhiều đồ cũ"),
            ),
            "Nếu tiền làm bạn thấy bất an, thì nhìn rõ từng khoản thay vì tránh né.",
        ),
        3: (
            "Lời nói của bạn có sức nặng hơn.",
            (
                ("messages_news", "đọc kỹ, hiểu sâu những tin mình nhận"),
                ("everyday_learning", "học sâu tới tận gốc một điều"),
                ("ways_of_speaking", "chọn lời ít mà chắc"),
                ("siblings", "nói ra một chuyện cũ với anh chị em"),
            ),
            "Nếu muốn nói một điều khó, thì viết nháp trước để giữ lời cho mềm.",
        ),
        4: (
            "Những gì nền móng nhất trong nhà muốn được làm mới.",
            (
                ("home_dwelling", "dọn dẹp, sửa sang chỗ ở từ trong ra ngoài"),
                ("how_things_close", "khép lại một chương trong nhà"),
                ("roots", "nhìn lại gốc rễ gia đình"),
                ("home_contentment", "tìm lại sự yên ổn thật trong nhà"),
            ),
            (
                "Nếu có chuyện cũ trong nhà làm bạn nặng lòng, "
                "thì viết về nó một lần cho trọn rồi cất đi."
            ),
        ),
        5: (
            "Điều bạn yêu thích có sức hút rất mạnh.",
            (
                ("pleasure_feasts", "mê một thú vui tới quên giờ"),
                ("creativity", "sáng tạo bằng cả tâm huyết"),
                ("romance", "rung động sâu và mãnh liệt"),
                ("sport_play", "chơi hết mình, muốn thắng"),
            ),
            "Nếu thấy mình mê một thứ quá, thì đặt giờ dừng để giữ niềm vui cho lâu.",
        ),
        6: (
            "Việc hằng ngày muốn được làm lại từ gốc.",
            (
                ("helpers", "đổi hẳn cách làm việc với người phụ giúp"),
                ("daily_work", "bỏ một cách làm cũ không còn hợp"),
                ("body_care_habits", "thay đổi sâu thói quen chăm cơ thể"),
                ("service", "giúp người theo cách thật lòng"),
            ),
            "Nếu một thói quen làm bạn mệt, thì thay nó bằng một việc nhỏ hơn thay vì bỏ hẳn.",
        ),
        7: (
            "Sự gắn bó với người khác trở nên sâu và mạnh.",
            (
                ("business_partners", "một mối hợp tác thay đổi tận gốc"),
                ("love", "tình cảm sâu và đậm"),
                ("open_opponents", "đối diện thẳng với một người không hợp"),
                ("desire_passion", "đam mê mãnh liệt"),
            ),
            "Nếu thấy một mối quan hệ quá sức, thì nói rõ ranh giới của mình.",
        ),
        8: (
            "Bạn được mời buông những điều cũ để nhẹ lòng.",
            (
                ("shared_money", "sắp xếp lại tiền chung tận gốc"),
                ("deep_fears", "đi thẳng vào một nỗi sợ sâu"),
                ("inner_change", "đổi thay lớn từ bên trong"),
                ("intimacy", "tin một người ở mức sâu nhất"),
            ),
            "Nếu có điều muốn buông, thì làm một việc nhỏ để đánh dấu, như dọn một ngăn kéo.",
        ),
        9: (
            "Niềm tin và cách nhìn đời được đào sâu.",
            (
                ("faith", "nhìn lại tận gốc điều mình tin"),
                ("higher_learning", "học sâu một lĩnh vực tới nơi"),
                ("life_philosophy", "đổi hẳn cách nhìn cuộc sống"),
                ("long_journeys", "một chuyến đi làm mình đổi khác"),
            ),
            "Nếu một niềm tin cũ lung lay, thì cho mình thời gian thay vì vội thay cái mới.",
        ),
        10: (
            "Vai trò của bạn ngoài xã hội muốn đổi từ gốc.",
            (
                ("career", "muốn đổi sâu cách mình làm việc"),
                ("authority", "học cách đứng vững trước người có quyền"),
                ("position", "nhận một vai trò nặng ký"),
                ("lifelong_goal", "điều muốn xây lâu dài rõ dần"),
            ),
            "Nếu thấy mình muốn đổi lớn, thì hỏi một người từng đi con đường đó rồi hẵng quyết.",
        ),
        11: (
            "Bạn muốn những tình bạn và mong ước thật sự có ý nghĩa.",
            (
                ("friends", "một tình bạn trở nên rất sâu"),
                ("trust", "học cách tin đúng người"),
                ("groups", "có tiếng nói mạnh trong một nhóm"),
                ("hopes_wishes", "một mong ước lớn đổi hướng"),
            ),
            "Nếu một nhóm làm bạn thấy mất mình, thì lùi lại một bước để nhìn rõ hơn.",
        ),
        12: (
            "Những gì nằm sâu trong lòng muốn được nhìn và buông.",
            (
                ("rest_sleep", "cần ngủ sâu để hồi lại"),
                ("quiet_sorrow", "điều đau lòng từ lâu được nhìn nhận"),
                ("solitude", "cần những lúc ở một mình thật lâu"),
                ("spiritual_life", "tìm đến sự tĩnh tâm sâu"),
            ),
            "Nếu một nỗi buồn cũ trồi lên, thì ngồi với nó một lúc và thở chậm.",
        ),
    },
}


def _build() -> dict[tuple[str, int], PlanetHouseCell]:
    cells: dict[tuple[str, int], PlanetHouseCell] = {}
    for planet in PLANETS:
        for house, (theme, ways, suggestion) in _RAW[planet].items():
            cells[(planet, house)] = PlanetHouseCell(
                planet=planet,
                house=house,
                theme=theme,
                ways=tuple(Way(meaning, text) for meaning, text in ways),
                suggestion=suggestion,
            )
    return cells


PLANET_HOUSE_CELLS: dict[tuple[str, int], PlanetHouseCell] = _build()


def cell(planet: str, house: int) -> PlanetHouseCell:
    """The cell for ``planet`` in ``house`` (1-12)."""

    try:
        return PLANET_HOUSE_CELLS[(planet, house)]
    except KeyError:
        raise KeyError(f"no cell for planet={planet!r}, house={house!r}") from None
