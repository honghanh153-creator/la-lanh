# US-25 — Hỏi Lá bằng lá số (hỏi về tháng này)

> Nguồn: owner chọn AK2 ngày 20.11.2026 sau thử 100 người giả (thiết kế A3: chủ đề tháng + một việc
> làm ngay + một câu mẫu; ngày chỉ hiện khi bấm "Xem lúc nào dễ hơn"). Báo cáo và bản mô tả nằm trên
> máy owner, ngoài repo; ở đây chỉ ghi hành vi.
>
> Owner chọn AS1 ngày 21.11.2026: không có ô gõ câu hỏi. Thay vào đó là câu hỏi làm sẵn để chọn
> (3 câu mỗi mảng, lấy từ điều người giả muốn hỏi nhiều nhất). Không thu chữ người dùng gõ nên không
> có câu đồng ý hay câu khủng hoảng riêng cho màn này.

## User story

Là người đang có chuyện cần lo trong tháng, tôi muốn hỏi Lá theo lá số của mình (chọn một mảng hoặc
một câu hỏi làm sẵn) và nhận một hướng nhìn cho tháng này, một việc làm được ngay và một câu mẫu để nói. Lá
không đoán chuyện gì sẽ xảy ra, không trả lời có/không, và chỉ cho tôi xem khoảng ngày dễ hơn khi tôi
tự bấm.

## Phạm vi

Bao gồm (PR theo thứ tự):

1. API và lõi tính (PR này): `/v1/month/status`, `/v1/month/answers`, `/v1/month/window`,
   `/v1/month/overview`; câu chữ chờ duyệt; 18 câu hỏi làm sẵn.
2. Lưu chủ động: bảng riêng mã hóa, danh sách riêng, xóa được, có trong xuất dữ liệu và xóa tài khoản.
3. Web: nút "Hỏi về tháng này" cạnh "Rút Tarot", màn hỏi, thẻ "Tháng này của bạn" trong Khám phá,
   lời nhắc đầu tuần (tắt sẵn).
4. Chạy 1000 người giả: mọi mảng và câu làm sẵn đều trả lời, không lẫn dữ liệu giữa người.

Không bao gồm: ô gõ câu hỏi (owner chọn AS1), báo trước sự kiện, "ngày xấu", bộ đếm câu hỏi, nhắc hỏi
thêm, gửi câu hỏi cho AI ngoài.

## Acceptance Criteria

