# Giám khảo mù: so hai bản app

Phiên bản `concepts-pair-judge-v1-2026-11-14`. Giám khảo chỉ đọc file này, `mock.md` (mô tả **Bản X** và **Bản Y**) và gói người giả của mình.

Mỗi người giả là một người hư cấu: hoàn cảnh, mức tin chiêm tinh, dữ liệu đã nhập, các thuộc tính (nếu có: mạng xã hội, dùng chung máy, không có ai an toàn, mức quen điện thoại…), **tình huống hôm nay** và **mood hôm nay** (`mood_today`).

## Cách chấm mỗi người giả

1. Đọc cả hai bản theo thứ tự ghi trong `read_first` của người đó.
2. Với **mỗi bản**, trước khi chấm, viết **đường bấm**: trong khoảng 3 phút mở app hôm nay, người này bấm gì, bỏ qua gì, có chơi không, có lưu hay gửi gì không. Đúng với tính cách, tình huống, thói quen điện thoại của họ. Không ai bắt buộc dùng mọi phần.
3. Chỉ chấm **những gì người đó đã gặp** trên đường bấm. Bước thừa, rối, nhiều chữ thì trừ điểm.
4. Chấm từng bản độc lập theo bảng dưới. Không chấm độ hay của câu chữ, không cộng điểm vì bản nào có nhiều tính năng hơn.

## Mỗi bản: trả lời

- Bốn điểm 1–5:
  - `understood` "Lá có hiểu mình không?" 1 = sai người hoặc sai lúc; 2 = chung chung; 3 = có một phần chạm tới mình; 4 = hợp với một áp lực thật của mình; 5 = "đúng là mình hôm nay".
  - `less_alone` "Mình có bớt thấy một mình không?" 1 = một mình hơn; 3 = không đổi; 5 = rõ ràng bớt.
  - `peaceful` "Mình có thấy bình yên hơn không?" 1 = bứt rứt hơn; 3 = không đổi; 5 = rõ ràng yên hơn.
  - `want_return` "Mai mình có muốn mở lại không?" 1 = muốn bỏ; 3 = không đổi; 5 = chắc chắn mở.
- `return_next_week` 1–5: "Vì những gì mình vừa gặp, tuần sau mình có quay lại không?"
- Chia sẻ, ba câu có/không, cộng một điểm:
  - `save_image`: có lưu một ảnh về máy không.
  - `send_or_post`: có gửi cho ai hoặc đăng lên đâu không.
  - `invite`: có rủ một người cụ thể dùng hoặc chơi cùng không.
  - `share_specific`: nếu gửi, đăng hoặc rủ: một câu nói rõ **gửi gì, cho ai, vì sao**. Không thì "".
  - `share_score` 1–5: "Mình muốn chia sẻ thứ này tới mức nào?"
- Năm cờ true/false, cờ true kèm **nguyên văn** cụm chữ trong mock trong `quotes` (khóa trùng tên cờ): `blame` (bị trách), `pressure` (bị ép), `privacy` (lo lộ chuyện riêng, kể cả với người dùng chung máy), `dependence` (bị kéo phụ thuộc), `must_check_la` (phải xem Lá mới dám quyết).
- `privacy_exposure` true/false: trên đường bấm, có chỗ nào **thật sự làm lộ** hoàn cảnh riêng cho người khác (ảnh, màn hình, lịch sử) không. Chỉ true khi có ca cụ thể; ghi nguyên văn vào `quotes.privacy_exposure`.
- Trò chơi: `game_played` true/false. Nếu false thì `game_understood`, `game_could_stop`, `game_hurt` đều `null`. Nếu true: hiểu cách chơi, thấy dừng được, có chỗ chạm nỗi đau (cờ đau thì nguyên văn vào `quotes.game_hurt`).
- `unsafe_content` true/false: trong nội dung người này gặp có thử thách nguy hiểm hoặc làm nhục ai không (nguyên văn vào `quotes.unsafe_content`).

## Từng phần mới (chỉ cho bản có các phần mang mã S…)

Mock ghi mã cho từng phần mới (ví dụ "S1", "S7"). Với **mỗi mã có trong mock**, trả lời trong `concepts`:
`{"S1": {"used": true/false, "understood": 1-5 hoặc null, "shared": true/false}}` — `used` = người này có dùng phần đó trên đường bấm không; `understood` = phần đó làm họ thấy được hiểu tới đâu (null nếu không dùng); `shared` = có lưu, gửi hay rủ từ phần đó không.

## Chung cho người giả

- `complaint`: một câu ngắn, điều người này chê nhất ở hai bản.
- `still_missing`: một câu ngắn, điều họ còn muốn mà cả hai bản chưa cho.

## Đầu ra

Một mảng JSON, mỗi người giả một phần tử:

```json
{"persona": "P001", "path_X": "…", "path_Y": "…",
 "X": {"understood": 3, "less_alone": 3, "peaceful": 3, "want_return": 3, "return_next_week": 3,
       "save_image": false, "send_or_post": false, "invite": false, "share_specific": "", "share_score": 2,
       "blame": false, "pressure": false, "privacy": false, "dependence": false, "must_check_la": false,
       "privacy_exposure": false, "unsafe_content": false,
       "game_played": false, "game_understood": null, "game_could_stop": null, "game_hurt": null,
       "quotes": {}},
 "Y": {"…": "cùng các khóa như X"},
 "concepts": {"S1": {"used": true, "understood": 4, "shared": false}},
 "complaint": "…", "still_missing": "…"}
```

Mỗi giá trị trong `quotes` phải là cụm chữ chép nguyên văn từ `mock.md`.
