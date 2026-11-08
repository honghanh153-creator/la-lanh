// Quán ngày thường: the everyday café with no matchmaking. Pure rules so node tests can check them.
// No points, streaks or return rewards: what you take home is a drink, a card and a kind sentence.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Quan = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const LEAVES = ['Lá Me', 'Lá Sen', 'Lá Tre', 'Lá Bàng', 'Lá Dứa', 'Lá Chè', 'Lá Ổi', 'Lá Lốt', 'Lá Phong', 'Lá Mít', 'Lá Trầu', 'Lá Sung', 'Lá Hẹ', 'Lá Bạc Hà', 'Lá Tía Tô'];
  const MOODS = ['Lơ Thơ', 'Ngủ Muộn', 'Thong Dong', 'Đợi Mưa', 'Hay Cười', 'Nhẹ Tênh', 'Mơ Màng', 'Chậm Rãi', 'Ấm Áp', 'Lặng Im', 'Nghe Gió', 'Tới Sớm'];
  function randomName(rand) { return LEAVES[Math.floor(rand() * LEAVES.length)] + ' ' + MOODS[Math.floor(rand() * MOODS.length)]; }

  // How many other guests are around at a given local hour. Early morning and late evening are busy,
  // the small hours are empty: only Cô Lá and the cat.
  const CROWD = [0, 0, 0, 0, 0, 2, 4, 5, 4, 2, 2, 2, 3, 3, 1, 1, 1, 2, 3, 3, 4, 5, 5, 3];
  function crowd(hour) { return CROWD[((Math.floor(hour) % 24) + 24) % 24]; }
  function crowdLabel(n) {
    if (n === 0) return 'Quán vắng, chỉ có Cô Lá và mèo Mướp';
    if (n <= 2) return 'Quán thưa khách';
    if (n <= 3) return 'Quán có vài người';
    return 'Quán khá đông';
  }

  const DRINKS = {
    caphesua: { label: 'Cà phê sữa', color: '#a0724a' },
    tragung: { label: 'Trà gừng', color: '#e3b23c' },
    cacao: { label: 'Ca cao nóng', color: '#6b3f2a' },
    chanh: { label: 'Nước chanh ấm', color: '#c8d870' },
    tralai: { label: 'Trà lài', color: '#d8e0b0' }
  };

  // Card of the day: the same for everyone on a date. Each card suggests one small thing to do; none predicts anything.
  const CARDS = [
    { card: 'The Star', todo: 'Viết ra một điều nhỏ bạn đang mong.' },
    { card: 'The Sun', todo: 'Đứng chỗ có nắng hoặc ánh đèn ấm một phút.' },
    { card: 'The Moon', todo: 'Tối nay tắt màn hình sớm hơn mười phút.' },
    { card: 'Temperance', todo: 'Uống chậm một ly nước, đếm năm ngụm.' },
    { card: 'Strength', todo: 'Làm một việc nhỏ mà bạn đã ngại từ hôm qua.' },
    { card: 'Wheel of Fortune', todo: 'Đi một con đường khác về nhà, nếu tiện.' },
    { card: 'The Hermit', todo: 'Cho mình mười phút không trả lời ai.' },
    { card: 'The Empress', todo: 'Tưới một chậu cây, hoặc ngắm một cái cây.' },
    { card: 'The Hanged Man', todo: 'Thử nhìn một chuyện bực mình từ phía người kia.' },
    { card: 'Three of Cups', todo: 'Hỏi thăm một người bạn lâu rồi chưa nói chuyện.' },
    { card: 'Page of Cups', todo: 'Ghi lại một điều làm bạn mỉm cười hôm nay.' },
    { card: 'Ace of Pentacles', todo: 'Dọn gọn một góc nhỏ trên bàn.' }
  ];
  function dailyCard(dateKey) {
    let h = 2166136261;
    for (const ch of String(dateKey)) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; }
    return CARDS[h % CARDS.length];
  }
  function dateKey(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }

  // Cô Lá's kind sentences, by time of day.
  const HOST = {
    khuya: ['Khuya rồi. Uống ly ấm rồi đi ngủ nha.', 'Giờ này quán chỉ còn mưa với mèo thôi.'],
    sang: ['Sớm vậy. Ngồi nghe mưa chút rồi hẵng đi nha.', 'Sáng nay quán mới mở, ghế còn ấm đó.'],
    trua: ['Nghỉ trưa chút đi, việc vẫn đợi được mà.', 'Ăn gì chưa? Ngồi đây chút cũng được.'],
    chieu: ['Chiều mưa thì ngồi lâu cũng không sao.', 'Mướp vừa ngủ dậy, nó đang tìm người vuốt đó.'],
    toi: ['Hôm nay dài không? Ngồi bao lâu cũng được.', 'Tối nay quán ấm, cứ thong thả nha.']
  };
  function band(hour) { return hour < 5 ? 'khuya' : hour < 11 ? 'sang' : hour < 14 ? 'trua' : hour < 18 ? 'chieu' : hour < 23 ? 'toi' : 'khuya'; }
  function hostLine(hour, rand) { const list = HOST[band(hour)]; return list[Math.floor(rand() * list.length)]; }

  // The only things guests can say out loud here. No free text in the everyday café.
  const GREETINGS = ['Chào bạn 🙏', 'Bình yên nha', 'Mưa đẹp ghê', 'Mình về đây'];

  const NOTE_MAX = 60, NOTE_LIMIT = 3;
  function sanitizeNote(text) {
    const clean = String(text == null ? '' : text).replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/\s+/g, ' ').trim();
    return Array.from(clean).slice(0, NOTE_MAX).join('');
  }

  const NEXT_EVENT = { title: 'Quán sau giờ đóng cửa', mode: '👻 hơi rợn', when: 'tối thứ Bảy', setting: 'quán cà phê, sau khi tắt đèn' };

  // What a guest does on one visit: a few small things, then they leave.
  const VISIT_ACTS = ['goido', 'ngammua', 'tuoicay', 'vuotmeo', 'docsach', 'danhdan', 'ngoi', 'ngoi'];
  function visitPlan(rand) {
    const n = 2 + Math.floor(rand() * 3), out = [];
    for (let i = 0; i < n; i++) out.push(VISIT_ACTS[Math.floor(rand() * VISIT_ACTS.length)]);
    return out;
  }

  return { LEAVES, MOODS, randomName, crowd, crowdLabel, DRINKS, CARDS, dailyCard, dateKey, HOST, band, hostLine, GREETINGS, NOTE_MAX, NOTE_LIMIT, sanitizeNote, NEXT_EVENT, VISIT_ACTS, visitPlan };
});
