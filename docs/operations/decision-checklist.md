# Checklist quyết định: Claude tự quyết hay hỏi owner

Owner yêu cầu ngày 31.10.2026. Áp dụng cho Claude và Codex trong vòng tự động (`collab-auto-loop-plan.md`).
Mục tiêu: owner chỉ được hỏi những việc thật sự cần owner. Mọi việc khác agent tự quyết, làm, rồi báo lại.

**Một luật duyệt (owner 15–16.11.2026):** chỉ 4 loại việc tới owner: (1) chi phí, dịch vụ mới hoặc quyền truy cập mới; (2) phát hành cho người dùng thật; (3) câu chữ về quyền riêng tư, sự đồng ý, khủng hoảng, an toàn (chặn phát hành, không chặn merge); (4) bật một tính năng thu thêm dữ liệu cá nhân. Mọi việc khác Codex duyệt. Bảng dưới đã chỉnh theo luật này; câu cũ trái luật này hết hiệu lực.

## 1. Năm câu hỏi trước mỗi quyết định

Trả lời lần lượt. Gặp **"có"** ở câu nào thì dừng ở câu đó và làm theo cột "Kết quả".

| # | Câu hỏi | Kết quả nếu "có" |
|---|---|---|
| Q1 | Việc này **có nằm trong danh sách cấm** ở mục 2 không? | Không làm. Hỏi owner, kèm đề xuất. |
| Q2 | Có **câu chữ mới mà người dùng nhìn thấy** không (copy, nhãn, thông báo, bản đọc)? | Ghi câu mới với cờ chờ duyệt (`status: pending`, xem dưới bảng); Codex duyệt rồi câu mới tới người dùng. Chỉ câu nhóm `privacy`, `consent`, `crisis`, `safety` cần owner duyệt, và chỉ chặn phát hành, không chặn merge. |
| Q3 | Có **thu thập, lưu, chia sẻ hay suy ra thêm dữ liệu cá nhân** không, hoặc đổi mục đích/thời hạn lưu? | Làm sau cờ tắt (không thu, không lưu), kèm phân tích privacy (AGENTS.md mục 3); Codex duyệt. **Bật** thu thập thật thì hỏi owner. |
| Q4 | Có **đảo một quyết định owner đã chốt** không (bỏ tính năng owner đã giao, đổi thứ tự ưu tiên owner đã chốt)? | Ghi vào file việc chờ owner, kèm 2 lựa chọn và khuyến nghị. Tính năng mới hay đổi cách làm trong kế hoạch đã chốt thì tự quyết, Codex duyệt. |
| Q5 | Có **tốn tiền, không hoàn tác được, hoặc ảnh hưởng người dùng thật ngay** không? | Hỏi owner. |
| — | Cả năm câu đều "không" | **Tự quyết, làm, báo lại** trong tóm tắt cuối lượt. |

**Q2 cho bản đọc (owner giao Claude chốt, 03.11.2026):**
- Bản đọc (Daily, Tarot, Khám phá, Hợp gu) do nhà máy nội dung sinh theo bộ chuẩn và đã qua đủ cổng tự động (lớp A lint, lớp B giám khảo, lớp C người đọc giả lập) thì không cần owner duyệt từng câu.
- Owner chỉ xem câu bị cổng gắn cờ và báo cáo điểm của mỗi đợt.
- Bộ chuẩn (C3a, `docs/plans/2026-11-02-daily-v2-content-quality-plan.md`) do Claude chốt và Codex review.
- Đổi bộ chuẩn thì qua PR như mọi tài liệu khác.
- **Cờ chờ duyệt (owner, 06.11.2026):** câu mới ghi vào `apps/api/app/domains/content/copy_registry.json` với `status: pending` và gọi qua `copy_text(id, câu đã duyệt hiện tại)`. Câu pending không bao giờ tới người dùng, nên PR được merge **không cần** `needs-owner`. Mỗi ngày tick của vòng tự động chạy `node scripts/codex-copy-review.mjs` một lần (từ giờ tự chạy 08:00, chỉ khi còn câu pending ngoài nhóm owner-only, tính một lượt vào trần Codex, chờ khi review.lock bận, bỏ qua khi PR lô trước còn mở; tối đa 200 câu một lô) để Codex (read-only) chấm lô pending và mở PR `agent/claude/copy-batch-YYYYMMDD`; câu Codex duyệt mới được phục vụ. Nhóm `privacy`, `consent`, `crisis`, `safety` vẫn chỉ owner duyệt (cổng `scripts.fallback_approval` từ chối duyệt của Codex cho nhóm này). Từ 16.11.2026 câu nhóm này chặn **phát hành**, không chặn merge: PR được merge khi app vẫn dùng câu đã duyệt.
- **Bài Học (owner 14.11.2026, đổi 15.11.2026):** bài đầu của mỗi khóa và danh sách lằn ranh đỏ do Codex duyệt; owner xem ngẫu nhiên. Các bài sau Codex duyệt theo đúng danh sách ấy, qua cờ chờ duyệt như trên. Câu về quyền riêng tư, đồng ý và hỗ trợ khi khủng hoảng trong bài Học vẫn cần owner duyệt. Nguồn: `docs/plans/2026-11-15-ke-hoach-7-tuan-moc-do.md`.
- Vẫn cần owner duyệt (từ 16.11.2026 chỉ chặn phát hành): lời giải thích quyền riêng tư, nội dung pháp lý về quyền riêng tư và sự đồng ý, câu hỗ trợ khi khủng hoảng, và mọi ngoại lệ của luật an toàn S1–S7. Copy giao diện thường (nút, thông báo, nhãn) và bảng nghĩa đi qua cờ chờ duyệt, Codex duyệt.

