# Daily chống lặp chủ đề theo người (21.11.2026)

Việc: điều kiện owner đặt cho bản phát hành 20.11: Daily đang xoay theo ngày lịch và không xét người đó đã đọc gì. Phiên điều phối giao ngày 21.11.
Agent: Claude (content-nguoi-moi). Review: Codex.
Mức: **M**. Đổi cách chọn tình huống Daily, đổi AC05 của US-21; không thu dữ liệu mới, không migration.
So sánh phương án (§7.2): comment Plan trên PR #841.

## 1. Vấn đề, có số

Daily chọn tình huống (chủ đề, `issue_key`, 15 chủ đề) trong **top-3** tình huống hợp lá số nhất của ngày, theo `day_index mod 3` (US-21 AC05). Guard hiện có chỉ nhìn lại 1–2 ngày (`_guard_issue_keys`). Vì vậy một người gặp lại cùng 3 chủ đề theo vòng 3 ngày.

Đo trên bản phát hành 20.11, 1000 người giả × 29 ngày, cùng lượt chạy với báo cáo content người mới 20.11 (`topic_repeat.py`):

| Chỉ số | Giá trị |
|---|---|
| Ngày có chủ đề đã gặp trong 6 ngày trước (`topic_7d`) | **81.1%** (22.870 / 28.217 ngày, 973 người) |
| Ngày có chủ đề đã gặp trong 2 ngày trước (`topic_3d`) | 41.6% |
| Ngày có nhóm chủ đề đã gặp trong 2 ngày trước (`theme_3d`) | 59.9% |
| Số chủ đề khác nhau trong 14 ngày đầu (trung vị) | **3** |
| Tiêu đề lặp trong 7 ngày (`headline_7d`) | 22.3% |

Số nền cho PR code là lượt 200 người trên `collab/integration`, ghi ở mục 6.

**Giới hạn do nội dung (đo khi làm PR 3–4).** Theo các lá số giả trong test, mỗi ngày lá số chỉ có trung bình 2,45 tình huống đủ điều kiện (trung vị 2), không phải 6. Vì vậy cửa sổ 7 ngày không thể sạch lặp. Việc làm được ở đây là phá vòng ngắn: lặp trong 3 ngày giảm mạnh, lặp trong 7 ngày giảm vừa. Muốn giảm sâu hơn phải tăng số tình huống đủ điều kiện cho mỗi lá số, tức thêm nội dung và luật. Đó là việc riêng, ghi ở mục 5.

## 2. Mục tiêu (US-21, đề xuất AC05 mới)

