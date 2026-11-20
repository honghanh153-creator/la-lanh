# US-25 — Hỏi Lá bằng lá số (hỏi về tháng này)

> Nguồn: owner chọn AK2 ngày 20.11.2026 sau thử 100 người giả (thiết kế A3: chủ đề tháng + một việc
> làm ngay + một câu mẫu; ngày chỉ hiện khi bấm "Xem lúc nào dễ hơn"). Báo cáo và bản mô tả nằm trên
> máy owner, ngoài repo; ở đây chỉ ghi hành vi.

## User story

Là người đang có chuyện cần lo trong tháng, tôi muốn hỏi Lá theo lá số của mình (chọn một mảng hoặc
gõ câu hỏi) và nhận một hướng nhìn cho tháng này, một việc làm được ngay và một câu mẫu để nói. Lá
không đoán chuyện gì sẽ xảy ra, không trả lời có/không, và chỉ cho tôi xem khoảng ngày dễ hơn khi tôi
tự bấm.

## Phạm vi

Bao gồm (PR theo thứ tự):

1. API và lõi tính (PR này): `/v1/month/status`, `/v1/month/answers`, `/v1/month/window`,
   `/v1/month/overview`; câu chữ chờ duyệt; đường câu gõ làm sẵn và tắt.
2. Lưu chủ động: bảng riêng mã hóa, danh sách riêng, xóa được, có trong xuất dữ liệu và xóa tài khoản.
3. Web: nút "Hỏi về tháng này" cạnh "Rút Tarot", màn hỏi, thẻ "Tháng này của bạn" trong Khám phá,
   lời nhắc đầu tuần (tắt sẵn).
4. Chạy 1000 người giả: không lọt câu khủng hoảng, không lẫn dữ liệu giữa người.

Không bao gồm: báo trước sự kiện, "ngày xấu", bộ đếm câu hỏi, nhắc hỏi thêm, gửi câu hỏi cho AI ngoài.

## Acceptance Criteria

