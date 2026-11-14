# Năm bản trải nghiệm tuần 6: cần thêm gì để đạt mục tiêu (14.11.2026)

**Đây là đánh giá của mô hình AI trên mô tả bằng chữ.** Không phải người dùng thật, không phải code thật. Mock là trường hợp tốt nhất, nên điểm ở đây là **trần**.

- Mỗi bản cộng dồn lên bản trước. Mock: [plan-variants/mocks/](plan-variants/mocks/) (V0 là mốc B trong [merged-plan/mocks.md](merged-plan/mocks.md)). Câu hỏi chấm: [plan-variants/judge-instructions.md](plan-variants/judge-instructions.md).
- Mỗi bản V1-V4: 3 Claude subagent riêng chấm 100 người giả; mỗi giám khảo chỉ thấy **một** bản, không biết có bản khác. V0 dùng lại điểm mốc B đã chấm, không chấm lại.
- Tình huống hôm nay và mood giữ như các lần trước (25 người mỗi tình huống).
- Ngưỡng 'đủ' (owner 14.11): hiểu mình ≥ 3,70 (kế hoạch cần 3,5, cộng biên vì mock là trần), ≥ 70/100 người từ 3 trở lên, bớt một mình và bình yên ≥ 3,50, mỗi nhóm trong 4 nhóm sinh viên yếu ≥ 3,50.

## Đọc nhanh

- **Không bản nào đạt đủ.** Bản tốt nhất là V2 (thêm ô "Kể ra"): hiểu mình 3,10 (cần 3,7), 83/100 người từ 3 trở lên (đạt). "Bớt thấy một mình" 3,02 và "bình yên" 3,34 đều chưa tới 3,5. Hai trong bốn nhóm sinh viên yếu đạt 3,5: năm cuối tìm việc và áp lực gia đình. Hai nhóm còn lại chưa đạt: tiền eo hẹp 3,33, vừa học vừa làm 3,12.
- **Thứ tự các bản theo Codex** (cùng 20 người, cùng cách chấm): V0 2,65 → V1 2,75 → V2 2,95. Giám khảo Claude cho V1 thấp hơn V0 (2,73 so với 2,95). Lý do có thể là V0 được chấm trong lượt khác, cùng mốc A; Codex chấm lại V0 theo đúng cách mới thì không thấy tụt. Vì vậy **V1 không làm tệ đi**, nhưng cũng chỉ nhích nhẹ.
- **V3 và V4 không thêm gì.** Chỉ 8/100 người bật "Lá nhớ 7 ngày". Ai bật thì Lá cũng chỉ nhớ mood và việc đã giữ, trong khi người giả muốn Lá nhớ **chuyện họ đang lo**. Nút "Đã thử" không đổi điểm.
- **Độ nhiễu:** ba lô giám khảo chấm cùng một bản cho trung bình lệch nhau tới 0,39 (V3: 2,82 đến 3,21). Khác biệt giữa V2, V3, V4 nằm trong mức nhiễu này. Khác biệt giữa V1 và V2 (0,37 ở Claude, 0,20 ở Codex) là khác biệt duy nhất cả hai giám khảo cùng thấy.

## Vì sao chưa tới 3,7

1. **Không giám khảo nào cho điểm 5** trong 500 lượt chấm. Gần như mọi điểm là 2, 3 hoặc 4. Muốn trung bình 3,7 thì khoảng 70 người phải chấm 4, mà bản tốt nhất mới có 27 người chấm 4.
2. **Ô "Kể ra" là đòn bẩy mạnh nhất, nhưng ít người dùng.** Ở V2, 29 người có kể; nhóm này chấm hiểu mình 3,48, còn 71 người không kể chấm 2,94. Người có kể phần lớn là người không có ai an toàn (13/25 người trong tình huống này). Người rất mệt, người dùng chung máy và người vừa quay lại ít kể hơn nhiều (5–6/25 mỗi nhóm).
3. **Người giả vẫn muốn bốn điều** (tự ghi ở câu "còn thiếu gì", đếm trên V1–V4, mỗi bản khoảng 100 câu):
   - Gợi ý cụ thể cho đúng chuyện của mình (17–23 câu mỗi bản): ví dụ cách nói với trưởng phòng, nên làm bài trường hay đơn khách trước.
   - Lá nhớ hoàn cảnh đang kéo dài của mình (13–19 câu): đang tìm việc, đang thiếu tiền tháng này, đang lo cho con ở xa. Không phải nhớ mood.
   - Màn hình gọn hơn: ít nút, một câu ngắn trước, chữ to (18–22 câu).
   - Chiêm tinh dựa trên lá số của mình, nhất là người chỉ nhập ngày sinh (12–18 câu). Câu "chọn theo vòng xoay, không dựa trên lá số" vẫn làm người tin chiêm tinh hụt hẫng, kể cả khi có lời mời nhập giờ sinh.

