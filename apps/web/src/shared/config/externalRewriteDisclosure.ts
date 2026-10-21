/**
 * OpenAI abuse-monitoring retention, worded to match the provider's full exception set
 * (OpenAI "Your data" — data retention controls for abuse monitoring, checked 2026-10-13).
 * `store:false` does not remove this retention. Shared so the onboarding privacy page and the
 * opt-in sheet in Mình can never drift apart.
 */
export const OPENAI_ABUSE_RETENTION_NOTICE =
  "OpenAI thường giữ dữ liệu kiểm soát lạm dụng tối đa 30 ngày; có thể giữ lâu hơn khi pháp luật yêu cầu hoặc khi cần bảo vệ dịch vụ hay bên thứ ba khỏi tổn hại.";

/**
 * What the AI rewrite receives (M1, 2026-10-20): only Lá's shared catalog wording for the Daily
 * note, never direct chart facts (the situation is still chosen from the chart, coarsely). The server refuses any other surface, so the copy names only the
 * Daily note. Shared so the onboarding privacy page and the opt-in sheet in Mình agree.
 */
export const OPENAI_REWRITE_SCOPE_NOTICE =
  "Lá chỉ gửi câu chữ chung trong kho nội dung của Lá cho note ngày (tình huống, cảnh minh hoạ và việc nhỏ đã chọn cho bạn hôm đó). Không gửi lá số (hành tinh, cung, nhà, góc chiếu), tên, ngày/giờ/nơi sinh, tọa độ hay mã nào nối được với bạn. Các mục khác, như Tarot, chưa dùng AI; khi có, Lá sẽ hỏi lại.";