**US-21 AC05 (mới; bản đã làm ở #842/#855, cập nhật theo đo đạc và góp ý P2 #844, #853):** Tình huống của ngày D được chọn trong **pool của ngày D** (tối đa `K = 6` tình huống đủ điều kiện, xếp theo độ hợp lá số như hiện nay). Thứ tự chọn:
1. Đi theo **thứ tự xoay cố định riêng của người** (`rotation_order`: hash của seed và mã chủ đề, các chủ đề liền nhau khác nhóm), bắt đầu từ vị trí `day_index`. Chọn tình huống đầu tiên chưa gặp trong 6 ngày trước.
2. Nếu tất cả đã gặp: chọn tình huống gặp lâu nhất, hoà thì theo cùng thứ tự xoay.

Không còn bậc "ưu tiên hạng" hay "nhóm chủ đề 2 ngày" riêng. Lượt 200 người cho thấy chọn theo hạng làm pool không đổi lặp ở biên khối (giờ gần đúng 11,9% → 14,7%). Thứ tự xoay theo ngày thì pool không đổi (dù cỡ 2 hay 5) xoay đều toàn cục, không phụ thuộc biên khối hay ngày bật; ví dụ ABAB|BABA của #853 không xảy ra (test với lịch sử bị đặt lại ở các vị trí bất kỳ, cỡ 2–6). "Đã gặp" là kết quả của **chính phép chọn này** ở các ngày trước, được **tính lại** từ lá số, transit từng ngày và seed của người đó. Không đọc và không lưu lịch sử (giữ quyết định owner 21.10 ở AC05 cũ). Pool 1 phần tử thì tình huống đứng yên, các ô vẫn đổi (như cũ).

**Tiêu chí đạt** (200 người giả × 29 ngày từ 21.11, cùng mẫu và đồng hồ cho trước và sau):

- `topic_3d` (chủ đề đã gặp trong 2 ngày trước) giảm ít nhất một nửa so với số nền.
- `topic_7d` giảm.
- Trung vị số chủ đề khác nhau trong 14 ngày không giảm.
- `theme_3d` giảm.
- `headline_7d` không tăng.
- An toàn không đổi: khủng hoảng bắt đủ, báo nhầm không tăng, không lộ chéo người dùng, không có ngày lỗi.
- Báo tỉ lệ ngày chọn tình huống hạng 4–6 (đổi lấy sự mới). Chỉ báo, không đặt ngưỡng; Codex xem.
- Thời gian tạo Daily tăng không quá 300 ms/ngày/người (đo trên máy, xem mục 4).

AC02, AC03, AC04, AC06 giữ nguyên.
- AC04: plan đã đóng băng replay đúng như đã lưu.
- AC06: ngày bị ép ngoại lệ không dịch vị trí của ngày sau. Mục này được thay bằng lịch theo khối ở mục 3, có test.

## 3. Cách làm

**Nhóm chủ đề (tag set).** Mỗi `issue_key` có đúng một nhóm, khai trong code, có test phủ đủ 15 chủ đề:

| Nhóm | Chủ đề |
|---|---|
| `overload` | too-many-open-loops, decision-fatigue, capacity-before-agreement, automatic-caretaking |
| `reply` | quick-reply, repair-reply, specific-feedback, missing-context |
| `friction` | avoid-small-conflict, group-pressure, defend-old-choice, changed-plan |
| `self-judgment` | comparison-loop, perfect-before-start |
| `needs` | name-the-need |

**Lịch theo khối, không lưu, khớp tuyệt đối.**
- Ngày được cắt thành khối **12 ngày**, lệch pha theo HMAC của người (giống khối ⚠ trong `variant_rotation.py`).
- Để chọn ngày D: tính lại pool của từng ngày từ đầu khối tới D, rồi chọn lần lượt theo AC05 mới. Mỗi khối bắt đầu với lịch sử rỗng.
- Vì vậy lịch sử dùng cho ngày D đúng bằng các ngày trước đó trong khối, như chúng đã được phục vụ (có test).
- Tối đa 11 lần tính lại cho mỗi Daily mới; plan giữ 6 ngày gần nhất.

Không mang ước lượng của khối trước sang (góp ý P2 của Codex, #844). Ước lượng đó không thể khớp với những gì khối trước đã phục vụ, vì khối trước lại được chọn dựa trên khối trước nữa, cứ thế ngược về ngày bật. Ví dụ ABC của Codex: mang sang thì mỗi tuần lặp B ở biên.

Pool không đổi xoay đều qua mọi biên khối nhờ thứ tự xoay theo ngày (mục 2), không cần cỡ khối là bội của cỡ pool. Biên khối chỉ có thể lặp khi pool đổi giữa các ngày.

**Ngày bật (góp ý P2 #853):** lịch sử bắt đầu **lạnh** ở ngày bật. Với ngày D sau ngày bật, chỉ các ngày từ `max(đầu khối, ngày bật)` tới D−1 được tính lại, bằng cách chọn mới. Những ngày trước ngày bật (phục vụ bằng cách cũ) không được dựng lại. Vì vậy lịch sử của mỗi ngày sau ngày bật vẫn khớp tuyệt đối với cái đã phục vụ (test `test_topic_schedule_starts_on_its_own_date`: ngày bật có lịch sử rỗng). Ở đúng ngày bật, chủ đề có thể trùng hôm trước một lần, vì cách cũ (`day_index mod 3`) và thứ tự xoay mới khác nhau; sau đó lịch đi đều.

**Người chỉ có ngày sinh** (pool cố định theo cung, AC07): không cần lịch sử.
- Pool đi theo một thứ tự cố định riêng cho từng người (`rotation_order`, xen kẽ nhóm chủ đề), theo `day_index % len(pool)`. Mỗi chủ đề quay lại đúng sau `len(pool)` ngày.
- Chỉ số lượt xuất hiện cho staircase của #778 là `day_index // len(pool)`: toàn cục, không đặt lại theo khối (góp ý P2 của Codex, #844).
- Test 90 ngày của AC03 và test thứ tự tiêu đề chạy cả khi bật lịch mới.
- Người có lá số đầy đủ giữ cách xoay tiêu đề, cảnh và việc nhỏ theo ngày như cũ.

**Không đổi:** không thêm cột, bảng, cookie, localStorage hay trường gửi từ app. Không có dữ liệu cá nhân mới; nhóm chủ đề là hằng số nội dung.

**Bật bằng ngày (theo tiền lệ `daily_variety_from`):**
- Setting `daily_topic_schedule_from`. Để trống thì giữ cách cũ.
- Không nâng `catalog_version`, vì nó nằm trong seed của từng người; nâng lên sẽ xáo lại mọi thứ tự xoay.
- Plan trước ngày bật giữ nguyên hash và định danh: trường `topic_history` không có mặt trong bản dump khi rỗng.
- Bật trên production là một bước trong lần phát hành (owner quyết lần phát hành).

## 4. File

| PR | File | Nội dung |
|---|---|---|
| 1 (PR này) | `docs/plans/2026-11-21-daily-topic-anti-repeat.md` | Plan |
| 2 | `apps/api/scripts/persona_metrics.py` (+ test), `qa/personas` | Chỉ số `topic_7d`, `topic_3d`, `theme_3d`, số chủ đề/14 ngày vào máy đo người giả, để trước/sau đo bằng code trong repo |
| 3 (#842) | `apps/api/app/domains/readings/daily_topics.py` (mới, + `tests/readings/test_daily_topics.py`) | Nhóm chủ đề, hàm chọn thuần theo AC05 mới, lịch theo khối, thứ tự cố định cho pool không đổi; chưa nối vào app |
| 4 | `apps/api/app/domains/readings/application.py`, `models.py`, `daily_psychology.py` (`_pick`, `_occurrence_index`), `app/config.py`, `app/main.py`, `scripts/persona_sim.py` | Nối lịch theo khối thay guard 1–2 ngày từ ngày bật, test trên đầu ra thật, số trước/sau 200 người trong PR |
| 5 | `docs/user-stories/US-21-…md` (AC05), runbook phát hành | AC05 mới, bước bật setting khi phát hành |

Không đụng file của #776 (web) hay #774 (Khám phá), cả hai đã merge. #726 (draft, transit giờ gần đúng) cũng sửa `application.py` và `daily_psychology.py`; PR 4 sẽ làm trên integration mới nhất và báo trong #726.

## 5. Rủi ro

- **Đổi độ hợp lấy sự mới:** hạng 4–6 vẫn là tình huống lá số đủ điều kiện, nhưng yếu hơn. Tỉ lệ được báo; nếu Codex thấy cao thì giảm `K`.
- **Chi phí tính:** tối đa 11 lần lập pool mỗi Daily mới. Nếu đo vượt 300 ms thì chỉ lập pool (không render) và cache theo request.
- **Đổi bộ khoá hay lens** bắt đầu một chuỗi mới (như AC05 cũ).
- **Trần nội dung:** 2–3 tình huống đủ điều kiện mỗi ngày giới hạn mức giảm của `topic_7d`. Việc tiếp theo (riêng): thêm tình huống đủ điều kiện cho mỗi lá số, đo bằng cùng chỉ số.
- **Bảo mật / riêng tư (G7, G8):** không đụng phiên, quyền hay log; không lưu và không gửi lịch sử. Mã chủ đề không rời server.

## 6. Đo

Mẫu: 200 người giả (mỗi người thứ 5 trong `personas-1000.json`), 29 ngày từ 21.11, SQLite tạm, không mạng, chạy qua `collab-test-guard`. Trước = `collab/integration` lúc mở PR 4; sau = PR 4.

Số nền 200 người (integration `fa349885`, 774 giây):

| Chỉ số | Số nền |
|---|---|
| `topic_7d` | 79.5% (4.425 / 5.568 ngày, 192 người) |
| `topic_3d` | 30.3% (1.689 ngày, 134 người) |
| `theme_3d` | 53.0% |
| `headline_7d` | 11.9% |
| `headline_14d` | 33.9% |
| Chủ đề khác nhau trong 14 ngày (trung vị) | 3 |
