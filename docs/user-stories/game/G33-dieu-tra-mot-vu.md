# G33 — Điều tra một vụ: cáo trạng, câu hỏi phụ, manh mối, buộc tội

> Phiên Tòa Tủ Lạnh. [PRD](../../foundation/game-line/phien-toa-tu-lanh-prd.md) §4.2 (pha 1–4), §6.2 ·
> [SRS](../../foundation/game-line/phien-toa-tu-lanh-srs.md) §3.3, §6. Phiếu đồng thời và lượt chọn bí mật: **G05**. Trạng thái: nháp.

## 1. User story

Là thành viên một đội hành tinh, tôi muốn nghe cáo trạng, trả lời một câu hỏi phụ vui, cùng đội giải các manh mối mã hoá trên màn
chiếu và chọn người để buộc tội, để có khoảnh khắc "à, Thủ Phạm mặc áo xanh dương" rồi cả phòng quay sang nhìn nhau.

## 2. Mục tiêu và ranh giới

### Mục tiêu

- Bốn pha trong ~4,5 phút, mỗi pha một việc rõ.
- Manh mối giải được theo đội trong 75 giây.
- Vai bí mật (Đồng Phạm, Kẻ Chủ Mưu, Thư Ký) hành động mà không lộ.

### Trong phạm vi

Cáo trạng; câu hỏi phụ + ràng buộc Thủ Phạm; lượt bí mật của Đồng Phạm, Kẻ Chủ Mưu, Thư Ký; sinh và lật manh mối; manh mối riêng
của Nhân Chứng và kết quả của Thư Ký; công cụ giải mã; thảo luận và phiếu buộc tội của đội.

### Ngoài phạm vi

Ra tòa, Phản đối, bỏ phiếu cả phòng (G34); tuyên án (G35).

## 3. Actor, điều kiện và output

- **Actor:** mọi người chơi theo vai; Thẩm Phán Lá (hệ thống).
- **Điều kiện:** vai theo vụ đã chia (G32).
- **Output:** manh mối của vụ; ghế bị cáo.

## 4. Luồng

```mermaid
sequenceDiagram
  participant D as Màn chiếu
  participant S as Máy chủ
  participant P as Điện thoại
  S->>D: pt.indictment (TPL-04 + cáo trạng) — 30 s
  S->>P: câu hỏi phụ (pt_side_prompt) + pt.secret_task (đệm cùng cỡ) — 60 s
  P->>S: lựa chọn câu hỏi phụ; Đồng Phạm tráo; Chủ Mưu đổi chữ; Thư Ký chọn manh mối
  S->>S: sinh manh mối (SRS §6)
  S->>D: pt.clues (mã hoá) + số đếm câu hỏi phụ — 75 s
  S->>P: pt.private_clue (Nhân Chứng, Thư Ký; người khác nhận đệm)
  S->>P: pt_team_accuse (theo đội) — 90 s
  P->>S: phiếu buộc tội
  S->>D: pt.bench (ghế bị cáo)
```

## 5. Giao diện và trạng thái

| Pha | Màn chiếu | Điện thoại |
|---|---|---|
| Cáo trạng | Số vụ, tên vụ, cáo trạng chữ lớn, búa gõ | "Nghe cáo trạng trên màn hình chung" |
| Câu hỏi phụ | Câu hỏi + 4 phương án, "Đã trả lời: x/y" | 4 phương án (giống nhau cho mọi vai); vai bí mật có thêm một thẻ việc cùng kích thước với thẻ "Bạn không có việc bí mật vụ này" của người khác |
| Lật manh mối | Manh mối theo hồ sơ, đánh số, kiểu mã; số đếm câu hỏi phụ (nhóm dưới 3 người hiện "dưới 3 người") | Công cụ giải mã; hồ sơ của đội nổi hơn; Nhân Chứng/Thư Ký thấy thẻ riêng |
| Buộc tội | "Các đội đưa bị cáo lên ghế" + đồng hồ | Danh sách người chơi (tìm theo biệt danh), `Buộc tội`, tiến độ phiếu trong đội (x/y) |

## 6. Quy tắc

