# Lá Lành Autopilot: thiết kế đầy đủ (Claude, bản để phản biện chéo)

Nguyên tắc: **mọi mã trong catalog đều có chỗ**. Tối ưu nghĩa là:
- ghép các ý trùng nhau vào cùng một thành phần, để chúng tăng sức cho nhau;
- tái dùng cái đã có;
- xếp giai đoạn theo phụ thuộc kỹ thuật thật.

Không bỏ ý nào. Ý nào cần đổi cách làm cho hợp với một owner, hai agent và chưa có người dùng thì ghi rõ đã đổi thế nào.

---

## 1. Kiến trúc: 12 thành phần trong 4 tầng

### Tầng 0: Nền tin cậy

Phải có tầng này trước thì mới cho máy tự chủ (L17, L10, C4, D25b).

- **T0.1 Luật một nguồn: `ops/policy.json`.** Gom mọi hằng số và quyết định đang rải rác (G5):
  - giờ chạy, cap Codex, thứ tự nhóm (R10), WIP;
  - ma trận lòng tin theo loại thay đổi (L3);
  - danh sách việc cứng chỉ owner được làm (C4: thêm câu chữ UI, mục đích và thời hạn lưu, giờ và nơi sinh);
  - mục tiêu và đối trọng của chỉ số;
  - ngân sách: lượt Codex, phút owner, ngân sách sự cố.

  Memory, SKILL và AGENTS.md chỉ trỏ tới file này. Có loader kèm phiên bản và hash, kiểm hash trước khi ghi (D12b).
- **T0.2 Khoá theo diff ngay tại cửa merge** (C4, Codex r1). Hàm `mergeGate()` tự phân loại diff, không dựa vào nhãn:
  - PR chạm policy, code cưỡng chế, bộ chấm/eval, workflow CI hay file test bị khoá → luôn chờ owner, và approval của owner phải khớp SHA;
  - PR gồm nhiều loại thay đổi thì chịu mức nghiêm nhất;
  - mỗi lệnh merge hoặc deploy kiểm quyền tại chỗ; đổi mức không tự cấp quyền.

  Agent không có credential để merge vào main hay deploy (D25b). Credential nằm ở job phát hành do owner bấm.
- **T0.3 Hàng rào kiến trúc cứng** (L10, L11, D1b, D20d, D14c):
  - mỗi tính năng một thư mục; kiểm import boundary trong CI;
  - kiểu bất biến: `ConsentedBirthData`, `ShareToken` không log được;
  - lint chặn dữ liệu sinh đi vào logger hoặc analytics; cấm comment trích lời review;
  - pnpm `minimumReleaseAge`; kiểm các hook global;
  - cấm `any`/`unknown` trừ ở biên nhận dữ liệu.

  Làm từng bước nhỏ, mỗi PR một luật (L16).
- **T0.4 Sandbox cho phiên Claude** (D25b, Seatbelt). Đang thử ở lần 3. Không tin thì không cho chạy đêm không người trông.

### Tầng 1: Thấy và kiểm

Agent phải có tay và mắt (L1, L2, D1c, D9b, D18, D22a, G6).

