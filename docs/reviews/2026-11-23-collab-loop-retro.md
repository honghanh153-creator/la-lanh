# Nhìn lại vòng tự động Claude ⇄ Codex: 23.11.2026

Tác giả: Claude (lượt retro tự động 23.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Báo số việc thật, không chia cho chỉ tiêu nào. Bản 22.11 nằm cùng PR này (#905); không còn ngày nào thiếu bản nhìn lại.

## 1. Số chính thức (bản chụp, chép nguyên)

- Đã gộp vào integration hôm nay: 7 PR (số PR, không phải số việc).
- Việc đạt tiêu chí: 0/3 việc đã chọn đạt đủ tiêu chí; 3 PR chưa gắn việc (#894, #905, #833), không tính.
- Việc kế hoạch 7 tuần: đã chọn 3 (tối thiểu 2 khi có việc sẵn sàng), đạt 0.
- PR đang mở: 48 (chờ owner: #902, #901, #900, #899, #894, #734).
- Sự cố đang mở: #890 [ops-alert] PR chưa có nhãn area (từ 22/11 15:03); #782 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-20 (từ 20/11 10:22); #511 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-14 (từ 14/11 18:29); #470 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-13 (từ 13/11 17:22); #408 [ops-alert] staging-ready failed 2026-11-10 15:29 UTC (từ 10/11 22:29); #370 [ops-alert] collab loop 2026-11-09 (từ 09/11 17:08); #368 [ops-alert] collab loop 2026-11-09 (từ 09/11 14:06); #352 [ops-alert] ssh failed 2026-11-08 15:29 UTC (từ 08/11 22:40); #334 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 20:51); #322 [ops-alert] collab loop 2026-11-08 (từ 08/11 17:09); #321 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 16:18); #318 [ops-alert] collab loop 2026-11-08 (từ 08/11 13:25); #317 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 13:25); #313 [ops-alert] collab loop 2026-11-08 (từ 08/11 10:51); #312 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-08 (từ 08/11 10:21); #311 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-08 (từ 08/11 05:07); #310 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-07 (từ 08/11 00:14); #309 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 23:24); #308 [ops-alert] collab loop 2026-11-07 (từ 07/11 22:53); #305 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 19:21); #304 [ops-alert] collab loop 2026-11-07 (từ 07/11 18:51); #303 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 17:20); #289 [ops-alert] collab loop 2026-11-07 (từ 07/11 13:21); #287 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-07 (từ 07/11 11:20); #285 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 10:29); #277 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-06 (từ 07/11 06:03); #276 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-07 (từ 07/11 06:03); #266 [ops-alert] collab loop 2026-11-06 (từ 06/11 13:54); #261 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-05 (từ 06/11 11:32); #260 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-06 (từ 06/11 11:32); #259 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-06 (từ 06/11 11:32); #244 [ops-alert] collab loop 2026-11-05 (từ 05/11 22:56); #231 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #230 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #205 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 04:46); #204 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 23:44); #196 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 20:33); #193 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 14:42).
- Lượt Codex hôm nay: 26/280; lỗi liên tiếp: 0.
- Lời hứa sửa quy trình: 63/68 đã chạy thật (đã merge, Codex duyệt), 2 đang làm, 1 chờ owner, 2 owner quyết không làm, rủi ro vẫn còn (L17, L24), **1 quá hạn** (L20).

Nguồn: bản chụp 2026-11-23 khung retro, lấy lúc 23:36, integration 5eaa982 · snapshot a83bf589e0b2

Các số ở những mục dưới lấy từ: `logs/tick-2026-11-23.log`, `state/2026-11-23.json`, `collab-turn --report` (23:37), `gh pr list` (PR gộp trong ngày), 23 comment `Review verdict` của Codex trên 16 PR trong ngày, `queue.md` của autopilot, `git log origin/main`.

## 2. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| PR người dùng thấy được (vào integration) | **4 PR** | #833 nút "Hôm nay chỉ muốn đọc"; #879 màn hình cho lúc Căng và lúc Lạc trôi (xong việc #701 cả ba lớp); #876 Lá pixel đủ 4 động tác (đang tắt); #776 chữ tiếng Việt đời thường ở các màn tuần đầu. Máy vẫn ghi 0/3 việc đạt đủ tiêu chí |
| Việc đã lên bản chạy thật | **0** | `main` không có commit mới trong ngày |
| Việc kế hoạch 7 tuần | 0 đạt tiêu chí (số máy) | 3 PR thuộc kế hoạch đã gộp: #833, #876, #879 |
| PR còn lại | 3 trong 7 | Quy trình: #893, #883, #887 |
| Lượt tick báo lỗi | 0 | 82 lượt chạy, khoảng nghỉ dài nhất 21 phút |
| Hàng chờ trống | 0 phút | |
| Từ mở PR tới gộp (7 PR hôm nay) | ngắn nhất 20 giờ (#893), dài nhất 72 giờ (#776) | Không PR nào gộp trong ngày nó được mở |
| Việc đang làm / trần | kế hoạch 0/1, chờ review 0/1; Daily 9/1 và 0/1; quy trình **23/1** và 6/1 | `collab-turn --report`. Hôm qua quy trình 33/1 |
| PR bị giữ vì "cùng file" | **21** trong 48 PR mở | 12 chờ #787, 3 chờ #795, 3 chờ #858, 2 chờ #770, 1 chờ #792. Hôm qua 41 |
| PR chờ Claude sửa | **8** | 7 PR câu Daily xung đột với integration (#847, #848, #849, #851, #859, #861, #862), 1 thiếu cổng trong mô tả (#855) |
| Issue sửa sau đang mở | **190** | Hôm qua 182. Hôm nay mở 8, đóng 0 |

Codex: 23 kết luận tự động trên 16 PR, 11 đồng ý, 12 yêu cầu sửa. Không có P0. Owner cho thêm 200 lượt Codex dự phòng trong ngày (đã ghi trong file trạng thái ngày); hôm nay dùng 26, chưa chạm phần dự phòng.

## 3. Mất thời gian ở đâu

| Chuyện | Bao lâu | Vì sao | Đã sửa chưa |
|---|---|---|---|
| Claude gần hết mức dùng tuần | Cả ngày: 92% đầu ngày, 96% lúc 22:48 | Máy chuyển sang chế độ dự phòng. `queue.md` không có ghi chú lượt autopilot nào trong ngày; 8 PR chờ Claude sửa không ai đụng | Chưa. Đường cho Codex sửa thay (#894) bị yêu cầu sửa 2 lần về bảo mật và đang chờ owner |
| Codex soát lại cùng một lỗi | Khoảng 7 trong 23 lượt | #894, #899, #900, #901, #902 đều chứa cùng file `codex-fallback.mjs`; Codex soát từng PR và báo cùng một lỗi đọc tên file. #858 được soát lại sau khi chỉ đồng bộ nhánh, kết luận giống hệt lần trước | Chưa. Xem S60, S61 |
| Codex hết lượt phía nhà cung cấp | 07:07–08:16, 14 lần bị từ chối | Tài khoản Codex chạm giới hạn dùng; sau 08:28 chạy lại bình thường | Tự hết. Máy đã ghi `limit` và không tính là lỗi |
| Máy chờ CI | 374 lần kiểm trả "chưa xong" (280 vì nhánh chưa có integration mới nhất), 44 lần "đạt" | Mỗi lần gộp là các PR sau phải đồng bộ rồi chờ CI lại (36 lần đồng bộ) | Chưa. S38 |
| Làn quy trình được ưu tiên vì bị bỏ quá 2 lượt | 27 lần trong ngày chỉ riêng làn quy trình | Làn quy trình có 23 PR nhưng phần lớn đang bị giữ, nên tới lượt cũng không có gì để làm | Chưa. S30 |
| 7 PR không có nhãn nhóm (#890) | Từ 22.11 15:03 | Hôm qua hẹn lượt autopilot kế gắn nhãn; hôm nay autopilot không chạy việc này | Đã gắn trong lượt retro này (mục 10) |

## 4. PR cần từ 3 vòng review

| PR | Vòng | Nguyên nhân gốc |
|---|---|---|
| #858 (biên nhận cho tick, soát đêm, người giả) | sửa ×4 trong 2 ngày; còn mở | Lần 3 và lần 4 là cùng một lỗi, chữ gần như y nguyên: lượt người giả hỏng vẫn ghi "xong", và test chỉ so chữ trong mã chứ không chạy đường hỏng. Giữa hai lần nhánh chỉ được đồng bộ, không có bản sửa. Đây là đường lỗi thiếu test (cùng loại với 22.11) cộng một lượt soát thừa. Áp dụng S54: lượt sửa kế phải nộp bảng mọi chỗ ghi biên nhận và test cho từng đường hỏng |
| #833 (nút "Hôm nay chỉ muốn đọc") | sửa, sửa, đồng ý, đồng ý; đã gộp | Hai lần sửa là cùng một lỗi (trạng thái thu gọn mất sau 5 phút rời màn). Lần sửa đầu không có test cho đúng tình huống Codex nêu |
| #894 và #899 (Codex sửa thay khi Claude hết mức) | mỗi PR sửa ×2; còn mở, chờ owner | Lỗi bảo mật trong cách chạy test của nhánh ngay trên máy và cách đọc danh sách file đổi. Lần 2 Codex tìm thêm đường thoát mới (móc Git), tức là thiết kế chưa có mô hình mối nguy đủ trước khi viết |

## 5. Điều tốt, có bằng chứng

- #833 đã gộp lúc 12:04. Hôm qua 25 PR đứng sau nó; hôm nay số PR bị giữ "cùng file" giảm từ 41 xuống 21.
- Việc #701 (mood Căng và Lạc trôi) xong cả ba lớp khi #879 gộp lúc 21:44.
- S29 bước 2 đã chạy: #883 bỏ giữ PR cùng sổ câu chữ khi gộp thử sạch (gộp 18:19). Bản đo gộp thử chạy 15 lần trong ngày.
- Lời hứa sửa quy trình đã chạy thật: 63/68 (hôm qua 59/64).
- Tick chạy cả ngày không có lượt lỗi. Số PR mở giảm từ 53 xuống 48; chỉ 1 PR mới mở trong ngày (#906).
- Làn quy trình giảm từ 33 xuống 23 việc đang làm.

## 6. Điều chưa tốt

- 0 việc lên bản chạy thật; máy ghi 0/3 việc đạt đủ tiêu chí.
- Claude ở 96% mức dùng tuần; 8 PR chờ Claude sửa đứng yên, trong đó 7 PR câu Daily.
- 12 trong 23 kết luận Codex là yêu cầu sửa; khoảng 7 lượt lặp lại lỗi đã biết.
- #858 bị yêu cầu sửa 4 lần và đang giữ 3 PR khác.
- Nợ sửa sau 190, hôm nay không đóng issue nào.
- L20 (mỗi tuần kiểm chính Codex) vẫn quá hạn từ 21.11.
- Không có issue plan riêng cho ngày 23.11; file trạng thái ghi "máy chọn theo cùng luật".

## 7. Học từ GitHub và nguồn gốc (kiểm 23.11.2026)

| Vấn đề | Cách làm học được | Nguồn | Mình áp dụng thế nào |
|---|---|---|---|
| Đọc sai tên file từ `git status` (#894 và 4 PR xếp sau) | Tài liệu Git: `-z` kết thúc mỗi mục bằng NUL và ngầm dùng `--porcelain=v1`; không có `-z` thì tên file có ký tự lạ bị bọc ngoặc kép. Dạng porcelain là dạng ổn định cho script | [git-status](https://git-scm.com/docs/git-status) (đọc 23.11) | Bản sửa #894 dùng `git status --porcelain -z` và không cắt khoảng trắng đầu dòng. Thêm vào danh sách soát của tác giả: mọi chỗ đọc đầu ra Git cho máy phải dùng `-z` |
| Codex soát lại khi nhánh chỉ đồng bộ (#858) | GitHub coi một lượt duyệt là cũ khi diff đổi so với lúc duyệt; bấm "Update branch" cũng tính, và nền gộp có thay đổi mới cũng làm duyệt cũ | [GitHub Docs — About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) (đọc 23.11) | Với kết luận **đồng ý** mình giữ cách của GitHub: head đổi là phải soát lại. Với kết luận **yêu cầu sửa** thì khác: nếu từ lần soát trước chỉ có commit đồng bộ, lỗi chặn vẫn còn nguyên, không cần tốn lượt Codex (S61) |
| Nhiều PR mang chung một file mới (#894, #899–#902) | Chuỗi PR xếp chồng: soát PR gốc trước, PR sau chỉ soát phần riêng. Máy mình đã giữ PR "xếp chồng trên nhánh khác" (ví dụ #860) | Luật giữ có sẵn trong `collab-turn` (không có nguồn ngoài mới hôm nay) | Mở rộng luật giữ: PR chứa trọn commit của một PR mở khác thì giữ tới khi PR gốc được đồng ý, dù đích là integration (S60) |
| PR thiếu nhãn nhóm (#890) | `actions/labeler` (nguồn đã kiểm ở retro 22.11, hôm nay không mở lại) | [actions/labeler](https://github.com/actions/labeler) | Đã gắn nhãn tay cho 7 PR. S59 (máy tự suy nhãn) vẫn trong hàng |

## 8. Chống AI bị "rotten" — cập nhật 23.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6 và các bản 08.11–22.11. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Một lỗi được báo lại nhiều lần mà không ai sửa | Cùng lỗi đọc tên file xuất hiện trong 6 kết luận trên 5 PR; cùng lỗi biên nhận người giả xuất hiện 2 lần liền trên #858 |
| Việc gấp viết xong trước khi nghĩ đủ mối nguy | Đường "Codex sửa thay" cho Codex quyền ghi và chạy test của nhánh trên máy; mỗi vòng soát lại lộ thêm một đường thoát |
| Retro tự dời hạn bài học | Bản 22.11 ghi "hạn mới 24.11" cho L20; Codex chặn vì chỉ owner được đổi hạn bài học. Đã sửa câu trong PR này |

**Điều học thêm:** lượt soát chỉ có giá trị khi có thứ mới để soát. Lỗi chặn chưa có bản sửa thì soát lại chỉ tốn lượt.

## 9. Cần owner

Không có mục mới từ retro. Bản chụp ghi 6 PR mang nhãn chờ owner (#894, #899, #900, #901, #902, #734); 5 PR đầu thuộc việc mức dùng Claude trong tuần chị đã trao đổi. Retro không hỏi lại.

## 10. Giải pháp, xếp theo tác động

Hôm nay **không mở PR quy trình mới**: làn quy trình 23/1, Claude ở 96% mức dùng tuần, và lượt retro bắt đầu sau 23:35 (R9). Việc làm ngay trong lượt này: gắn nhãn nhóm cho 7 PR của #890 và sửa câu về hạn L20 trong bản 22.11. Các việc AUTO còn lại nằm trong hàng đợi autopilot.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| — | Gắn nhãn `area:` cho 7 PR trong #890 | actions/labeler | cả 5 "không" | AUTO | **Đã làm** 23.11: #734, #797, #799, #836 → `area:feature`; #770, #826, #837 → `area:ops` |
| — | Gỡ 7 PR câu Daily đang xung đột (#847, #848, #849, #851, #859, #861, #862) và #855 | R7, số đo mục 2 | cả 5 "không" | AUTO | Hàng đợi, ưu tiên 1 khi Claude có mức dùng trở lại |
| S61 | Không gọi Codex soát lại khi kết luận gần nhất là yêu cầu sửa và từ đó chỉ có commit đồng bộ | GitHub Docs (duyệt cũ) | cả 5 "không" | AUTO | Mới, dự kiến 25.11 |
| S60 | Giữ PR chứa trọn commit của một PR mở khác tới khi PR gốc được đồng ý | luật giữ xếp chồng có sẵn | cả 5 "không" | AUTO | Mới, dự kiến 25.11 |
| S54 | Áp dụng cho #858: bảng mọi chỗ ghi biên nhận, test chạy thật từng đường hỏng | retro 21.11 | cả 5 "không" | AUTO | Lượt sửa #858 kế |
| S29 | Chỉ giữ PR "cùng file" khi gộp thử báo xung đột thật | git-merge-tree | cả 5 "không" | AUTO | Bước 2 xong cho sổ câu chữ (#883). Phần còn lại: mở rộng cho mọi file, dự kiến 25.11 |
| S59 | Lệnh mở PR và tick tự suy nhãn `area:` | actions/labeler | cả 5 "không" | AUTO | Chưa làm, trễ so với 24.11 nếu mai không xong |
| S30 + S49 | Lệnh mở PR từ chối khi làn chạm trần | Dependabot | cả 5 "không" | AUTO | **Trễ lần tám** |
| L20 | Kiểm chính Codex tuần này | lời hứa L20 | cả 5 "không"; dùng 1 lượt Codex | AUTO | Quá hạn từ 21.11; hạn giữ nguyên. Dự kiến làm bù 24.11 |
| S58, S38, S41, S50, S53, S55, S56, S57 | Như retro 22.11 | retro 17.11–22.11 | cả 5 "không" | AUTO | Chưa làm |
| S36, S37, S43, S27+, S51, S45, S33, S34, S42 | Như retro 20.11 | retro 14.11–19.11 | cả 5 "không" | AUTO | Chưa làm. Nợ sửa sau hôm nay: 190 |

## 11. Bước bị chặn

Không có tới lúc viết file này.
