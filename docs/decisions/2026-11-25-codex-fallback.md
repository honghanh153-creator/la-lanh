# Codex sinh bản vá, CI chạy mã nhánh (#894, #899)

Ngày 25–26.11.2026. Mức L. Bản sửa do Codex làm, cần Codex review và Anti phản biện đúng head trước merge.

## Vấn đề đã kiểm chứng

Owner yêu cầu chuyển việc sang Codex khi Claude gần hết hạn mức và phải có phản biện độc lập. Bản đầu chạy test nhánh trong `sandbox-exec` trên Mac. Canary native gọi `sysctl(CTL_KERN, KERN_PROCARGS2, PID)` đã đọc được env của một PID giả ngoài sandbox cùng UID. `deny default`, `process-info` chỉ self và danh sách sysctl hẹp không chặn đường này. Test dùng `/bin/ps` trước đó tạo cảm giác an toàn sai vì binary setuid không chạy được trong sandbox.

Không dùng dữ liệu hay env thật của owner cho phép thử. Không mở syscall rộng, không bỏ qua test để tuyên bố đã gỡ. Hướng giữ fallback trước lượt là an toàn nhưng chưa khôi phục chức năng, nên cần đổi cách thực thi.

## Quyết định

1. **Codex chỉ sinh dữ liệu JSON.** Chạy CLI trong cwd tạm trống, read-only, `--ignore-user-config`, tắt shell, apps, MCP cấu hình riêng, plugin, hook, browser, computer use và agent con. Catalog từ binary đã kiểm được thu hẹp: shell disabled, apply_patch null, tool mode direct, không tool bổ sung. Giữ đăng nhập hiện có, không sao chép token hoặc thay cấu hình toàn máy. Phiên bản CLI khác bản đã kiểm thì giữ trước lượt, chờ kiểm chứng lại.
2. **Context chỉ có mã công khai.** Host đọc file thường trong clone mới, public diff và phát hiện review. Không theo symlink hoặc đọc `.git`, env, cấu hình riêng. Context vượt giới hạn bị giữ trước quota, không cắt âm thầm.
3. **Host áp JSON đã kiểm.** Mỗi edit có path, hash nội dung cũ và nội dung mới hoặc null để xóa. Kiểm toàn bộ trước khi ghi: đường tương đối trong clone, không traversal, symlink, trùng/đè đường dẫn, file cổng hoặc env; hash phải khớp bản đã gửi. Model không có công cụ đọc/ghi file hay thực thi lệnh.
4. **Kiểm tĩnh trước push, test trong CI.** Host kiểm Git metadata, file cổng, dấu xung đột, nội dung/mode và dữ liệu riêng tư. Chỉ code tin cậy của ops chạy; không chạy script/test/config nhánh trên Mac. Sau push PR nhánh, thông báo rõ test còn chờ CI, không phát biên nhận PASS sớm.
5. **Dùng CI đã có.** `collab-cron.sh` đã đặt `LA_LANH_CHECK_SOURCE=ci`. Author check đọc job `pr-check / check` đúng head và base đã thử từ merge commit. Mặc định Author check là CI ngay khi thiếu env; local phải được chọn rõ. PR có dấu Codex sửa luôn dùng CI kể cả caller xin local. CI là `pull_request`, token chỉ đọc, không secrets, checkout không giữ credential. Merge vẫn đòi CI/Author check, Codex review và phản biện thứ hai đúng head.

## Chốt bảo vệ giữ lại

- PR/file thực từ Git được đối chiếu trước lượt; file env và cổng giữ sớm, cả xung đột và thay đổi staged từ merge. Không chỉ tin danh sách API có thể thiếu trang.
- Clone mới riêng từng lượt, ngoài thư mục state; dọn khi kết thúc. Git không chạy hook/fsmonitor; chuẩn bị và kiểm tra không dùng config global/system, push chỉ dùng cấu hình xác thực tin cậy của owner.
- Khóa quota trước model call; giới hạn ngày và giờ không đổi. Không chuẩn bị được writer thì không gọi model, không giữ quota, không gắn lỗi runtime thành việc của owner/Claude.
- Ghi provenance cục bộ trước push. Comment lỗi vẫn bắt buộc phản biện thứ hai; không force push, không đổi `main` hoặc deploy.

## Sửa sau phản biện Anti ngày 27.11

- Khi giải xung đột, file cổng nhận nguyên nội dung và mode từ integration được giữ trong merge. Đối chiếu với integration trước writer và giữ snapshot để writer hay bước kiểm không thể sửa chúng. File cổng do PR đổi, xung đột ở cổng và cổng mới không được miễn kiểm.
- Phiên Anti hết hạn được xử lý trước khi đọc API. Lỗi đọc, mở phiên, trả sai mẫu, dùng công cụ hoặc đăng review đều giữ PR và nhường hàng. Mỗi head thử tối đa hai lần, cách ít nhất 10 phút; hết lượt thì chờ người phản biện khác hoặc head mới. Chọn PR chưa thử trước PR thử lại. Không hạ tiêu chuẩn nội dung hay biên nhận để mở cổng.
- Daemon khởi động lại được chọn theo hub hợp lệ mới nhất. `modifiedResponse` rỗng dùng nội dung `response`, không vứt một câu trả lời hợp lệ.
- `research-sources` và `collab-size` là gate root tường minh. Test đối chiếu mọi lệnh Node trực tiếp trong workflow CI với danh sách bảo vệ để không bỏ sót lại.

## Kiểm chứng và giới hạn

Probe trên CLI 0.171.0-alpha.13 đã xác nhận catalog nhận shell disabled/apply_patch null. Model bị yêu cầu đọc file canary và tạo file bằng tool đã trả `NO_TOOLS`; không có command/MCP event, file không được tạo. Đây là phép thử capability, chưa thay kiểm chứng bản sửa cuối qua CI và Anti.

CI chỉ bắt đầu sau push nhánh PR. Bản push có thể chưa xanh, nhưng không thể merge khi thiếu các cổng. Chất lượng bản vá còn phụ thuộc context đủ và review; giới hạn context/phiên bản hoặc JSON sai phải báo giữ rõ lý do, không lặp tốn lượt để giả có tiến triển.

## Nguồn đã đọc

- Apple XNU `sysctl_procargsx`: https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sysctl.c — đối chiếu bằng canary thật trên PID giả.
- OpenAI Codex registry `add_shell_tools` và `ApplyPatchHandler`: https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/spec_plan.rs — đối chiếu với CLI đang cài và probe thật.
- OpenAI `ModelInfo`: https://github.com/openai/codex/blob/main/codex-rs/protocol/src/openai_models.rs — các trường shell, apply_patch và tool mode.
- Nguồn CI và kiểm head/base trong repo: `.github/workflows/pr-check.yml`, `scripts/collab-check.mjs`, `scripts/collab-cron.sh`.
