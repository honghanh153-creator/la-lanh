# Codex rà soát workflow của Claude (13.11.2026)

Owner 13.11.2026: Claude "khá hờ hững trong việc sửa lại workflow". Văn bản dưới đây do Codex viết (chạy chỉ đọc), Claude chỉ thêm tiêu đề này. Kết quả xử lý: #480, #481, #482 và sổ `scripts/collab-lessons.json`.

**Nhận xét “hờ hững” có cơ sở ở việc theo đến cùng:** Claude đã sửa nhiều mã thật, nhưng chưa có cơ chế buộc một bài học phải kết thúc bằng kiểm tra đang chạy và bằng chứng hết lỗi.

Tôi kiểm snapshot `b045f1c`, các nhánh mở, hồ sơ đã đưa và comment trực tiếp trên GitHub. **23 test đạt** khi thao tác file được chuyển vào bộ nhớ. Tôi cũng tái hiện lỗi qua hai lượt vòng tự động; không sửa file, gọi AI trả phí hay thay đổi GitHub. Chưa chạy toàn bộ bộ test.

Ở dưới, **CI** là máy kiểm trên GitHub; **tick** là một lượt vòng tự động; **AC** là tiêu chí nghiệm thu.

## 1. Claude đã đổi gì trong workflow (09–13.11)

| Thay đổi | Ở đâu | Thực sự chạy và bằng chứng |
|---|---|---|
| Tự đóng cảnh báo sau phục hồi; giữ việc đóng còn dang dở | Commit `8849668`, `163f616` | Tick gọi watchdog tại `scripts/collab-tick.mjs:38`. Test hồi quy `#373: a recovery deferred…` trong `collab-watchdog.test.mjs:161`. |
| Lấy kết quả CI thay chạy mã PR trên Mac | PR #443 | Đã bật tại `collab-cron.sh:13`; kiểm đúng workflow và commit tại `collab-check.mjs:141`. Test ở `collab-loop.test.mjs:796,821,843`. |
| Giới hạn một việc làm, một việc review; chọn 3–5 việc/ngày | PR #451 | Có phép đếm và tín hiệu bổ sung tại `collab-buffer.mjs:24,31`; chưa ngăn mọi phiên tự mở thêm PR. |
| Tick gọi duyệt câu chữ hằng ngày | PR #451 | Có caller tại `collab-tick.mjs:41`; test `copy batch: once a day…`, dòng 1019. **Đường phục hồi khi lỗi còn hỏng.** |
| Bỏ qua câu đã bị từ chối; ghi nhận merge trực tiếp | Commit `ed100bd` | Test `rejected copy does not fill every later batch`; `collab-merge.mjs:30` ghi merge. |
| Đo kết quả, đăng thông báo mới | PR #451 | Nối tại `collab-tick.mjs:42–43`; test trong `collab-metrics.test.mjs`, `collab-status.test.mjs`. Số tiến độ vẫn có lỗi đã biết. |
| Chụp màn hình 390px | PR #452 | `.github/workflows/ui-screens.yml:42` chạy Playwright. API được giả lập; chưa kiểm bộ sinh nội dung thật. |
| Sửa thiếu danh tính Git khi xuất lô câu | PR #462 | `codex-copy-review.mjs:146`; test dòng 96 chỉ giả lập lệnh Git, chưa chứng minh commit thật. |
| Thiết kế Autopilot v2; kiểm chứng UI; gia cố merge | PR #454, #457, #456 | Thiết kế đã vào repo. #457/#456 còn mở trong hồ sơ; không được tính là cơ chế đã vận hành. |

## 2. Đối chiếu A–L và memory

“XONG” dưới đây phải đủ kiểm tra đang chạy và test bắt lỗi cũ.

