# Mầm xanh pixel, tuần 2: khung và 4 động tác thử (#714, #715)

Ngày 22.11.2026. Người làm: Claude. Review: Codex (vòng tự động).

## Nguồn

- Kế hoạch 7 tuần (`docs/plans/2026-11-15-ke-hoach-7-tuan-moc-do.md`): tuần 2 chạy nền "Thử 4 động tác Mầm xanh bằng code, chưa bật"; mốc "4 động tác Mầm xanh làm thử (đo bằng máy)": mỗi động tác ≤ 8 KB, đứng yên khi giảm chuyển động, mỗi lần chạy ≤ 5 giây, bấm được bằng bàn phím.
- Ghi chép sáng tạo 15.11 (`docs/reviews/2026-11-15-sang-tao-viral.md`): Lá pixel là Mầm xanh, vẽ bằng code, không thuê họa sĩ; hình 48×48 điểm, mỗi động tác 12–24 hình; 6 nhóm động tác; luật nhây (Lá chỉ nhây bằng việc của chính Lá).
- Issue #714 (khung + 2 động tác) và #715 (2 động tác còn lại + máy kiểm trong CI).

## Chưa có user story

Lá pixel chưa có US riêng. Tuần 5 (Mầm xanh thay "Vibe") cần một US trước khi bật cho người dùng. Tuần 2 chỉ là bản thử sau cờ tắt nên dùng tiêu chí đạt của hai issue.

## Tiêu chí đạt

| Mã | Tiêu chí | Ở đâu | Kiểm bằng |
|---|---|---|---|
| #714 AC1 | Khung vẽ Lá pixel bằng code, theo Mầm xanh đang có, không file ảnh ngoài | `shared/ui/companion/pixel/pixelSprite.ts` | test: chỉ có `<path>` vẽ bằng code, không `<image>`, đúng bảng màu Mầm xanh |
| #714 AC2 | 2 động tác đầu; mỗi động tác ≤ 8 KB; mỗi lần chạy ≤ 5 giây | `pixel/moves/chao.ts`, `pixel/moves/ngoiCung.ts` | test đo byte file và số hình / tốc độ |
| #714 AC3 | Giảm chuyển động thì đứng yên; bấm được bằng bàn phím; có tên cho trình đọc màn hình | `pixel/PixelLa.tsx` | test component |
| #714 AC4 | Sau cờ tắt, không màn người dùng nào hiện | `pixel/flag.ts` | test: cờ tắt và chỉ trang thử nội bộ dùng Lá pixel |
| #714 AC5 | Ghi giờ làm thực tế | mô tả PR | — |
| #715 AC1 | Thêm 2 động tác, đủ 4 | `pixel/moves/kinhRoi.ts`, `pixel/moves/uongTra.ts` | test đếm |
| #715 AC2 | Một test trong CI kiểm cả 4 (≤ 8 KB, ≤ 5 giây, đứng yên khi giảm chuyển động, bấm được bằng bàn phím), đỏ khi một động tác vượt | `pixel/moves.budget.test.tsx` | chạy trong `pnpm check` (web:test); có ca đối chứng âm |
| #715 AC3 | Vẫn sau cờ tắt | như #714 AC4 | như #714 AC4 |

## Bốn động tác

Chọn mỗi động tác ở một nhóm khác nhau, không dùng nhóm "Nhây" (nhóm này chỉ dùng khi người dùng tự chạm Lá để chơi):

1. **Chào** (Vui): nhún lên, vẫy tay, lá trên đầu lắc.
2. **Ngồi cùng** (Buồn và ngồi cùng): thở chậm, mắt dịu, một trái tim nhỏ hiện rồi tan.
3. **Kính rơi** (Lá tự hỏng việc): đeo kính đen làm dáng, kính trượt xuống rơi, Lá ngượng.
4. **Uống trà** (Việc nhỏ): nâng cốc, hơi bốc lên, nhấp một ngụm, lè lưỡi vì nóng.

## Cách làm

- Hình 48×48 điểm vẽ bằng công thức (thân bầu dục, mầm và hai lá, mắt, má, tay), viền tự sinh, gộp thành `<path>` theo màu. Không file ảnh.
- Mỗi động tác là một file dữ liệu nhỏ: tốc độ và danh sách dáng (độ nhún, độ bẹp, mắt, miệng, tay, lá, đạo cụ). Chạy một lần rồi về dáng nghỉ, không lặp.
- Giảm chuyển động (cài đặt máy, công tắc chuyển động trong app, hoặc `still`): chỉ vẽ dáng nghỉ, bấm không chạy.
- Lá là một nút; Enter và Space chạy động tác.
- Chỉ trang thử `/companion-lab` dùng Lá pixel. Cờ `PIXEL_LA_ON_USER_SCREENS` tắt.

## PR

1. `agent/claude/mam-xanh-pixel-1` → #714.
2. `agent/claude/mam-xanh-pixel-2` (dựng trên PR 1) → #715.

## Dữ liệu và an toàn

Không thu, không lưu, không gửi dữ liệu nào. Trang thử không đọc dữ liệu người dùng. Không có câu chữ mới cho người dùng (nhãn chỉ ở trang thử nội bộ).