- **T1.1 Skill `verify-la-lanh` + CLI** (L1). Phần cố định viết thành CLI: Playwright/CDP, chụp 390px (#452 đã merge), ghi trace, console, network, a11y (axe), Lighthouse (G8). Agent chỉ phán đoán phần còn lại.
- **T1.2 `feature-map.json`** (L2, D15a). Ghi mỗi tính năng:
  - đường người dùng đi tới, route, testid;
  - component trong design system dùng ở đâu (D15a);
  - dữ liệu giả để chạy.

  Có skill tạo và skill bảo trì bản đồ. CI kiểm mọi route đều có trong bản đồ.
- **T1.3 Hành trình UAT bị khoá** (D3b, D17b, D18c, C8). Repo con `uat/`, agent build không được sửa (khoá diff T0.2). Hai lớp:
  - lớp mock chạy mỗi PR;
  - lớp **API thật trên staging với dữ liệu giả** chạy mỗi đêm và trước phát hành.

  Hành trình: khách → ngày sinh → Daily → mood → lưu → chia sẻ → mời Hợp gu → thu hồi → xoá dữ liệu. Codex viết test từ use case (D17a, D17b), không xem code.
- **T1.4 Verifier theo AC** (D18a, D18b, L6). Mỗi AC của việc đang làm là một lượt verifier chạy trên bản xem thử theo SHA. Verifier đọc spec và code gốc trước, rồi mới đọc diff, và trả pass/fail kèm ảnh.
  - Tối ưu: chạy **tuần tự** trong một lượt Codex. Số verifier mỗi PR co giãn theo rủi ro: UI/logic 1–3, câu chữ 0. Không phải 10 agent song song.
  - Fuzz như người dùng (L6) cho PR UI có rủi ro cao.
- **T1.5 Bằng chứng gắn vào PR** (D1c, D9b, D22a). Ảnh trước/sau ở 390px là bắt buộc. Video ngắn ghi bằng Playwright cho hành trình có tương tác. Link bản xem thử theo SHA (D9b) sau khi có staging cho mỗi PR.
- **T1.6 Bot tái hiện lỗi** (L14, D3c, D8b). Mỗi ops-alert, finding hay báo lỗi được chạy lại trên staging. Kết luận một trong ba: tái hiện được / đã sửa trên integration / cần thêm thông tin. Chỉ khi tái hiện được mới mở việc sửa, kèm test tái hiện (D20c).
- **T1.7 Eval nội dung** (D21a, D27b, D20a, C9, D29b):
  - bộ mẫu vàng JSONL gồm lá số giả × ngày, luật phải nói/cấm nói; **20% giữ kín** ngoài repo do Codex giữ (D21a);
  - chạy giống nhau ở local, CI và staging (D27b);
  - lá số: mở rộng test đối chiếu swetest có sẵn (C9, D20a), thêm ca nửa đêm, DST, giờ lịch sử Việt Nam;
  - so có và không có skill (D29b, D16c).
- **T1.8 Test sạch** (D20b, D7a, D10c, D7d):
  - không có test chập chờn; mỗi đêm chạy lặp lại để săn;
  - Codex dò test vô nghĩa (D7a);
  - giữ cả bộ test ≤ 15 phút trên CI (D10c);
  - xếp thứ tự test theo độ thay đổi × độ phủ (D7d).

### Tầng 2: Điều khiển

- **T2.1 Cảm biến `metrics.json`** (#451 + C5). Mỗi chỉ số có nguồn ngoài tay bên bị đo, lịch sử, cỡ mẫu tối thiểu và đối trọng. Danh sách đầy đủ ở mục 4.
- **T2.2 Bộ quyết định `decide()`**: hàm thuần, có test từng nhánh. Xem mục 2.
- **T2.3 Tầng mục tiêu `goals.json` + điều phối**. Xem mục 3.
- **T2.4 Bộ phản biện `critic()`**. Xem mục 6.
- **T2.5 Vòng ngoài** (L15, D9d, D8a, D5d, D2c). Các routine theo dõi tín hiệu và **ghi vào sổ phát hiện**, không sửa ngay (L5):
  - ops-watch, CodeQL/Dependabot, sổ khoảng trống #177;
  - phản hồi 1 chạm (D9e) và lỗi runtime sau khi có tester (D5b);
  - agent độ tin cậy hằng tuần xếp hạng theo tác động × rủi ro (D8a);
  - agent nghiên cứu mẫu hình bên ngoài hằng tuần (D5d), chỉ nhận mẫu có từ hai nguồn trở lên;
  - Repo Assist có menu việc sửa được (D2c).

  Dùng sự kiện GitHub thay cho thăm dò định kỳ khi có thể (D9d).
- **T2.6 Sổ phát hiện + gom gốc** (L5, L4, D29a, D26b). Mọi phát hiện vào `findings.jsonl` có mã loại. Điều phối gom các mục cùng gốc (L4). Mỗi lần agent báo "đã xong" phải kèm check chứng minh (D26b, `observation`).

### Tầng 3: Học

- **T3.1 Lỗi lặp → luật cứng** (D1a, L10, D2d, D20c, Q1). Một loại finding lặp ≥ 2 lần thì thành lint hoặc test, kèm thông báo lỗi tiếng Việt chỉ cách sửa. Một bài học chỉ vào AGENTS.md khi đã được xác nhận 2 lần (D30b).
- **T3.2 "Nằm mơ"** (D1e, D12a, L9, D13c, D26a). Batch đọc lưu trữ phiên (D26a, đã lọc secret và dữ liệu owner), review, CI fail và sự cố. Kết quả là đề xuất sửa luật hoặc skill, có đếm số lần và ví dụ. Owner nhận hoặc bỏ.
  - Tối ưu: chạy **mỗi đêm** nhưng chỉ đề xuất khi có mẫu đủ (≥ 3 lần lặp); thường thì im lặng. Đề xuất được gom vào phiên của owner.
- **T3.3 Đăng ký skill/prompt có phiên bản + eval** (D5c, D13b, D14a, D14b, D27c, L12, D29c, D23):
  - mỗi skill có bộ eval (thư mục tên trung tính, giám khảo khác model, nhiều model);
  - chạy lại mỗi khi skill đổi hoặc model đổi;
  - CI chấm skill; phiên bản 0.x/1.0 làm tín hiệu tin cậy;
  - kiểm 5 kiểu hỏng (chồng lấn, trôi, không kích hoạt, cũ, quá tải); bỏ skill không còn tác dụng (D29c);
  - bản đồ model theo việc (D23);
  - thử model rẻ hơn trên PR cũ (D13b).
- **T3.4 Gu của owner thành dữ liệu** (D30a, D16a, D4c, D7b). Mọi lần owner sửa câu được ghi thành cặp trước/sau.
  - Owner được sửa thẳng trong sheet hoặc màn duyệt, agent mở PR (D4c).
  - Áp mẫu sửa cho cả kho bằng codemod (D7b).
  - Bộ chấm được hiệu chỉnh theo owner; độ khớp đo trên **bộ mẫu riêng chưa dùng để dạy** (D16a, D29b). Bộ chấm chỉ được dùng để tự duyệt khi độ khớp ≥ ngưỡng trong policy.
- **T3.5 Wiki sản phẩm + nguyên tắc** (D6a, D15c, D9c, D10a). `docs/brain/` được cập nhật mỗi đêm từ việc đã merge. Có file nguyên tắc (north star, câu chữ dễ hiểu, cung = nghĩa). ADR một trang có sơ đồ cho mỗi quyết định hệ thống; agent kiểm PR theo ADR (D10a). Blueprint = skill + công thức + ADR (D9c).
- **T3.6 Kiểm định nghi thức** (D11d). Mỗi tháng, giữ / bỏ / thử với chính vòng auto.

---

## 2. Luồng mỗi tick (24/7): `decide()`

Trạng thái **đóng băng** là trạng thái bền, giữ qua các tick (Codex r1). Khi đóng băng, chỉ nhánh 1–2 chạy. Không có đường rơi xuống việc mới.

```
0. Tiền kiểm: policy hợp lệ (hash), đủ quyền cho hành động, khoá tick; lỗi → dừng an toàn + báo
1. SỰ CỐ (P0/P1, ops-alert, guardrail chạm)
   → bật ĐÓNG BĂNG; làn sự cố: chỉ PR sửa đúng sự cố, ngân sách sự cố riêng
   → hết ngân sách sự cố hoặc 3 lần không phục hồi → DỪNG AN TOÀN + báo owner ngay (đẩy điện thoại)
2. ỐNG HỎNG (CI integration đỏ, UAT trượt)
   → lỗi code: bot tái hiện → sửa có test; lỗi hạ tầng: thử lại ≤3 lần giãn cách → ops-alert → ĐÓNG BĂNG
3. KẸT (PR không tiến N tick hoặc > 24h) → cách ly (nhãn), 4 dòng vào thẻ, rời WIP
4. DỞ DANG (WIP 1 làm + 1 review) → prTurn: check(CI) → verifier theo AC → Codex review (≤2 vòng, quá thì
   gửi owner bản bất đồng 4 dòng — D3a) → merge qua mergeGate (khoá diff + lòng tin theo loại)
5. NGÂN SÁCH (cap Codex / quota) → đặt giờ thử lại; chỉ việc không cần Codex; giữ ngân sách sự cố
6. PHÁT HÀNH (integration chưa vào main > policy.release.maxLag, hoặc mục tiêu cần người dùng)
   → "đóng băng phát hành" kiểu OSS vacation (D22c): không merge tính năng mới, chỉ sửa; dựng GÓI PHÁT HÀNH
     (bản chạy staging, UAT xanh, ảnh, nội dung mẫu, lỗi còn lại, cách quay lui đã diễn tập) → thẻ owner
7. MỤC TIÊU → điều phối của mục tiêu ưu tiên cao nhất đưa giả thuyết kế tiếp (mục 3)
8. CHỈ SỐ ĐỎ ngoài mục tiêu → việc theo bảng chỉ số → hành động (mục 4)
9. BACKLOG có AC + "người dùng thấy gì" (E2, D22b issue-first) → điểm = tác động × độ chắc ÷ cỡ
10. RẢNH → eval, săn test chập chờn, kiểm mẫu, nằm mơ; ghi "rảnh có chủ đích"
```

**Hồ sơ đêm (G1):** cùng `decide()`, gom các giờ chặn riêng của plan, check và review về policy (C3).
- Nhánh 4 chỉ merge những loại thay đổi có quyền tự merge ban đêm.
- Không tạo thẻ mới. Chỉ gom lại cho bản sáng.
- Codex hết cap: đặt giờ thử lại; lô duyệt câu dùng chung bộ đếm (C3).

**Chạy được ban đêm thật:**
- (a) Mac không ngủ khi cắm sạc;
- (b) phần nặng chạy trên CI (#443);
- (c) Claude chạy theo lịch launchd, không phụ thuộc app đang mở;
- (d) có phép thử "một đêm": crash giữa chừng, hết quota, mất mạng → vòng phải dừng an toàn và tự chạy lại được (Codex r1).

**Chạy bóng** (C7): `decide()` chạy song song với vòng cũ 3 ngày, ghi lại "sẽ làm gì". Chỉ một bộ thực thi được thật sự thực thi.
- Tiêu chí đạt: ≥ 90% tick khớp; mọi chỗ lệch có giải thích; vượt qua phép thử crash/quota.
- Đạt thì chuyển quyền; có công tắc quay về vòng cũ.

---

## 3. Tầng mục tiêu (R3, L13, L4, D3f, D28a, E5)

1. Owner nói một câu → `goals.json` lưu nguyên văn.
2. **Dịch**: chỉ số chính, các chỉ số tạo ra nó (cây chỉ số), điểm xuất phát, mục tiêu, hạn ("khẩu phần thời gian" E5) và đối trọng.
   - Chưa đo được → việc đầu tiên là lắp đo (G8), có cổng riêng tư; dữ liệu được ẩn danh trước khi cho model đọc (D6c).
3. **critic(goal)** (mục 6). Owner trả lời 1 thẻ.
4. **Giả thuyết**: "làm X thì Y tăng Z vì W", có điểm ưu tiên, điều kiện bỏ và bằng chứng. Nguồn giả thuyết:
   - dữ liệu, chuẩn ngành (E6), agent nghiên cứu (D5d);
   - TRIZ "làm sao cho tệ nhất" (D28b);
   - ý sản phẩm đã học: D24a/b/c, D25c, D12c, D11a, D22d, D9e, E6;
   - thứ tự mặc định là kéo yếu tố yếu nhất lên trước (D5e).
5. **Leo đồi** (L13): mỗi giả thuyết là một chuỗi việc nhỏ.
   - làm → verify (T1) → **giám khảo khác model** chấm trên **bộ giữ kín** (T1.7) → giữ hoặc quay lui.
   - Baseline, đối trọng và bộ chấm bị khoá khỏi nhánh đang tối ưu (Codex r1, T0.2).
   - Tính năng mới nằm sau cờ (D4d, D11b).
6. **Điều phối**: một mục tiêu là một điều phối, gồm file trạng thái và lượt Claude riêng (L4). Nó gom việc cùng gốc.
   - Nhiều mục tiêu thì chạy tuần tự theo ưu tiên, WIP 1+1 cho toàn hệ. Lý do: một owner, ngân sách Codex có hạn.
   - **Owner nâng WIP trong policy thì chạy song song được.**
7. **Thẻ mục tiêu** theo phiên của owner: đã thử gì, điểm, bỏ gì, cược tiếp. Hai chu kỳ không nhích thì dừng và hỏi.
   - Đếm số thí nghiệm mỗi tuần (D28a) để thấy độ mạnh dạn.

**Chỉ số thay thế và chỉ số thật:** Lighthouse, a11y và điểm AI chỉ là chỉ số thay thế (Codex r1).
- Mỗi mục tiêu phải ghi rõ chỉ số thật đi kèm: người dùng hoặc tester làm xong hành trình, bấm "hợp", quay lại hôm sau.
- Chưa có người dùng thì gắn nhãn "chưa xác nhận bằng người dùng". Để có người dùng thì phải phát hành (C8, D10b).

---

## 4. Chỉ số → hành động (R4, C5, D4a, D5a, D16b, E3, E4, D10b)

Mỗi chỉ số có: nguồn ngoài tay bên bị đo, cỡ mẫu tối thiểu, đối trọng, hành động khi dưới mục tiêu, hành động khi chạm mức chặn.

| Chỉ số | Mục tiêu | Đối trọng | Dưới → | Chạm mức chặn → |
|---|---|---|---|---|
| Daily phục vụ được, **đo qua runtime** | 156/156 trước tester | owner bác ở mẫu | lô duyệt + sinh phần thiếu | dừng tự duyệt, lô cho owner |
| UAT đạt (mock mỗi PR, thật mỗi đêm) | 100% | test khoá | nhánh 2 | đóng băng |
| Lỗi lọt theo nguyên nhân gốc / theo bản phát hành | giảm | tester/owner phát hiện | test lẽ ra bắt | hạ lòng tin loại đó |
| Merge không phải sửa thêm (D4a) | ≥ 80% | lỗi lọt | spec + AC trước khi code ở vùng đó | — |
| Số vòng tới đúng (D5a) | ≤ 1,5 | kiểm mẫu review | luật cứng từ finding | bản bất đồng cho owner |
| Lead time p95 + tuổi PR mở (E3) | ≤ 24h | lỗi lọt | chia nhỏ | về WIP cũ |
| Thời gian tới người dùng (E4) | ≤ 7 ngày | lỗi theo bản | gói phát hành | — |
| Tổng tải owner (phút + thẻ + mẫu tồn) | ≤ ngân sách policy | tỷ lệ bác | gộp thẻ | ngừng sinh thẻ cùng loại |
| Skill: kích hoạt / quỹ đạo / kết quả (D16b) | theo eval | giám khảo khác model | sửa skill | bỏ skill (D29c) |
| Tester: đọc xong, D1, "hợp" (D9e, D10b) | đặt sau tuần 1 | cỡ mẫu tối thiểu | viết lại tình huống | — |
| Thí nghiệm/tuần (D28a) | ≥ 2 | tỷ lệ quay lui | thêm giả thuyết | — |

Luật chung: chỉ số tăng mà đối trọng xấu đi thì tính là không tăng. Báo cáo luôn tách 3 trạng thái: PR mở / đã merge / đang chạy (C10).

---

## 5. Lòng tin theo loại thay đổi + chế độ toàn tự động (L3, L6, L7, L8, D27a, D4b, D7c, R2, C1)

Mỗi PR được tự gắn nhãn **loại + rủi ro + cỡ** (D4b, D7c), từ diff và đường dẫn.
- Lên mức chỉ khi đủ **cỡ mẫu tối thiểu** (vd ≥ 20 PR loại đó) và chỉ số sạch (Codex r1).
- Hạ mức tự động khi có lỗi lọt hoặc owner bác vượt ngưỡng.

| Loại | Bắt đầu | Mức cao nhất cho phép |
|---|---|---|
| docs, test | tự merge 24/7 | — |
| câu chữ thường | Codex duyệt lô; mức thay đổi nhỏ thì tự phát hành (D27a) | tự phát hành khi bộ chấm khớp owner |
| UI | tự merge khi có bằng chứng T1 | tự merge đêm + xem lại buổi sáng (L6) |
| logic API | merge ban ngày | đêm, khi có test tái hiện |
| dữ liệu, riêng tư, xoá, auth, migration, câu nhạy cảm, policy, bộ chấm | owner (cửa một chiều, L8) | không đổi |
| phát hành | owner bấm gói | L4: tự phát hành sau cờ khi đủ điều kiện C1 |

**Toàn tự động (R2 = L4):** owner bật trong policy. Chỉ có hiệu lực khi đủ các điều kiện sau:
- quay lui đã diễn tập trên staging, chứng minh image cũ không hỏng dữ liệu mới, hoặc có migration hai chiều;
- quay lui giữ đúng việc xoá và thu hồi;
- có đường xử lý khi quay lui thất bại;
- canary có thời gian quan sát, cỡ mẫu tối thiểu, đối chứng, SLO và error budget (D11b); thiếu tín hiệu thì giữ, không lên 100%;
- kiểm mẫu 5% (L7). Mẫu chưa xem tính là chưa đạt. Owner bác > 10% thì tự hạ.

Trước khi đủ điều kiện, bật L4 chỉ có tác dụng như L3, và thẻ ghi rõ còn thiếu gì.

---

## 6. Bộ phản biện (R5, C6, D3a, D19b, D6b, E1, E2, D11c, D15b, D28c, D19a, D17a)

**Đầu vào:**
- plan 08:50 của máy;
- mục tiêu hoặc plan của owner, cả ghi âm và ghi chú (D15b, D28c: chuyển thành PRD rồi thành việc);
- spec mới.

**Kiểm tuân thủ:**
- ưu tiên R10;
- kéo được chỉ số nào;
- sức chứa: WIP, Codex, phút owner;
- luật cứng;
- xung đột với quyết định cũ (ghi ngày);
- có AC (EARS D19a, use case D17a), "người dùng thấy gì" và cách kiểm.

**Phản biện mục tiêu:**
- ưu tiên hay chỉ số có sai không;
- chi phí cơ hội;
- phương án không làm gì;
- bằng chứng nào cho thấy sai;
- điều kiện tiên quyết.

**Cách làm:**
- Phản biện chạy trong **phiên mới**, bằng Codex (khác model, D19b).
- Hỏi ngược "hỏi tôi thật nhiều" trước khi chốt spec (D19a).
- Hai bên lệch nhau thì tối đa 2 vòng, rồi gửi owner bản bất đồng 4 dòng (D3a).

**Đầu ra:** Nhận / Nhận nếu sửa / Phản biện. Có thể đề xuất đảo thứ tự. Owner quyết; ngoại lệ được ghi kèm hạn hết hiệu lực.

Việc mơ hồ phải có PRD ngắn hoặc thẻ 2 phương án (D6b). Owner duyệt spec và bằng chứng, không duyệt diff (D11c, E1).

---

## 7. Bề mặt owner (R6, G7)

Định cỡ theo khoảng 1 giờ mỗi 2–3 ngày (Codex r1).

- **Kênh:**
  - bình luận mới trên GitHub (owner bật thông báo cho cập nhật của chính mình, G7);
  - đẩy lên điện thoại cho sự cố hoặc dừng an toàn.
- **Mỗi sáng:** một tóm tắt tự động, chỉ để lướt. Gồm việc đã merge qua đêm, chỉ số tăng/giảm, đóng băng nếu có.
- **Phiên owner:** gói duyệt gom từ lần trước. Gồm:
  - thẻ quyết định (gộp khi trùng, có tuổi, trần số lượng);
  - mẫu 5%;
  - đề xuất từ "nằm mơ";
  - thẻ mục tiêu;
  - gói phát hành.
- **Báo ngay chỉ khi:** sự cố, dừng an toàn, đóng băng. Thông báo merge thì gom, không báo từng cái.

---

## 8. Giai đoạn theo phụ thuộc kỹ thuật (mỗi giai đoạn có phép nghiệm thu)

| GĐ | Nội dung | Phụ thuộc | Nghiệm thu |
|---|---|---|---|
| P0 | Sửa findings chặn của #448–#451, review lại đúng head, merge (Codex r1); sandbox lần 3 | — | 5 PR merged và đang chạy; sandbox 7/7 |
| P1 | T0.1 policy + T0.2 khoá diff tại `mergeGate` + T2.1 chỉ số đáng tin (C5) + sổ phát hiện T2.6 | P0 | PR sửa policy, bộ chấm hay workflow tự bị giữ (test với dữ liệu giả); chỉ số có nguồn và đối trọng |
| P2 | T1.1 verify + T1.2 bản đồ + Lighthouse/a11y + T1.5 bằng chứng + T0.3 hàng rào đầu tiên + T3.1 lỗi lặp → luật | P1 | Mọi PR UI có bằng chứng; ≥ 3 luật cứng từ finding |
| P3 | T2.2 `decide()` + phục hồi + hồ sơ đêm + chạy bóng 3 ngày + phép thử crash/quota | P1, P2 | ≥ 90% khớp; dừng an toàn đúng |
| P4 | Chuyển quyền cho `decide()`; mở đêm theo ma trận lòng tin; bản sáng; T2.4 critic cho plan 08:50 | P3 | Một đêm chạy hết không ai can thiệp; critic phản biện đúng 3 plan mẫu |
| P5 | T1.3 UAT khoá (mock + staging) + T1.6 bot tái hiện + T1.7 eval nội dung (mẫu vàng + giữ kín + swetest) + T1.8 test sạch | P2 | UAT xanh mỗi đêm; eval có điểm xuất phát |
| P6 | T2.3 tầng mục tiêu, mục tiêu đầu "UX tốt hơn" + T1.4 verifier theo AC + T3.4 ghi gu owner | P4, P5 | Owner nói 1 câu → sáng sau có cây chỉ số, giả thuyết, việc đầu đã chạy |
| P7 | Gói phát hành + đóng băng phát hành + cờ + 5 tester (C8) + phản hồi 1 chạm + telemetry ẩn danh (cổng riêng tư) | P5 | Owner bấm phát hành; tester dùng; chỉ số thật có số |
| P8 | T3.2 nằm mơ + T3.3 đăng ký skill/eval + T3.5 wiki/ADR + T2.5 vòng ngoài đầy đủ + bộ chấm theo gu (khi đủ dữ liệu) + T3.6 | P6, P7 | Đề xuất có đếm; skill có eval; wiki tự cập nhật |
| P9 | L3 rồi L4 theo điều kiện C1 + ý sản phẩm theo mục tiêu (D24, D25c, D12c, D11a, D22d) | P7, diễn tập quay lui | Diễn tập đạt; canary có SLO |

---

## 9. Ma trận truy vết (mọi mã → thành phần → giai đoạn)

| Mã | Thành phần | GĐ |
|---|---|---|
| R1, G1 | hồ sơ đêm, launchd, phép thử một đêm | P3–P4 |
| R2 | mục 5, L4 | P9 |
| R3 | T2.3 | P6 |
| R4 | mục 4 | P1, P6 |
| R5 | T2.4 | P4 |
| R6, G7 | mục 7 | P0 (#451), P4 |
| R7 | nghiệm thu từng GĐ = code chạy | tất cả |
| R8 | ma trận này | — |
| R9 | quy trình thiết kế | — |
| R10 | T0.1 | P1 |
| G2 | `decide()`, bỏ quota | P0 (#451), P3 |
| G3 | T2.1 + lô duyệt câu | P0, P1 |
| G4 | P7 | P7 |
| G5 | T0.1 | P1 |
| G6, U9 | T1.1, T1.5 | P2 |
| G8 | Lighthouse/a11y P2; telemetry P7; `noindex` → thẻ owner trong critic(goal "traffic") | P2, P7 |
| D1a, D1b, D1c, D1d, D1e | T3.1, T0.3, T1.5, critic + Codex review theo persona (riêng tư, câu chữ, north star, chiêm tinh) trong ma trận CI, T3.2 | P2, P8 |
| D2a, D2b, D2c, D2d | T2.5 (read-only, đầu ra hẹp), a11y đêm trong T1.1, T2.5 Repo Assist, T3.1 | P2, P8 |
| D3a, D3b, D3c, D3d, D3e, D3f | critic 2 vòng + bản bất đồng, T1.3, T1.6, dòng CLAUDE.md (P1), worktree mới mỗi lượt (đã có), T2.3 | P1–P6 |
| D4a, D4b, D4c, D4d, D4e | chỉ số, nhãn loại/rủi ro, T3.4 sửa trực tiếp, cờ, luật cứng "trường lưu mới" | P1–P7 |
| D5a, D5b, D5c, D5d, D5e | chỉ số, T2.5 sau tester, T3.3, T2.5 nghiên cứu, thứ tự giả thuyết | P1–P8 |
| D6a, D6b, D6c | T3.5, critic thẻ 2 phương án, ẩn danh trước khi model đọc | P4–P8 |
| D7a, D7b, D7c, D7d | T1.8, T3.4 codemod, nhãn rủi ro, T1.8 | P1–P6 |
| D8a, D8b, D8c | T2.5, T1.6, Codex review chặn sửa lấy lệ | P2–P8 |
| D9a, D9b, D9c, D9d, D9e | mã lỗi máy đọc được trong CLI và CI, T1.5, T3.5, T2.5 sự kiện, phản hồi 1 chạm | P2–P8 |
| D10a, D10b, D10c | T3.5 ADR, chỉ số tester + P7, T1.8 | P5–P8 |
| D11a, D11b, D11c, D11d | ý sản phẩm (Lá Dám prototype), cờ + SLO, owner duyệt spec, T3.6 | P4–P9 |
| D12a, D12b, D12c | T3.2, T0.1 hash, ý sản phẩm "Lá hiểu bạn dần" (có đồng ý) | P1, P8, P9 |
| D13a, D13b, D13c, D13d | hook chặn sửa câu chữ khi chưa nạp skill viết (T0.3), T3.3, T3.2, kiến trúc 4 tầng | P2–P8 |
| D14a, D14b, D14c, D14d | T3.3, T3.3, T0.3, skill nằm trong repo | P2–P8 |
| D15a, D15b, D15c, D15d | T1.2, critic đầu vào ghi âm, T3.5, điều phối theo vai trò (mục tiêu) | P2–P8 |
| D16a, D16b, D16c, D16d | T3.4, chỉ số skill, T1.7 có/không skill, UAT toàn hệ | P5–P8 |
| D17a, D17b, D17c | critic use case, T1.3, kiểm tái tạo trong T3.3 eval skill | P5–P8 |
| D18a, D18b, D18c | T1.4, T1.4, T1.3 | P5–P6 |
| D19a, D19b, D19c | critic, critic, retro-spec + yêu cầu phi chức năng mỗi lát (critic kiểm) | P4 |
| D20a, D20b, D20c, D20d, D20e | T1.7, T1.8, T1.6/T3.1, T0.3, review bảo mật toàn repo mỗi tháng trong T2.5 | P2–P8 |
| D21a | T1.7 giữ kín | P5 |
| D22a, D22b, D22c, D22d | T1.5 video, nhánh 9 issue-first + WIP, nhánh 6 đóng băng phát hành, ý sản phẩm café | P2–P9 |
| D23 | T3.3 bản đồ model, phiên ngắn mỗi việc | P8 |
| D24a, D24b, D24c | giả thuyết mục tiêu "nội dung/UX" (cần riêng tư cho mood) | P6–P9 |
| D25a, D25b, D25c | công cụ chỉ ra bản nháp + hook kiểm đầu ra cho nội dung sinh, T0.2/T0.4, ý sản phẩm widget Hợp gu | P1–P9 |
| D26a, D26b, D26c | T3.2 lưu phiên, T2.6, quét bằng model rẻ trong T3.1 | P1–P8 |
| D27a, D27b, D27c | mục 5 câu chữ, T1.7, T3.3 | P5–P8 |
| D28a, D28b, D28c | chỉ số thí nghiệm, nguồn giả thuyết, critic đầu vào ghi âm | P4–P6 |
| D29a, D29b, D29c | T2.6, T1.7/T3.4, T3.3 | P1–P8 |
| D30a, D30b | T3.4, T3.1 | P2–P6 |
| L1, L2 | T1.1, T1.2 | P2 |
| L3 | mục 5 | P1, P4 |
| L4 | T2.3, T2.6 | P6 |
| L5 | T2.6 | P1 |
| L6 | T1.4 fuzz + đêm tự merge + bản sáng | P4–P6 |
| L7 | kiểm mẫu 5% | P4 |
| L8 | danh sách cửa một chiều | P1 |
| L9 | T3.2 + skill nhớ lại | P8 |
| L10, L11 | T0.3, T3.1 | P2 |
| L12 | T3.3 | P8 |
| L13 | T2.3 leo đồi | P6 |
| L14 | T1.6 | P5 |
| L15 | T2.5 | P8 |
| L16 | PR nguyên tử (luật cỡ PR) | đã có |
| L17 | T0 trước | P1–P2 |
| L18 | cảnh báo ghi trong mục 3 (chỉ số thay thế/thật) và mục 5 (lòng tin từng bước) | — |
| E1, E2 | critic, nhánh 9 | P4 |
| E3, E4 | chỉ số | P1 |
| E5 | khẩu phần thời gian của mục tiêu | P6 |
| E6 | nguồn giả thuyết | P6 |
| U1, U3, U8 | xong (#448–#450) | P0 |
| U2, U4, U5, U7 | giả thuyết của mục tiêu "UX tốt hơn" | P6 |
| U6 | giữ nguyên quyết định 10.10 của owner; critic chỉ nêu lại nếu dữ liệu tester cho thấy cần | — |
| U9 | sửa ngay | P2 |
| C1 | mục 5 | P9 |
| C2 | mục 2 | P3 |
| C3 | hồ sơ đêm | P3 |
| C4 | T0.2 | P1 |
| C5 | mục 4 | P1 |
| C6 | mục 6 | P4 |
| C7 | chạy bóng | P3 |
| C8 | P7 | P7 |
| C9 | T1.7 | P5 |
| C10 | báo cáo 3 trạng thái | P1 |

## 10. Đề xuất bỏ (owner quyết)

Không có. Mọi mục đều có chỗ. Mục duy nhất giữ nguyên trạng là U6 (lối "xem bản mẫu" ở màn chào), vì đây là quyết định đã có của owner, không phải do Claude cắt.