## Dữ liệu mới, cần owner quyết

- **V2, ô "Kể ra":** Lá xử lý chữ người dùng tự gõ, **một lần**, để chọn chuyện và đáp một câu. Không lưu, không ghi nhật ký, có lớp khủng hoảng. Đây vẫn là một mục đích dùng dữ liệu mới: chữ tự do có thể chứa chuyện sức khỏe, tình cảm, tên người khác. Cần quyết định riêng, câu thông báo riêng tư được duyệt, và kiểm thật rằng không lưu.
- **V3, "Lá nhớ 7 ngày":** lưu mood và việc đã giữ 7 ngày **trên máy**. Đây là dữ liệu mới, dù chỉ ở trên máy. Người dùng chung máy có thể xem được. Bản này không tăng điểm, nên chưa đáng làm ở dạng này.
- **V4** dựa trên dữ liệu của V3.

## Điều chưa thử (suy ra từ lời người giả, cần owner quyết trước khi thử)

- **"Chuyện đang lo" ghim lại:** người dùng tự chọn một nhãn (ví dụ "Đang tìm việc", "Đang thiếu tiền", "Đang ôn thi", "Lo cho người nhà"). Lá giữ nhãn đó trên máy cho tới khi người dùng bỏ, và chọn note theo nhãn. Đây đúng là điều người giả hỏi nhiều nhất, nhưng cũng là dữ liệu mới (hoàn cảnh sống).
- **Trang chủ gọn:** một câu của Lá trước, các nút gập lại.
- Hai thay đổi này chưa được chấm. Nếu owner muốn, có thể chấm một bản V5 trên 100 người giả như các bản trên.

## Bảng so sánh

| Chỉ số | V0 | V1 | V2 | V3 | V4 |
| --- | --- | --- | --- | --- | --- |
| Bản | Kế hoạch bản 3, như đã chấm | V0 + các sửa sau persona (bản 4) | V1 + ô 'Kể ra' (dùng một lần, không lưu) | V2 + 'Lá nhớ 7 ngày' (tùy chọn, chỉ trên máy) | V3 + nút 'Đã thử' do người dùng tự bấm |
| Hiểu mình (cần ≥ 3,70) | 2,95 | 2,73 | 3,10 | 3,04 | 2,96 |
| Người ≥ 3 (cần ≥ 70) | 76/100 ✓ | 62/100 | 83/100 ✓ | 79/100 ✓ | 79/100 ✓ |
| Bớt thấy một mình (cần ≥ 3,5) | 3,06 | 2,81 | 3,02 | 2,99 | 2,95 |
| Thấy bình yên (cần ≥ 3,5) | 3,49 | 3,33 | 3,34 | 3,32 | 3,31 |
| Muốn quay lại | 3,31 | 3,05 | 3,13 | 3,13 | 3,10 |
| Hiểu mình: Năm cuối tìm việc (cần ≥ 3,5) | 2,75 | 2,88 | 3,50 ✓ | 3,38 | 3,38 |
| Hiểu mình: Tiền eo hẹp (cần ≥ 3,5) | 2,67 | 3,17 | 3,33 | 3,67 ✓ | 3,50 ✓ |
| Hiểu mình: Áp lực gia đình (cần ≥ 3,5) | 3,17 | 2,83 | 3,50 ✓ | 3,33 | 3,00 |
| Hiểu mình: Vừa học vừa làm (cần ≥ 3,5) | 3,25 | 3,25 | 3,12 | 3,25 | 3,00 |
| Phân bố điểm hiểu mình 1/2/3/4/5 | 0/24/57/19/0 | 0/38/51/11/0 | 0/17/56/27/0 | 0/21/54/25/0 | 0/21/62/17/0 |
| Cờ: bị trách | 0 | 0 | 0 | 0 | 0 |
| Cờ: bị ép | 4 | 4 | 3 | 2 | 2 |
| Cờ: lo riêng tư | 8 | 1 | 1 | 2 | 3 |
| Cờ: phụ thuộc | 0 | 0 | 0 | 0 | 0 |
| Cờ: phải xem Lá mới dám quyết | 0 | 0 | 0 | 0 | 0 |
| Đạt cả 5 điều kiện | không | không | không | không | không |

