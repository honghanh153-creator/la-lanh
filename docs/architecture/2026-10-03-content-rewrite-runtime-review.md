---
title: Content Rewrite Runtime Architecture Review
date: 2026-10-03
status: proposed
decision: hybrid-runtime-domain-owned-semantics
source_plan: docs/plans/2026-10-03-gpt-6-luna-all-content-rewrite-plan.md
---

# Content Rewrite Runtime Architecture Review

## Kết luận

Chọn kiến trúc **hybrid shared runtime + domain-owned semantics**.

- Dùng chung provider transport, attempt lifecycle, lease/send marker, retry policy, cost metrics và kill switch.
- Mỗi domain vẫn sở hữu semantic compiler, consent, surface policy, candidate revision, activation, retention và deletion.
- Shared ledger chỉ giữ encrypted minimised brief và transient provider result; không giữ raw chart, câu hỏi Tarot, profile hay domain model.
- Domain projector tiêu thụ accepted result theo idempotency key. Runtime không được tự sửa projection của Reading, Radar, Matching, Tarot hoặc Share.

Hướng này giữ được độ sâu của một runtime dùng chung mà không biến `content_rewrite` thành god-object.

## Usage trước interface

```python
# Daily domain
brief = daily_rewrite.compile(plan, context, authorization)
artifact = await rewrite_runtime.submit(brief)

# Read path luôn có deterministic fallback.
projection = await daily_rewrite.resolve(
    artifact_key=artifact.key,
    fallback=deterministic_revision,
)
```

```python
# Worker dùng chung, không import ReadingPlan/TarotSession/RadarResult.
attempt = await attempt_store.lease(now=clock.now())
policy = policy_registry.for_surface(attempt.surface)
result = await provider.generate(policy.provider_request(attempt.decrypt_brief()))
receipt = policy.evaluate(result)
await attempt_store.complete(attempt, result, receipt)
await accepted_results.publish(attempt.result_ref)
```

```python
# Domain projector là owner duy nhất của revision/projection.
accepted = await accepted_results.claim(surface=Surface.DAILY)
candidate = daily_rewrite.materialise(accepted)
await reading_repository.save_candidate_if_current(candidate)
```

Callers chỉ cần biết `submit` và cách resolve projection của chính domain. Lease, send marker, provider schema, retry, encryption và cost accounting bị giấu sau runtime.

## Type sketch

```python
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

SafeInput = TypeVar("SafeInput")
Draft = TypeVar("Draft")

@dataclass(frozen=True, slots=True)
class ArtifactKey:
    surface: str
    owner_namespace: str
    owner_key: str
    blueprint_hash: str
    model_version: str
    prompt_version: str
    schema_version: str
    gate_version: str
    candidate_variant: str = "runtime"

@dataclass(frozen=True, slots=True)
class RewriteBrief(Generic[SafeInput]):
    key: ArtifactKey
    authorization_receipt_id: str
    safe_input: SafeInput

@dataclass(frozen=True, slots=True)
class AcceptedResult:
    key: ArtifactKey
    encrypted_output_ref: str
    gate_receipt_ref: str

class RewriteRuntime(Protocol):
    async def submit(self, brief: RewriteBrief[object]) -> ArtifactKey: ...
    async def cancel_owner(self, owner_namespace: str, owner_key: str) -> None: ...

class SurfacePolicy(Protocol, Generic[SafeInput, Draft]):
    surface: str
    def build_request(self, safe_input: SafeInput) -> dict[str, object]: ...
    def parse_and_gate(self, response: object, safe_input: SafeInput) -> Draft: ...

class DomainProjector(Protocol):
    surface: str
    async def project(self, accepted: AcceptedResult) -> None: ...
```

Các transport type, OpenAI response type, database row và domain model không được export qua public protocol.

## Module map

