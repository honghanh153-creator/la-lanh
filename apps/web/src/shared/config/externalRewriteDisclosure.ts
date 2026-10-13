/**
 * OpenAI abuse-monitoring retention, worded to match the provider's full exception set
 * (OpenAI "Your data" — data retention controls for abuse monitoring, checked 2026-10-13).
 * `store:false` does not remove this retention. Shared so the onboarding privacy page and the
 * opt-in sheet in Mình can never drift apart.
 */
export const OPENAI_ABUSE_RETENTION_NOTICE =
  "OpenAI thường giữ dữ liệu kiểm soát lạm dụng tối đa 30 ngày; có thể giữ lâu hơn khi pháp luật yêu cầu hoặc khi cần bảo vệ dịch vụ hay bên thứ ba khỏi tổn hại.";