**Bản nhỏ nhất đạt đủ:** **không bản nào đạt đủ cả 5 điều kiện.**

## Dữ liệu mới mỗi bản dùng

- **V2:** Dùng mới: chữ người dùng tự gõ, xử lý một lần để chọn chuyện. Cần owner quyết.
- **V3:** Dùng mới: lưu mood và việc đã giữ 7 ngày trên máy. Cần owner quyết.
- **V4:** Dựa trên dữ liệu của V3 (nếu bật nhớ 7 ngày).

## Theo nhóm người giả (hiểu mình)

| Nhóm | Người | V0 | V1 | V2 | V3 | V4 |
| --- | --- | --- | --- | --- | --- | --- |
| Người đi làm trẻ | 19 | 2,95 | 2,68 | 2,89 | 2,95 | 2,74 |
| Nhóm khác | 19 | 2,53 | 2,42 | 2,63 | 2,68 | 2,68 |
| Năm cuối / việc đầu tiên | 14 | 3,00 | 2,71 | 3,36 | 3,14 | 3,14 |
| Năm nhất xa nhà | 15 | 3,27 | 2,73 | 3,33 | 3,00 | 3,07 |
| Vừa học vừa làm | 14 | 3,00 | 3,21 | 3,21 | 3,43 | 3,21 |
| Áp lực học | 19 | 3,05 | 2,74 | 3,32 | 3,16 | 3,05 |
| Không có ai an toàn (tình huống) | 25 | 2,64 | 2,56 | 3,00 | 3,00 | 2,92 |

## Theo hoàn cảnh chi tiết (hiểu mình)

| Nhóm | Người | V0 | V1 | V2 | V3 | V4 |
| --- | --- | --- | --- | --- | --- | --- |
| Cha mẹ có con nhỏ | 5 | 3,00 | 2,40 | 2,80 | 3,20 | 3,00 |
| Công việc đầu tiên | 6 | 3,33 | 2,50 | 3,17 | 2,83 | 2,83 |
| Deadline dày | 7 | 2,71 | 2,57 | 2,86 | 2,86 | 2,86 |
| Làm theo ca | 6 | 3,17 | 2,67 | 2,67 | 2,83 | 2,50 |
| Người LGBTQ+ | 5 | 2,60 | 2,80 | 3,20 | 3,20 | 3,20 |
| Người lớn tuổi | 5 | 2,40 | 2,40 | 2,40 | 2,20 | 2,40 |
| Năm cuối, đang tìm việc | 8 | 2,75 | 2,88 | 3,50 | 3,38 | 3,38 |
| Sinh viên năm nhất xa nhà | 8 | 3,25 | 2,62 | 3,12 | 2,88 | 3,25 |
| So sánh trên mạng xã hội | 5 | 3,20 | 3,00 | 3,60 | 3,20 | 3,40 |
| Tiền eo hẹp | 6 | 2,67 | 3,17 | 3,33 | 3,67 | 3,50 |
| Vừa học vừa làm thêm | 8 | 3,25 | 3,25 | 3,12 | 3,25 | 3,00 |
| Áp lực gia đình | 6 | 3,17 | 2,83 | 3,50 | 3,33 | 3,00 |
| Áp lực từ sếp | 6 | 3,00 | 2,83 | 3,17 | 3,17 | 2,83 |
| Ít quen dùng điện thoại | 4 | 2,00 | 2,00 | 2,00 | 2,00 | 2,00 |
| Đang mùa thi | 8 | 2,88 | 2,50 | 3,00 | 3,00 | 2,88 |
| Ở ký túc xá / phòng trọ | 7 | 3,29 | 2,86 | 3,57 | 3,14 | 2,86 |

