# Người giả hằng đêm (200 trong 1000)

Owner quyết ngày 15.11.2026 (hub #2): ngày nào nhánh chung có thay đổi liên quan tính năng app, cuối ngày cho 200 người giả bốc ngẫu nhiên trong 1000 vào thử; sáng hôm sau owner xem trong báo cáo 07:00. Codex phản biện thiết kế trước khi xây: chốt hai SHA, cùng 200 hồ sơ, cùng đồng hồ, dữ liệu và cách chấm; lỗi an toàn hoặc lộ dữ liệu báo ngay; lượt Codex tính vào trần chung; kết quả người giả **không thay** QA trình duyệt.

## Chạy khi nào

- Tác vụ hẹn giờ trên máy owner, khoảng 23:00, trước mốc 23:35 vòng tự động ngừng nhận việc mới. Sau 23:35 lệnh `prepare` từ chối chạy, kể cả khi vừa chờ xong khóa; mỗi lượt mô phỏng bị cắt ở 23:59.
- Chỉ chạy khi diff từ đầu ngày tới cuối ngày của `collab/integration` có file chạm app: `apps/web/src`, `apps/web/public`, `apps/api/app`, migration, `apps/mobile`, `packages`, assets, file cấu hình web, dependency (`package.json`, lockfile, `pyproject.toml`, `uv.lock`), `vendor/`, `infra/`, `Dockerfile`. File không phân loại được cũng chạy. Chỉ đổi docs, scripts, qa, test thì không chạy; báo cáo ghi lý do.
- Đầu ngày: `git rev-list -1 --first-parent --before="<ngày> 00:00 +0700" origin/collab/integration`. Cuối ngày: tip lúc chạy. Cả hai SHA ghi trong báo cáo.

## Cách chạy cố định

- 200 người: xếp 1000 id theo `sha256("personas-nightly:<ngày>:<id>")`, lấy 200 nhỏ nhất. Hạt `personas-nightly:<ngày>` ghi trong báo cáo. Không ai chọn tay.
- Hai clone riêng dưới `~/.cache/la-lanh-collab/personas-nightly/`. Clone đầu ngày lấy app của SHA đầu ngày nhưng bộ chạy và cách chấm (`apps/api/scripts/persona_*.py`, `qa/personas`) của SHA cuối ngày, để hai bên chỉ khác code app.
- Cùng ngày bắt đầu mô phỏng, cùng giờ, SQLite tạm, không mạng. Báo cáo của cả hai bản dựng bằng code cuối ngày.
- Giữ khóa việc nặng `check.lock` (cùng khóa author check) và chờ tới khi không còn test nặng nào chạy, tối đa 30 phút. `persona_sim` đã được tính là việc nặng (`heavyPatterns`), nên author check cũng chờ nó.
- Ghi tải máy (load average, mẫu 15 giây) và thời gian của từng bản vào báo cáo.

## Chấm

- Nội dung mới (chưa có điểm theo hash) được chia thành `judge-NN.jsonl`, mỗi tệp tối đa 75 mục. Mỗi tệp giao cho một Claude subagent **mới**, mù với ngưỡng, theo `qa/personas/judge-prompt.md` mục A.
- Điểm đã chấm được giữ qua các đêm ở `personas-nightly/labels/`, nên đêm sau chỉ chấm phần mới.
- Codex chấm đối chiếu 10 mục mới chọn trước theo hạt (`<hạt>:codex`), tối đa 1 lượt mỗi đêm. Lượt gọi giữ khóa `review.lock` như các lần review Codex khác, được tính vào `codexRuns` **trước khi** gọi (gọi lỗi vẫn tính), chừa `auditReserve`, và không chạy quá 23:59. Hết trần hoặc khóa đang bận thì bỏ qua; báo cáo ghi rõ.

## Báo ngay

Ngay sau hai lượt mô phỏng, trước bước chấm, `prepare` mở hoặc cộng dồn issue `[ops-alert] người giả hằng đêm` khi có một trong các điều sau (các kiểm này không cần giám khảo, nên chấm chậm hay Codex lỗi cũng không làm trễ cảnh báo). `finish` kiểm lại trên báo cáo cuối và chỉ báo lý do mới:

- một ngưỡng nhóm "An toàn" đạt ở đầu ngày nhưng trượt ở cuối ngày;
- số câu khủng hoảng được chuyển sang hỗ trợ giảm, hoặc số lần báo nhầm (câu "chết" nghĩa bóng, câu hỏi Tarot thường) tăng;
- chữ một người giả gõ hiện trên màn của người giả khác (lộ dữ liệu giữa người dùng).

Issue chỉ ghi SHA, ngày và loại lỗi, không ghi chữ người giả. Tác vụ hẹn giờ gửi thêm thông báo đẩy cho owner.

## Kết quả

`/Users/<owner>/Documents/New project/la-lanh-bao-cao/<ngày hôm sau>/personas/` (đổi bằng `LA_LANH_REPORT_DIR`):

- `report.md`: hai SHA, hạt, số file đổi, cảnh báo an toàn (đầu tiên), bảng ngưỡng đầu ngày so với cuối ngày, Codex đối chiếu, tải máy;
- `metrics.json`: cùng số liệu dạng máy đọc;
- `start.md`, `end.md`: báo cáo đầy đủ của từng bản.

Báo cáo 07:00 (`la-lanh-bao-cao-7h`) đọc thư mục này.

## Lời giao cho tác vụ hẹn giờ 23:00

Dán nguyên văn khi tạo tác vụ (owner duyệt việc tạo tác vụ):

> Chạy người giả hằng đêm của Lá Lành. Repo: thư mục ops clone `~/.cache/la-lanh-collab/ops` (đã ở `origin/collab/integration`; nếu chưa có thì `git clone https://github.com/honghanh153-creator/la-lanh.git` vào đó, rồi `git fetch origin collab/integration && git checkout --detach FETCH_HEAD`). PATH: `$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.local/bin:/usr/bin:/bin`.
> 1. `node scripts/personas-nightly.mjs prepare`. Nếu `alert` là true, gửi ngay thông báo đẩy: "Người giả hằng đêm: <reasons>. Xem issue ops-alert." Nếu `status` là `skipped`, `refused` hoặc `busy` thì dừng; với `busy` hoặc `error` gửi thông báo đẩy một câu cho owner.
> 2. Với mỗi tên trong `chunks`, giao một Claude subagent mới, song song tối đa 12, theo `qa/personas/judge-prompt.md` mục A. `<PACKETS>` là `~/.cache/la-lanh-collab/personas-nightly/<ngày>/<tên>.jsonl`, `<OUT>` là `.../<ngày>/out/<tên>.json`, rubric là `judge-rubric.md` trong cùng thư mục. Mỗi subagent chạy `node scripts/personas-nightly.mjs check --date <ngày> <tên>` tới khi in `ok`. Nếu `labelPackets` > 0, làm tương tự với `label-01.jsonl` theo mục B (`check ... label-01` kiểm dạng nhãn `light`/`not_light`).
> 3. `node scripts/personas-nightly.mjs merge --date <ngày> <các tệp out>`.
> 4. `node scripts/personas-nightly.mjs codex --date <ngày>`.
> 5. `node scripts/personas-nightly.mjs finish --date <ngày>`. Nếu `alert` là true (lý do mới chưa báo ở bước 1), gửi thông báo đẩy như bước 1.
> Không đăng chữ người giả, ảnh hay dữ liệu cá nhân lên GitHub. Không merge, không deploy.
