// Error wording for "Xoá lịch sử" on the profile page.

export const HISTORY_CLEAR_FAILED = "Chưa xác nhận được việc xoá lịch sử. Kiểm tra kết nối rồi thử lại; hồ sơ vẫn được giữ.";

// New wording about an incomplete erase on this device is privacy copy (R2 kind 3, Codex auto-2 on
// #734): it waits for the owner as `privacy.history-clear-device-failed` (pending in
// apps/api/app/domains/content/copy_registry.json). Until it is approved, the screen shows the
// history-clear error the app already shows, which also says to try again and that the profile is
// kept. Approving it means setting `approved` here in the same change as the registry entry.
export const LOCAL_ERASE_FAILED = {
  id: "privacy.history-clear-device-failed",
  text: "Chưa xoá xong phần lưu trên máy này. Thử xoá lại nhé; hồ sơ vẫn được giữ.",
  approved: false,
} as const;

export const localEraseFailedText = (): string =>
  LOCAL_ERASE_FAILED.approved ? LOCAL_ERASE_FAILED.text : HISTORY_CLEAR_FAILED;