| AC | Nội dung | Kiểm bằng |
|---|---|---|
| AC01 | Chọn một trong 6 mảng (Công việc, Tiền, Tình cảm, Gia đình, Học, Sức khỏe tinh thần) cho ra câu trả lời 3 phần: "Tháng này của bạn ở chuyện này", "Có thể làm ngay", "Có thể nói". | `test_api.py::test_topic_answer_has_three_parts_basis_and_no_date` |
| AC02 | Có dòng "Dựa vào: <hành tinh> × <nhà>" từ transit thật trong tháng, bấm xem thêm được; và dòng "Đây là một góc nhìn để bạn tự quyết, không phải điều chắc chắn sẽ xảy ra." | `test_facts.py::test_in_house_fact_is_true_on_the_days_it_counts`, `test_api.py` |
| AC03 | Cùng lá số + mảng + tháng cho cùng câu trả lời; không dùng AI ngoài. | `test_facts.py::test_same_chart_topic_month_gives_the_same_fact`, `test_api.py::test_answers_are_deterministic_over_http` |
| AC04 | Không đoán sự kiện, không có/không. Câu hỏi về kết quả, thời điểm, "có nên", ý người khác được trả lời bằng một câu mở đầu "Lá không …" rồi việc làm được. | `test_copy.py::test_no_prediction_no_date_no_yes_no`, `test_question.py`, `test_api.py::test_typed_outcome_question_gets_no_yes_no…` |
| AC05 | Câu trả lời không có ngày. Khoảng ngày chỉ đến từ yêu cầu riêng khi bấm "Xem lúc nào dễ hơn", chỉ là khoảng dễ hơn (≤ 3 ngày, từ hôm nay), kèm "Làm lúc nào cũng được; khoảng này chỉ dễ hơn một chút." Không có "ngày xấu". | `test_api.py::test_window_only_on_its_own_request`, `test_facts.py::test_window_is_real_short…` |
| AC06 | Không tự lưu: hỏi, xem khoảng ngày, xem thẻ tháng không ghi dòng nào. | `test_api.py::test_answering_stores_nothing` |
| AC07 | Thẻ tháng trong Khám phá: 4 mảng (Công việc, Tình cảm, Tiền, Bản thân), mỗi mảng một dòng và một việc nhỏ, không ngày. | `test_api.py::test_overview_card_has_four_areas_and_no_dates` |
| AC08 | Câu gõ: làm sẵn, tắt (`LA_LANH_MONTH_TYPED_QUESTIONS_ENABLED=false`); bật cũng chưa mở khi owner chưa duyệt câu đồng ý và câu khủng hoảng; cần `consent_version`. | `test_api.py::test_typed_question_*` |
| AC09 | Câu gõ qua lớp an toàn như Tarot trước mọi kiểm tra khác: 100% câu khủng hoảng được chuyển hướng, báo nhầm ≤ 2%. | `test_api.py::test_every_crisis_phrase_is_routed_on_the_typed_path`, `test_false_alarms_stay_at_or_below_two_percent` |
| AC10 | Câu gõ không bị lưu, ghi log, lặp lại trong câu trả lời hay gửi đi; giữ trong thời gian một request. | `test_api.py` (canary trong log, phản hồi và số dòng bảng) |
| AC11 | Tính năng chỉ hiện khi mọi câu chữ đã được duyệt (`/v1/month/status.available`); chưa duyệt thì trả "chưa sẵn sàng", không trả nửa câu. | `test_api.py::test_status_*`, `test_pending_copy_answers_unavailable_not_half` |
| AC12 | Lưu chủ động, mục riêng, xóa được; máy chủ tự tính lại câu trả lời, không nhận chữ từ máy khách; có trong xuất dữ liệu; xóa có nhật ký; xóa giờ/nơi sinh thì xóa theo. | `test_saved.py` |
| AC13 | Nút trên Trang chủ cạnh "Rút Tarot"; nút ngày thu gọn sẵn; không nhắc, không đếm; không hiện câu trả lời trên Trang chủ; lời nhắc đầu tuần tắt sẵn. | PR 3 |
| AC14 | 1000 người giả: không lọt câu khủng hoảng, không lẫn dữ liệu giữa người. | PR 4 |

## Cách tính (tóm tắt)

- Nhà: giờ sinh chính xác dùng nhà của lá số; còn lại dùng nhà tính theo cung Mặt Trời. Ngày sinh rơi
  đúng ngày đổi cung (chưa rõ cung Mặt Trời) thì chỉ dựa vào cung của hành tinh trên trời.
- Mỗi mảng có nhà riêng (Công việc 10, 6; Tiền 2, 8; Tình cảm 5, 7; Gia đình 4; Học 3, 9; Sức khỏe
  tinh thần 12, 1). Lấy mẫu 6 hành tinh lúc 12 giờ trưa giờ Việt Nam mỗi ngày trong tháng; hành tinh ở
  lâu nhất (có trọng số, hành tinh chậm nhẹ hơn) trong nhà của mảng là "Dựa vào". Không có hành tinh
  nào đủ 5 ngày thì dùng sao chủ của nhà đầu.
- Khoảng ngày: các ngày liền nhau (tối đa 3) từ hôm nay khi Mặt Trăng đi qua nhà của mảng.

## Dữ liệu cá nhân

Xem `docs/legal/store-privacy-data-map.md`, mục "Hỏi Lá bằng lá số delta".

## Definition of Done còn mở

- Codex duyệt câu chữ `month.*` (135 câu, đang chờ). Chưa duyệt thì tính năng ẩn.
- Owner duyệt nguyên văn câu đồng ý (`consent.month.typed_question`) và câu khủng hoảng
  (`crisis.self_harm.notice.month`), rồi mới bật câu gõ.
- PR 2–4.
