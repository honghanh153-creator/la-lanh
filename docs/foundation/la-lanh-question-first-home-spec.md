# Lá Lành — Question-first Home

Status: implemented slice for beta review  
Updated: 2026-09-28

## Product promise

Home giúp người dùng bắt đầu từ câu hỏi thật thay vì phải hiểu tên tính năng. Sản phẩm có ba lối chính:

| Người dùng muốn hiểu | Nhãn trên Home | Capability đích | Kết quả được hứa |
|---|---|---|---|
| Bản thân | Mình | `/natal` | Hiểu vì sao mình hay lặp lại một kiểu chuyện |
| Một người hoặc một kết nối | Một người | `/radar` | Hiểu vì sao có lúc rất hợp, có lúc lại cấn |
| Bối cảnh đang tác động | Chuyện đang xảy ra | `/insights/current-sky?tradition=western` | Nhìn bối cảnh hôm nay đang đẩy điều gì lên |

`Lá Hỏi` đứng cạnh ba lối này như một cách tự soi theo câu hỏi. Tarot không chứng minh hoặc thay đổi chart, không đọc ý định người khác và không quyết định thay người dùng.

## Home hierarchy

1. Brand, profile và lời chào ngắn.
2. Câu hỏi `Bạn đang muốn hiểu điều gì?`.
3. Tarot spotlight: `Có một chuyện cứ chạy trong đầu?` → `Hỏi Lá ngay`.
4. Ba lối `Mình`, `Một người`, `Chuyện đang xảy ra`.
5. `Tín hiệu hôm nay`: Daily Note hiện có, context, resonance, gift, mood, save/share và chart unlock.
6. Bản đọc về mình đã mở, chỉ hiện khi hồ sơ sinh đã đủ lớp.
7. Bottom navigation hiện tại.

Tarot đứng trước ba lối trong cùng block để CTA không bị bottom navigation che trên viewport mobile đầu tiên. Home không có ô nhập tự do và không lưu lựa chọn lối đi. Mỗi lựa chọn là một link rõ đích đến, nên Back hoạt động theo lịch sử trình duyệt và analytics không cần nhận nội dung riêng tư.

## Copy contract

- Nhãn chính dùng ngôn ngữ đời thường trước thuật ngữ astrology.
- Mỗi CTA nói rõ tap sẽ mở gì; tránh `Khám phá`, `Xem thêm` hoặc `Thử ngay` khi đứng một mình.
- Không hứa biết mọi câu trả lời, dự đoán chắc chắn, đọc suy nghĩ hoặc đưa ra compatibility verdict.
- Tarot luôn có một dòng giữ quyền tự quyết: `Một góc tự soi, không quyết định thay bạn.`
- Daily Note được gọi là `tín hiệu hôm nay`, không phải lời phán hoặc câu trả lời toàn diện.

## Lá Chứng retirement

Lá Chứng không còn là acquisition hoặc social-proof surface của sản phẩm.

- Home và navigation không có entry Lá Chứng.
- Route tạo, preview và public link cũ render trang tĩnh `Lá Chứng đã khép lại`; trang không đọc token, không gọi API và không hiển thị dữ liệu lời mời.
- Backend trả `410 Gone` cho create, resend, replacement, public preview và submit để client cũ cũng không thể phát sinh hoạt động mới.
- Route quản lý dữ liệu cũ vẫn hoạt động: chủ lời mời có thể xem danh sách, thu hồi lời mời đang chờ, ẩn hoặc xóa kết quả; người từng phản hồi có thể rút phản hồi bằng receipt trên thiết bị.
- Database records và delete/revoke/withdraw contracts không bị xóa. Data migration và retention cleanup phải có inventory và kế hoạch riêng để không làm mất quyền của chủ thể dữ liệu.

## Data privacy

| Surface | Dữ liệu mới được thu | Lưu ở đâu | Ghi chú |
|---|---|---|---|
| Question router | Không | Không lưu | Chỉ điều hướng tới route có sẵn |
| Tarot spotlight | Không | Không lưu | Notice và collection xảy ra trong `/tarot` |
| Daily Note | Không thay đổi | Theo contract hiện có | Không mở rộng purpose trong slice này |
| Lá Chứng retired page | Không | Không lưu | Không fetch capability token; chỉ liên kết sang quyền quản lý cũ |

Birth data, relationship data và Tarot question vẫn là dữ liệu cá nhân/nhạy cảm theo policy nội bộ. Chúng không được đưa vào URL, analytics, log hoặc copy của Home.

## Security and abuse controls

- Old invite token không được validate hoặc reflect trên retired page.
- Không redirect old public invite sang route có side effect.
- Không thêm remote asset, third-party SDK hoặc new analytics event trong slice này.
- Existing Tarot encryption, guest ownership, retention và delete behavior là authority; Home không được bypass chúng.

## Accessibility and responsive behavior

- Link/card có accessible name mô tả kết quả.
- Tap target tối thiểu 44×44 CSS pixels.
- Normal text đạt contrast tối thiểu 4.5:1; large text tối thiểu 3:1.
- Focus ring nhìn thấy trên theme dark và light.
- 320px không scroll ngang; 200% text zoom không che CTA.
- DOM order khớp visual order: question router → Tarot → Daily.

## Acceptance checklist

- [x] Một người mới có thể trả lời `app này giúp gì?` trong first viewport.
- [x] Ba lối và Tarot mở route thật, không có shell rỗng.
- [x] Daily Note và các hành động cũ vẫn hoạt động.
- [x] Không còn text/link `Lá Chứng` trong Home hoặc navigation.
- [x] Route public/create Lá Chứng cũ không fetch dữ liệu; route quản lý chỉ fetch khi chủ thể mở rõ ràng.
- [ ] Light-theme visual pass riêng chưa chạy; dark-theme, keyboard route semantics và viewport mobile/desktop đã qua QA.

Verification 2026-09-28: 127 web unit tests, 5 focused API tests, production build and 8 Playwright mobile/desktop scenarios passed. The only build note is the pre-existing Vite chunk-size warning.

## References

- `docs/foundation/la-lanh-tarot-engine-spec.md`
- `docs/foundation/la-lanh-reading-knowledge-spec.md`
- `plans/2026-09-28-2042-feat-question-first-home-plan.md`
- [Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=)
- [OWASP Privacy by Design](https://owasp.org/www-chapter-los-angeles/assets/prez/OWASPLA_prez_2024_01.pdf)
- [WCAG 2.2](https://www.w3.org/TR/WCAG/)
