/**
 * Labels for "Hỏi về tháng này" (US-25). Each one mirrors a month.ui entry in
 * apps/api/app/domains/content/copy_registry.json; monthCopy.test.ts keeps them equal. The
 * screens show only when the server says every one of them is approved (/v1/month/status).
 */
export const MONTH_COPY = {
  "month.ui.entry": "Hỏi về tháng này",
  "month.ui.intro": "Chọn một chuyện bạn đang lo. Lá trả lời theo lá số của bạn và các hành tinh trong tháng.",
  "month.ui.topic_heading": "Bạn muốn hỏi chuyện gì?",
  "month.ui.type_label": "Hoặc gõ câu hỏi của bạn",
  "month.ui.type_submit": "Hỏi Lá",
  "month.ui.part_theme": "Tháng này của bạn ở chuyện này",
  "month.ui.part_act": "Có thể làm ngay",
  "month.ui.part_say": "Có thể nói",
  "month.ui.window_button": "Xem lúc nào dễ hơn",
  "month.ui.window_label": "Khoảng dễ hơn",
  "month.ui.window_none": "Tháng này Lá chưa thấy khoảng nào dễ hơn hẳn. Bạn cứ làm lúc nào thấy tiện.",
  "month.ui.save": "Lưu",
  "month.ui.saved": "Đã lưu",
  "month.ui.saved_heading": "Câu đã lưu",
  "month.ui.saved_empty": "Bạn chưa lưu câu nào.",
  "month.ui.delete": "Xóa",
  "month.ui.change_topic": "Chọn mảng khác",
  "month.ui.try_label": "Thử",
  "month.ui.reminder_toggle": "Nhắc mình đầu tuần trên Trang chủ",
  "month.ui.reminder_home": "Đầu tuần rồi. Xem tháng này của bạn trong Khám phá.",
  "month.ui.error": "Lá chưa trả lời được lúc này. Bạn thử lại sau nhé.",
} as const;

export type MonthCopyId = keyof typeof MONTH_COPY;

export const monthCopy = (id: MonthCopyId): string => MONTH_COPY[id];

export const MONTH_TOPICS = [
  { key: "work", label: "Công việc" },
  { key: "money", label: "Tiền" },
  { key: "love", label: "Tình cảm" },
  { key: "family", label: "Gia đình" },
  { key: "study", label: "Học" },
  { key: "mind", label: "Sức khỏe tinh thần" },
] as const;
