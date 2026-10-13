"""Read-time presentation voice for the reviewed Daily psychology matrix.

The stored revision always holds the direct wording. A voice only changes how
the same meaning is presented to its owner at read time:

* matching is by exact direct text, so stored notes need no migration;
* anything not authored here (natal readings, legacy copy) stays direct;
* a generated (Luna) revision is never voiced piecemeal: the roast voice is served
  from the deterministic baseline of the same plan, or the generated text stays
  fully direct when that baseline is unavailable (see ``voice_from_baseline``);
* issue, scene facts, action instruction, evidence, disclaimer and provenance are
  never rewritten — the roast voice only adds a frame around them;
* energy and self-care examples get the gentle frame, never the sharper jab.

Roast rules (owner decision 2026-10-11): tease the behaviour in the reading, never
the reader's identity, body, gender, family, money, intelligence or mental health.
No profanity, slurs, sexual content, fatalism, event certainty, or claims about
another person's private thoughts. Every jab is paired with the unchanged action.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domains.readings.companion import roast_companion_line
from app.domains.readings.daily_personalization import PLACEMENT_MEANINGS
from app.domains.readings.daily_psychology import (
    DAILY_ISSUES,
    DailyIssuePattern,
    split_scene_lead,
)
from app.domains.readings.models import (
    ReadingContentProjection,
    ReadingPurpose,
    ReadingRevisionSource,
    SemanticArena,
)

READING_VOICE_VERSION = "daily-roast-voice-v1"


class ReadingVoice(StrEnum):
    DIRECT = "direct"
    ROAST = "roast"


@dataclass(frozen=True)
class RoastIssueVoice:
    """Roast presentation of one Daily issue; meaning stays with the direct matrix."""

    headlines: tuple[tuple[str, str], ...]
    jab: str
    gentle_jab: str
    scene_tag: str
    action_frame: str
    gentle_action_frame: str


ROAST_ISSUES: dict[str, RoastIssueVoice] = {
    "missing-context": RoastIssueVoice(
        (
            (
                "Bạn đọc lại tin nhắn vì chưa hiểu ý.",
                "Đọc tin nhắn lần thứ năm rồi đó nha, ý vẫn chưa ra.",
            ),
            (
                "Tin nhắn ngắn, bạn lại nghĩ thêm nhiều chuyện.",
                "Tin nhắn có vài chữ, bạn tự viết thêm cả tập phim.",
            ),
            (
                "Bạn đang đoán ý từ một tin nhắn.",
                "Thám tử tin nhắn lại đang phá án một mình.",
            ),
            (
                "Một tin nhắn chưa rõ làm bạn nghĩ mãi.",
                "Một tin nhắn chưa rõ mà não đã mở 12 tab.",
            ),
            (
                "Bạn chưa rõ người kia đang hỏi điều gì.",
                "Người kia hỏi gì còn chưa rõ, bạn đã vào vai thám tử.",
            ),
            (
                "Bạn đọc được câu chữ, chưa hiểu yêu cầu.",
                "Đọc hết chữ rồi mà yêu cầu vẫn trốn đâu mất.",
            ),
        ),
        "Thôi nào thám tử, vài chữ trong tin nhắn chưa đủ dữ kiện để phá án đâu.",
        "Đoán ý qua vài chữ dễ mệt đầu lắm, mình hỏi lại cho nhẹ nha.",
        "Nghe quen không, thám tử tin nhắn?",
        "Đóng hồ sơ thám tử lại nào.",
        "Nhẹ đầu hơn bằng một bước nhỏ nha.",
    ),
    "too-many-open-loops": RoastIssueVoice(
        (
            (
                "Bạn bắt đầu nhiều việc, chưa xong việc nào.",
                "Mở màn cả chục việc, chưa việc nào tới tập cuối.",
            ),
            (
                "Bạn đổi việc liên tục, việc cũ vẫn còn.",
                "Nhảy việc nhanh như lướt story, việc cũ vẫn nằm chờ.",
            ),
            (
                "Việc đang làm dở lại bị bỏ sang bên.",
                "Việc đang làm dở lại bị cho ra rìa, tội nó ghê.",
            ),
            (
                "Bạn bận cả buổi, việc vẫn chưa xong.",
                "Bận rộn cả buổi mà việc vẫn chưa chịu xong.",
            ),
            (
                "Việc mới đến, bạn bỏ dở việc đang làm.",
                "Việc mới vừa ló mặt, việc đang làm đã bị bỏ rơi.",
            ),
            (
                "Bạn mở thêm việc khi việc cũ chưa xong.",
                "Não đang mở 12 tab mà bạn vẫn mở thêm tab mới.",
            ),
        ),
        "Plot twist: mở nhiều tab không có nghĩa là xong nhiều việc.",
        "Ôm nhiều việc cùng lúc dễ hụt sức, mình gom lại từng việc thôi.",
        "Tab nào cũng mở, tab nào cũng dở.",
        "Đóng bớt tab trong đầu nào.",
        "Từ từ thôi, mỗi lần một việc.",
    ),
    "changed-plan": RoastIssueVoice(
        (
            (
                "Một cuộc hẹn đổi giờ làm bạn phải sắp lại.",
                "Hẹn đổi giờ một cái, cả lịch của bạn phải xếp hình lại.",
            ),
            (
                "Lịch đã xếp xong, giờ hẹn lại đổi.",
                "Vừa xếp lịch gọn như chơi xếp gạch, giờ hẹn lại đổi.",
            ),
            (
                "Bạn đang phải xếp lại một cuộc hẹn.",
                "Bạn lại kiêm luôn chức thư ký xếp lịch hẹn.",
            ),
            (
                "Giờ hẹn đổi, kế hoạch của bạn cũng đổi.",
                "Giờ hẹn đổi một phát, kế hoạch của bạn đổi theo cả chùm.",
            ),
            (
                "Giờ hẹn mới chưa rõ, lịch bạn đã đổi.",
                "Giờ hẹn mới chưa chốt mà lịch bạn đã dọn sẵn rồi.",
            ),
            (
                "Bạn phải chọn lại giờ cho cuộc hẹn.",
                "Cuộc hẹn quay lại vòng chọn giờ, bạn lại phải bấm chọn.",
            ),
        ),
        "Chưa ai chốt giờ mới mà bạn đã xoay cả lịch, nhanh tay quá nha.",
        "Lịch bị xáo một chút thôi, chốt lại cho rõ là ổn.",
        "Lịch của bạn đang chơi xếp hình bất đắc dĩ.",
        "Chốt cho rõ rồi hẵng xoay lịch nào.",
        "Mình chốt lại từng bước nha.",
    ),
    "comparison-loop": RoastIssueVoice(
        (
            (
                "Thấy người khác làm tốt, bạn chê việc mình.",
                "Người ta vừa làm tốt, bạn đã quay sang chê việc của mình.",
            ),
            (
                "Bạn so việc của mình với thành quả người khác.",
                "Bạn đem việc đang làm đi so với phần đẹp nhất người khác khoe.",
            ),
            (
                "Xem thành quả người khác, bạn lại thấy mình chậm.",
                "Lướt thành quả người khác xong, bạn lại thấy mình đang đi chế độ chậm.",
            ),
            (
                "Việc mình vừa làm bỗng thấy chưa đủ tốt.",
                "Việc vừa làm xong bỗng bị chính bạn chấm lại thấp hơn.",
            ),
            (
                "Bạn quên phần đã xong khi xem người khác.",
                "Mải xem người khác, bạn quên luôn phần mình đã xong.",
            ),
            (
                "Một lời khen người khác khiến bạn tự chê.",
                "Người khác được khen, sao bạn lại là người tự chê?",
            ),
        ),
        "Ủa, đem bản nháp của mình so với bản đẹp nhất của người ta là kèo lệch đó nha.",
        "So với người khác dễ quên phần mình đã làm, mình đếm lại cho công bằng nha.",
        "Kèo so sánh này hơi lệch đó.",
        "Quay về sân nhà mình nào.",
        "Nhẹ nhàng nhìn lại phần của mình nha.",
    ),
    "automatic-caretaking": RoastIssueVoice(
        (
            (
                "Bạn nhận lời giúp trước khi xem mình còn sức.",
                "Bạn nhận lời giúp trước khi xem pin mình còn mấy vạch.",
            ),
            (
                "Bạn đang mệt, vẫn nhận thêm việc giúp người khác.",
                "Pin đã đỏ mà vẫn nhận thêm việc giúp người khác.",
            ),
            (
                "Muốn giúp người khác, bạn quên lịch của mình.",
                "Mải làm siêu anh hùng, bạn quên mất lịch của chính mình.",
            ),
            (
                "Bạn giúp thêm một việc dù đã khá mệt.",
                "Đã khá mệt rồi, bạn vẫn tặng thêm một suất giúp đỡ.",
            ),
            (
                "Bạn giúp người khác rồi thiếu giờ cho mình.",
                "Giúp người khác xong thì giờ của mình đã hết veo.",
            ),
            (
                "Bạn nhận giúp khi phần mình vẫn còn dở.",
                "Việc mình còn dở mà bạn đã nhận thêm ca giúp người ta.",
            ),
        ),
        "Làm siêu anh hùng hoài thì ai sạc pin cho bạn đây?",
        "Giúp người khác là dễ thương, sức của bạn cũng cần được chừa phần.",
        "Bạn tốt bụng ghê, mỗi tội quên mình.",
        "Chừa lại chút pin cho mình nào.",
        "Chừa chút sức cho mình nha.",
    ),
    "decision-fatigue": RoastIssueVoice(
        (
            (
                "Bạn chọn mãi vẫn chưa biết chọn cái nào.",
                "Vòng tuyển chọn đã sang mùa hai mà chưa có người thắng.",
            ),
            (
                "Càng xem nhiều lựa chọn, bạn càng khó chọn.",
                "Càng mở thêm lựa chọn, bạn càng lạc giữa chợ phương án.",
            ),
            (
                "Bạn đang mệt mà vẫn cố chọn cho đúng.",
                "Mệt rồi mà vẫn cố chọn đáp án hoàn hảo, căng ghê.",
            ),
            (
                "Một lựa chọn nhỏ cũng làm bạn nghĩ lâu.",
                "Một lựa chọn bé xíu mà bạn họp bàn như chuyện quốc gia.",
            ),
            (
                "Bạn đã mệt, danh sách lựa chọn còn dài.",
                "Sức thì cạn dần, danh sách lựa chọn thì dài thêm.",
            ),
            (
                "Bạn tìm thêm phương án khi chưa chọn xong.",
                "Chưa chọn xong mà bạn đã đi săn thêm phương án.",
            ),
        ),
        "Lựa chọn không chạy mất đâu, chỉ có sức bạn là đang tụt dần.",
        "Đầu mệt thì chọn gì cũng khó, mình bớt lựa chọn cho nhẹ nha.",
        "Bảng so sánh của bạn chắc dài hơn bài luận rồi.",
        "Gạch bớt vài phương án nào.",
        "Cho đầu nghỉ một chút nha.",
    ),
    "perfect-before-start": RoastIssueVoice(
        (
            (
                "Bạn định gửi rồi, nhưng lại sửa thêm.",
                "Ngón tay đã chạm nút gửi, rồi lại quay về sửa thêm.",
            ),
            (
                "Bạn có thể sửa mãi một việc đã đủ dùng.",
                "Việc đã đủ dùng mà bạn vẫn đánh bóng như sắp đi thi.",
            ),
            (
                "Bản nháp xong rồi, bạn vẫn chưa gửi.",
                "Bản nháp xong rồi mà vẫn nằm trong máy, ngại ra mắt.",
            ),
            (
                "Bạn sửa thêm vài chữ rồi lại chưa gửi.",
                "Sửa ba chữ, ngắm lại, rồi vẫn chưa gửi, quen không?",
            ),
            (
                "Bạn đã đủ ý, vẫn chờ thêm để gửi.",
                "Ý đã đủ rồi, bạn vẫn ngồi chờ một thời điểm hoàn hảo.",
            ),
            (
                "Bạn chỉnh bản nháp thay vì xin góp ý.",
                "Bạn tự chỉnh bản nháp hoài thay vì cho người khác góp ý.",
            ),
        ),
        "Bản nháp sinh ra là để được góp ý, đâu phải để nằm chờ hoàn hảo.",
        "Muốn làm cho đúng là tốt, góp ý sớm sẽ đỡ cho bạn phải sửa một mình.",
        "Nút gửi đang chờ bạn hơi lâu rồi đó.",
        "Thả bản nháp ra đời nào.",
        "Nhẹ tay với mình thôi nha.",
    ),
    "group-pressure": RoastIssueVoice(
        (
            (
                "Bạn gật đầu, nhưng vẫn chưa hiểu hết.",
                "Đầu gật đều đều, phần hiểu thì vẫn đang tải.",
            ),
            (
                "Cả nhóm chốt rồi, bạn vẫn muốn hỏi thêm.",
                "Cả nhóm chốt đơn rồi, câu hỏi của bạn vẫn nằm trong nháp.",
            ),
            (
                "Bạn đồng ý theo dù còn một chỗ chưa rõ.",
                "Bạn bấm đồng ý theo đoàn dù còn một chỗ chưa rõ.",
            ),
            (
                "Mọi người đồng ý, bạn vẫn chưa hiểu vì sao.",
                "Mọi người đồng thanh đồng ý, còn bạn vẫn đang hỏi vì sao.",
            ),
            (
                "Nhóm đã chốt, câu hỏi của bạn còn đó.",
                "Nhóm chốt xong rồi, câu hỏi của bạn vẫn đứng chờ ở cửa.",
            ),
            (
                "Bạn theo ý nhóm khi chưa rõ một phần.",
                "Bạn đi theo đoàn dù bản đồ còn thiếu một mảnh.",
            ),
        ),
        "Gật đầu cho nhanh thì dễ, làm theo điều mình chưa hiểu mới mệt nè.",
        "Chưa hiểu thì hỏi lại là chuyện bình thường, không ai chấm điểm đâu.",
        "Cái gật đầu này hơi vội rồi.",
        "Giơ tay lên, không ai trừ điểm đâu.",
        "Hỏi lại cho rõ nha.",
    ),
    "avoid-small-conflict": RoastIssueVoice(
        (
            (
                "Bạn chưa đồng ý, nhưng vẫn nói là được.",
                "Trong đầu chưa đồng ý, miệng đã kịp nói được.",
            ),
            (
                "Bạn nói được rồi mới thấy không muốn làm.",
                "Chữ được vừa bay ra, bạn mới thấy mình không muốn làm.",
            ),
            (
                "Bạn nhận lời dù việc đó không tiện.",
                "Không tiện chút nào mà bạn vẫn nhận lời ngọt xớt.",
            ),
            (
                "Bạn muốn từ chối, nhưng lại nhận lời.",
                "Kịch bản là từ chối, lên sóng thì thành nhận lời.",
            ),
            (
                "Bạn nhận việc để khỏi phải nói không.",
                "Bạn nhận thêm việc chỉ để né chữ không.",
            ),
            (
                "Bạn muốn nói không, câu trả lời lại khác.",
                "Trong lòng muốn nói không, câu trả lời lại quay xe.",
            ),
        ),
        "Chữ không cũng là một câu trả lời lịch sự, đâu phải lời tuyên chiến.",
        "Nói không nhẹ nhàng cũng là cách giữ sức cho mình.",
        "Chữ được đó nghe hơi gượng nha.",
        "Tập nói thật một chút nào.",
        "Nói nhẹ thôi, rõ là được.",
    ),
    "defend-old-choice": RoastIssueVoice(
        (
            (
                "Cách cũ chưa hiệu quả, bạn vẫn làm tiếp.",
                "Cách cũ chưa ra kết quả mà bạn vẫn trung thành dữ.",
            ),
            (
                "Bạn đã làm nhiều nhưng kết quả chưa khá hơn.",
                "Công bỏ ra nhiều lắm, kết quả vẫn đứng im nhìn bạn.",
            ),
            (
                "Bạn làm thêm dù cách đó chưa có kết quả.",
                "Cách này chưa có kết quả, bạn vẫn nạp thêm công.",
            ),
            (
                "Bạn chưa muốn đổi cách đã làm lâu.",
                "Cách quen lâu năm, bạn vẫn chưa nỡ chia tay.",
            ),
            (
                "Bạn giữ cách cũ vì đã bỏ nhiều công.",
                "Lỡ bỏ nhiều công rồi nên bạn cứ ôm cách cũ.",
            ),
            (
                "Kết quả chưa tốt, bạn vẫn ngại đổi cách.",
                "Kết quả chưa ổn mà bạn vẫn ngại đổi cách, chung thủy ghê.",
            ),
        ),
        "Chung thủy với cách cũ cũng dễ thương, có điều kết quả chưa thấy đáp lại.",
        "Đổi cách không làm mất phần công bạn đã bỏ ra đâu.",
        "Công sức đã bỏ ra đang giữ chân bạn đó.",
        "Nhìn kết quả thật trước khi chung thủy tiếp nào.",
        "Nhìn lại một chút thôi nha.",
    ),
    "capacity-before-agreement": RoastIssueVoice(
        (
            (
                "Bạn muốn giúp, nhưng chưa biết làm lúc nào.",
                "Tim nói giúp ngay, lịch thì chưa biết nhét vào đâu.",
            ),
            (
                "Bạn muốn nhận việc, lịch chưa có chỗ.",
                "Bạn muốn nhận việc, mà lịch đã kín như rạp ngày lễ.",
            ),
            (
                "Bạn chưa biết dành giờ nào để giúp.",
                "Lời hứa giúp thì có, giờ để giúp thì chưa thấy đâu.",
            ),
            (
                "Bạn muốn giúp thêm dù giờ trống còn ít.",
                "Giờ trống đếm trên đầu ngón tay mà bạn vẫn muốn giúp thêm.",
            ),
            (
                "Bạn nhận thêm việc khi chưa xem lịch.",
                "Nhận việc trước, mở lịch sau, combo quen thuộc nha.",
            ),
            (
                "Việc được nhờ chưa có giờ trong lịch bạn.",
                "Việc được nhờ vẫn chưa có chỗ ngồi trong lịch của bạn.",
            ),
        ),
        "Lịch của bạn đâu có co giãn như quần thun nha.",
        "Muốn giúp là quý, mà thời gian của bạn cũng có hạn thật.",
        "Lịch của bạn đang bị xin thêm chỗ đó.",
        "Mở lịch ra trước khi hứa nào.",
        "Nhìn lịch trước cho đỡ mệt nha.",
    ),
    "quick-reply": RoastIssueVoice(
        (
            (
                "Bạn định trả lời khi chưa đọc hết.",
                "Chưa đọc tới dòng cuối, ngón tay đã muốn rep.",
            ),
            (
                "Bạn gõ câu trả lời khi tin nhắn còn dài.",
                "Tin nhắn còn cả đoạn dài, bạn đã gõ phản hồi rồi.",
            ),
            (
                "Bạn định gửi trước khi hiểu hết câu hỏi.",
                "Câu hỏi chưa hiểu hết mà nút gửi đã sẵn sàng.",
            ),
            (
                "Bạn muốn trả lời ngay một tin nhắn khó chịu.",
                "Một tin nhắn khó chịu, ngón tay bạn muốn phản đòn liền.",
            ),
            (
                "Bạn đọc nửa tin nhắn rồi bắt đầu đáp.",
                "Đọc được nửa tin nhắn, bạn đã vào chế độ đáp trả.",
            ),
            (
                "Bạn chưa đọc hết, câu trả lời đã có.",
                "Chưa đọc hết mà câu trả lời đã nằm sẵn trong đầu.",
            ),
        ),
        "Ngón tay nhanh hơn mắt một chút thì thường thôi, gửi trước khi đọc hết mới là kèo khó.",
        "Muốn đáp nhanh chỉ là phản xạ, đọc hết rồi trả lời vẫn chưa muộn.",
        "Tốc độ gõ phím này hơi gắt đó.",
        "Khoan bấm gửi nha.",
        "Thở ra một hơi rồi mình làm nè.",
    ),
    "repair-reply": RoastIssueVoice(
        (
            (
                "Bạn gửi rồi mới thấy câu mình hơi gắt.",
                "Bấm gửi xong mới thấy câu mình hơi nhiều gia vị.",
            ),
            (
                "Bạn đọc lại câu đã gửi và muốn sửa.",
                "Đọc lại câu vừa gửi, bạn chỉ ước có nút thu hồi.",
            ),
            (
                "Ý bạn muốn nói khác câu vừa gửi.",
                "Ý trong đầu một kiểu, câu vừa gửi đi một kiểu.",
            ),
            (
                "Câu trả lời đã gửi nghe gắt hơn dự tính.",
                "Câu trả lời đã gửi cay hơn công thức bạn định nấu.",
            ),
            (
                "Bạn muốn nói lại ý trong tin đã gửi.",
                "Tin đã gửi rồi, giờ bạn muốn xin quay lại cảnh đó.",
            ),
            (
                "Tin nhắn vừa gửi chưa đúng cách bạn muốn nói.",
                "Tin vừa gửi đi lạc tông so với điều bạn muốn nói.",
            ),
        ),
        "Lỡ tay nêm hơi mặn thì nêm lại, chưa cần đổ cả nồi đâu.",
        "Câu hơi gắt thì sửa được, bạn không cần tự trách lâu.",
        "Câu đó hơi nhiều ớt thật.",
        "Gỡ lại cho êm nào.",
        "Sửa nhẹ là được nha.",
    ),
    "specific-feedback": RoastIssueVoice(
        (
            (
                "Bạn có bản nháp, nhưng câu hỏi còn chung.",
                "Bản nháp có rồi, câu hỏi thì vẫn chung chung như dự báo thời tiết.",
            ),
            (
                "Bạn xin góp ý mà chưa chỉ phần cần xem.",
                "Xin góp ý mà không chỉ chỗ, người đọc phải chơi trò dò mìn.",
            ),
            (
                "Câu hỏi về bản nháp chưa đủ cụ thể.",
                "Câu hỏi về bản nháp còn mơ hồ như đề bài thiếu dữ kiện.",
            ),
            (
                "Bạn gửi bản nháp nhưng chưa nói cần góp ý gì.",
                "Gửi bản nháp kèm một dấu hỏi to đùng, không chú thích.",
            ),
            (
                "Người đọc chưa biết phần nào bạn muốn hỏi.",
                "Người đọc đang phải dò xem bạn muốn hỏi phần nào.",
            ),
            (
                "Bạn hỏi ổn chưa thay vì hỏi đúng phần.",
                "Câu ổn chưa của bạn rộng quá, khó ai trả lời trúng.",
            ),
        ),
        "Hỏi chung chung thì nhận góp ý chung chung, công bằng ghê.",
        "Chỉ đúng chỗ cần xem sẽ giúp người đọc góp ý dễ hơn nhiều.",
        "Người đọc cần bản đồ, đâu cần đoán.",
        "Khoanh vùng cho người ta nào.",
        "Chỉ một chỗ thôi là đủ nha.",
    ),
    "name-the-need": RoastIssueVoice(
        (
            (
                "Bạn muốn được giúp nhưng chưa nói cần gì.",
                "Muốn được giúp mà đề bài thì giấu kỹ quá.",
            ),
            (
                "Bạn nói mệt, chưa nói muốn được giúp gì.",
                "Bạn báo mệt rồi, còn cần giúp gì thì vẫn bí mật.",
            ),
            (
                "Bạn cần giúp một việc nhưng nói chưa rõ.",
                "Cần giúp một việc mà nói vòng như câu đố.",
            ),
            (
                "Bạn muốn người kia hiểu điều mình cần giúp.",
                "Bạn mong người kia hiểu ý, mà ý thì chưa nói ra.",
            ),
            (
                "Bạn than việc nhiều mà chưa nhờ việc cụ thể.",
                "Than việc nhiều cả buổi mà chưa nhờ được việc nào.",
            ),
            (
                "Bạn chưa nói việc nào cần người kia giúp.",
                "Việc cần người kia giúp vẫn đang nằm trong đầu bạn.",
            ),
        ),
        "Người kia đâu có đọc được suy nghĩ, đề bài phải ghi rõ chứ.",
        "Mệt thì cứ nói, kèm một việc cụ thể để người kia dễ giúp.",
        "Đề bài còn thiếu một dòng quan trọng.",
        "Ghi rõ đề bài nào.",
        "Nói rõ một chút thôi nha.",
    ),
}

# Same placement meaning, roast wording. Gentle examples keep the direct sentence.
ROAST_PLACEMENT_MEANINGS: dict[str, str] = {
    "quick-reply": "Bạn hay muốn trả lời trước khi kịp hiểu rõ, tốc hành ghê.",
    "defend-old-choice": "Bạn khá chung thủy với cách quen, kể cả khi kết quả mới cần kiểm tra.",
    "group-pressure": "Bạn dễ hòa theo cả nhóm cho êm, dù mình còn chưa hiểu rõ.",
    "automatic-caretaking": "Bạn hay bật chế độ giúp người khác trước khi kiểm tra sức mình.",
    "decision-fatigue": "Thiếu sức hoặc thiếu một tiêu chí rõ là bạn chọn mãi chưa xong.",
    "missing-context": "Bạn rất muốn hiểu người kia, có điều dữ kiện còn thiếu vài mảnh.",
    "perfect-before-start": "Bạn muốn làm thật chuẩn chỉnh, mà góp ý thì vẫn cần ghé qua.",
    "too-many-open-loops": "Bạn mê thử việc mới trong khi việc trước còn dở dang.",
    "avoid-small-conflict": "Bạn ưu tiên giữ hòa khí, kể cả khi phải nhận điều mình không muốn.",
    "changed-plan": "Bạn đổi cách làm khá lẹ, có điều lịch vẫn cần hai bên thống nhất.",
    "specific-feedback": "Bạn muốn được hiểu đúng, nên phản hồi càng cụ thể càng hợp với bạn.",
    "name-the-need": "Bạn hay giữ điều riêng cho mình, mà nhu cầu thì vẫn cần nói ra.",
    "capacity-before-agreement": "Bạn hay ôm trách nhiệm, trong khi thời gian có giới hạn thật.",
}

_ISSUES = {issue.key: issue for issue in DAILY_ISSUES}
_HEADLINE_ROAST: dict[str, str] = {
    direct: roast for voice in ROAST_ISSUES.values() for direct, roast in voice.headlines
}
_HEADLINE_ISSUE: dict[str, str] = {
    direct: key for key, voice in ROAST_ISSUES.items() for direct, _ in voice.headlines
}
_ACTION_ISSUE: dict[str, str] = {
    action: issue.key
    for issue in DAILY_ISSUES
    for action in (*issue.advice, *issue.relationship_advice)
}
_PLACEMENT_ROAST: dict[str, str] = {
    PLACEMENT_MEANINGS[key]: roast for key, roast in ROAST_PLACEMENT_MEANINGS.items()
}
_GENTLE_ARENAS = frozenset({SemanticArena.ENERGY, SemanticArena.SELF_CARE})


def _validate_catalog() -> None:
    if set(ROAST_ISSUES) != set(_ISSUES):
        raise ValueError("Every Daily issue needs exactly one roast voice entry")
    for key, voice in ROAST_ISSUES.items():
        directs = tuple(direct for direct, _ in voice.headlines)
        if set(directs) != set(_ISSUES[key].headlines) or len(directs) != len(set(directs)):
            raise ValueError(f"Roast headlines for {key} must cover every direct headline")
    if len(set(_HEADLINE_ROAST.values())) != len(_HEADLINE_ROAST):
        raise ValueError("Roast headlines must be distinct")
    if set(ROAST_PLACEMENT_MEANINGS) != set(PLACEMENT_MEANINGS):
        raise ValueError("Every placement meaning needs one roast wording")


_validate_catalog()


@dataclass(frozen=True)
class DailySections:
    hook: str
    thesis: str
    manifestation: str
    micro_action: str


def _thesis_matches(issue: DailyIssuePattern, thesis: str) -> bool:
    # Current theses end with the takeaway; saved v6 theses carry the meaning.
    return f" {issue.takeaway} " in f" {thesis} " or f" {issue.meaning} " in f" {thesis} "


def _resolve_issue(sections: DailySections) -> str | None:
    if sections.hook in _HEADLINE_ISSUE:
        return _HEADLINE_ISSUE[sections.hook]
    if sections.micro_action in _ACTION_ISSUE:
        return _ACTION_ISSUE[sections.micro_action]
    return next(
        (issue.key for issue in DAILY_ISSUES if _thesis_matches(issue, sections.thesis)),
        None,
    )


def roast_daily_sections(sections: DailySections) -> DailySections:
    """Roast wording for one direct Daily card; unmatched sections pass through."""

    key = _resolve_issue(sections)
    if key is None:
        return sections
    issue = _ISSUES[key]
    voice = ROAST_ISSUES[key]
    arena, scene = split_scene_lead(sections.manifestation)
    gentle = arena in _GENTLE_ARENAS

    hook = _HEADLINE_ROAST.get(sections.hook, sections.hook)
    if _HEADLINE_ISSUE.get(sections.hook, key) != key:
        hook = sections.hook

    thesis = sections.thesis
    if _thesis_matches(issue, thesis):
        if thesis.endswith(f" {issue.takeaway}"):
            # The jab is Roast's insight sentence; keeping the direct takeaway
            # after it would say the same thing twice.
            thesis = thesis[: -len(issue.takeaway) - 1]
        if not gentle:
            for direct, roast in _PLACEMENT_ROAST.items():
                # v7: the tendency is the whole remaining thesis; v6: it opens it.
                if thesis == direct or thesis.startswith(f"{direct} "):
                    thesis = f"{roast}{thesis[len(direct) :]}"
                    break
        thesis = f"{voice.gentle_jab if gentle else voice.jab} {thesis}"

    manifestation = sections.manifestation
    if scene in issue.scenes:
        manifestation = f"{sections.manifestation} {voice.scene_tag}"

    micro_action = sections.micro_action
    if _ACTION_ISSUE.get(micro_action) == key:
        frame = voice.gentle_action_frame if gentle else voice.action_frame
        micro_action = f"{frame} {micro_action}"

    return DailySections(hook, thesis, manifestation, micro_action)


def roast_legacy_text(value: str) -> str:
    """Legacy title/body only change when they equal an authored direct headline."""

    return _HEADLINE_ROAST.get(value, value)


def apply_content_voice(
    content: ReadingContentProjection, voice: ReadingVoice
) -> ReadingContentProjection:
    if (
        voice is ReadingVoice.DIRECT
        or content.purpose is not ReadingPurpose.DAILY_NOTE
        or content.source is not ReadingRevisionSource.DETERMINISTIC
    ):
        # Roast matches exact deterministic wording. A generated rewrite only keeps
        # some of it (e.g. the thesis), so voicing it would half-roast the card.
        return content
    current = content.sections
    roasted = roast_daily_sections(
        DailySections(current.hook, current.thesis, current.manifestation, current.micro_action)
    )
    # Lá's line voices with the card: only an authored direct line has a roast pair.
    companion = roast_companion_line(current.companion) if current.companion is not None else None
    if (
        roasted
        == DailySections(current.hook, current.thesis, current.manifestation, current.micro_action)
        and companion == current.companion
    ):
        return content
    experiment = content.experiment
    if experiment is not None and experiment.action == current.micro_action:
        # The action key stays bound to the stored direct action; only the label changes.
        experiment = experiment.model_copy(update={"action": roasted.micro_action})
    return content.model_copy(
        update={
            "sections": current.model_copy(
                update={
                    "hook": roasted.hook,
                    "thesis": roasted.thesis,
                    "manifestation": roasted.manifestation,
                    "micro_action": roasted.micro_action,
                    "companion": companion,
                }
            ),
            "experiment": experiment,
        }
    )


def voice_from_baseline(
    content: ReadingContentProjection,
    baseline: ReadingContentProjection | None,
    voice: ReadingVoice,
) -> ReadingContentProjection:
    """Voice a generated card through its deterministic baseline, never piecemeal.

    ``baseline`` must be the caller-verified deterministic revision of the same
    owner and plan. The returned card keeps the generated revision's identity
    (revision id, evidence, experiment key), so activation, experiments, saves and
    resonance stay bound to what is active; only the displayed wording comes from
    the voiced baseline. Without a usable baseline the generated text is returned
    unchanged in the direct voice.
    """

    if voice is ReadingVoice.DIRECT or content.source is ReadingRevisionSource.DETERMINISTIC:
        return apply_content_voice(content, voice)
    if (
        baseline is None
        or baseline.source is not ReadingRevisionSource.DETERMINISTIC
        or baseline.purpose is not content.purpose
    ):
        return content
    voiced = apply_content_voice(baseline, voice)
    card_voiced = (
        voiced.sections.model_copy(update={"companion": baseline.sections.companion})
        != baseline.sections
    )
    if not card_voiced:
        # The baseline card has no authored voice either; keep the generated card whole.
        # Lá's line alone never swaps Luna's card for the deterministic one.
        return content
    experiment = content.experiment
    if experiment is not None:
        # The key stays bound to the active revision's stored action; the label
        # follows the displayed (voiced baseline) action, as for deterministic roast.
        experiment = experiment.model_copy(update={"action": voiced.sections.micro_action})
    return content.model_copy(
        update={
            "source": ReadingRevisionSource.DETERMINISTIC,
            "sections": voiced.sections,
            "experiment": experiment,
        }
    )
