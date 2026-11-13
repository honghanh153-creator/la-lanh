# Làn tài liệu: viết spec, duyệt doc (bổ sung thiết kế v2)

Nền đang có trong repo (dùng lại, không xây mới):
- `docs/user-stories/` gồm 19 US, mỗi US có AC/DoD, cùng bản đồ phụ thuộc và **hợp đồng sở hữu** (mỗi hành vi chỉ thuộc một US);
- `la-lanh-prd.md`, `la-lanh-srs.md`, product plan v2, các spec engine;
- quy trình G1–G10 (`product-development-process.md`), G1 = tài liệu và hợp đồng sản phẩm;
- `docs/decisions/` có 5 quyết định;
- skill chấm điểm có sẵn: `cham-diem-prd`, `cham-diem-srs` (chấm 4 mức, có bằng chứng, kết luận "đủ để làm chưa").

## 1. Chuỗi tài liệu: loại nào, khi nào cần

| Tài liệu | Bắt buộc khi | Ai viết | Ai chấm | Owner xem gì |
|---|---|---|---|---|
| **Brief 1 trang** (vấn đề, người dùng, kết quả mong muốn, giá trị A–E, chỉ số) | mọi mục tiêu hoặc ý mới | Claude, từ lời owner hoặc ghi âm | critic(goal) | thẻ 1 trang |
| **PRD** | tính năng mới, hoặc ý còn mơ hồ (D6b, Emma) | Claude (skill viết PRD) | Codex, phiên mới, theo `cham-diem-prd` | tóm tắt + câu hỏi mở dạng 2 phương án |
| **US + AC** (Given/When/Then, EARS cho yêu cầu hệ thống, luồng phụ, trạng thái loading/empty/error/offline, NFR, map dữ liệu riêng tư, câu chữ, chỉ số) | mọi hành vi người dùng thấy | Claude | Codex, theo bảng "sẵn sàng" | chỉ phần đổi phạm vi |
| **SRS / spec kỹ thuật** (API, dữ liệu, migration, lỗi, bảo mật) | chạm API, dữ liệu, migration | Claude | Codex, theo `cham-diem-srs` | không, trừ chạm dữ liệu cá nhân |
| **ADR 1 trang có sơ đồ** | đổi kiến trúc hoặc chọn công nghệ | Claude | Codex | quyết định A/B |
| **Spec chạy được** (UAT, eval, test giữ kín) | mọi AC | **Codex**, viết từ spec, không xem code | Claude rà xem test có bám spec không | không |

Tối ưu: không phải việc nào cũng cần đủ chuỗi. Mức S chỉ cần AC trong US. Mức M cần US + spec kỹ thuật. Mức L cần đủ chuỗi (khớp mức S/M/L của G1–G10).

## 2. Cổng "sẵn sàng để làm" (Definition of Ready)

`decide()` chỉ nhặt việc có US ở trạng thái **ready**. Một US ready khi:
1. Mỗi AC có mã cố định, kiểm được, có luồng chính, luồng phụ và trường hợp biên.
2. Đủ trạng thái: loading, empty, error, offline, hết hạn.
3. Có NFR: tốc độ, a11y, 360/390px, native (nếu có).
4. Có map dữ liệu: trường nào được thu, lưu, xoá, ai đọc; khớp data map và privacy copy.
5. Câu chữ đánh dấu rõ: dùng câu đã duyệt / câu mới cần duyệt / câu chỉ owner duyệt.
6. Có giá trị (A–E), có "người dùng thấy gì", có chỉ số hoặc cược.
7. Có phác thảo test cho từng AC. Spec chạy được ở trạng thái đỏ trước khi code.
8. Không chồng chéo hợp đồng sở hữu của US khác.
9. Codex chấm đạt ngưỡng (vd ≥ mức 3/4 với từng phần) **trong phiên mới**. Câu hỏi mở đã được trả lời, hoặc đã thành thẻ cho owner.

## 3. Cách viết spec (học có chọn lọc)

- **Hỏi trước khi viết** (Graziano): Claude chỉ hỏi những dữ kiện quyết định kết quả. Câu nào trả lời được bằng repo hay quyết định cũ thì tự tra, không hỏi owner.
- **Use case có luồng phụ** (Martinelli): ghi rõ hết hạn, bị thu hồi, tự mời chính mình, mất mạng, dữ liệu thiếu.
- **Phản biện spec trong phiên mới** (Graziano, Codex): tìm chỗ mâu thuẫn, điểm mù, trường hợp biên bị thiếu.
- **"Làm sao cho tệ nhất"** (TRIZ) cho tính năng nhạy cảm như Hợp gu, Lá Dám, café: mỗi câu trả lời thành một AC "không được".
- **Retro-spec** (Graziano): code đã có mà chưa có spec thì viết spec ngược từ code, đánh dấu chỗ lệch thành câu hỏi.
- **Spec đổi trước, code đổi sau** (Martinelli): muốn đổi hành vi thì sửa US/AC trước, rồi PR code trỏ tới phiên bản AC mới.

