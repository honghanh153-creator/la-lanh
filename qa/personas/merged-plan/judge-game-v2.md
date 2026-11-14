# Giám khảo mù: chỉ phần chuyện vui ở Mốc B

Phiên bản `merged-plan-game-v2-2026-11-14`. Chỉ đọc file này, `mocks.md` và `personas.json`.

Mỗi người giả là người hư cấu, có hoàn cảnh, tình huống hôm nay và mood hôm nay ở Mốc B (`mood_today_moment_B`). Đặt mình vào vị trí người đó ở **Mốc B** (cuối tuần 6) và quyết định thật thà: người này, hôm nay, có bấm vào "Chơi một chút" không. Không bắt buộc ai phải chơi.

Mỗi người giả trả lời:

- `played_game` true/false: có vào "Chơi một chút" không.
- `why`: một câu ngắn tiếng Việt thường, vì sao vào hoặc không vào.
- Nếu `played_game` là false: `game_understood`, `game_could_stop`, `game_hurt` đều là `null` (không áp dụng).
- Nếu `played_game` là true:
  - `game_understood` true/false: hiểu cách chơi ngay.
  - `game_could_stop` true/false: thấy dừng chơi được bất cứ lúc nào.
  - `game_hurt` true/false: có chỗ trong chuyện vui chạm vào nỗi đau của mình.
  - `quote`: nếu `game_hurt` true, chép nguyên văn cụm chữ trong `mocks.md` gây ra cảm giác đó; còn lại "".

Đầu ra: một mảng JSON, mỗi người giả một phần tử:

{"persona": "P001", "played_game": true, "why": "…", "game_understood": true, "game_could_stop": true, "game_hurt": false, "quote": ""}
