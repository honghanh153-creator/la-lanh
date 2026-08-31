import type { ZodiacSign } from "../api/client";

export const signDetails: Record<ZodiacSign, { label: string; symbol: string; note: string }> = {
  aries: { label: "Bạch Dương", symbol: "♈︎", note: "Điều đầu tiên bạn muốn làm thường là điều đáng nghe nhất." },
  taurus: { label: "Kim Ngưu", symbol: "♉︎", note: "Chậm một nhịp không có nghĩa là đứng yên." },
  gemini: { label: "Song Tử", symbol: "♊︎", note: "Có một câu hỏi đang mở đúng cánh cửa bạn cần." },
  cancer: { label: "Cự Giải", symbol: "♋︎", note: "Bạn không cần giải thích mọi điều mình đang cảm thấy." },
  leo: { label: "Sư Tử", symbol: "♌︎", note: "Đừng thu nhỏ niềm vui chỉ để vừa với căn phòng." },
  virgo: { label: "Xử Nữ", symbol: "♍︎", note: "Việc nhỏ bạn làm hôm nay đang đỡ lấy một điều lớn." },
  libra: { label: "Thiên Bình", symbol: "♎︎", note: "Một lựa chọn thật lòng đáng giá hơn một câu trả lời đẹp." },
  scorpio: { label: "Bọ Cạp", symbol: "♏︎", note: "Điều chưa nói ra vẫn đang chỉ cho bạn một hướng đi." },
  sagittarius: { label: "Nhân Mã", symbol: "♐︎", note: "Tò mò thêm một chút — câu chuyện chưa dừng ở đây." },
  capricorn: { label: "Ma Kết", symbol: "♑︎", note: "Bạn không cần hoàn thành tất cả để thấy mình đã đi xa." },
  aquarius: { label: "Bảo Bình", symbol: "♒︎", note: "Ý nghĩ khác thường ấy có thể là tín hiệu, không phải nhiễu." },
  pisces: { label: "Song Ngư", symbol: "♓︎", note: "Tin vào điều bạn cảm được trước khi gọi tên được nó." },
};