| AC | Nội dung | Kiểm bằng |
|---|---|---|
| AC01 | Chọn một trong 6 mảng (Công việc, Tiền, Tình cảm, Gia đình, Học, Sức khỏe tinh thần) cho ra câu trả lời 3 phần: "Tháng này của bạn ở chuyện này", "Có thể làm ngay", "Có thể nói". | `test_api.py::test_topic_answer_has_three_parts_basis_and_no_date` |
| AC02 | Có dòng "Dựa vào: <hành tinh> × <nhà>" từ transit thật trong tháng, bấm xem thêm được; và dòng "Đây là một góc nhìn để bạn tự quyết, không phải điều chắc chắn sẽ xảy ra." | `test_facts.py::test_in_house_fact_is_true_on_the_days_it_counts`, `test_api.py` |
| AC03 | Cùng lá số + mảng + tháng cho cùng câu trả lời; không dùng AI ngoài. | `test_facts.py::test_same_chart_topic_month_gives_the_same_fact`, `test_api.py::test_answers_are_deterministic_over_http` |
| AC04 | Không đoán sự kiện, không có/không. Câu làm sẵn đều là câu hỏi "làm sao", không có câu hỏi kết quả hay "có nên". | `test_copy.py::test_no_prediction_no_date_no_yes_no`, `test_api.py::test_every_preset_answers_without_yes_no` |
| AC05 | Câu trả lời không có ngày. Khoảng ngày chỉ đến từ yêu cầu riêng khi bấm "Xem lúc nào dễ hơn", chỉ là khoảng dễ hơn (≤ 3 ngày, từ hôm nay), kèm "Làm lúc nào cũng được; khoảng này chỉ dễ hơn một chút." Không có "ngày xấu". | `test_api.py::test_window_only_on_its_own_request`, `test_facts.py::test_window_is_real_short…` |
| AC06 | Không tự lưu: hỏi, xem khoảng ngày, xem thẻ tháng không ghi dòng nào. | `test_api.py::test_answering_stores_nothing` |
| AC07 | Thẻ tháng trong Khám phá: 4 mảng (Công việc, Tình cảm, Tiền, Bản thân), mỗi mảng một dòng và một việc nhỏ, không ngày. | `test_api.py::test_overview_card_has_four_areas_and_no_dates` |
| AC08 | Mỗi mảng có 3 câu hỏi làm sẵn (18 câu). Chọn một câu thì câu trả lời có thêm chính câu hỏi đó và một việc cụ thể cho tình huống ấy ("Với câu này"); 3 phần còn lại và dòng "Dựa vào" vẫn lấy từ lá số, giống khi chọn mảng. | `test_api.py::test_preset_question_answer`, `test_facts.py::test_preset_answer_keeps_the_chart_parts`, `test_copy.py::test_three_preset_questions_per_topic_each_with_a_tip` |
| AC09 | Câu làm sẵn phải thuộc đúng mảng đã chọn; sai thì từ chối (422). | `test_api.py::test_preset_must_match_its_topic` |
| AC10 | Không có ô gõ: yêu cầu kèm chữ tự do bị từ chối ở bước kiểm tra dữ liệu, không đọc, không lặp lại. Không có câu đồng ý, câu khủng hoảng hay công tắc cho câu gõ. | `test_api.py::test_free_text_is_not_accepted`, `test_copy.py::test_month_copy_is_pending_user_copy_and_no_typed_question_copy_ships` |
| AC11 | Tính năng chỉ hiện khi mọi câu chữ đã được duyệt (`/v1/month/status.available`); chưa duyệt thì trả "chưa sẵn sàng", không trả nửa câu. | `test_api.py::test_status_*`, `test_pending_copy_answers_unavailable_not_half` |
| AC12 | Lưu chủ động, mục riêng, xóa được; máy chủ tự tính lại câu trả lời, không nhận chữ từ máy khách; có trong xuất dữ liệu; xóa có nhật ký; xóa giờ/nơi sinh thì xóa theo. | `test_saved.py` |
| AC13 | Nút trên Trang chủ cạnh "Rút Tarot"; nút ngày thu gọn sẵn; không nhắc, không đếm; không hiện câu trả lời trên Trang chủ; lời nhắc đầu tuần tắt sẵn. Màn hỏi có 6 mảng và danh sách câu hỏi làm sẵn theo mảng, không có ô gõ; câu trả lời có "Câu hỏi khác về chuyện này". Nhãn giao diện `month.ui.*` cũng chờ duyệt; màn chỉ hiện khi duyệt đủ. | `apps/web/src/features/month/MonthAskPage.test.tsx`, `HomePage.test.tsx`, `monthCopy.test.ts` |
| AC14 | 1000 người giả: mọi mảng và câu làm sẵn đều trả lời, không lẫn dữ liệu giữa người. | PR 4 |

## Cách tính (tóm tắt)

- Nhà: giờ sinh chính xác dùng nhà của lá số; còn lại dùng nhà tính theo cung Mặt Trời. Ngày sinh rơi
  đúng ngày đổi cung (chưa rõ cung Mặt Trời) thì chỉ dựa vào cung của hành tinh trên trời.
- Mỗi mảng có nhà riêng (Công việc 10, 6; Tiền 2, 8; Tình cảm 5, 7; Gia đình 4; Học 3, 9; Sức khỏe
  tinh thần 12, 1). Lấy mẫu 6 hành tinh lúc 12 giờ trưa giờ Việt Nam mỗi ngày trong tháng; hành tinh ở
  lâu nhất (có trọng số, hành tinh chậm nhẹ hơn) trong nhà của mảng là "Dựa vào". Không có hành tinh
  nào đủ 5 ngày thì dùng sao chủ của nhà đầu.
- Khoảng ngày: các ngày liền nhau (tối đa 3) từ hôm nay khi Mặt Trăng đi qua nhà của mảng.
- Câu làm sẵn: chọn từ khoảng 4000 câu hỏi Tarot của 1000 người giả, nhóm theo mảng và tình huống
  hay gặp nhất (nói chuyện khó với sếp, việc dồn, giữ sức khi tăng ca; hết tiền cuối tháng, nhắc
  trả tiền, từ chối khi kẹt tiền; gần nhau hơn, nói mình mệt, yêu xa; bố mẹ hỏi điểm/việc làm, nói
  về con đường mình chọn, bị so sánh; nhiều môn thi, giữ sức mùa thi, bắt đầu đồ án; nhớ nhà, thức
  khuya, nặng lòng). Câu "Với câu này" không phụ thuộc lá số; phần tháng vẫn theo lá số.

## Dữ liệu cá nhân

Xem `docs/legal/store-privacy-data-map.md`, mục "Hỏi Lá bằng lá số delta".

## Definition of Done còn mở

- Codex duyệt câu chữ `month.*` (164 câu: 126 câu trả lời, 2 dòng, 36 câu làm sẵn; đang chờ). Chưa
  duyệt thì tính năng ẩn.
- PR 2–4.
