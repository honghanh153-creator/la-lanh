---
title: GPT-6 Luna All Content Rewrite Plan - Document Review
date: 2026-10-03
document_type: unified-plan
status: reviewed-and-amended
reviewed_document: docs/plans/2026-10-03-gpt-6-luna-all-content-rewrite-plan.md
---

# Document review

## Verdict

Plan đủ rõ để bước sang implementation theo từng surface sau khi áp dụng các sửa đổi dưới đây. Không còn blocker cần product decision mới. Rủi ro chính còn lại nằm ở migration của worker/gates và chất lượng corpus, không phải ở phạm vi sản phẩm.

## Review coverage

| Lens | Kết quả |
|---|---|
| Coherence | Tìm thấy xung đột giữa immutable generation key và Studio regenerate; đã thêm `candidate_variant`. |
| Feasibility | Generic cascade và startup fallback không khớp code hiện tại; đã chuyển sang explicit cleanup và fail-fast khi flag bật nhưng thiếu secret/governance. |
| Product | Giữ đúng quyết định: Luna viết lại toàn bộ personalised interpretive content, không chạm static/legal/transactional copy. |
| Design | Runtime fallback và UI disclaimer vẫn tách riêng; Studio không trở thành dependency của app. |
| Security/privacy | Đã thêm authorization recheck, consent revocation, encrypted transient storage, retention và Studio redaction. |
| Scope | Chuyển U5-U9 thành các release slice độc lập; 670-case corpus được xây cộng dồn theo surface. |
| Adversarial | Loại central content god-object và giả định polymorphic FK cascade; giữ ambiguous-timeout no-retry. |

## Findings đã áp dụng

### 1. Editorial regenerate xung đột với immutable generation key

Nếu cùng key chỉ được generate một lần thì thao tác `regenerate` trong Studio không có semantics hợp lệ. Plan giờ dùng `candidate_variant`: runtime reopen vẫn reuse active artifact, còn editorial regenerate tạo candidate riêng và không overwrite lịch sử.

### 2. Missing provider key không thể vừa fail-fast vừa “deterministic-only”

Current `Settings` cố ý reject startup khi generation đã bật nhưng thiếu API key hoặc governance approval. Plan giờ giữ safeguard này; deterministic-only chỉ áp dụng khi feature bị tắt hoặc provider lỗi sau một cấu hình hợp lệ.

### 3. Generic owner key không tạo được cascade thật

Một ledger tham chiếu Reading, Tarot, Radar, Matching và Share không thể có một foreign key trỏ đến năm bảng owner. Plan giờ yêu cầu domain gọi idempotent cancellation/purge và có retention sweeper cho orphan thay vì tuyên bố cascade không thể thực thi.

### 4. Consent mới chỉ xuất hiện như điều kiện phụ

Plan trước đó chưa biến purpose-scoped authorization và revocation thành acceptance contract đầy đủ. R19/AE7 giờ yêu cầu kiểm consent ở enqueue lẫn send time, chặn quyền bị suy rộng giữa Reading và Radar/Matching, và hủy pending work sau revocation.

### 5. Generated candidate là dữ liệu nhạy cảm nhưng retention chưa đủ cụ thể

R20 và Data Lifecycle giờ yêu cầu encrypt safe brief/output at rest, per-surface retention, purge/tombstone theo owner lifecycle, và không hiển thị raw values trong Studio/telemetry.

### 6. Rollout vô tình phụ thuộc U10 Content Studio

U11 trước đó phụ thuộc U10 dù Product Contract nói Studio không phải runtime dependency. Dependency đã được tách: release gate có CLI artifacts; Studio được mở rộng dần và có thể vẫn tắt ở production.

### 7. Shared service có nguy cơ thành god-object

KTD1/KTD4 đã đổi từ generic service sở hữu quá nhiều knowledge sang hybrid runtime: shared attempt lifecycle, domain-owned compiler/policy/revision/projection. Chi tiết nằm trong architecture review đi kèm.

## Evidence từ code và history

- `apps/api/app/config.py`: generation enabled yêu cầu provider, API key và governance approval; Studio beta auth bị chặn ở staging/production.
- `apps/api/app/domains/readings/worker.py`: lease, send marker và ambiguous-timeout handling là lifecycle đã được kiểm chứng, nên phải được tái sử dụng thay vì viết lại theo từng domain.
- `apps/api/app/domains/readings/gates.py`: current meaning gate so prose bằng blueprint; U2 cần characterization-first rồi mới chuyển sang semantic ownership checks.
- `apps/api/app/infrastructure/generation/base.py`: provider boundary hiện import trực tiếp Reading types, xác nhận cần tách transport kernel.
- `apps/api/app/domains/tarot`, `radar`, `matching`, `share`: mỗi domain có encryption/deletion ownership riêng, không phù hợp với central revision store.
- Git history `1a3bbc6`, `0b3fecb`, `b6b6589`: lần lượt thiết lập worker safety, semantic coherence và Studio safeguard.

## Residual risks

- Chưa có analytics/incident evidence trong repo để xác định threshold cost, latency và rejection rate tối ưu; U11 phải đo ở shadow rollout.
- Fixed corpus chỉ chứng minh các case đã lấy mẫu; beta feedback vẫn cần được review theo surface, không dùng làm training data tự động.
- Managed identity cho Production Studio vẫn là follow-up vận hành; điều này không chặn runtime rewrite hoặc CLI release gate.

## Review process note

Đã thử khởi chạy các runner kiến trúc read-only độc lập, nhưng host policy chặn việc gửi repository source ra external model service. Review này vì vậy được thực hiện hoàn toàn local bằng source và Git history; không có dữ liệu dự án nào được xuất ra ngoài.
