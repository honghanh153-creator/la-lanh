# Thư viện prompt cảnh cho Nơi bình yên

Ngày soạn: 01.11.2026. Trạng thái: **bản đầu**; cột "Tình trạng" cập nhật sau đợt thử giai đoạn 1 cùng ngày. Chủ sản phẩm đã ưng hướng "góc nhà bình yên" ngày 01.11. Từng cảnh vẫn phải được duyệt trên video thật.

Thư viện này dùng để tạo ảnh và video cảnh cho Nơi bình yên một cách đồng nhất. Mỗi prompt gồm hai phần:

- **Khung chung:** phong cách và danh sách "không". Giữ nguyên ở mọi cảnh.
- **Chủ thể:** thay theo từng cảnh.

Đọc cùng:

- [Kế hoạch hướng góc nhà](../plans/2026-11-01-noi-binh-yen-homey-plan.md)
- Checklist phong cách ở §7.5 của [PRD](../foundation/la-lanh-noi-binh-yen-prd.md)
- Script xử lý `docs/operations/nby-media-pipeline.md` (có trong PR #68, chưa vào integration)

Prompt viết bằng tiếng Anh, vì Veo chỉ nhận prompt tiếng Anh.

## 1. Quy trình trong Google Flow

1. **Tạo ảnh tĩnh trước.**
   - Model: Nano Banana, tỷ lệ 9:16, 2 biến thể mỗi lần.
   - Ghép prompt từ khung ảnh (§2) và chủ thể (§4).
   - Chọn ảnh đạt checklist §7.5. Kiểm kỹ: không có chữ, logo hay người lạ trong ảnh; đồ vật không méo.
2. **Tạo video từ ảnh.**
   - Chế độ Frames. Khung đầu là ảnh đã chọn.
   - Muốn video lặp liền mạch thì đặt khung cuối là chính ảnh đó. Nếu bỏ trống khung cuối, script sẽ lặp bằng cách hòa 1 giây cuối vào đầu.
   - Model: Veo 3.1 Fast, 8 giây. Chỉ dùng Quality khi Fast cho lỗi hình rõ.
   - Prompt: khung video (§3) cộng với chuyển động riêng của cảnh.
3. **Xem lại 3 vòng lặp.** Kiểm méo, chớp, vật mới xuất hiện, và chỗ nối.
4. **Nếu cần dài hơn,** dùng Extend (nối từ khung cuối). Không cắt cảnh.
5. **Ghi sổ đăng ký** (PRD §8.3) cho mỗi clip giữ lại: công cụ, gói, model, ngày tạo, prompt ảnh, prompt video. Chụp điều khoản của gói tại ngày tạo.
6. **Tải bản gốc** (cần chủ sản phẩm đồng ý từng lần) vào một thư mục riêng ngoài git. Sau đó chạy `scripts/media/nby-media.sh`.

Không dùng ảnh hay khung hình từ reel tham chiếu làm đầu vào. Prompt không nêu tên nghệ sĩ, nhiếp ảnh gia hay thương hiệu.

## 2. Khung chung cho ảnh

**Màu thật, không filter** (chủ sản phẩm, 01.11): "mình muốn màu sắc thật, cảm giác sống động chứ không phải giống như đang có một filter". Khung cũ có cụm `warm muted film colors`, tạo màu phim ngả cam, bạc màu. Không dùng cụm đó nữa.

Đặt chủ thể vào chỗ `<SUBJECT>`:

```text
Photorealistic vertical 9:16 photo, close and intimate. <SUBJECT>. True-to-life natural colors exactly as the eye sees them, like an unedited photo from a modern full-frame camera: accurate white balance, natural saturation and contrast, crisp detail, clean deep shadows, bright clean daylight. Alive, fresh and calm. No color filter, no film look, no vintage or sepia tone, no orange tint, no haze, no faded blacks. No people, no text, no logos, no writing on objects.
```

Cảnh đêm (H5) thay `bright clean daylight` bằng `real warm lamplight with natural night colors`. Cảnh mưa (H2) giữ ánh sáng mưa thật, không thêm nắng.

Trong `<SUBJECT>`, tả màu thật của vật: `lush green`, `white curtain`, `blue patterned tiles`, `clear blue sky`. Tránh các từ làm màu ngả phim: `muted`, `film`, `vintage`, `nostalgic`, `golden haze`, `dreamy`.

Riêng cảnh ngoài trời rộng, có thể thay "close and intimate" bằng một góc máy cụ thể, ví dụ "Low viewpoint from inside a dense bank of wildflowers".

## 3. Khung chung cho video

**Máy đứng yên, cảnh phải sống** (chủ sản phẩm, 01.11): video thiếu "sự sống động của những hình ảnh xung quanh"; "có gió thì phải lay động, còn mưa thì lá phải như nào". Khung cũ chỉ xin chuyển động "rất nhỏ, gần như không thấy", nên cảnh gần như đứng im. Khung mới xin chuyển động **rõ, đều và liên tục** của gió, mưa, nước và ánh sáng, nhưng vẫn êm: không bão, không giật.

```text
Camera completely static on a tripod, <CAMERA_FEEL>. The scene itself is alive and keeps moving the whole time: <MOTION>. <LIGHT>, true-to-life natural colors, no color grading, no film look. Calm but clearly alive, never frozen. No people, no hands, no arms, no human body parts; nobody enters the frame or touches anything; every movement comes only from wind, rain, water, steam or light. No new objects, no camera movement. Ambient sound: <SOUND>.
```

| Chỗ trống | Cách viết |
|---|---|
| `<CAMERA_FEEL>` | Một câu đặt người xem vào chỗ ngồi, ví dụ "like sitting quietly at the kitchen table". |
| `<MOTION>` | 3–5 chuyển động **thấy rõ** của môi trường, lấy từ bảng dưới. Mỗi cảnh có ít nhất một nguồn chuyển động lớn (gió hoặc mưa) và một chi tiết nhỏ (hơi nước, bóng lá). |
| `<LIGHT>` | Ánh sáng thật của cảnh, ví dụ "Real early-morning sunlight". |
| `<SOUND>` | Âm thanh nền. Tiếng trong clip chỉ để tham khảo, vì app dùng âm thanh có license riêng (NBY-06). |

**Chuyển động phải không đều** (chủ sản phẩm, 01.11): "vấn đề là ở việc thiếu chú ý tới tiểu tiết, các action nhìn khá đều đều trong khi thực tế thì có lẽ không như vậy". Ngoài đời, gió đến từng cơn rồi lặng, giọt mưa trúng lá này rồi lá khác, phần lớn lá đứng yên phần lớn thời gian. Prompt phải ghi rõ:

- `Motion must be irregular and natural like real life, never uniform or rhythmic`.
- Chuyển động theo cơn, có lúc nghỉ: `uneven gusts ... then they slow down and almost stop for a moment before the next gust`.
- Chỉ một phần vật chuyển động mỗi lúc: `only some leaves move at a time while others stay still`.
- Mỗi chi tiết có thời điểm riêng: `a drop falls only now and then`, `drips fall at uneven intervals`, `ripples appear at random spots`.

Đánh đổi đã thấy (01.11): prompt "không đều" cho chuyển động tự nhiên hơn nhưng ít hơn (mưa 4,7%, bếp 10,2% điểm ảnh chuyển động), so với prompt "rõ, liên tục" (mưa 27,7%, bếp 22%). Cần chủ sản phẩm chấm bằng mắt.

**Chi tiết nhỏ cần ghi rõ:**

| Chi tiết | Viết | Lỗi đã gặp |
|---|---|---|
| Hơi nước | `only a very faint, thin, almost invisible translucent wisp of steam, barely visible against the light, breaking up and disappearing quickly, not white smoke, not thick, not continuous` | Hơi trắng, dày, liên tục như khói (bếp, Grok, 01.11) |
| Con vật | `once, around the middle of the clip, the tip of its tail gives one slow, gentle flick and settles back`; `does not stand up, walk or look at the camera` | (đạt 01.11: đuôi mèo vẫy một lần ở giây 2,8–3,3) |
| Cây tiền cảnh | `small potted plants with small and medium leaves, none of them large or dominating the frame` | Chậu lá to choán khung, nhìn lạ (mưa, Grok, 01.11) |
| Ánh sáng mưa | `bright, soft overcast daylight, airy and light, well exposed, not dark, not moody` | Màu đậm, tối (mưa, Grok, 01.11) |
| Vật rơi | Không xin vật rơi; thêm `no falling leaves or objects` | Một chiếc lá xanh tự rơi xuống bàn (mưa, Grok, 01.11) |

**Từ vựng chuyển động:**

| Nguồn | Viết như thế này | Tránh |
|---|---|---|
| Gió | `a steady breeze clearly sways the leaves and branches, the plant leaves flutter, turn and bounce back, the trees outside sway continuously, the curtain billows in and out by itself from the open window, hanging clothes swing` | `tremble slightly`, `almost imperceptibly`, `barely` |
| Mưa | `steady rain falls in visible streaks, raindrops hit the leaves so they bounce, dip and spring back, water runs off the leaf tips and drips from the roof edge in a constant stream, puddles on the tiles ripple with every drop, wet leaves glisten` | `gentle rain` một mình (ra mưa gần như không thấy) |
| Ánh sáng | `leaf shadows dance across the table as the branches outside sway, sunlight flickers through the moving leaves` | `the sunlight creeps slowly` |
| Hơi nước | `thin steam curls up and drifts sideways in the breeze` | hơi nước dày, cuộn lớn |
| Con vật (D26) | `the cat sleeps, its side rising and falling with each breath, one ear twitches` | để con vật đứng dậy, đi lại |

Không viết: người đi qua, bàn tay chạm vào vật, cửa đóng sầm, chim bay vào khung, đổi góc máy, gió mạnh làm đồ đổ.

## 4. Danh mục chủ thể

### Góc nhà (H)

| ID | Cảnh | `<SUBJECT>` | Tình trạng 01.11 |
|---|---|---|---|
| H1 | Bếp buổi sáng | `A small, lived-in home kitchen corner in early morning: a worn wooden table by a window, soft golden sunbeams falling across it with floating dust motes, a clay teapot with gentle steam, a simple ceramic cup, a linen cloth, a few herbs and a small bunch of wildflowers in a glass jar, a potted green plant on the windowsill` | Ảnh đạt. Video 8 giây (khung đầu = khung cuối) có hơi trà bốc lên; hơi nước hơi dày, cần chủ sản phẩm xem có quá đậm không |
| H2 | Hiên mưa mái ngói | `Gentle rain on a quiet afternoon at an old countryside home in Southeast Asia: rain drips softly from the edge of a terracotta tile roof, a low wooden table on the tiled porch with a small teapot and two tiny tea cups, potted green plants and a pot of jasmine glistening with raindrops, a warm lamp glowing softly inside the open wooden door` | Ảnh đạt, chất Việt Nam rõ. Video 8 giây: mưa rơi từ mái, đèn trong nhà sáng đều. Ứng viên tốt nhất |
| H3 | Góc đọc sách (bản Việt Nam) | `A small reading corner in a Vietnamese apartment on a quiet morning: a ginger cat curled up asleep in a warm patch of sunlight on patterned cement floor tiles, beside it a rattan chair with a soft cotton blanket, an open book face down and a cup of tea on a low wooden stool, a sheer curtain glowing softly, a few potted plants` | Bản trước trông giống nhà châu Âu và thiếu con mèo. Prompt đã sửa (đưa con mèo lên đầu) cho ra ghế mây, gạch bông, mèo ngủ trong nắng. Video 8 giây: mèo ngủ yên suốt clip. Dùng để quyết D26 |
| H4 | Ban công chung cư (bản Việt Nam) | `A tiny Vietnamese apartment balcony at sunrise: potted herbs, chili and a small lime tree in plastic and clay pots, trailing pothos on the railing, a few clean white clothes drying on a line and gently lifting in the breeze, a small plastic stool with a glass of iced tea, soft blurred low-rise Vietnamese rooftops with water tanks in the background` | Prompt đã sửa cho ra nhà ống, bồn nước inox, ghế nhựa: chất Việt Nam rõ. Chỉ có ảnh, chưa làm video |
| H5 | Bàn học buổi tối | `A small study desk by a window in a Vietnamese apartment in the evening: a warm desk lamp glowing, a notebook and a pen, a cup of tea with faint steam, a small potted plant, soft city lights blurred far outside the window, a gentle rain on the glass` | Ảnh đạt: đèn bàn, mưa trên kính, phố đêm mờ. Chỉ có ảnh, chưa làm video. Thẻ `dem` |
| H6 | Sân gạch, giàn hoa giấy | `A quiet tiled courtyard of an old Vietnamese house at midday: magenta bougainvillea flowers hanging from a trellis, soft dappled shade on red brick tiles, a large glazed ceramic water jar, a bamboo chair, a few fallen petals on the bricks, potted plants along a yellow lime-washed wall` | Ảnh đạt: tường vàng, hoa giấy, chum sành, ghế tre. Video 8 giây: hoa lay nhẹ, nhưng một cánh hoa rơi sát ống kính thành đốm hồng mờ giữa khung, nên lần sau bỏ "one petal drifts down". Thẻ `nang` |

### Thiên nhiên và cửa sổ (N)

| ID | Cảnh | Prompt đã dùng | Tình trạng 01.11 |
|---|---|---|---|
| N1 | Bờ hoa nhìn biển (giống R1) | Ảnh: `Low viewpoint from inside a dense bank of wildflowers on a coastal hillside: soft out-of-focus white and pale pink cosmos and small yellow wildflowers in the near foreground, sharper flowers in the midground, beyond them a calm turquoise sea and one huge soft white cumulus cloud filling most of a pale blue sky. Late morning sun, gentle sea haze, pastel natural colors` | Có video 8 giây. Chuyển động hoa và sóng đạt |
| N2 | Phòng nhìn ra biển, rèm lanh | Video: `Camera completely static, like a quiet moment in a seaside room. The thin linen curtain breathes slowly in a soft sea breeze, the cosmos flowers in the glass vase tremble slightly, faint steam rises from the tea cup, outside the wildflowers on the hillside sway gently, small waves roll slowly on the distant turquoise sea, the huge white cloud drifts almost imperceptibly.` | Có video |
| N3 | Hiên nhìn ra biển | Video: giống N2, nhưng `<CAMERA_FEEL>` là `like sitting quietly on a seaside cottage veranda`, và thêm `gentle light and shadow on the wooden floor`, `a faint creak of old wood` | Có video. Chủ sản phẩm đã so sánh với N2 |
| N4 | Cửa sổ gỗ mờ sương, cốc trà | Ảnh: `an old weathered wooden casement window, closed, its glass covered in soft morning condensation with a few water droplets. Outside it is blue hour just before sunrise: a misty meadow of small white and yellow wildflowers rolling gently to distant soft hills, pale sky. On the wooden windowsill a simple ceramic cup of tea with faint steam` | Có clip hơi trà (8 giây), clip cửa mở rồi mặt trời lên (16 giây, có Extend). Là ứng viên cho "Thở cùng cảnh" cách 1 |

## 5. Ví dụ video theo khung mới (chưa chạy: gói Flow hết credit tới 21.11)

```text
H1: Camera completely static on a tripod, like sitting quietly at the kitchen table. The scene itself is alive and keeps moving the whole time: a steady breeze through the open window clearly sways the trees outside, the leaves of the potted plant on the sill flutter and bounce back, the herbs and wildflowers in the glass jar nod in the breeze, leaf shadows dance across the wooden table, thin steam curls up from the clay teapot and drifts sideways. Real early-morning daylight, true-to-life natural colors, no color grading, no film look. Calm but clearly alive, never frozen. No people, no hands, no arms, no human body parts; nobody enters the frame or touches anything; every movement comes only from wind, water, steam or light. No new objects, no camera movement. Ambient sound: leaves rustling in the breeze, morning birds, a faint kettle simmer.

H2: Camera completely static on a tripod, like sitting on the porch watching the rain. The scene itself is alive and keeps moving the whole time: steady rain falls in visible streaks in front of the green garden, raindrops hit the leaves of the potted plants so they bounce, dip and spring back, water runs off the leaf tips and pours from the terracotta roof edge in a constant stream, puddles on the red tiles ripple with every drop, the wet leaves glisten, the lamp inside glows steadily. Real rainy daylight, true-to-life natural colors, no color grading, no film look. Calm but clearly alive, never frozen. No people, no hands, no arms, no human body parts; nobody enters the frame or touches anything; every movement comes only from rain, water and wind. No new objects, no camera movement. Ambient sound: steady rain on tiles and leaves, water dripping and splashing.

H3: Camera completely static on a tripod, like sitting quietly in a sunny reading corner. The scene itself is alive and keeps moving the whole time: a breeze through the open window makes the white curtain billow in and out by itself, the leaves of the potted plants flutter and bounce back, leaf shadows from the trees outside dance on the patterned floor, the ginger cat keeps sleeping, its side rising and falling with each breath and one ear twitching. Real morning daylight, true-to-life natural colors, no color grading, no film look. Calm but clearly alive, never frozen. No people, no hands, no arms, no human body parts; nobody enters the frame or touches the curtain or anything else; every movement comes only from wind, light and the sleeping cat's breathing. No new objects, no camera movement. Ambient sound: curtain and leaves rustling, distant morning birds.
```

## 6. Lỗi hay gặp và cách sửa

Đợt thử 01.11 (giai đoạn 1): 6 ảnh góc nhà mới và 4 video H1, H2, H3, H6 (làm từ ảnh theo khung cũ `warm muted film colors`, nên bị chê "giống filter"; ảnh H1, H2, H3, H6 đã tạo lại bằng khung §2 mới; video H1, H2, H3 đã làm lại theo màu thật, H6 chưa. Chủ sản phẩm xem bản làm lại: H3 bị loại vì có bàn tay thả rèm; H1, H2 màu đạt nhưng "thiếu sống động", nên §3 viết lại khung video), đều Veo 3.1 Fast 8 giây, 720p, khung đầu và khung cuối là cùng một ảnh. Cả 4 video giữ nguyên bố cục, không có vật mới hay người. Chưa kiểm chỗ nối khi lặp và chưa kiểm nhấp nháy; hai việc này cần file tải về.


| Lỗi | Cách sửa |
|---|---|
| Cảnh trông như nhà châu Âu | Thêm chi tiết Việt Nam cụ thể: gạch bông, mái ngói, ghế mây, ghế nhựa, ấm đất, bồn nước trên mái. Ghi rõ "Vietnamese" ngay từ đầu chủ thể |
| Vật bị thiếu (ví dụ con mèo) | Đưa vật đó lên đầu chủ thể, và ghi rõ vị trí ("in the warm patch of sunlight on the floor") |
| **Bàn tay người hiện ra** (video H3 ngày 01.11: một bàn tay thả rèm) | Loại clip ngay. Lỗi hay xảy ra khi prompt tả một vật "như có người làm" (rèm "thở", cốc trà vừa rót). Ghi rõ nguồn của chuyển động (`by itself from the open window`) và giữ câu `No people, no hands, no arms, no human body parts; nobody enters the frame or touches anything`. Khi duyệt, xem từng giây ở mép khung |
| Cảnh gần như đứng im, "thiếu sống động" (H1, H2 ngày 01.11) | Dùng khung §3 mới: xin chuyển động rõ và liên tục của gió, mưa; bỏ `tremble slightly`, `almost imperceptibly` |
| Mưa chỉ thành dòng ở mép mái, lá bị mưa mà không động (Grok, Flow ngày 01.11) | Đặt lá làm chủ thể cận cảnh; ghi `rain falls evenly across the whole frame`, `each hit makes the leaf dip, shake and spring back`. Chưa kiểm được là có sửa được không; nếu không, dùng video quay thật cho cảnh mưa |
| Vật bay sát ống kính thành đốm mờ (cánh hoa rơi) | Không yêu cầu vật rơi hay bay; chỉ tả chuyển động tại chỗ (lay, rung, thở) |
| Có chữ trên đồ vật (sách, hộp, biển) | Thêm `no writing on objects`. Nếu vẫn có chữ thì chọn biến thể khác, không sửa ảnh bằng tay |
| Video thêm vật mới hoặc chim bay vào | Giữ `No new objects`, và thêm `no birds` |
| Máy quay vẫn trôi | Mở đầu bằng `Camera completely static, almost a still photograph` |
| Ánh sáng chớp hoặc cháy trắng | Đổi sang `soft diffused light`. Loại clip có chớp theo kiểm nhấp nháy của NBY-09 |
| Màu như có filter: ngả cam, bạc màu, vùng tối xám (chủ sản phẩm chê 01.11) | Dùng khung §2: `true-to-life natural colors`, `accurate white balance`, `no film look`, `no orange tint`, `no faded blacks`. Không chỉnh màu thêm khi xử lý (xem kế hoạch §3) |
| Màu quá rực, "lộ AI" | Giữ `natural saturation`; bớt các tính từ như `magical`, `vivid`, `dreamy` |

## 7. Không bao giờ

- Không có người, khuôn mặt, bàn tay, cánh tay hay bóng người, kể cả thoáng qua ở mép khung.
- Không có chữ, logo, nhãn hàng, địa danh nhận diện được.
- Không có biểu tượng tôn giáo, bàn thờ, vật phẩm phong thủy.
- Không có cảnh buồn hay đáng sợ: giông bão, cây chết, phòng tối đen.
- Không mô phỏng gần như nguyên khung một reel cụ thể.
- Không đưa dữ liệu của người dùng vào prompt.