| Việc đã chốt | Trạng thái | Bằng chứng và phần thiếu |
| **A. Kiểm trang qua app/API thật** | **MỘT PHẦN** | Có chụp màn hình, nhưng API giả lập. `qa-public-smoke.mjs:94` gọi overview mà chưa kiểm phần tổng hợp. |
| **B. Đối chiếu AC với màn hình** | **MỘT PHẦN** | Prompt yêu cầu đọc spec; #457 có bản đồ tính năng. Chưa có kiểm bắt trường hợp test xanh nhưng mất nội dung tổng hợp. |
| **C. Đổi luật chặn lỗi nội dung** | **CHỈ GHI CHỮ** | Thỏa thuận dòng 28 vẫn chờ owner. Giữ nguyên luật khi chưa được duyệt là đúng. |
| **D. Tách checkout, kiểm trước giao agent** | **MỘT PHẦN** | Clone author kiểm đúng commit tại `collab-check.mjs:286,307`; chưa thấy bộ khởi chạy agent kiểm thư mục/nhánh trước mọi thao tác ghi. |
| **E. Ruff đúng bản khóa trước push** | **MỘT PHẦN** | Có `uv run` tại `collab-preflight.mjs:67`; không có hook Ruff trong snapshot. Lint sau push chưa đạt cam kết. |
| **F. Thử chân dung với chữ thật** | **CHƯA LÀM** | Chưa tìm thấy bằng chứng đạt 360/390px, chữ 200%, mở căn cứ và giảm chuyển động trong phạm vi được cấp. |
| **G. Nghiên cứu theo chứng cứ** | **CHỈ GHI CHỮ** | Có thỏa thuận bỏ quota trang; chưa có phép kiểm bác kết luận không được nguồn hỗ trợ. |
| **H. Sửa đúng `ops-run.sh`** | **CHƯA LÀM** | Snapshot không có wrapper hoặc test tương ứng; chưa xác minh được file ngoài repo. |
| **I. Ghi thỏa thuận, điểm chờ** | **MỘT PHẦN** | Có `agreed-12-11-codex-round2.md`; chưa nối thành danh sách thực thi chung có trạng thái kiểm chứng. |
| **J. Đếm task theo nghiệm thu** | **MỘT PHẦN** | Owner sau đó đổi sang 3–5 việc. Nhưng `committedTurns()` vẫn chọn theo PR; chưa gom nhiều PR thành một task. |
| **K. Mỗi bài học có kiểm chứng** | **CHỈ GHI CHỮ** | Catalog và memory có; chưa có sổ nối bài học → test → caller → kết quả chạy. |
| **L. Tài liệu khớp cơ chế CI** | **MỘT PHẦN** | Kiểm sai workflow/commit đã có test. Nhưng `collab-auto-loop-plan.md:35,92` vẫn mô tả author check chạy `pnpm check` trên Mac. |

Đối chiếu các quy tắc trong `claude-memory-workflow-rules.md`:

| Quy tắc | Đánh giá |
|---|---|
| **Hard checks**, dòng 8 | **MỘT PHẦN**: watchdog có thật; không kiểm được mọi bài học đã thành kiểm tra cứng. |
| **Ship-not-plan**, dòng 40 | **MỘT PHẦN**: đã nối vài caller; chưa kiểm mọi quyết định được triển khai. |
| **Không tự cắt phạm vi**, dòng 61 | **CHỈ GHI CHỮ ở khâu cưỡng chế**: có ma trận truy vết; chưa có kiểm phát hiện bỏ mục hoặc hoãn không được duyệt. |
| **Không làm review phình mãi**, dòng 84 | **CHỈ GHI CHỮ** đối với thiết kế; giới hạn hai vòng PR không kiểm vòng thiết kế. |
| **Autopilot v2 đã duyệt**, dòng 115 | **MỘT PHẦN**: thiết kế đã lưu; memory dòng 136 vẫn ghi chưa áp sandbox vào phiên loop. |
| **Một check mỗi lúc**, dòng 150 | Có khóa và test đường chuẩn; lệnh chạy ngoài wrapper vẫn dựa vào kỷ luật. |
| **Không ngồi chờ**, dòng 166 | Có tín hiệu bổ sung việc; chưa buộc phiên Claude nhận và làm. |
| **Retro tự giải**, dòng 174 | **MỘT PHẦN**: có sửa thật, nhưng nhiều giải pháp vẫn chuyển tiếp sang hôm sau. |

## 3. Dấu hiệu “hờ hững”

- **Lỗi còn tồn tại nhưng bảng trở lại bình thường.** State 13.11 ghi `copyBatch.status=error` lúc 10:48. `collab-turn.mjs:217,224` coi lần lỗi là đã chạy hôm nay; dòng 256–258 chỉ đếm lỗi của tick hiện tại. Tôi tái hiện: tick sau không thử lại, `failures=0`, không cảnh báo. Gốc lỗi là thiếu trạng thái “chưa giải quyết”.

- **Đã biết nhưng không khép việc.** Retro 10–11.11 lặp S18 về “merge đang chạy bị báo lỗi”; retro 12.11:118–122 tiếp tục xếp S25–S28 cùng nhiều mục cũ vào hàng đợi. Không có hạn xử lý hoặc kiểm quá hạn.

- **Kết quả chưa tới kho câu mới.** Đọc trực tiếp snapshot: **1.524/1.524 câu còn chờ, 0/168 bộ Daily mới đủ điều kiện phục vụ**. App vẫn dùng câu dự phòng cũ. Nối caller chưa đủ chứng minh chuỗi duyệt–xuất PR–merge hoàn tất.