```text
apps/api/app/
├── domains/content_rewrite/
│   ├── contracts.py       # ArtifactKey, RewriteBrief, receipts
│   ├── runtime.py         # submit/cancel; no domain imports
│   ├── worker.py          # lease/send/complete lifecycle
│   ├── registry.py        # composition-root policy registration
│   ├── repository.py      # narrow attempt-store protocol
│   └── postgres.py        # encrypted generic attempt ledger
├── domains/readings/rewrite.py
├── domains/tarot/rewrite.py
├── domains/radar/rewrite.py
├── domains/matching/rewrite.py
├── domains/share/rewrite.py
│   # each owns compiler, policy, projector and domain revision
└── infrastructure/generation/
    ├── base.py            # provider-neutral transport result
    └── openai.py          # Responses API only
```

`main.py` là composition root duy nhất đăng ký `surface -> policy/projector`. Registry không được trở thành service locator mà domain code gọi tùy ý.

## Grounding: hệ thống hiện tại hoạt động thế nào

1. `GenerationProvider` hiện phụ thuộc trực tiếp vào `ReadingPlan` và trả `ReadingCandidate`; vì vậy boundary chưa thể phục vụ Tarot/Radar/Matching mà không kéo Reading types sang các domain khác.
2. `ReadingGenerationWorker` đã có lifecycle quan trọng: durable lease, send marker, retry chỉ khi chắc chắn chưa gửi và không retry ambiguous timeout.
3. Reading domain đã sở hữu revision và projection, gồm trạng thái available/active và explicit activation. Đây là ownership tốt, không nên chuyển vào generic ledger.
4. `meaning_gate` hiện yêu cầu prose trùng tuyệt đối với semantic blueprint. Muốn cho phép rewrite, phải đổi sang kiểm tra immutable semantic keys, required concepts và evidence coverage, không được bỏ gate.
5. Content Studio hiện là Daily matrix control plane và beta bearer auth bị chặn ở staging/production. Runtime không được phụ thuộc vào Studio và plan không được lách safeguard này.
6. Tarot, Radar, Matching và Share có encryption/deletion model riêng. Generic runtime phải gọi explicit cancellation port; một `owner_type + owner_id` không thể tạo foreign-key cascade thật đến nhiều bảng khác nhau.

## Why: vì sao các boundary hiện tại tồn tại

- Commit `1a3bbc6` đưa vào Reading worker và generation boundary để giữ provider call ngoài transaction, phân biệt retry-safe với ambiguous delivery và bảo toàn deterministic result.
- Commit `0b3fecb` thêm semantic blueprint/meaning gate sau các lỗi nội dung không nhất quán; do đó rewrite không được quay lại cách kiểm prose chỉ bằng prompt.
- Commit `b6b6589` thêm Content Studio, revision conflict handling và chặn beta token auth ở production; đây là safeguard có chủ ý, không phải thiếu wiring.

Không có issue tracker, product analytics hay incident log trong workspace để xác minh tần suất lỗi vận hành; kết luận trên chỉ dựa vào source và Git history.

## Ba candidate đã so sánh

| Candidate | Điểm mạnh | Điểm yếu quyết định | Kết quả |
|---|---|---|---|
| A. Central generic ledger + generic revisions | Một worker, một schema audit, rollout đồng đều | Ledger phải hiểu mọi domain, activation và deletion; polymorphic owner không có FK thật; dễ thành content god-object | Loại |
| B. Shared provider kernel, mỗi domain có queue riêng | Ownership và referential integrity rõ nhất | Lặp lease/send-marker/retry/metrics/encryption ở 5 domain; hành vi lỗi dễ lệch | Không chọn làm base |
| C. Shared attempt runtime + domain revisions | Dùng chung phần khó, giữ meaning/consent/projection ở domain; migration theo surface | Cần registry chặt và explicit cleanup thay vì cascade | Chọn |

## Red-flag screening

### Shallow module

`RewriteRuntime` chỉ có `submit` và `cancel_owner`, nhưng giấu encryption, idempotency, lease, send marker, retry, provider adaptation, cost và kill switch. Đây là deep module. Không thêm các method kiểu `minimise`, `build_prompt`, `run_gate`, `save_revision` cho caller điều phối.