**Cải thiện trải nghiệm người dùng (owner, 31.10.2026):** việc giúp người dùng dùng app dễ, rõ, êm hơn mà không vướng Q1–Q5 thì agent **chủ động làm luôn**, không chờ được giao: sửa lỗi hiển thị, trạng thái lỗi/đang tải rõ ràng hơn, bỏ thông tin kỹ thuật lộ ra người dùng, tránh lặp, tăng khả năng tiếp cận, tăng tốc. Nếu việc đó cần câu chữ mới thì vẫn qua Q2 (cờ chờ duyệt, Codex duyệt; nhóm privacy/consent/crisis/safety thì owner).

## 2. Danh sách cấm (luôn cần lệnh riêng của owner)

- Merge vào `main`, release, deploy, SSH hay chạm server/database thật.
- Bật provider, đổi IAM, secret, budget, gọi API trả phí ngoài review Codex trong vòng tự động.
- Đọc dữ liệu thật của người dùng trên production, kể cả của owner (owner có thể tự xem rồi gửi đúng trường cần).
- Cài PostgreSQL hoặc chạy probe #106 (owner loại trừ riêng ngày 29.10).
- Đăng dữ liệu cá nhân, ngày/giờ/nơi sinh thật, ảnh chụp tài khoản lên repo public.
- Viết `Duyệt`, `Giữ`, `Bỏ #N` thay owner trên issue plan.

## 3. Việc Claude tự quyết (ví dụ đã chốt)

| Loại việc | Tiêu chí đã thỏa | Ví dụ |
|---|---|---|
| Sửa lỗi kỹ thuật không đổi câu chữ | Q1–Q5 đều "không"; có test đỏ→xanh | #144 Jyotish 503, #142 kiểm tra "máy bận" |
| Thay đổi quy trình trong vòng tự động | Miễn phí, hoàn tác được; vẫn qua Codex review | Ops đi trước (#135), tick tự check (#137) |
| Sửa fix-forward P2 | Đã có verdict; không đổi copy | #140 |
| Hướng kỹ thuật khi dữ liệu thiếu | Không đổi dữ liệu thu thập | E1 #143: giờ khoảng vẫn đọc hành tinh, bỏ nhà/cung mọc |
| Việc local, miễn phí, riêng tư | Không chạm production | Cài job launchd, dọn lượt autopilot treo |
| Cải thiện trải nghiệm không đổi câu chữ | Q1–Q5 đều "không" | Thống nhất mức dữ liệu trên trang Khám phá, giấu footer kỹ thuật (#143 E4) |

## 4. Input cần có trước khi quyết

Trước khi push: chạy nhanh lint/format/test của đúng phần đã sửa (vài giây), để author check không fail vì lỗi định dạng (bài học #144).


| Input | Lấy ở đâu |
|---|---|
| Yêu cầu gốc và AC | PRD/SRS/US, issue task |
| Quyết định owner đã chốt | `collab-auto-loop-plan.md` §2, hub #2, memory của Claude |
| Bằng chứng | Repro (dữ liệu tổng hợp), test đỏ trên code cũ, log |
| Ảnh hưởng | Copy? Dữ liệu? Chi phí? Hoàn tác được không? |
| Cổng tự động | `pnpm check` (gồm `fallback_approval`, content audits), Codex review |

## 5. Khi phải hỏi owner

- Một câu hỏi, có **lựa chọn đánh số + khuyến nghị**, nói rõ hậu quả mỗi lựa chọn.
- Không hỏi lại điều owner đã chốt; không hỏi việc thuộc mục 3.
- Trong lúc chờ owner, làm tiếp việc khác (§3.2 cách làm hằng ngày); không ngồi chờ.
- Việc chờ owner được gắn `needs-owner` và hiện ở bảng trạng thái trên issue plan.

## 6. Ghi lại

Mỗi quyết định owner mới: ghi ngay vào `collab-auto-loop-plan.md` §2 hoặc hub #2 để mọi session đều đọc được. Quyết định Claude tự đưa ra: ghi trong PR/issue liên quan, nêu câu hỏi nào trong mục 1 đã được trả lời "không".
