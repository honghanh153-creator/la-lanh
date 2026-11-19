// Error wording for "Xoá lịch sử" on the profile page.

export const HISTORY_CLEAR_FAILED = "Chưa xác nhận được việc xoá lịch sử. Kiểm tra kết nối rồi thử lại; hồ sơ vẫn được giữ.";

// Wording about an incomplete erase on this device is privacy copy (R2 kind 3, Codex auto-2 on
// #734), registered as `privacy.history-clear-device-failed` in
// apps/api/app/domains/content/copy_registry.json. The owner wrote and approved this sentence in
// chat on 19.11.2026 (approvals item AF, answer AF2). `approved` here and the registry status
// change together; while it is false the screen falls back to the history-clear error above.
export const LOCAL_ERASE_FAILED = {
  id: "privacy.history-clear-device-failed",
  text: "Hình như bạn chưa xoá phần lưu thông tin trên máy này. Thử xoá lại nhé.",
  approved: true,
} as const;

export const localEraseFailedText = (): string =>
  LOCAL_ERASE_FAILED.approved ? LOCAL_ERASE_FAILED.text : HISTORY_CLEAR_FAILED;