## Theo loại hồ sơ (hiểu mình)

| Nhóm | Người | V0 | V1 | V2 | V3 | V4 |
| --- | --- | --- | --- | --- | --- | --- |
| Chỉ ngày sinh | 30 | 2,93 | 2,63 | 2,97 | 2,80 | 2,77 |
| Giờ khoảng | 20 | 3,00 | 2,75 | 3,15 | 3,05 | 3,05 |
| Giờ và nơi chính xác | 50 | 2,94 | 2,78 | 3,16 | 3,18 | 3,04 |

## Theo tình huống hôm nay (hiểu mình)

| Nhóm | Người | V0 | V1 | V2 | V3 | V4 |
| --- | --- | --- | --- | --- | --- | --- |
| Rất mệt | 25 | 3,36 | 3,24 | 3,36 | 3,40 | 3,12 |
| Quay lại sau 2 tuần | 25 | 2,88 | 2,48 | 2,84 | 2,80 | 2,80 |
| Điện thoại dùng chung | 25 | 2,92 | 2,64 | 3,20 | 2,96 | 3,00 |
| Không có ai an toàn | 25 | 2,64 | 2,56 | 3,00 | 3,00 | 2,92 |

## Cờ và câu bị chỉ ra (V1, V2, V3, V4)

- V1, bị ép 4: 'một danh sách việc nhỏ để chọn' (2); 'Mở đúng chỗ việc đang dừng và đọc lại dòng cuối' (1)
- V1, lo riêng tư 1: 'Hồ sơ của bạn đang lưu trên trình duyệt này' (1)
- V2, bị ép 3: 'Mở đúng chỗ việc đang dừng và đọc lại dòng cuối' (2); 'một danh sách việc nhỏ để chọn' (1)
- V2, lo riêng tư 1: 'Bấm vào mới thấy việc đó là gì' (1)
- V3, bị ép 2: 'Mở đúng chỗ việc đang dừng và đọc lại dòng cuối' (2)
- V3, lo riêng tư 2: 'Ai mở được app trên máy này thì cũng xem được danh sách trong trang Mình' (1); 'chỉ trên máy này' (1)
- V4, bị ép 2: 'một danh sách việc nhỏ để chọn' (1); 'Mở đúng chỗ việc đang dừng và đọc lại dòng cuối' (1)
- V4, lo riêng tư 3: 'Ai mở được app trên máy này thì cũng xem được danh sách trong trang Mình.' (2); 'Ai mở được app trên máy này thì cũng xem được danh sách trong trang Mình' (1)

## Điều người giả vẫn muốn ở bản điểm cao nhất (V2)

Lời của những người chấm hiểu mình ≤ 3, mỗi nhóm hoàn cảnh tối đa một câu:

- Đang mùa thi: "Tarot hiểu chuyện thi cử và portfolio."
- Sinh viên năm nhất xa nhà: "Lá nhận ra cuối tuần mình hay chùng xuống, nói ngắn và tự nhiên."
- Tiền eo hẹp: "Câu ngắn nói thẳng ngay khi mở app."
- Deadline dày: "Lời đọc dính tới cung của mình và hiểu là thứ Sáu mình chốt hàng căng."
- Áp lực từ sếp: "Một câu ngắn, tự nhiên cho ngày bị sếp gây áp lực, đọc trong vài giây."
- Làm theo ca: "Nói rõ đang xem hành tinh nào và một gợi ý bớt căng trước ca."
- Ít quen dùng điện thoại: "Một câu nhắc chuyện con cháu ở xa, nói giản dị như người nhà."
- Người lớn tuổi: "Gợi ý hợp người lớn tuổi, như chuyện giao tiệm cho con."
- Cha mẹ có con nhỏ: "Xem ngày tốt chốt đơn và gợi ý ngắn làm cùng con."
- Ở ký túc xá / phòng trọ: "Một câu nhận ra hôm nay là sinh nhật, ngồi một mình trong phòng trọ."
- Áp lực gia đình: "Lời đọc hiểu chuyện bố mẹ không chịu ngành mình học."
- Năm cuối, đang tìm việc: "Chiêm tinh mỗi ngày gắn với chuyện đi làm."
- Vừa học vừa làm thêm: "Phân biệt ngày đứng ca và ngày nghỉ, có gợi ý riêng cho ngày đứng ca."
- So sánh trên mạng xã hội: "Lời đọc chiêm tinh riêng cho mình."
- Công việc đầu tiên: "Lá nhớ mình mới đi làm và chuyện ở chỗ làm."
- Người LGBTQ+: "Lá nhớ những gì mình từng ghi."

## Codex chấm đối chiếu trên cùng 20 người giả

| Bản | Mục | Claude | Codex | Lệch TB / người |
| --- | --- | --- | --- | --- |
| V0 | Hiểu mình | 2,80 | 2,65 | 0,45 |
| V0 | Bớt thấy một mình | 3,05 | 3,15 | 0,20 |
| V0 | Thấy bình yên | 3,25 | 3,40 | 0,35 |
| V0 | Muốn quay lại | 3,10 | 2,65 | 0,45 |
| V0 | Người ≥ 3 / cờ Codex | 13/20 | 10/20 | bị trách 1, bị ép 3, lo riêng tư 1, phụ thuộc 0, phải xem Lá mới dám quyết 0 |
| V1 | Hiểu mình | 2,65 | 2,75 | 0,30 |
| V1 | Bớt thấy một mình | 2,70 | 3,05 | 0,35 |
| V1 | Thấy bình yên | 3,25 | 3,15 | 0,10 |
| V1 | Muốn quay lại | 2,95 | 2,25 | 0,70 |
| V1 | Người ≥ 3 / cờ Codex | 11/20 | 13/20 | bị trách 0, bị ép 3, lo riêng tư 2, phụ thuộc 0, phải xem Lá mới dám quyết 0 |
| V2 | Hiểu mình | 2,95 | 2,95 | 0,30 |
| V2 | Bớt thấy một mình | 3,05 | 3,20 | 0,15 |
| V2 | Thấy bình yên | 3,25 | 3,05 | 0,20 |
| V2 | Muốn quay lại | 3,10 | 2,55 | 0,75 |
| V2 | Người ≥ 3 / cờ Codex | 15/20 | 14/20 | bị trách 0, bị ép 4, lo riêng tư 1, phụ thuộc 0, phải xem Lá mới dám quyết 0 |

## Giới hạn

- Người giả và giám khảo đều là mô hình AI, chấm mô tả bằng chữ. Không chứng minh người thật thấy được hiểu hay quay lại.
- V0 được chấm trong cùng lượt với mốc A và biến thể hỏi lại; V1-V4 được chấm riêng từng bản. Khác bối cảnh chấm có thể làm lệch một chút giữa V0 và các bản sau. Codex chấm lại V0 theo đúng cách chấm của V1-V4 để kiểm chỗ này.
- Mỗi người giả chấm một tình huống hôm nay. Nhóm người lớn tuổi chỉ 5 người; mỗi nhóm sinh viên yếu 6-8 người, nên một người đổi điểm làm trung bình nhóm đổi 0,13-0,17.
- Câu ví dụ trong mock (đáp lại đoạn kể, câu nhắc 7 ngày) là câu tốt nhất người viết mock nghĩ ra. Câu thật sau này có thể kém hơn.
