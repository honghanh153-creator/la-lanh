// Thử thách đôi · L1 Sĩ số +1: two people are one team; each holds half of the facts and half of the answer.
// Pure rules so node tests can check them. No DOM, no storage, no scores.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Duo = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  // Six fictional guest-book lines from last night. They are records, never anyone playing tonight,
  // so the "extra line" can never point at a real person in the room (format S2).
  const NAMES = ['An', 'Bình', 'Chi', 'Duy', 'Hà', 'Linh'];

  const FIELDS = {
    cup: { name: 'Ly', labels: ['Cà phê', 'Trà', 'Ca cao'], colors: ['#a0724a', '#d8c070', '#6b3f2a'], photo: 'Ảnh ly trên bàn' },
    umbrella: { name: 'Ô', labels: ['Ô vàng', 'Ô xanh'], colors: ['#f2b45a', '#6aa7e8'], photo: 'Ảnh giá ô ở cửa' }
  };

  // Two rounds; the roles swap so nobody always leads.
  // photo: who holds the photos (and counts); ledger: who holds the guest book (and names the line).
  const ROUNDS = [
    { id: 'r1', title: 'Sổ khách có 6 dòng, ảnh chỉ có 5 ly', fields: ['cup'], photo: 'you', ledger: 'mate',
      rows: { cup: [0, 1, 1, 0, 2, 0] } },
    { id: 'r2', title: 'Hai ảnh, một dòng thừa', fields: ['cup', 'umbrella'], photo: 'mate', ledger: 'you',
      rows: { cup: [0, 0, 1, 1, 0, 1], umbrella: [1, 0, 0, 0, 1, 1] } }
  ];

  function tally(round, field, without) {
    const out = FIELDS[field].labels.map(() => 0);
    round.rows[field].forEach((v, i) => { if (i !== without) out[v] += 1; });
    return out;
  }
  // The photos are derived, never stored: they show every line except the extra one.
  function extraOf(round) {
    const c = candidates(round, photoCounts(round));
    return c.length === 1 ? c[0] : -1;
  }
  // The real photos. Each round is written so exactly one line explains them; tests check it.
  const PHOTOS = { r1: { cup: [3, 2, 0] }, r2: { cup: [2, 3, 0], umbrella: [2, 3] } };
  function photoCounts(round) { return PHOTOS[round.id]; }
  const same = (a, b) => a.length === b.length && a.every((v, i) => Number(v) === Number(b[i]));
  // Lines that, once removed, make the book match the given counts for every field.
  function candidates(round, counts) {
    return NAMES.map((_, i) => i).filter(i => round.fields.every(f => counts[f] && same(tally(round, f, i), counts[f])));
  }

  // The answer is one sentence. Each teammate holds the chips for one blank.
  // r1: the ledger holder names the line; the photo holder says which cup is missing.
  // r2: the ledger holder (you) names the line; the photo holder says what is missing in each photo.
  function blanks(round) {
    const out = [{ key: 'name', owner: round.ledger, label: 'Dòng thừa là', options: NAMES.slice() }];
    for (const f of round.fields) out.push({ key: f, owner: round.photo, label: f === 'cup' ? 'vì ảnh thiếu một ly' : 'và giá ô thiếu một', options: FIELDS[f].labels.slice() });
    return out;
  }

  // One official submission needs both teammates to lock. A wrong answer gets one shared sentence that
  // never says which blank was wrong or who filled it.
  function judge(round, answer, locks) {
    if (!locks || !locks.you || !locks.mate) return { status: 'waiting', text: 'Đang đợi cả hai cùng chốt.' };
    const blanksAll = blanks(round);
    if (blanksAll.some(b => answer[b.key] == null)) return { status: 'incomplete', text: 'Câu trả lời còn chỗ trống.' };
    const x = extraOf(round);
    const ok = answer.name === NAMES[x] && round.fields.every(f => answer[f] === FIELDS[f].labels[round.rows[f][x]]);
    return ok ? { status: 'solved', text: 'Khớp cả sổ lẫn ảnh. Một ngọn đèn trên mái quán sáng lên.' }
      : { status: 'retry', text: 'Chưa khớp. Đọc lại cùng nhau rồi chốt lần nữa, không mất gì.' };
  }

  // What the teammate concludes from a note. They only use what the note says plus their own half.
  // r1: the teammate has the book; the note carries your photo counts.
  function mateNameFromCounts(round, counts) {
    const c = candidates(round, counts);
    return c.length === 1 ? NAMES[c[0]] : null;
  }
  // r2: the teammate has the photos; given the line you named, they fill what is missing in each photo.
  function mateReasonFor(round, name) {
    const i = NAMES.indexOf(name), out = {};
    const counts = photoCounts(round);
    for (const f of round.fields) {
      const full = tally(round, f, -1);
      const k = full.findIndex((v, j) => v !== counts[f][j]);
      out[f] = k >= 0 ? FIELDS[f].labels[k] : null;
    }
    // The teammate also says whether that line fits both photos, without saying which one would.
    out.fits = i >= 0 && candidates(round, counts).includes(i);
    return out;
  }
  // The teammate reads their photos aloud, one short line each.
  function photoLines(round) {
    const counts = photoCounts(round);
    return round.fields.map(f => FIELDS[f].photo + ': ' + FIELDS[f].labels.map((l, i) => counts[f][i] + ' ' + l.toLowerCase()).filter(s => !s.startsWith('0 ')).join(', '));
  }
  function ledgerLines(round) {
    return NAMES.map((n, i) => n + ': ' + round.fields.map(f => FIELDS[f].labels[round.rows[f][i]].toLowerCase()).join(', '));
  }
  function noteFromCounts(round, counts) {
    return round.fields.map(f => FIELDS[f].labels.map((l, i) => (counts[f][i] || 0) + ' ' + l.toLowerCase()).join(', ')).join(' · ');
  }

  // Two moods on the same puzzle. Safety: the team uses the gentler courage level of the two;
  // "Mình sợ quá" turns the lights on for both and never says who pressed it.
  const MODES = {
    hai: { label: 'Hài', icon: '😂', intro: 'Chiều ấm. Mướp nhảy vào ảnh tạo dáng, không tính nó nha.', reveal: 'Ảnh tạo dáng của cả đội: Mướp chen giữa, mặt rất nghiêm túc.' },
    rung: { label: 'Hơi rợn', icon: '👻', intro: 'Quán tối, chỉ còn đèn pin. Có một bóng mờ sau hàng ghế cuối.', reveal: 'Bóng mờ sau hàng ghế là cây treo áo đội cái mũ của Cô Lá.' }
  };
  const COURAGE = { nhe: { label: 'Nhẹ', rank: 0 }, vua: { label: 'Vừa', rank: 1 } };
  function teamCourage(a, b) { return COURAGE[a].rank <= COURAGE[b].rank ? a : b; }

  // Break corner: one optional question each, a little deeper than small talk. Always skippable.
  const QUESTIONS = ['Món ăn nào làm bạn nhớ nhà?', 'Gần đây điều gì làm bạn cười to nhất?', 'Một nơi bạn muốn ngồi lâu thật lâu?'];
  const MATE_ANSWERS = {
    'Món ăn nào làm bạn nhớ nhà?': 'Canh chua mẹ nấu, chua hơi quá tay.',
    'Gần đây điều gì làm bạn cười to nhất?': 'Con mèo nhà bên đi lùi khỏi cái hộp.',
    'Một nơi bạn muốn ngồi lâu thật lâu?': 'Bậc thềm nhà cũ, lúc trời vừa tạnh mưa.'
  };
  const MATE_ASKS = 'Hôm nay có gì làm bạn thấy nhẹ lòng không?';
  const YOUR_ANSWERS = ['Ly trà nóng lúc nãy', 'Được ngồi yên một chút', 'Giải đố xong cùng nhau', 'Để mình nghĩ thêm'];

  // "Đi tiếp cùng nhau?" is a quiet two-way yes. The result never says who said no.
  function together(you, mate) {
    return you && mate ? { status: 'tiep', text: 'Hai bạn đi tiếp cùng nhau sang level sau.' }
      : { status: 'xoay', text: 'Lượt xoay mới: mỗi người ghép một đội khác. Không ai biết ai đã chọn gì.' };
  }

  // Short gestures; no free chat in the challenge.
  const GESTURES = [
    { id: 'doc', label: 'Đọc giúp mình', icon: '📖' },
    { id: 'doi', label: 'Đợi mình chút', icon: '✋' },
    { id: 'dem', label: '3-2-1 chốt', icon: '⏱' },
    { id: 'dap', label: 'Đập tay', icon: '🙌' }
  ];
  const NOTE_MAX = 60;

  return { NAMES, FIELDS, ROUNDS, PHOTOS, tally, extraOf, photoCounts, candidates, blanks, judge, mateNameFromCounts, mateReasonFor,
    photoLines, ledgerLines, noteFromCounts, MODES, COURAGE, teamCourage, QUESTIONS, MATE_ANSWERS, MATE_ASKS, YOUR_ANSWERS, together, GESTURES, NOTE_MAX };
});