## 4. Duyệt doc: ai duyệt gì, owner bỏ ra bao nhiêu

- **Codex duyệt chất lượng** theo rubric, mỗi lần một phiên mới, khác model với bên viết. Tối đa 2 vòng. Còn bất đồng thì gửi owner bản 4 dòng.
- **critic() duyệt sự phù hợp**: ưu tiên, giá trị, sức chứa, luật cứng, xung đột với quyết định cũ.
- **Owner duyệt ý định, không duyệt văn bản** (Foxwell: review spec chứ không review diff). Owner nhận một **thẻ spec** gồm:
  - người dùng thấy gì (kèm ảnh mock nếu là UI);
  - danh sách AC tên ngắn;
  - phần thay đổi phạm vi;
  - câu hỏi mở dạng 2 phương án;
  - rủi ro riêng tư.

  Mất khoảng 3–5 phút mỗi thẻ, nằm trong 20 phút "thẻ quyết định" của phiên owner. Câu nhạy cảm và dữ liệu cá nhân thì owner duyệt chính văn.
- **Duyệt mù theo bằng chứng.** Sau khi build, verifier đối chiếu từng AC với app chạy thật. Owner nghiệm thu bằng ảnh và kết quả AC, không đọc diff.

## 5. Giữ tài liệu khớp với app (không trôi)

- Mỗi PR đổi hành vi phải ghi mã AC trong body. Preflight chặn nếu thiếu. PR không cần US thì ghi lý do, ví dụ "vận hành".
- **Kiểm trôi mỗi đêm**: so feature map, route, hợp đồng API và trường dữ liệu với US/SRS/data map. Chỗ lệch ghi vào sổ phát hiện, rồi sinh việc sửa doc hoặc sửa code.
- Mỗi AC có trạng thái: chưa làm / đang làm / có test / đạt trên integration / đạt trên production. Bảng này lấy từ CI, không ai tự điền.
- Wiki `docs/brain/` và ADR được cập nhật từ việc đã merge (Stoneham, Batey).
- Bài học chỉ vào AGENTS.md khi đã đúng 2 lần (Overweg).

## 6. Chỉ số của làn tài liệu (đều có đối trọng)

| Chỉ số | Mục tiêu | Đối trọng | Dưới mục tiêu → |
|---|---|---|---|
| % US ready trong hàng chờ của mục tiêu | đủ cho 1 tuần WIP | điểm chấm Codex | viết hoặc chấm spec trước khi code |
| % AC có test chạy được | 100% AC ready | test bị khoá, chấm test vô nghĩa | Codex viết test thiếu |
| Spec bị sửa sau khi đã bắt đầu code | ≤ 20% | số câu hỏi trả lời trước | thêm vòng hỏi trước khi viết |
| Số chỗ trôi doc/app mỗi đêm | giảm | — | việc sửa doc |
| Phút owner mỗi thẻ spec | ≤ 5 | tỷ lệ owner phải hỏi lại | rút gọn thẻ |

## 7. Vị trí trong `decide()`

Làn tài liệu không phải nhánh riêng. Nó đi vào:
- **nhánh 7 (mục tiêu)**: giả thuyết cần US ready → việc đầu tiên là viết hoặc chấm spec;
- **nhánh 9 (backlog)**: chỉ nhặt US ready;
- **nhánh 10 (rảnh)**: retro-spec, kiểm trôi.

WIP: 1 doc đang viết + 1 doc đang chấm, **tách khỏi** WIP code, để việc viết spec không chặn code và ngược lại. Tổng phút owner vẫn chung một ngân sách.

## 8. Ánh xạ mã học được

- E1, E2: chuỗi spec → phiên mới → review theo spec.
- D6b: PRD khi mơ hồ.
- D11c: owner duyệt spec, không duyệt diff.
- D17a, D17b: use case và test hộp đen.
- D19a, D19b, D19c: EARS, phản biện phiên mới, retro-spec.
- D21a: spec chạy được, giữ kín.
- D10a: ADR.
- D6a, D15c: wiki và context trong repo.
- D28b, D28c: TRIZ; ghi âm → PRD.
- D30b: bài học đúng 2 lần.
- R5: critic.
- R7: doc phải khớp code đang chạy.
- AGENTS.md cổng 1: doc, API contract, privacy copy khớp runtime.
