"""Scene and small step keyed by the asked action (audit T02/T03, decisions C4/C5).

Copy decided row by row under the owner's delegation of 26/10/2026 in
docs/reviews/2026-10-22-t02-t03-tarot-copy-workbook.xlsx: one chosen draft per row, four rows
polished by Codex. Three scene rows were dropped and fall back to the action's ``general`` row.

A framed reading whose QuestionFrame carries an action shows, at the spread's one step role, the
action's scene for the frame's topic (else the action's ``general`` scene) and the action's step
for that role. Any other position, a frame without an action and an action without a row keep
the card x topic scene and the goal or card step, as before. Stored readings keep their text.

Codex r47 (whole-output composition): the step agrees with the reading's stance (plan_step and
PREP_STEPS), and relationships scenes that presume a partner show only when the question names
one (PARTNER_SCENES). Openings presume no event the closed labels do not establish.

New copy here needs owner approval; the module is in the fallback approval scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domains.tarot.models import (
    QuestionFrame,
    TarotAction,
    TarotContext,
    TarotQuestionForm,
    TarotStance,
    TarotStanceLevel,
)
from app.domains.tarot.stance import SELF_CARE_ACTIONS

ACTION_COPY_VERSION = "tarot-action-copy-v1"

ACTION_SCENES: dict[tuple[str, str], str] = {
    ("nhan_loi", "general"): (
        "Người quen hỏi bạn có rảnh sáng thứ Bảy không, và bạn đang mở lịch xem buổi đó đã có hẹn "
        "gì chưa."
    ),
    ("nhan_loi", "relationships"): (
        "Sau buổi cà phê đầu tiên, người kia rủ bạn đi xem phim tuần sau, còn bạn vẫn cầm điện "
        "thoại chưa trả lời."
    ),
    ("nhan_loi", "work"): (
        "Sếp vừa nhắn hỏi bạn nhận thêm phần báo cáo được không, trong khi bảng việc tuần này của "
        "bạn đã kín đến thứ Năm."
    ),
    ("nhan_loi", "energy"): (
        "Cuối một ngày làm việc dài, bạn đang nằm trên ghế thì có lời mời đi sinh nhật bạn cùng "
        "lớp tối nay."
    ),
    ("tu_choi", "general"): (
        "Lời mời vào câu lạc bộ vẫn chưa được trả lời, và lịch tuần này của bạn đã có ba buổi tối "
        "kín."
    ),
    ("tu_choi", "relationships"): (
        "Sau buổi gặp đầu, người kia rủ bạn đi tiếp cuối tuần, và tin nhắn đó ở trạng thái đã xem "
        "từ tối qua."
    ),
    ("tu_choi", "work"): (
        "Đồng nghiệp nhắn hỏi bạn đổi ca trực Chủ nhật, đúng ngày bạn đã hẹn về thăm nhà từ tuần "
        "trước."
    ),
    ("tu_choi", "communication"): (
        "Bạn bè nhắn nhờ bạn làm giúp một việc lúc mười giờ tối, và bạn đã gõ “ừ được” ba lần rồi "
        "xóa."
    ),
    ("tu_choi", "energy"): (
        "Bạn ngồi trên giường, mắt đã díp lại, thì nhóm bạn nhắn hỏi bạn có đến buổi tụ tập lúc "
        "tám giờ không."
    ),
    ("tu_choi", "self_care"): (
        "Buổi tối bạn để dành để đọc sách thì có tin nhắn nhờ sửa giúp bài thuyết trình, gửi kèm "
        "chữ “gấp”."
    ),
    ("noi_ra", "general"): (
        "Một câu trêu cũ lại được nhắc trong bữa ăn, mọi người cười, còn bạn chỉ cười theo rồi im "
        "lặng."
    ),
    ("noi_ra", "relationships"): (
        "Người yêu gợi ý tối nay lại đi chơi, còn bạn trả lời “sao cũng được” dù trong lịch đã "
        "ghi giờ đọc sách."
    ),
    ("noi_ra", "work"): (
        "Trong cuộc họp, deadline được chốt vào thứ Tư, và bạn nhìn bảng việc của mình rồi gật "
        "đầu theo mọi người."
    ),
    ("noi_ra", "communication"): (
        "Cả nhóm đang chốt phương án trên cuộc gọi, bạn bật mic lên định nói rồi lại tắt."
    ),
    ("noi_ra", "self_care"): (
        "Mẹ nhắc lại kế hoạch về quê cuối tuần, còn bạn gật đầu dù đã định dành hai ngày đó để "
        "ngủ bù."
    ),
    ("nhan_lai", "general"): (
        "Một người bạn lâu không gặp nhắn hỏi thăm từ hôm qua, và tin nhắn vẫn hiện chấm xanh "
        "chưa trả lời."
    ),
    ("nhan_lai", "relationships"): (
        "Buổi hẹn hôm qua kết thúc lúc mười giờ, và từ đó đến giờ bạn mở khung chat mấy lần mà "
        "chưa ai nhắn gì."
    ),
    ("nhan_lai", "work"): (
        "Khách hàng gửi câu hỏi lúc chín giờ tối, và thông báo email vẫn sáng trên màn hình khóa "
        "của bạn."
    ),
    ("nhan_lai", "communication"): (
        "Bạn đọc tin nhắn mới nhất và thấy câu đùa của mình được hiểu thành lời chê, kèm một biểu "
        "tượng mặt buồn."
    ),
    ("hoi_lai", "general"): (
        "Bạn cuộn lại đoạn chat dài và thấy ba người nói ba thời gian khác nhau, không ai chốt "
        "câu cuối."
    ),
    ("hoi_lai", "relationships"): (
        "Bạn đọc lại tin nhắn “thôi bỏ qua đi” của người yêu lần thứ ba, chỗ đó vẫn chưa ai nói "
        "tiếp."
    ),
    ("hoi_lai", "work"): (
        "Sếp giao việc trong hai phút ở hành lang, và bạn về chỗ ngồi với tờ ghi chú chỉ có ba chữ."
    ),
    ("hoi_lai", "communication"): (
        "Bạn nhận được tin nhắn “ừ, tùy bạn” và đọc đi đọc lại mà vẫn chưa rõ đó là đồng ý hay "
        "không."
    ),
    ("cho_them", "general"): (
        "Chủ nhà hẹn bạn trả lời trước thứ Sáu, hôm nay mới là thứ Hai, và bạn vẫn chưa đi xem "
        "căn thứ hai."
    ),
    ("cho_them", "relationships"): (
        "Từ chiều đến giờ, bạn đã mở khung chat với người kia bốn lần, và tin cuối cùng vẫn là "
        "của bạn."
    ),
    ("cho_them", "work"): (
        "Phần việc tiếp theo của bạn cần một quyết định của trưởng nhóm, và cuộc họp chốt chuyện "
        "đó vừa dời sang tuần sau."
    ),
    ("cho_them", "communication"): (
        "Tin nhắn vừa đến làm bạn nóng mặt, và bạn đã gõ một đoạn trả lời dài với ba dấu chấm than."
    ),
    ("cho_them", "energy"): (
        "Đã gần nửa đêm, bạn vẫn ngồi trước hai lựa chọn viết trên giấy, mắt cay và ly nước đã "
        "cạn từ lâu."
    ),
    ("bat_dau", "general"): (
        "Hộp màu bạn mua từ tháng trước vẫn nằm nguyên trong túi giấy ở góc bàn, chưa bóc lớp "
        "nilon."
    ),
    ("bat_dau", "relationships"): (
        "Người bạn mới quen hay nhắn hỏi bạn đã ăn tối chưa, và bạn để ý mình hay trả lời tin đó "
        "nhanh nhất."
    ),
    ("bat_dau", "work"): (
        "File kế hoạch dự án phụ đã được tạo từ đầu năm, và bạn đổi tên file nhiều lần hơn sửa "
        "nội dung bên trong."
    ),
    ("bat_dau", "energy"): (
        "Đôi giày thể thao để ở cửa đã phủ một lớp bụi mỏng, và chiều nào bạn cũng đi ngang qua nó."
    ),
    ("bat_dau", "self_care"): (
        "Báo thức reo, bạn với lấy điện thoại và đọc tin nhắn công việc trước cả khi ngồi dậy."
    ),
    ("dung_lai", "general"): (
        "Ba tuần liền bạn đến lớp buổi tối muộn mười phút, ngồi cuối lớp và ghi chép được nửa "
        "trang."
    ),
    ("dung_lai", "relationships"): (
        "Tối nào trước khi ngủ, bạn cũng mở trang cá nhân của người cũ và xem hết các story mới "
        "đăng."
    ),
    ("dung_lai", "work"): (
        "Dự án của bạn đã kéo dài sáu tuần, các con số tuần này vẫn giống tuần đầu, và nhóm vừa "
        "họp lại lần thứ tư."
    ),
    ("dung_lai", "communication"): (
        "Cuộc tranh luận trong nhóm chat của bạn đã qua hơn trăm tin nhắn, và mọi người đang nhắc "
        "lại những ý đã nói từ đầu."
    ),
    ("dung_lai", "energy"): (
        "Đồng hồ góc màn hình đã chỉ tám giờ tối, bạn dụi mắt lần thứ ba và vẫn còn hai email "
        "chưa trả lời."
    ),
    ("dung_lai", "self_care"): (
        "Báo thức năm giờ reo, bạn tắt đi rồi nằm thêm một tiếng, và cả buổi sáng thấy người uể "
        "oải."
    ),
    ("doi_viec", "general"): (
        "Bạn mở trang tuyển dụng trong giờ nghỉ trưa, lưu lại hai tin, rồi tắt màn hình khi đồng "
        "nghiệp đi ngang."
    ),
    ("doi_viec", "work"): (
        "Lời mời từ công ty mới nằm trong hộp thư của bạn từ hôm thứ Hai, kèm hạn trả lời là cuối "
        "tuần này."
    ),
    ("doi_viec", "energy"): (
        "Bạn về đến nhà là nằm luôn, bữa tối gọi giao tận nơi, và ngày nghỉ chỉ đủ để ngủ bù."
    ),
    ("xin_gop_y", "general"): (
        "Kế hoạch chuyến đi một mình nằm trong file ghi chú, chỉ có bạn từng đọc, và ngày đặt vé "
        "đang đến gần."
    ),
    ("xin_gop_y", "relationships"): (
        "Đêm qua bạn nằm nghĩ về lần cãi nhau đến hai giờ sáng, và sáng nay mở khung chat với bạn "
        "thân nhưng chưa gõ gì."
    ),
    ("xin_gop_y", "work"): (
        "Hạn nộp là thứ Sáu, và từ đầu tuần đến giờ chưa ai ngoài bạn mở file kế hoạch đó."
    ),
    ("xin_gop_y", "communication"): (
        "Sau buổi thuyết trình, mọi người nói “ổn đó” rồi về chỗ, và bạn không biết phần nào mình "
        "làm tốt."
    ),
    ("nghi_ngoi", "general"): (
        "Bạn đã ngáp liên tục từ chiều thứ Năm, và vẫn đang xếp thêm việc cho hai ngày cuối tuần."
    ),
    ("nghi_ngoi", "work"): (
        "Lịch làm việc tuần sau còn trống ngày thứ Hai, còn bạn đã làm liền ba cuối tuần để kịp "
        "dự án."
    ),
    ("nghi_ngoi", "energy"): (
        "Mới chín giờ tối, mắt bạn đã cay, và bạn đọc lại cùng một tin nhắn mà không nhớ nó nói gì."
    ),
    ("nghi_ngoi", "self_care"): (
        "Bạn về đến nhà lúc tám giờ, mở laptop ra bàn ăn, trong khi cơm tối vẫn chưa ăn được "
        "miếng nào."
    ),
    ("gui_di", "general"): (
        "Bạn mở bản nháp email gửi người bạn cũ, sửa thêm một dấu phẩy, rồi lại đóng lại."
    ),
    ("gui_di", "relationships"): (
        "Món quà bạn gói xong vẫn để trên kệ từ tuần trước, còn sinh nhật người đó là ngày mai."
    ),
    ("gui_di", "work"): (
        "Email bạn soạn sẵn đã có tệp đính kèm, con trỏ chuột dừng trên nút gửi, và đồng hồ chỉ "
        "năm giờ chiều."
    ),
    ("gui_di", "communication"): (
        "Trong khung chat có một đoạn tin dài ba màn hình bạn soạn từ tối qua, vẫn chưa gửi."
    ),
    ("xin_loi", "general"): (
        "Hôm qua bạn đến muộn bốn mươi phút, mọi người đã gọi món xong, còn tin báo muộn thì bạn "
        "gửi khi đã đến cửa."
    ),
    ("xin_loi", "relationships"): (
        "Lần nói chuyện vừa rồi dừng lại sau một câu nặng lời của bạn, và từ đó khung chat với "
        "người kia chỉ còn vài chữ ngắn."
    ),
    ("xin_loi", "work"): (
        "Phần việc của bạn chậm hai ngày, đồng nghiệp phải ở lại muộn để ghép báo cáo, và sáng "
        "nay chỉ chào bạn một câu."
    ),
    ("xin_loi", "communication"): (
        "Bạn đã gõ một tin xin lỗi dài, đến giữa đoạn thì phần “tại vì” đã dài hơn phần xin lỗi."
    ),
    ("hen_gap", "general"): (
        "Bạn thấy ảnh người bạn cũ vừa về thành phố, và khung chat của hai người dừng ở lời chúc "
        "sinh nhật năm ngoái."
    ),
    ("hen_gap", "relationships"): (
        "Bạn và người kia nhắn tin gần như mỗi tối suốt hai tuần, và hôm qua người kia gửi ảnh "
        "một quán cà phê mới mở."
    ),
    ("hen_gap", "work"): (
        "Chuỗi email giữa bạn và khách hàng đã sang lần trả lời thứ mười hai, và hai bên vẫn hiểu "
        "khác nhau một mục yêu cầu."
    ),
    ("hen_gap", "communication"): (
        "Bạn và người kia đã nhắn qua lại hai tiếng, mỗi tin trả lời lại ngắn hơn, và cả hai đều "
        "gõ rồi xóa nhiều lần."
    ),
    ("chia_se", "general"): (
        "Nhóm bạn hỏi kết quả kỳ thi trong lúc ăn trưa, và bạn trả lời “chưa có” dù đã biết từ "
        "hôm qua."
    ),
    ("chia_se", "relationships"): (
        "Người yêu hỏi hôm nay đi làm thế nào, và bạn trả lời “bình thường” trong khi vai vẫn còn "
        "mỏi vì căng cả ngày."
    ),
    ("chia_se", "work"): (
        "Bảng việc của bạn có sáu đầu việc cùng hạn thứ Sáu, và trong cuộc họp sáng nay bạn vẫn "
        "nói “em ổn”."
    ),
    ("chia_se", "communication"): (
        "Trong bữa tối với nhóm bạn, có người hỏi dạo này nhà bạn sao rồi, và bạn đổi sang chuyện "
        "khác ngay."
    ),
    ("chia_se", "self_care"): (
        "Cả tuần bạn trả lời “mình ổn” mỗi khi được hỏi thăm, rồi chuyển sang chuyện khác."
    ),
    ("dat_ranh_gioi", "general"): (
        "Ở bữa tiệc, một người quen hỏi bạn lương bao nhiêu, mọi người quay sang chờ, và bạn cười "
        "gượng."
    ),
    ("dat_ranh_gioi", "work"): (
        "Sáng Chủ nhật, nhóm chat công việc có mười tin mới, và một tin gắn tên bạn hỏi “xử lý "
        "luôn được không”."
    ),
    ("dat_ranh_gioi", "communication"): (
        "Một người bạn hay mượn đồ rồi quên trả, và hôm nay lại nhắn hỏi mượn chiếc máy ảnh của "
        "bạn."
    ),
    ("dat_ranh_gioi", "energy"): (
        "Tuần này bạn có năm buổi hẹn sau giờ làm, và tối thứ Năm bạn ngủ gật ngay trên ghế sofa."
    ),
    ("dat_ranh_gioi", "self_care"): (
        "Sau mỗi lần gặp người bạn đó, bạn về nhà soi gương lâu hơn và nhớ lại từng câu nhận xét "
        "về mình."
    ),
    ("ket_thuc", "general"): (
        "Bạn là người duy nhất còn nhắn nhắc lịch trong nhóm, và tin nhắc gần nhất chỉ có một "
        "lượt xem."
    ),
    ("ket_thuc", "relationships"): (
        "Tháng này bạn và người yêu đã cãi nhau bốn lần, lần nào cũng về chuyện cũ, và lần nào "
        "cũng dừng bằng im lặng."
    ),
    ("ket_thuc", "work"): (
        "Ca làm thêm sáng thứ Bảy bắt đầu lúc bảy giờ, và đã ba tuần bạn đến nơi với đôi mắt còn "
        "ngái ngủ."
    ),
    ("thu_lai", "general"): (
        "Tờ kết quả kỳ thi trước vẫn kẹp trong cuốn sách ôn của bạn, và lịch đăng ký đợt mới vừa "
        "mở sáng nay."
    ),
    ("thu_lai", "relationships"): (
        "Người cũ nhắn hỏi thăm sau nửa năm im lặng, và bạn đã đọc tin đó nhiều lần từ tối qua."
    ),
    ("thu_lai", "work"): (
        "Email trả lời từ công ty lần trước vẫn nằm trong hộp thư của bạn, và họ vừa đăng tuyển "
        "lại đúng vị trí đó."
    ),
    ("thu_lai", "communication"): (
        "Lần trước bạn giải thích một mạch, người kia gật gù rồi hỏi lại đúng câu bạn vừa nói xong."
    ),
    ("thu_lai", "self_care"): (
        "Tuần trước bạn tắt điện thoại lúc mười một giờ được ba tối, rồi tối thứ Năm lại lướt đến "
        "một giờ sáng."
    ),
    ("hoc_them", "general"): (
        "Bạn xem phim có phụ đề, nghe ra vài câu quen, rồi tua lại để nghe thêm lần nữa."
    ),
    ("hoc_them", "work"): (
        "Trong cuộc họp, đồng nghiệp dựng xong biểu đồ trong mười phút, việc bạn thường mất cả "
        "buổi chiều."
    ),
    ("hoc_them", "self_care"): (
        "Bạn hay dừng lại xem người ta vẽ ở góc phố, và đã lưu hơn năm mươi bức tranh vào điện "
        "thoại."
    ),
    ("tap_trung", "general"): (
        "Bạn đọc được hai trang thì điện thoại sáng lên, và nửa tiếng sau cuốn sách vẫn mở ở "
        "trang đó."
    ),
    ("tap_trung", "work"): (
        "Màn hình của bạn mở mười hai tab cho ba dự án, và sáng nay bạn chuyển qua lại mà chưa "
        "xong việc nào."
    ),
    ("tap_trung", "energy"): (
        "Bạn để dành việc khó nhất đến chiều, và lúc ba giờ chiều bạn đọc cùng một email lần thứ "
        "tư."
    ),
    ("sap_xep_lai", "general"): (
        "Lịch thứ Tư của bạn có bốn việc chồng lên nhau, còn thứ Sáu thì gần như trống trơn."
    ),
    ("sap_xep_lai", "relationships"): (
        "Buổi hẹn tối thứ Sáu trùng với hạn nộp báo cáo của bạn, và người yêu vừa nhắn đã đặt bàn "
        "lúc bảy giờ."
    ),
    ("sap_xep_lai", "work"): (
        "Ba deadline rơi vào cùng ngày thứ Năm, và danh sách việc của bạn đang xếp theo thứ tự "
        "việc nào đến trước."
    ),
    ("sap_xep_lai", "energy"): (
        "Ba đêm liền bạn ngủ lúc hai giờ sáng, và sáng nào cũng bấm báo thức thêm năm phút ba lần."
    ),
    ("nho_giup", "general"): (
        "Đồ đạc đã đóng xong mười thùng giấy, ngày chuyển là thứ Bảy, và danh sách người giúp vẫn "
        "chỉ có tên bạn."
    ),
    ("nho_giup", "relationships"): (
        "Tối nay bạn rửa bát xong lại phơi đồ, trong lúc người yêu ngồi xem điện thoại ở phòng "
        "khách."
    ),
    ("nho_giup", "work"): (
        "Phần báo cáo cần số liệu từ ba phòng ban, và bạn đã ở lại muộn hai tối chỉ để ghép bảng."
    ),
    ("nho_giup", "energy"): (
        "Bạn vừa đi làm về đã vào bếp nấu cơm, trong khi đống quần áo chưa gấp vẫn chờ trên ghế."
    ),
    ("nho_giup", "self_care"): (
        "Bạn thân nhắn hỏi “dạo này sao rồi”, và bạn trả lời bằng một biểu tượng cười rồi tắt màn "
        "hình."
    ),
    ("gop_y", "general"): (
        "Lịch trình chuyến đi bạn bè lên có bảy điểm trong một ngày, và cả nhóm đang thả tim vào "
        "tin nhắn đó."
    ),
    ("gop_y", "relationships"): (
        "Lần thứ ba trong tháng, bạn đứng chờ người yêu trước rạp phim hai mươi phút, vé đã in "
        "sẵn trong tay."
    ),
    ("gop_y", "work"): (
        "Phần slide của bạn cùng nhóm có số liệu cũ từ năm ngoái, và buổi thuyết trình diễn ra "
        "sáng mai."
    ),
    ("gop_y", "communication"): (
        "Một người bạn hỏi “thấy sao”, bạn trả lời “ổn mà” trong khi đang khoanh ba chỗ trên bản "
        "in."
    ),
    ("de_xuat", "general"): (
        "Cả nhóm đã bàn chuyến đi hai tuần mà chưa chốt, và trong ghi chú điện thoại bạn có sẵn "
        "một lịch trình khác."
    ),
    ("de_xuat", "relationships"): (
        "Cuối tuần trước bạn dọn nhà một mình cả buổi sáng, còn danh sách việc nhà chưa bao giờ "
        "được viết ra."
    ),
    ("de_xuat", "work"): (
        "Mỗi tuần nhóm mất nửa ngày để nhập lại cùng một bảng số liệu, và bạn đã dựng sẵn một mẫu "
        "tự động trên máy mình."
    ),
    ("de_xuat", "communication"): (
        "Bạn giơ tay định nói trong cuộc họp, nhưng hai người khác đã lên tiếng trước và cuộc họp "
        "chuyển sang mục sau."
    ),
    ("don_dep", "general"): (
        "Chiếc ghế trong phòng đã thành chỗ treo quần áo, và bạn phải dời một chồng đồ mới ngồi "
        "xuống được."
    ),
    ("don_dep", "work"): (
        "Bàn làm việc của bạn có bốn chiếc cốc, một chồng giấy in và hai sợi cáp sạc quấn vào nhau."
    ),
    ("don_dep", "energy"): (
        "Mỗi lần về phòng, bạn bước qua hai túi đồ chưa mở, rồi nằm luôn lên giường mà không bật "
        "đèn."
    ),
    ("don_dep", "self_care"): (
        "Góc đọc sách bạn từng thích giờ chất thùng hàng và quần áo, và cuốn sách đọc dở nằm dưới "
        "cùng."
    ),
    ("ra_ngoai", "general"): (
        "Đã hai cuối tuần liền bạn chỉ đi từ giường ra bàn và ngược lại, rèm cửa vẫn kéo kín."
    ),
    ("ra_ngoai", "relationships"): (
        "Nhóm bạn mới quen tạo nhóm chat rủ đi ăn tối thứ Bảy, và mọi người đã thả tim trừ bạn."
    ),
    ("ra_ngoai", "energy"): (
        "Chiều nay trời mát, nắng chiếu qua khe rèm, còn bạn vẫn ngồi ở đúng chỗ từ lúc ăn trưa."
    ),
    ("ra_ngoai", "self_care"): (
        "Bạn đứng ở cửa, đã đi giày, rồi lại ngồi xuống mở điện thoại xem có ai rảnh đi cùng không."
    ),
    ("o_nha", "general"): (
        "Lời mời sinh nhật tối nay vẫn ở trên màn hình, và bạn đã thay sẵn đồ ngủ từ lúc bảy giờ."
    ),
    ("o_nha", "relationships"): (
        "Cả tuần bạn và người yêu gặp nhau toàn ở quán xá, và trong tủ lạnh vẫn còn gói mì Ý mua "
        "từ tuần trước."
    ),
    ("o_nha", "energy"): (
        "Sau sáu ngày đi sớm về khuya, sáng Chủ nhật bạn mở mắt lúc mười giờ và vẫn thấy người "
        "nặng trĩu."
    ),
    ("o_nha", "self_care"): (
        "Cả ngày bạn nói chuyện với khách hàng, và vừa về đến nhà bạn tắt chuông điện thoại ngay "
        "ở cửa."
    ),
    ("doi_thoi_quen", "general"): (
        "Sáng nào bạn cũng tự hứa tối nay ngủ sớm, rồi mười hai giờ đêm lại mở thêm một tập phim."
    ),
    ("doi_thoi_quen", "relationships"): (
        "Tối nào bạn cũng mở mạng xã hội, và tên người cũ hiện đầu tiên trong mục tìm kiếm gần đây."
    ),
    ("doi_thoi_quen", "work"): (
        "Bạn đang xem phim với bạn bè thì điện thoại rung, và bạn mở email công việc ngay giữa "
        "cảnh hay nhất."
    ),
    ("doi_thoi_quen", "energy"): (
        "Chiều nào gần bốn giờ bạn cũng ghé quầy cà phê dưới tòa nhà, gọi đúng một món quen."
    ),
    ("doi_thoi_quen", "self_care"): (
        "Cả tuần bạn ăn trưa tại bàn, và hôm nay mới để ý cây ngoài cửa sổ đã ra hoa."
    ),
    ("tu_thuong", "general"): (
        "Bạn vừa gạch dòng cuối trong danh sách việc của tuần, ngồi yên một lúc mà chưa biết làm "
        "gì tiếp."
    ),
    ("tu_thuong", "work"): (
        "Email xác nhận dự án hoàn thành vừa đến, mọi người trong nhóm thả tim, và bạn mở ngay "
        "việc tiếp theo."
    ),
    ("tu_thuong", "energy"): (
        "Cuối một tuần dài, bạn ngồi bệt xuống sàn ngay khi vào nhà, túi xách vẫn còn đeo trên vai."
    ),
    ("tu_thuong", "self_care"): (
        "Bạn kể với bạn bè chuyện vừa làm được, rồi chèn thêm câu “cũng may thôi” ở cuối."
    ),
    ("viet_ra", "general"): (
        "Đầu óc bạn xoay quanh năm chuyện cùng lúc, và bạn đã mở điện thoại ba lần mà quên mình "
        "định làm gì."
    ),
    ("viet_ra", "relationships"): (
        "Lần trước hai người ngồi nói chuyện, bạn quên mất điều quan trọng nhất và chỉ nhớ ra khi "
        "đã về đến nhà."
    ),
    ("viet_ra", "work"): (
        "Đến buổi đánh giá, sếp hỏi tháng này bạn đã làm gì, và bạn chỉ nhớ ra được hai việc."
    ),
    ("viet_ra", "communication"): (
        "Bạn có ba điểm muốn nêu trong buổi họp chiều nay, và bây giờ chỉ còn nhớ rõ một điểm."
    ),
    ("viet_ra", "energy"): (
        "Tối thứ Sáu bạn thấy kiệt sức, nhưng khi bạn bè hỏi mệt vì gì, bạn không kể ra được việc "
        "nào cụ thể."
    ),
    ("viet_ra", "self_care"): (
        "Cuối ngày bạn nhớ lại một chuyện vui nhỏ ban sáng, rồi đến khi ngủ dậy đã quên mất nó."
    ),
}

ACTION_STEPS: dict[tuple[str, str], str] = {
    ("nhan_loi", "focus"): (
        "Khi lời mời vẫn đang chờ, mở lịch và khoanh đúng khoảng giờ việc đó cần."
    ),
    ("nhan_loi", "next"): (
        "Khi định gõ “được”, hỏi lại một chi tiết còn thiếu: mấy giờ, ở đâu hoặc mất bao lâu."
    ),
    ("nhan_loi", "alternative"): (
        "Khi chữ “được” sắp bật ra, nhắn trước một câu: “Cho mình mười phút xem lịch nhé.”"
    ),
    ("nhan_loi", "criterion"): (
        "Viết ra một việc bạn sẵn lòng lùi lại nếu nhận lời này, và đặt nó cạnh lời mời để so."
    ),
    ("nhan_loi", "opening"): (
        "Mở lời: “Mình nhận lời nhé, mình thống nhất thời gian cụ thể với bạn được không?”"
    ),
    ("tu_choi", "focus"): "Gửi câu từ chối trong mười phút tới, không cần kèm lý do dài.",
    ("tu_choi", "next"): (
        "Gửi lời từ chối bằng một câu ngắn và ghi lại bạn thấy thế nào ngay sau đó."
    ),
    ("tu_choi", "alternative"): (
        "Khi bạn định giải thích dài, chỉ giữ lại một câu từ chối và một câu cảm ơn."
    ),
    ("tu_choi", "criterion"): (
        "Ghi một dòng: buổi tối nay dành cho việc gì của bạn; lời nhờ nào chạm vào đó thì trả lời "
        "không."
    ),
    ("tu_choi", "opening"): (
        "Mở lời: “Cảm ơn bạn đã nghĩ đến mình, nhưng lần này mình không nhận được.”"
    ),
    ("noi_ra", "focus"): (
        "Nói hoặc nhắn đúng một câu bắt đầu bằng “Mình thấy…” ngay trong hôm nay, rồi dừng ở đó."
    ),
    ("noi_ra", "next"): (
        "Viết điều muốn nói thành một câu dưới hai mươi chữ, rồi đọc to một lần để nghe nó có "
        "đúng ý không."
    ),
    ("noi_ra", "alternative"): (
        "Khi bạn định cười cho qua, nói một câu ngắn: “Chỗ này mình thấy không ổn lắm.”"
    ),
    ("noi_ra", "criterion"): (
        "Trả lời một câu trên giấy: “Nếu im thêm một tháng, mình có còn thấy ổn không?”"
    ),
    ("noi_ra", "opening"): "Mở lời: “Mình có một chuyện muốn nói, bạn có năm phút không?”",
    ("nhan_lai", "focus"): (
        "Nhắn một câu ngắn trong mười phút tới, không cần chờ nghĩ ra tin hoàn hảo."
    ),
    ("nhan_lai", "next"): (
        "Gửi một tin ngắn và đặt điện thoại xuống ba mươi phút trước khi xem lại."
    ),
    ("nhan_lai", "alternative"): "Khi bạn gõ rồi xóa đến lần thứ ba, gửi luôn phiên bản ngắn nhất.",
    ("nhan_lai", "criterion"): (
        "Viết ra điều bạn muốn tin nhắn này làm được, như hỏi thăm hay chốt lịch, và chọn cách "
        "nhắn đúng điều đó."
    ),
    ("nhan_lai", "opening"): "Mở lời: “Xin lỗi mình trả lời muộn, mình đọc tin bạn rồi đây.”",
    ("hoi_lai", "focus"): (
        "Khi còn một chỗ chưa rõ, nhắn đúng một câu hỏi về chỗ đó: “Phần này bạn muốn nói là…?”"
    ),
    ("hoi_lai", "next"): "Nhắc lại điều bạn hiểu bằng một câu rồi hỏi “mình hiểu vậy đúng không?”.",
    ("hoi_lai", "alternative"): (
        "Khi bạn định gật đầu cho qua, nói “cho mình hỏi lại chỗ này chút”."
    ),
    ("hoi_lai", "criterion"): (
        "Viết ra một chi tiết mà nếu biết rõ thì bạn chọn được ngay, và hỏi đúng chi tiết đó."
    ),
    ("hoi_lai", "opening"): "Mở lời: “Mình muốn hỏi lại chỗ này cho rõ, ý bạn là…?”",
    ("cho_them", "focus"): "Đặt một mốc chờ cụ thể, ví dụ tối thứ Sáu, và ghi nó vào lịch.",
    ("cho_them", "next"): (
        "Đặt nhắc hẹn ba ngày nữa với một câu hỏi: “Từ hôm nay đến giờ, điều gì đã khác?”"
    ),
    ("cho_them", "alternative"): (
        "Khi bạn định lật điện thoại lên xem lần nữa, đặt nó sang phòng khác mười lăm phút."
    ),
    ("cho_them", "criterion"): (
        "Chọn khoảng thời gian dài nhất bạn sẵn lòng chờ, và ghi mốc đó vào lịch."
    ),
    ("cho_them", "opening"): (
        "Mở lời: “Mình cần thêm vài ngày để nghĩ, thứ Sáu mình trả lời bạn nhé.”"
    ),
    ("bat_dau", "focus"): "Đặt hẹn giờ mười phút và làm đúng một bước mở đầu, hết giờ thì dừng.",
    ("bat_dau", "next"): "Làm thử mười phút và ghi lại một điều bạn thích, một điều bạn thấy khó.",
    ("bat_dau", "alternative"): (
        "Khi bạn định chờ có đủ thời gian rảnh, làm mười phút ngay trong khoảng trống đang có."
    ),
    ("bat_dau", "criterion"): (
        "Ghi ra số giờ tối đa bạn dành được mỗi tuần, và chỉ chọn cách bắt đầu vừa với con số đó."
    ),
    ("bat_dau", "opening"): (
        "Mở lời: “Mình đang muốn bắt đầu việc này, bạn làm cùng mình buổi đầu không?”"
    ),
    ("dung_lai", "focus"): "Khi đến mốc giờ bạn đặt, tắt màn hình ngay, kể cả khi việc còn dở.",
    ("dung_lai", "next"): "Dừng đúng một lần hôm nay và ghi lại điều bạn thấy ngay sau đó.",
    ("dung_lai", "alternative"): (
        "Khi tay bạn định mở lại ứng dụng đó, đặt điện thoại sang phòng khác."
    ),
    # Wiring edit: shorter so the Roast lead-in stays within 28 words, and no longer ends like
    # tap_trung/next ("… tờ giấy dán ở màn hình").
    ("dung_lai", "criterion"): (
        "Chọn một dấu hiệu dừng, ví dụ đồng hồ chỉ tám giờ, và ghi nó lên một mẩu giấy dán "
        "cạnh bàn."
    ),
    ("dung_lai", "opening"): "Mở lời: “Mình xin dừng ở đây hôm nay, mai mình nói tiếp nhé.”",
    ("doi_viec", "focus"): (
        "Viết ra ba điều bạn muốn có ở công việc tiếp theo, chỉ trong mười phút."
    ),
    ("doi_viec", "next"): (
        "Nhắn hỏi một người đang làm ở hướng bạn quan tâm: một ngày làm việc của họ thế nào."
    ),
    ("doi_viec", "alternative"): (
        "Khi bạn mở trang tuyển dụng lúc đang mệt, ghi một dòng về điều hôm nay làm bạn mệt nhất."
    ),
    ("doi_viec", "criterion"): (
        "Viết ra một điều bạn không muốn đánh đổi, như giờ về nhà hay việc học, và chấm hai hướng "
        "theo điều đó."
    ),
    ("doi_viec", "opening"): (
        "Mở lời: “Mình đang tìm hiểu một hướng mới, bạn kể mình nghe công việc của bạn được không?”"
    ),
    ("xin_gop_y", "focus"): "Nhắn một người bạn tin để xin năm phút góp ý cho một phần cụ thể.",
    ("xin_gop_y", "next"): (
        "Hỏi một người một câu cụ thể về phần bạn băn khoăn nhất, và ghi lại câu trả lời."
    ),
    ("xin_gop_y", "alternative"): (
        "Khi bạn định tự sửa thêm một lần nữa, gửi bản hiện tại cho một người đọc trước."
    ),
    ("xin_gop_y", "criterion"): (
        "Viết ra bạn cần góp ý về điều gì, nội dung hay cách trình bày, và chọn người hợp với "
        "đúng điều đó."
    ),
    ("xin_gop_y", "opening"): (
        "Mở lời: “Bạn đọc giúp mình phần này năm phút được không? Mình muốn biết chỗ nào khó hiểu.”"
    ),
    ("nghi_ngoi", "focus"): "Khi mắt bắt đầu cay, gập máy lại và nằm xuống mười phút.",
    ("nghi_ngoi", "next"): "Đi ngủ sớm hơn ba mươi phút tối nay, không cần bù việc vào lúc khác.",
    ("nghi_ngoi", "alternative"): (
        "Khi bạn định nghỉ “sau khi xong việc này”, nghỉ ngay mười phút trước đã."
    ),
    ("nghi_ngoi", "criterion"): (
        "Chọn một giờ cố định để dừng việc tối nay và ghi nó vào lịch như một cuộc hẹn."
    ),
    ("nghi_ngoi", "opening"): (
        "Mở lời: “Hôm nay mình hết sức rồi, mình xin nghỉ, mai mình trả lời nhé.”"
    ),
    ("gui_di", "focus"): "Khi bản nháp đã đọc xong một lần, bấm gửi mà không sửa thêm.",
    ("gui_di", "next"): "Gửi đi hôm nay và ghi lại cảm giác của bạn ngay sau đó.",
    ("gui_di", "alternative"): "Khi bạn định sửa thêm một dấu phẩy, dừng tay và bấm gửi.",
    ("gui_di", "criterion"): (
        "Chọn một giờ muộn nhất để gửi đi hôm nay, kể cả khi bản đó chưa hoàn hảo."
    ),
    ("gui_di", "opening"): "Mở lời: “Mình gửi bạn bản này, bạn xem khi tiện nhé.”",
    ("xin_loi", "focus"): "Nhắn một câu xin lỗi nói đúng việc bạn đã làm, chưa kèm lời giải thích.",
    ("xin_loi", "next"): (
        "Nói lời xin lỗi ngắn và nghe hết phản hồi trước khi giải thích thêm điều gì."
    ),
    ("xin_loi", "alternative"): (
        "Khi bạn định im lặng chờ chuyện tự qua, gửi một câu: “Mình xin lỗi về chuyện hôm trước.”"
    ),
    ("xin_loi", "criterion"): (
        "Viết ra đúng việc bạn muốn nhận lỗi, tách khỏi phần bạn thấy chưa công bằng."
    ),
    ("xin_loi", "opening"): (
        "Mở lời: “Mình xin lỗi về câu mình nói lần trước. Mình muốn nghe bạn nói.”"
    ),
    ("hen_gap", "focus"): "Nhắn đề nghị hai khung giờ bạn thật sự rảnh, để người kia chọn.",
    ("hen_gap", "next"): "Hỏi người kia tuần này rảnh buổi nào trước khi chọn quán.",
    ("hen_gap", "alternative"): (
        "Khi bạn gõ lời rủ rồi lại xóa, gửi bản ngắn nhất: “Cuối tuần đi cà phê không?”"
    ),
    ("hen_gap", "criterion"): (
        "Viết ra điều bạn muốn có từ buổi gặp, như trò chuyện hay chốt việc, và chọn kiểu gặp hợp "
        "với điều đó."
    ),
    ("hen_gap", "opening"): "Mở lời: “Bạn rảnh lúc nào để mình hẹn gặp và nói chuyện một chút?”",
    ("chia_se", "focus"): (
        "Kể với một người bạn tin đúng một câu về chuyện bạn đang mang, không cần kể hết."
    ),
    ("chia_se", "next"): "Chia sẻ một phần nhỏ với một người và ghi lại bạn thấy thế nào sau đó.",
    ("chia_se", "alternative"): (
        "Khi bạn định trả lời “mình ổn”, nói thêm một câu thật: “Thật ra hôm nay hơi mệt.”"
    ),
    ("chia_se", "criterion"): (
        "Chọn một người từng giữ chuyện riêng của bạn cẩn thận, và chia sẻ với người đó trước."
    ),
    ("chia_se", "opening"): (
        "Mở lời: “Mình muốn kể bạn nghe một chuyện, bạn chỉ cần nghe thôi nhé.”"
    ),
    ("dat_ranh_gioi", "focus"): (
        "Khi có người hỏi tới chuyện bạn không muốn kể, nói một câu ngắn: “Chuyện này mình xin "
        "giữ riêng.”"
    ),
    ("dat_ranh_gioi", "next"): (
        "Đặt một giới hạn nhỏ, ví dụ không trả lời việc sau chín giờ tối, và giữ nó tối nay."
    ),
    ("dat_ranh_gioi", "alternative"): (
        "Khi bạn định cười gượng cho qua, nói “chuyện này mình không muốn bàn” bằng giọng bình "
        "thường."
    ),
    ("dat_ranh_gioi", "criterion"): (
        "Chọn một việc cụ thể bạn thôi làm từ hôm nay, như trả lời tin sau chín giờ tối."
    ),
    ("dat_ranh_gioi", "opening"): "Mở lời: “Mình quý bạn, nhưng chuyện này mình muốn giữ riêng.”",
    ("ket_thuc", "focus"): "Viết một câu về lý do bạn muốn kết thúc, chỉ để riêng bạn đọc.",
    ("ket_thuc", "next"): (
        "Viết hai dòng, điều bạn giữ lại và điều bạn khép lại, và đọc lại vào ngày mai."
    ),
    ("ket_thuc", "alternative"): (
        "Khi bạn định nhắn thêm để kéo dài, viết tin đó vào ghi chú thay vì gửi."
    ),
    ("ket_thuc", "criterion"): (
        "Viết ra điều bạn cần mà chuyện này không còn đáp ứng, càng cụ thể càng tốt."
    ),
    ("ket_thuc", "opening"): (
        "Mở lời: “Mình muốn dừng chuyện này, và mình muốn nói với bạn trực tiếp.”"
    ),
    ("thu_lai", "focus"): (
        "Chọn một chỗ lần trước chưa ổn và làm lại đúng chỗ đó trong mười phút hôm nay."
    ),
    ("thu_lai", "next"): "Làm lại một phần nhỏ theo cách khác lần trước và ghi lại điều khác đi.",
    ("thu_lai", "alternative"): (
        "Khi bạn định làm lại y như lần trước, đổi một chi tiết nhỏ trước khi bắt đầu."
    ),
    ("thu_lai", "criterion"): (
        "Viết ra một điều đã khác so với lần trước, và dùng nó làm căn cứ để chốt có làm lại không."
    ),
    ("thu_lai", "opening"): "Mở lời: “Lần trước mình nói hơi nhanh, cho mình nói lại một lần nhé?”",
    ("hoc_them", "focus"): "Học đúng mười phút hôm nay với bài ngắn nhất bạn tìm được.",
    ("hoc_them", "next"): "Học một buổi ngắn và ghi lại một điều bạn hiểu thêm.",
    ("hoc_them", "alternative"): (
        "Khi bạn định lưu thêm một khóa học, mở bài đầu của khóa đã lưu và học năm phút."
    ),
    ("hoc_them", "criterion"): (
        "Viết ra bạn học để làm gì, cho việc hay cho vui, và chọn cách học hợp với mục đích đó."
    ),
    ("tap_trung", "focus"): "Úp điện thoại xuống bàn và làm một việc duy nhất trong mười phút tới.",
    ("tap_trung", "next"): (
        "Chọn một việc quan trọng nhất hôm nay và viết nó lên tờ giấy dán ở màn hình."
    ),
    ("tap_trung", "alternative"): (
        "Khi tay bạn định mở tab mới, ghi việc đó ra giấy nháp và quay lại việc đang làm."
    ),
    ("tap_trung", "criterion"): (
        "Viết ra việc nào xong hôm nay thì các việc khác nhẹ đi, và chọn nó làm việc chính."
    ),
    ("sap_xep_lai", "focus"): (
        "Mở lịch tuần này và dời đúng một việc từ ngày dồn nhất sang ngày trống hơn."
    ),
    ("sap_xep_lai", "next"): (
        "Xếp lại danh sách việc theo hạn chót và đánh dấu việc nào đang nằm sai chỗ."
    ),
    ("sap_xep_lai", "alternative"): (
        "Khi bạn định thêm việc vào ngày đã kín, đặt nó sang ngày còn trống gần nhất."
    ),
    ("sap_xep_lai", "criterion"): (
        "Viết ra một khoảng giờ bạn muốn giữ nguyên dù lịch có đổi, và xếp các việc quanh nó."
    ),
    ("sap_xep_lai", "opening"): (
        "Mở lời: “Thứ Sáu mình bị trùng việc, mình dời sang thứ Bảy được không?”"
    ),
    ("nho_giup", "focus"): "Gửi lời nhờ cho đúng một việc nhỏ ngay hôm nay.",
    ("nho_giup", "next"): "Nhờ một việc nhỏ trước và ghi lại cảm giác của bạn khi được giúp.",
    ("nho_giup", "alternative"): (
        "Khi bạn định nói “thôi để mình làm”, đổi thành “bạn làm phần này giúp mình nhé”."
    ),
    ("nho_giup", "criterion"): (
        "Chọn việc chiếm nhiều giờ nhất mà không cần đúng bạn làm, và nhờ việc đó trước."
    ),
    ("nho_giup", "opening"): "Mở lời: “Mình đang hơi quá tải, bạn giúp mình phần này được không?”",
    ("gop_y", "focus"): "Nói một góp ý về một việc cụ thể, kèm một điều bạn thấy đã làm tốt.",
    ("gop_y", "next"): "Hỏi trước “mình góp một ý được không?”, và chỉ nói khi người kia gật đầu.",
    ("gop_y", "alternative"): "Khi bạn định nói “ổn mà”, nói thêm một chỗ cụ thể sửa được.",
    ("gop_y", "criterion"): (
        "Chọn một tiêu chí: góp ý về việc làm, không nói về con người, và lọc lại những ý định nói."
    ),
    ("gop_y", "opening"): "Mở lời: “Bạn có muốn nghe một góp ý của mình về chuyện này không?”",
    ("de_xuat", "focus"): "Viết đề xuất của bạn thành ba dòng: vấn đề, cách làm, bước bắt đầu.",
    ("de_xuat", "next"): "Đưa đề xuất cho một người đọc trước và hỏi họ chỗ nào chưa rõ.",
    ("de_xuat", "alternative"): (
        "Khi bạn định giữ ý tưởng trong sổ, đọc nó lên ở lượt nói tiếp theo."
    ),
    ("de_xuat", "criterion"): (
        "Viết ra đề xuất này giúp được ai và bớt được việc gì, và dùng nó để chốt có đưa ra không."
    ),
    ("de_xuat", "opening"): (
        "Mở lời: “Mình có một cách làm khác cho phần này, mọi người nghe hai phút nhé?”"
    ),
    ("don_dep", "focus"): (
        "Đặt hẹn giờ mười phút và dọn đúng một bề mặt, như mặt bàn hay chiếc ghế."
    ),
    ("don_dep", "next"): (
        "Dọn một góc nhỏ trong mười phút và ghi lại bạn có muốn ngồi ở đó lâu hơn không."
    ),
    ("don_dep", "alternative"): (
        "Khi bạn định đặt thêm đồ lên chiếc ghế, cất món đó vào đúng chỗ của nó."
    ),
    ("don_dep", "criterion"): (
        "Viết ra một góc bạn muốn dùng được trở lại, và chỉ dọn góc đó trước."
    ),
    ("ra_ngoai", "focus"): "Ra khỏi nhà mười phút, đi bộ đến đầu ngõ hoặc tiệm gần nhất.",
    ("ra_ngoai", "next"): "Ra ngoài một lần ngắn hôm nay và ghi lại tâm trạng khi về.",
    ("ra_ngoai", "alternative"): "Khi bạn định nằm lướt điện thoại tiếp, đi giày và bước ra cửa.",
    ("ra_ngoai", "criterion"): (
        "Viết ra điều bạn muốn có khi ra ngoài, gặp người hay đổi không khí, và chọn nơi hợp với "
        "điều đó."
    ),
    ("o_nha", "focus"): (
        "Chọn một việc bạn thích làm ở nhà tối nay và chuẩn bị sẵn nó ngay bây giờ."
    ),
    ("o_nha", "next"): (
        "Ở nhà tối nay với một việc bạn chọn trước, như nấu một món hay xem một bộ phim."
    ),
    ("o_nha", "alternative"): (
        "Khi bạn định nhận lời đi chơi chỉ vì ngại từ chối, trả lời “tối nay mình ở nhà nhé”."
    ),
    ("o_nha", "criterion"): (
        "Viết ra điều bạn cần nhất tối nay, nghỉ ngơi hay gặp người, và chọn ở nhà hay đi theo "
        "điều đó."
    ),
    ("doi_thoi_quen", "focus"): "Đặt điện thoại sạc ở ngoài phòng ngủ tối nay.",
    ("doi_thoi_quen", "next"): (
        "Ghi lại giờ thói quen đó bắt đầu trong ba tối liền, chưa cần đổi gì."
    ),
    ("doi_thoi_quen", "alternative"): (
        "Khi đến giờ quen thuộc của thói quen cũ, đứng dậy rót một ly nước."
    ),
    ("doi_thoi_quen", "criterion"): (
        "Chọn một thay đổi bạn giữ được bảy ngày, và bỏ qua những thay đổi lớn hơn thế."
    ),
    ("tu_thuong", "focus"): (
        "Chọn một món tự thưởng nhỏ hôm nay, như ly trà bạn thích, và thưởng thức nó mà không làm "
        "việc khác."
    ),
    ("tu_thuong", "next"): (
        "Kể cho một người nghe việc bạn vừa làm xong, không thêm câu “cũng may thôi”."
    ),
    ("tu_thuong", "alternative"): (
        "Khi bạn định mở ngay việc tiếp theo, dừng mười phút để ăn một món bạn thích."
    ),
    ("tu_thuong", "criterion"): (
        "Chọn một mốc rõ để tự thưởng, như gạch xong dòng cuối, và thưởng ngay khi tới mốc."
    ),
    ("viet_ra", "focus"): (
        "Đặt hẹn giờ năm phút và viết ra mọi thứ đang trong đầu, không cần sắp xếp."
    ),
    ("viet_ra", "next"): "Ghi lại một việc mỗi tối trong ba ngày và đọc lại vào ngày thứ tư.",
    ("viet_ra", "alternative"): (
        "Khi đầu óc bắt đầu xoay vòng lúc nửa đêm, ghi việc đó vào tờ giấy cạnh giường."
    ),
    ("viet_ra", "criterion"): "Viết mỗi lựa chọn lên một cột và ghi dưới mỗi cột điều bạn lo nhất.",
}

# Wiring condition 1 of the delegated decision: an opening must read naturally for every topic of
# its action. These topics get their own opening (authored in the wiring PR, Claude, 27/10/2026).
ACTION_OPENINGS_BY_TOPIC: dict[tuple[str, str], str] = {
    ("nhan_lai", "relationships"): "Mở lời: “Mình đọc tin rồi, giờ mình nhắn lại đây.”",
    ("nhan_lai", "communication"): (
        "Mở lời: “Mình nhắn lại về chuyện lúc trước, mình muốn nói thêm một chút.”"
    ),
    ("cho_them", "relationships"): (
        "Mở lời: “Mình cần chút thời gian để nghĩ, vài hôm nữa mình nhắn bạn nhé.”"
    ),
    ("bat_dau", "relationships"): (
        "Mở lời: “Mình muốn cùng bạn bắt đầu một việc nhỏ, bạn nghe mình kể nhé?”"
    ),
    ("bat_dau", "self_care"): (
        "Mở lời: “Mỗi sáng mình giữ mười phút cho riêng mình, lúc đó mình chưa trả lời tin "
        "nhắn nhé.”"
    ),
    ("xin_gop_y", "relationships"): (
        "Mở lời: “Mình muốn nghe bạn nghĩ thật về chuyện này, bạn nói thẳng giúp mình nhé.”"
    ),
    ("gui_di", "relationships"): "Mở lời: “Mình có cái này muốn gửi bạn, bạn xem khi tiện nhé.”",
    ("xin_loi", "general"): (
        "Mở lời: “Mình xin lỗi về chuyện vừa rồi, phần đó là lỗi của mình. Mình muốn nghe bạn nói.”"
    ),
    ("xin_loi", "work"): (
        "Mở lời: “Mình xin lỗi về chuyện vừa rồi, phần đó là lỗi của mình. Mình muốn nghe bạn nói.”"
    ),
    ("dat_ranh_gioi", "work"): (
        "Mở lời: “Ngoài giờ làm mình ít xem tin nhắn, việc gấp thì bạn gọi mình nhé.”"
    ),
    ("dat_ranh_gioi", "energy"): (
        "Mở lời: “Dạo này mình cần nghỉ nhiều hơn, tuần này mình chỉ nhận một buổi gặp thôi nhé.”"
    ),
    ("dat_ranh_gioi", "self_care"): (
        "Mở lời: “Dạo này mình cần giữ khoảng cách một chút, mình nói trước để bạn biết.”"
    ),
    ("thu_lai", "general"): (
        "Mở lời: “Mình định thử lại chuyện này lần nữa, bạn nhắc mình giữ lời nhé?”"
    ),
    ("thu_lai", "relationships"): (
        "Mở lời: “Mình muốn thử nói chuyện lại một lần nữa, bạn cho mình vài phút nhé?”"
    ),
    ("thu_lai", "work"): (
        "Mở lời: “Mình định thử lại chuyện này lần nữa, bạn nhắc mình giữ lời nhé?”"
    ),
    ("thu_lai", "self_care"): (
        "Mở lời: “Mình định thử lại chuyện này lần nữa, bạn nhắc mình giữ lời nhé?”"
    ),
    ("sap_xep_lai", "energy"): (
        "Mở lời: “Từ tuần này mình ngủ sớm hơn, sau mười giờ mình trả lời bạn vào sáng hôm sau "
        "nhé.”"
    ),
    ("sap_xep_lai", "self_care"): (
        "Mở lời: “Mình đang xếp lại lịch tuần này cho đỡ dồn, mình dời việc này sang hôm khác "
        "được không?”"
    ),
    ("de_xuat", "relationships"): (
        "Mở lời: “Mình có một ý muốn đề xuất, bạn nghe mình nói hai phút nhé?”"
    ),
}

# Scene rows that presume a romantic partner or a date ("người yêu", "người cũ", a first
# coffee, "buổi hẹn"). The relationships topic also covers family and friends, so these rows show
# only when the question names a partner (question_frame.names_partner); otherwise the action's
# ``general`` row stands in. Codex r47: the scene must not invent who the other person is.
PARTNER_SCENES: frozenset[tuple[str, str]] = frozenset(
    (action, "relationships")
    for action in (
        "bat_dau",
        "chia_se",
        "doi_thoi_quen",
        "dung_lai",
        "gop_y",
        "hen_gap",
        "hoi_lai",
        "ket_thuc",
        "nhan_lai",
        "nhan_loi",
        "nho_giup",
        "noi_ra",
        "o_nha",
        "sap_xep_lai",
        "thu_lai",
        "tu_choi",
    )
)

# Preparation steps (Codex r47): when the cards ask for more care ("cân nhắc thêm"), pull two
# ways or answer a "when" question with what to have ready, the step role prepares the asked
# action instead of carrying it out. Self-care and boundary actions keep their own step
# (stance.SELF_CARE_ACTIONS, owner decision 2026-10-19). "choice" is the step of a two-option
# question the cards do not settle: it names neither option.
PREP_STEPS: dict[str, str] = {
    "nhan_loi": (
        "Trước khi trả lời lời mời, mở lịch và ghi ra một việc bị lùi lại nếu bạn nhận lời."
    ),
    "noi_ra": (
        "Viết điều bạn muốn nói thành một câu, để qua một đêm và sáng mai đọc lại xem còn đúng ý "
        "không."
    ),
    "nhan_lai": (
        "Gõ tin bạn định gửi vào ghi chú, ba mươi phút sau đọc lại rồi mới chọn gửi hay sửa."
    ),
    "hoi_lai": (
        "Ghi ra đúng một chỗ bạn chưa hiểu, kèm điều bạn đang đoán về chỗ đó, trước khi nhắn hỏi."
    ),
    "cho_them": (
        "Ghi vào lịch một ngày để xem lại chuyện này, và đến ngày đó mới chốt chờ tiếp hay thôi."
    ),
    "bat_dau": (
        "Ghi ra một thứ cần có sẵn để bắt đầu, như giờ rảnh hay dụng cụ, và kiểm xem đã có chưa."
    ),
    "doi_viec": (
        "Trong mười phút, ghi ra hai điều bạn muốn giữ ở công việc hiện tại và hai điều bạn muốn "
        "đổi."
    ),
    "xin_gop_y": (
        "Đánh dấu đúng một phần bạn muốn được góp ý, và viết một câu hỏi cụ thể cho phần đó."
    ),
    "gui_di": "Đọc lại bản này một lượt và ghi ra một điều bạn muốn người nhận hiểu đúng nhất.",
    "xin_loi": (
        "Viết câu xin lỗi vào ghi chú, đọc to một lần, rồi gạch bớt những chữ đang biện minh."
    ),
    "hen_gap": "Mở lịch và khoanh hai khung giờ bạn thật sự rảnh, chưa cần nhắn rủ ngay.",
    "chia_se": ("Viết ra một câu bạn muốn kể và một phần bạn muốn giữ riêng, trước khi kể với ai."),
    "ket_thuc": (
        "Viết hai cột, điều chuyện này còn cho bạn và điều nó không còn đáp ứng, rồi để đó một "
        "ngày."
    ),
    "thu_lai": "Ghi ra điều khiến lần trước chưa ổn và một chi tiết bạn đổi được ở lần này.",
    "hoc_them": (
        "Ghi ra bạn muốn học để làm gì trong một câu, rồi xem bài đầu mà chưa đăng ký khóa nào."
    ),
    "tap_trung": (
        "Ghi ra ba việc đang kéo sự chú ý của bạn, và khoanh việc nào xong thì các việc kia nhẹ đi."
    ),
    "sap_xep_lai": "Mở lịch tuần này và đánh dấu những ngày đang dồn việc, chưa cần dời việc nào.",
    "gop_y": (
        "Viết góp ý bạn định nói ra giấy, giữ ý về việc làm và gạch những ý nói về con người."
    ),
    "de_xuat": (
        "Viết đề xuất thành ba dòng, vấn đề, cách làm, bước đầu, rồi đọc lại xem dòng nào còn "
        "thiếu."
    ),
    "don_dep": "Đi một vòng và ghi ra góc bạn muốn dùng lại trước tiên, chưa cần dọn ngay.",
    "ra_ngoai": (
        "Ghi ra bạn muốn ra ngoài để làm gì, gặp người hay đổi không khí, rồi chọn một chỗ gần nhà."
    ),
    "o_nha": "Ghi ra điều bạn cần nhất tối nay, nghỉ hay gặp người, trước khi trả lời lời rủ.",
    "doi_thoi_quen": "Ghi ra lúc thói quen cũ hay bắt đầu và việc bạn thường làm ngay trước đó.",
    "viet_ra": "Ghi một dòng về điều đang chiếm đầu bạn nhất, chưa cần viết hết mọi thứ.",
    "choice": (
        "Viết hai lựa chọn thành hai cột, dưới mỗi cột ghi điều bạn được và điều bạn lo nhất."
    ),
}
CHOICE_STEP = "choice"


class StepMode(StrEnum):
    ACT = "act"  # the asked action's own step
    PREPARE = "prepare"  # a preparation step for the same action
    CHOOSE = "choose"  # a two-option question the cards do not settle


@dataclass(frozen=True)
class StepPlan:
    """What the step role says, decided from closed labels: the frame and the stance."""

    action: TarotAction | None
    mode: StepMode
    cautious: bool  # the cards ask for care first: no "do it now" lead-in either


_CAUTIOUS = frozenset(
    {TarotStanceLevel.CONSIDER, TarotStanceLevel.UNCLEAR, TarotStanceLevel.CLARIFY_CHOICE}
)


def plan_step(frame: QuestionFrame | None, reading_stance: TarotStance | None) -> StepPlan:
    """The step role's copy for the whole reading (Codex r47): the asked action's step only when
    the reading leans toward trying it or the question asks how; a preparation step when the
    cards ask for care, pull two ways or the question asks when; for a choice, the chosen
    option's step, or a step that names neither option when the cards do not choose."""

    if frame is None:
        return StepPlan(None, StepMode.ACT, cautious=False)
    cautious = frame.form is TarotQuestionForm.TIMING or (
        reading_stance is not None and reading_stance.level in _CAUTIOUS
    )
    if frame.form is TarotQuestionForm.CHOICE:
        if (
            reading_stance is not None
            and reading_stance.level is TarotStanceLevel.LEAN_TRY
            and reading_stance.action is not None
        ):
            return StepPlan(reading_stance.action, StepMode.ACT, cautious=False)
        mode = StepMode.CHOOSE if frame.action is not None else StepMode.ACT
        return StepPlan(None, mode, cautious)
    action = frame.action
    if action is None or action in SELF_CARE_ACTIONS or not cautious:
        return StepPlan(action, StepMode.ACT, cautious)
    return StepPlan(action, StepMode.PREPARE, cautious)


def action_scene(
    action: TarotAction | None, topic: TarotContext, *, partner: bool = True
) -> str | None:
    """The action's scene for the topic, else its ``general`` scene; None without an action.

    ``partner`` False (the question names no partner) skips the rows in PARTNER_SCENES."""

    if action is None:
        return None
    key = (action.value, topic.value)
    if not partner and key in PARTNER_SCENES:
        key = (action.value, TarotContext.GENERAL.value)
    return ACTION_SCENES.get(key) or ACTION_SCENES.get((action.value, TarotContext.GENERAL.value))


def action_step(action: TarotAction | None, role: str, topic: TarotContext) -> str | None:
    """The action's step for a step role (an opening may depend on the topic); None if absent."""

    if action is None:
        return None
    if role == "opening":
        by_topic = ACTION_OPENINGS_BY_TOPIC.get((action.value, topic.value))
        if by_topic is not None:
            return by_topic
    return ACTION_STEPS.get((action.value, role))