### Information leakage

OpenAI schema, transport response và SQL rows chỉ tồn tại trong infrastructure/runtime. Domain nhận safe typed brief và accepted result reference; provider không trả semantic key để tránh model sửa ownership data.

### Temporal decomposition

Không tách các module công khai theo thứ tự `minimise -> call -> validate -> save`. Mỗi surface policy đóng gói knowledge của surface; runtime đóng gói lifecycle bất đồng bộ.

### Pass-through layers

Không tạo `ContentRewriteService` chỉ forward sang provider. Runtime phải thực sự sở hữu idempotency, persistence và failure semantics; domain projector phải thực sự sở hữu revision transaction.

### Shared mutable state

- Unique key trên full `ArtifactKey` ngăn duplicate attempt.
- Lease token + send marker giữ single-send semantics.
- Projector kiểm domain version trước khi ghi candidate.
- `candidate_variant` cho editorial regenerate; không overwrite immutable runtime key.
- Consent được kiểm lại ngay trước send marker, không chỉ khi enqueue.

## Failure semantics

| Failure | Runtime result | User-visible behavior |
|---|---|---|
| Generation disabled | Không enqueue | Deterministic content |
| Enabled nhưng thiếu key/governance | Startup fail-fast | Không deploy cấu hình sai |
| Consent revoked before send | Cancelled + purge brief | Deterministic content |
| Failure proven before send | Retry within cap | Deterministic content trong lúc chờ |
| Ambiguous timeout after send marker | Terminal ambiguous; no retry | Deterministic content |
| Invalid schema/refusal/gate fail | Rejected receipt | Deterministic content |
| Accepted result but stale domain version | Projector discards/tombstones | Existing active revision |
| Studio unavailable | No effect on runtime | Existing active/deterministic revision |

## Privacy and retention boundary

- Domain minimiser chạy trước `submit`; unknown fields bị reject.
- Safe brief vẫn được coi là sensitive: encrypt at rest, không log value, có per-surface TTL.
- Studio chỉ thấy allowlisted evidence labels và field manifest, không thấy birth data, third-party data hoặc raw Tarot question.
- Deletion/revocation gọi `cancel_owner` idempotently; retention sweeper xử lý orphan nếu domain transaction và runtime transaction không cùng database boundary.
- Batch chỉ nhận synthetic/redacted fixtures.

## Migration sequence

1. Characterise Reading worker, gates và revision activation hiện tại.
2. Tách provider transport khỏi `ReadingPlan/ReadingCandidate` nhưng chưa đổi runtime behavior.
3. Thêm generic attempt ledger và chạy song song; request cũ tiếp tục drain ở Reading queue.
4. Cut over chỉ Daily enqueue mới; không dual-send cùng artifact.
5. So revision parity, failure behavior, consent và deletion; sau đó mới bỏ old enqueue path.
6. Mỗi surface tiếp theo thêm policy + projector + corpus riêng; rollout độc lập.
7. Studio thêm tab sau khi surface có audit contract; production rollout vẫn chạy được bằng CLI artifacts nếu Studio chưa deploy.

## Quyết định bị loại

- Không tạo universal prompt/schema cho mọi surface.
- Không để model trả hoặc sửa evidence/semantic keys.
- Không cho generic ledger trực tiếp update domain projection.
- Không giả định `owner_type/owner_id` tạo được database cascade thật.
- Không biến `store: false` thành tuyên bố Zero Data Retention.
- Không cho missing production key âm thầm chạy deterministic khi generation flag đã bật; cấu hình sai phải fail-fast.

## Điều kiện để chuyển sang implementation

- Plan và type sketch thống nhất về `candidate_variant`, consent recheck, encryption/TTL và explicit owner cancellation.
- U5 là slice độc lập có thể ship; U6-U9 không nằm trong một all-or-nothing migration.
- Release evaluation không phụ thuộc Production Studio.
- Characterization tests khóa lifecycle hiện tại trước khi refactor worker/gates.
