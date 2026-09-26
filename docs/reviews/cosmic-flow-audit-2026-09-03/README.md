# Cosmic Glass Signal — flow audit 2026-09-03

## Overall verdict

Sau vòng sửa: **passed cho web/PWA reference US01–US06**. Lỗi visual lớn nhất là Home chỉ dùng palette/background Cosmic Glass nhưng mất paper-note typography; lỗi flow lớn nhất là route mới giữ vị trí scroll của route cũ và preview được bàn giao thẳng ở Home. Cả hai đã được sửa.

## Flow đã kiểm

| Bước | Màn/trạng thái | Health | Evidence |
|---:|---|---|---|
| 1 | Welcome — value proposition | Good | `10-welcome-1.png` |
| 2 | Welcome — guest-first, chưa cần tài khoản | Good | `11-welcome-2.png` |
| 3 | Consent tối thiểu trước DOB | Good sau khi sửa paper contrast | `14-consent-fixed-final.png` |
| 4 | Nhập ngày sinh + age/privacy hint | Good | `15-birth-date.png` |
| 5 | Basic reveal `Vibe · Mềm` + factual provenance | Good | `16-reveal-vibe.png` |
| 6 | Home + paper Note + mood + save/share + unlock | Good | `18-home-top-fixed.png` |
| 7 | Share card 9:16/1:1 | Good | `19-share-card.png` |
| 8 | Contextual deep-profile prompt | Good | `20-unlock-prompt.png` |
| 9 | Exact time + city + separate deep consent | Good | `21-deep-consent.png` |
| 10 | Full natal success / Aura | Good | `22-aura-success.png` |
| 11 | Delete test data và trả preview về người mới | Good | `23-final-welcome.png` |

## Các lỗi đã sửa

1. Home Note: dùng asset giấy xé + ghim thật, Be Vietnam Pro 800 cho headline, coral underline, content center và glass frame như selected reference.
2. Scale: logo, greeting và persona pill được giảm về nhịp của source thay vì typography quá lớn.
3. Consent: body copy trên giấy từng bị dùng màu text của dark theme; hiện dùng ink color riêng cho opaque paper.
4. Navigation: AppShell reset `scrollY=0` sau mỗi pathname change, nên màn mới không còn mở giữa trang.
5. Profile: bỏ text glyph trang trí trong control, dùng Phosphor icons nhất quán.
6. Preview state: dữ liệu QA đã được xóa qua chính privacy flow; browser đang ở `/welcome`.

## Accessibility limits

- DOM semantics, labels, pressed/checked states, keyboard-sized controls và không horizontal overflow đã được kiểm trong browser.
- Screenshot không chứng minh đầy đủ VoiceOver/TalkBack, 200% text, Reduce Transparency hoặc native safe-area; đây vẫn là native release gate.
