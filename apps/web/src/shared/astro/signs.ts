import type { ZodiacSign } from "../api/client";

export const signDetails: Record<ZodiacSign, { label: string; symbol: string; note: string }> = {
  aries: { label: "Bạch Dương", symbol: "♈︎", note: "Bạn hay bắt tay vào việc trước khi người khác kịp bàn xong." },
  taurus: { label: "Kim Ngưu", symbol: "♉︎", note: "Bạn làm chậm mà chắc, và không thích bị giục." },
  gemini: { label: "Song Tử", symbol: "♊︎", note: "Bạn hay tò mò, hỏi nhiều và học điều mới rất nhanh." },
  cancer: { label: "Cự Giải", symbol: "♋︎", note: "Bạn hay nhận ra người bên cạnh đang buồn trước khi họ nói ra." },
  leo: { label: "Sư Tử", symbol: "♌︎", note: "Bạn vui nhất khi được là chính mình và được người khác nhìn thấy." },
  virgo: { label: "Xử Nữ", symbol: "♍︎", note: "Bạn hay để ý chi tiết và thấy yên tâm khi mọi việc gọn gàng." },
  libra: { label: "Thiên Bình", symbol: "♎︎", note: "Bạn hay cân nhắc cho công bằng trước khi chọn." },
  scorpio: { label: "Bọ Cạp", symbol: "♏︎", note: "Bạn ít kể về mình, nhưng nhìn người rất kỹ." },
  sagittarius: { label: "Nhân Mã", symbol: "♐︎", note: "Bạn thích đi đây đó, học thêm và không muốn ở mãi một chỗ." },
  capricorn: { label: "Ma Kết", symbol: "♑︎", note: "Bạn chịu khó, làm từng bước và giữ lời." },
  aquarius: { label: "Bảo Bình", symbol: "♒︎", note: "Bạn hay nghĩ khác số đông và muốn làm theo cách riêng." },
  pisces: { label: "Song Ngư", symbol: "♓︎", note: "Bạn dễ cảm thông và hay hiểu người khác mà không cần họ giải thích." },
};