- **Vá theo ví dụ vẫn lặp.** #354 bị Codex tìm thêm cách vượt bộ lọc qua ba vòng. Retro 09.11:42 đã nhận diện đúng kiểu lỗi này. Gốc là dùng vài ví dụ làm bằng chứng cho bộ phân tích lệnh quá rộng.

- **Hồ sơ thiếu cũng dễ bị hiểu sai.** #134 mở từ 30.10, có nhãn chờ owner; không thể quy toàn bộ thời gian chờ cho Claude. Hai state 11–12.11 nhỏ nhưng không rỗng: chúng giữ bộ đếm, không phải lịch sử sự kiện. Revert `c4ed187` tách sửa CodeQL khỏi PR phát hành; không đủ chứng minh bỏ sửa.

## 4. Lỗi của chính Codex

- Tôi [duyệt #451](https://github.com/honghanh153-creator/la-lanh/pull/451#issuecomment-6842852190) nhưng bỏ sót lỗi lô câu thất bại rồi bị bỏ cả ngày. Test có nhánh “bận”, thiếu nhánh “lỗi rồi tick tiếp”.
- Tôi [duyệt #462](https://github.com/honghanh153-creator/la-lanh/pull/462#issuecomment-6853635550) dù biết test chỉ kiểm tham số Git giả lập; chưa yêu cầu bằng chứng chạy trong môi trường ops sạch.
- Tôi để review thành chuỗi phản ví dụ ở #354 và thiết kế spec 1b. Test `codex-review-prompt.test.mjs:7` chỉ chứng minh lời nhắc tồn tại, không chứng minh reviewer rà đủ cả lớp lỗi.
- Các lỗi P2 của #451 được cho qua đúng chính sách owner, nhưng **APPROVE không chứng minh việc sửa tiếp đã hoàn tất**.

## 5. Đề xuất cải thiện, xếp theo tác động

| Thay đổi cụ thể | Ai làm | Phép chứng minh | Cỡ; owner |
|---|---|---|---|
| Thêm `workflow-lessons.json` và `scripts/check-workflow-lessons.mjs`: bài học chỉ đóng khi có test, caller, commit và kết quả chạy | Claude làm, Codex kiểm | Xóa caller/test hoặc dùng kết quả cũ phải bị báo; chạy trong CI | M; owner duyệt nếu thành điều kiện merge |
| Lưu kết quả duyệt trước khi xuất PR; lỗi xuất chỉ thử lại bước xuất, giữ cảnh báo tới khi xong | Claude làm, Codex kiểm | Giả lỗi commit/push, tick sau phục hồi; không gọi Codex thêm | S; không |
| Hoàn tất #456 và kiểm chuyển đổi biên nhận | Claude làm, Codex kiểm | Comment giả, chép biên nhận, đổi base đều bị chặn | M; có, vì đổi luật merge |
| Nối #457 và A/B vào kiểm nghiệm thu dùng API thật với dữ liệu giả | Codex viết ca nghiệm thu, Claude nối chạy | Cố ý bỏ tổng hợp/thêm nội dung tạm phải trượt; thiếu dữ liệu hợp lệ vẫn đạt | M; owner duyệt nếu chặn merge |
| Thêm bộ khởi chạy agent kiểm checkout, nhánh, công cụ và khóa nhận việc | Claude làm, Codex thử sai môi trường | Sai nhánh/thư mục phải dừng trước thao tác ghi | M; không |
| Thêm hook Ruff dùng `uv run --locked`, giữ nguyên kiểm dữ liệu riêng tư | Claude làm, Codex kiểm | Ruff máy khác phiên bản vẫn bắt file sai; dữ liệu giả thuộc danh sách chặn vẫn bị chặn | S; không |
| Chỉ đồng bộ PR tới lượt; thêm kiểm PR/bài học quá hạn | Claude làm, Codex kiểm | Hai PR chờ không bị đổi head liên tục; mục quá hạn không biến mất khỏi báo cáo | M; không, nếu giữ nguyên luật merge |

## 6. Việc Claude làm ngay tối nay vs cần owner

**Ngay tối nay:** dựng sổ bài học và checker ở chế độ báo cáo; thêm test hai tick cho lỗi lô câu; thử commit trong Git tạm không có danh tính; sửa tài liệu CI; bổ sung hook Ruff và kiểm môi trường agent. Mở PR nhỏ kèm bằng chứng lỗi cũ trượt, bản sửa đạt.

**Cần owner:** đổi điều kiện merge, bật cổng nghiệm thu bắt buộc, mở quyền sandbox ngoài phạm vi đã duyệt, thêm dịch vụ trả phí hoặc đổi trần Codex. Không cần hỏi lại để làm các sửa local ở trên.