Theo SRS PT-FR-20 đến PT-FR-29 và §6. Đặc biệt:

1. Giao diện câu hỏi phụ của Thủ Phạm giống hệt người khác; máy chủ ghi đè lựa chọn bằng ràng buộc (PT-SEC-04).
2. Manh mối nói về vai ("Thủ Phạm…"), không nói về biệt danh (PT-PRV-02).
3. Số đếm câu hỏi phụ chỉ theo phương án.
4. Không manh mối nào dùng câu `skip`.

## 7. Tiêu chí chấp nhận

- **G33-AC01:** Cáo trạng hiện đúng mẫu vụ với chỗ trống đã bốc; chế độ Tất niên có câu dẫn.
- **G33-AC02:** Thủ Phạm bấm phương án khác ràng buộc: số đếm và manh mối dùng phương án ràng buộc; điện thoại Thủ Phạm không hiện gì
  khác thường.
- **G33-AC03:** Mỗi hồ sơ có đúng 2 manh mối thật từ hai câu khác nhau, 1 manh mối câu hỏi phụ, và tối đa 1 manh mối giả cho mỗi Đồng
  Phạm của hồ sơ; manh mối giả trùng giá trị thật bị bỏ.
- **G33-AC04:** Đúng một chữ của một manh mối bị thay bằng chữ của Kẻ Chủ Mưu mỗi vụ (khi Kẻ Chủ Mưu còn trong phòng).
- **G33-AC05:** Kết quả của Thư Ký đúng nhãn `that`/`gia`/`bi_sua`; chỉ Thư Ký nhận.
- **G33-AC06:** Nhân Chứng mỗi đội nhận một manh mối thật cho hồ sơ của đội; người khác nhận gói đệm cùng cỡ (PT-TH-07).
- **G33-AC07:** Hết giờ: Đồng Phạm/Chủ Mưu chưa chọn được máy chủ chọn ngẫu nhiên; Thư Ký chưa chọn thì không kiểm.
- **G33-AC08:** Phiếu buộc tội chỉ thành viên đội được bầu, không chọn được chính mình; hoà thì rút thăm và màn chiếu hiện "Tòa rút
  thăm"; đội không ai bầu thì không buộc tội.
- **G33-AC09:** Tám người thử lần đầu (2 đội × 4) giải được ít nhất 2/3 manh mối trong 75 giây ở chơi thử giấy.
- **G33-AC10:** Gói `display` không chứa ràng buộc, lựa chọn của từng người, hay nhãn thật/giả của manh mối trước "Sự thật là".
- **G33-AC11:** Số đếm câu hỏi phụ không hiện con số cho phương án có 1–2 người (RP-PRV-10).

## 8. Trường hợp biên

| Trường hợp | Cách xử lý |
|---|---|
| Thủ Phạm chỉ có đúng 3 câu trả lời | 2 manh mối thật + 1 cho Nhân Chứng (trường thứ ba) |
| Đồng Phạm không có trường chung với Thủ Phạm | Không có manh mối giả từ người đó |
| Phòng ồn, đội không nghe nhau | Công cụ giải mã trên điện thoại; host +30 s |
| Một người bị nhiều đội buộc tội | Ghế bị cáo gộp trùng (G34) |

## 9. Definition of Done

- G33-AC01–AC11 pass; chơi thử giấy xác nhận độ khó.
- Mẫu manh mối được owner duyệt văn phong.
- Review bảo mật lượt chọn bí mật và gói đệm.
- Không còn lỗi P0/P1.

## 10. Bàn giao

- **Nguồn:** báo cáo (bước 1–4 của mỗi vụ; manh mối mã hoá Caesar/emoji/thiếu chữ); research note §3 (Takumi); SRS §3.3, §6.
- **Đã xử lý:** câu hỏi phụ là câu hư cấu, lưu như phiếu; ghi đè ở máy chủ để Thủ Phạm không lộ.
- **Rủi ro mở:** người mặc màu áo hiếm dễ bị chú ý — đo bằng khảo sát "bị nhắm vào".
- **AC/DoD chưa xong:** toàn bộ.
