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
    umbrella: { name: 'Ô', labels: ['Ô vàng', 'Ô xanh'], colors: ['#f2b45a', '#6aa7e8'], photo: 'Ảnh giá ô ở cửa' },
    handle: { name: 'Quai ly', labels: ['Quai bên trái', 'Quai bên phải'], colors: ['#f3ead8', '#f3ead8'], photo: 'Ảnh quai ly' }
  };

  // Two rounds; the roles swap so nobody always leads.
  // photo: who holds the photos (and counts); ledger: who holds the guest book (and names the line).
  const ROUNDS = [
    { id: 'r1', title: 'Sổ khách có 6 dòng, ảnh chỉ có 5 ly', fields: ['cup'], photo: 'you', ledger: 'mate',
      rows: { cup: [0, 1, 1, 0, 2, 0] } },
    { id: 'r2', title: 'Hai ảnh, một dòng thừa', fields: ['cup', 'umbrella'], photo: 'mate', ledger: 'you',
      rows: { cup: [0, 0, 1, 1, 0, 1], umbrella: [1, 0, 0, 0, 1, 1] } }
  ];

  // Level 2 · Sĩ số +1 khó. V1: the cup photo was taken through the glass cabinet, so left and right are
  // swapped (the corner stamp says so). V2: a route with a back door that only opens one way; reading
  // the door sign needs one teammate to hold the light switch while the other looks.
  const L2 = [
    { id: 'g1', kind: 'mirror', title: 'Ảnh chụp qua gương tủ kính', fields: ['cup', 'handle'], mirrored: ['handle'], photo: 'you', ledger: 'mate',
      method: 'Hỏi ảnh được chụp thế nào trước khi tin điều nó cho thấy.',
      rows: { cup: [0, 1, 0, 2, 1, 0], handle: [1, 1, 0, 0, 0, 0] } },
    { id: 'g2', kind: 'route', title: 'Cửa sau chỉ mở một chiều', fields: [], map: 'you', log: 'mate', needsSwitch: true,
      method: 'Có đường nhanh hơn chưa chắc đi được theo cả hai chiều.',
      rows: { trip: [[3, 0, 1], [0, 2, 3], [2, 0, 3], [0, 3, 2], [1, 3, 2], [2, 3, 4]] } }
  ];
  // Café floor plan for the route round. The back door (Sân sau → Kho) only opens one way.
  const PLACES = ['Kho', 'Quầy', 'Cửa trước', 'Sân sau'];
  const PATHS = [[0, 1, 1], [1, 2, 2], [1, 3, 2], [3, 0, 1, 'oneway'], [2, 3, 4]];
  function earliest(a, b, ignoreOneWay) {
    const d = PLACES.map(() => Infinity); d[a] = 0;
    for (let k = 0; k < PLACES.length; k++) for (const [u, v, w, one] of PATHS) {
      if (d[u] + w < d[v]) d[v] = d[u] + w;
      if ((!one || ignoreOneWay) && d[v] + w < d[u]) d[u] = d[v] + w;
    }
    return d[b];
  }
  const LEVELS = { 1: null, 2: L2 };

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
  const PHOTOS = { r1: { cup: [3, 2, 0] }, r2: { cup: [2, 3, 0], umbrella: [2, 3] }, g1: { cup: [3, 1, 1], handle: [3, 2] } };
  function photoCounts(round) { return PHOTOS[round.id]; }
  // What the photo looks like: mirrored fields read left/right swapped.
  function seenCounts(round) {
    const out = {};
    for (const f of round.fields) out[f] = (round.mirrored || []).includes(f) ? photoCounts(round)[f].slice().reverse() : photoCounts(round)[f].slice();
    return out;
  }
  const same = (a, b) => a.length === b.length && a.every((v, i) => Number(v) === Number(b[i]));
  // Lines that, once removed, make the book match the given counts for every field.
  function candidates(round, counts) {
    if (round.kind === 'route') return NAMES.map((_, i) => i).filter(i => { const [a, b, m] = round.rows.trip[i]; return earliest(a, b, counts && counts.ignoreOneWay) > m; });
    return NAMES.map((_, i) => i).filter(i => round.fields.every(f => counts[f] && same(tally(round, f, i), counts[f])));
  }

  // The answer is one sentence. Each teammate holds the chips for one blank.
  // r1: the ledger holder names the line; the photo holder says which cup is missing.
  // r2: the ledger holder (you) names the line; the photo holder says what is missing in each photo.
  const BLANK_LABEL = { cup: 'vì ảnh thiếu một ly', umbrella: 'và giá ô thiếu một', handle: 'có' };
  const BLANK_TITLE = { cup: 'Loại ly', umbrella: 'Màu ô', handle: 'Bên quai' };
  function blanks(round) {
    if (round.kind === 'route') return [
      { key: 'name', owner: round.map, label: 'Dòng thừa là', title: 'Tên dòng thừa', options: NAMES.slice() },
      { key: 'shortest', owner: round.map, label: 'vì đi nhanh nhất cũng mất', title: 'Đi nhanh nhất', options: ['1', '2', '3', '4', '5'], unit: 'phút' },
      { key: 'logged', owner: round.log, label: 'mà sổ chỉ ghi', title: 'Sổ ghi', options: ['1', '2', '3', '4', '5'], unit: 'phút' }
    ];
    const out = [{ key: 'name', owner: round.ledger, label: 'Dòng thừa là', title: 'Tên dòng thừa', options: NAMES.slice() }];
    for (const f of round.fields) out.push({ key: f, owner: round.photo, label: BLANK_LABEL[f], title: BLANK_TITLE[f], options: FIELDS[f].labels.slice() });
    return out;
  }
  // The expected sentence, derived from the data, never stored.
  function answerOf(round) {
    const x = extraOf(round);
    if (x < 0) return null;
    if (round.kind === 'route') { const [a, b, m] = round.rows.trip[x]; return { name: NAMES[x], shortest: String(earliest(a, b)), logged: String(m) }; }
    const out = { name: NAMES[x] };
    for (const f of round.fields) out[f] = FIELDS[f].labels[round.rows[f][x]];
    return out;
  }

  // One official submission needs both teammates to lock. A wrong answer gets one shared sentence that
  // never says which blank was wrong or who filled it.
  function judge(round, answer, locks) {
    if (!locks || !locks.you || !locks.mate) return { status: 'waiting', text: 'Đang đợi cả hai cùng chốt.' };
    const blanksAll = blanks(round);
    if (blanksAll.some(b => answer[b.key] == null)) return { status: 'incomplete', text: 'Câu trả lời còn chỗ trống.' };
    const exp = answerOf(round);
    const ok = !!exp && Object.keys(exp).every(k => String(answer[k]) === exp[k]);
    return ok ? { status: 'solved', text: 'Khớp cả sổ lẫn ' + (round.kind === 'route' ? 'sơ đồ' : 'ảnh') + '. Một ngọn đèn trên mái quán sáng lên.' }
      : { status: 'retry', text: 'Chưa khớp. Đọc lại cùng nhau rồi chốt lần nữa, không mất gì.' };
  }

  // The confirmation flow, pure so timing orders can be tested. Events:
  // youLock (you press Chốt), mateReady / mateNotReady (the teammate's blanks are filled or cleared),
  // answerChanged (someone edits the sentence), retry (a wrong answer), solved.
  // The teammate locks as soon as you have locked and their half is ready, in either order, so an
  // early Chốt never stalls. judge is true only on the step where both locks first become true, and
  // nothing happens after the round is settled, so one round can never be settled twice.
  function newConfirm(mateReady) { return { locks: {}, mateReady: !!mateReady, settled: false }; }
  function confirmStep(st, ev) {
    const s = { locks: Object.assign({}, st.locks), mateReady: !!st.mateReady, settled: !!st.settled };
    if (s.settled) return { state: s, judge: false };
    const before = !!(s.locks.you && s.locks.mate);
    if (ev === 'youLock') { s.locks.you = true; if (s.mateReady) s.locks.mate = true; }
    else if (ev === 'mateReady') { s.mateReady = true; if (s.locks.you) s.locks.mate = true; }
    else if (ev === 'mateNotReady') { s.mateReady = false; s.locks.mate = false; }
    else if (ev === 'answerChanged' || ev === 'retry') s.locks = {};
    else if (ev === 'solved') { s.settled = true; return { state: s, judge: false }; }
    return { state: s, judge: !before && !!(s.locks.you && s.locks.mate) };
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
  // Route round: the teammate reads the scan log; given the line you named, they read its logged minutes.
  function logLines(round) {
    return NAMES.map((n, i) => { const [a, b, m] = round.rows.trip[i]; return n + ': ' + PLACES[a] + ' → ' + PLACES[b] + ', ' + m + ' phút'; });
  }
  function mateLogged(round, name) {
    const i = NAMES.indexOf(name);
    return i < 0 ? null : String(round.rows.trip[i][2]);
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
    hai: { label: 'Hài', icon: '😂', intro: 'Chiều ấm. Mướp nhảy vào ảnh tạo dáng, không tính nó nha.', reveal: 'Ảnh tạo dáng của cả đội: Mướp chen giữa, mặt rất nghiêm túc.', reveal2: 'Ảnh tạo dáng: cả đội cùng đẩy cửa sau theo chiều ngược, cửa vẫn không nhúc nhích.' },
    rung: { label: 'Hơi rợn', icon: '👻', intro: 'Quán tối, chỉ còn đèn pin. Có một bóng mờ sau hàng ghế cuối.', reveal: 'Bóng mờ sau hàng ghế là cây treo áo đội cái mũ của Cô Lá.', reveal2: 'Tiếng gõ ở cửa sau hoá ra là Mướp muốn vào kho tìm cá khô.' }
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
  // Level 2 goes a little deeper, still optional.
  const QUESTIONS_L2 = ['Gần đây điều gì làm bạn thấy được hiểu?', 'Một thói quen nhỏ giúp bạn bình tĩnh?', 'Bạn mong ai đó hỏi mình câu gì nhiều hơn?'];
  Object.assign(MATE_ANSWERS, {
    'Gần đây điều gì làm bạn thấy được hiểu?': 'Bạn mình nhớ mình không ăn hành, tự dặn quán giùm.',
    'Một thói quen nhỏ giúp bạn bình tĩnh?': 'Tưới cây buổi sáng, chậm thôi.',
    'Bạn mong ai đó hỏi mình câu gì nhiều hơn?': '"Hôm nay bạn có mệt không?" Câu đó dễ thương ghê.'
  });
  const MATE_ASKS_L2 = 'Có điều gì bạn muốn người khác hiểu về mình hơn?';
  const YOUR_ANSWERS_L2 = ['Mình chậm nhưng chắc', 'Mình ít nói nhưng để ý', 'Mình cần chút thời gian', 'Để lần sau nha'];
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

  LEVELS[1] = ROUNDS;
  return { newConfirm, confirmStep, L2, LEVELS, PLACES, PATHS, earliest, seenCounts, answerOf, logLines, mateLogged, QUESTIONS_L2, MATE_ASKS_L2, YOUR_ANSWERS_L2, NAMES, FIELDS, ROUNDS, PHOTOS, tally, extraOf, photoCounts, candidates, blanks, judge, mateNameFromCounts, mateReasonFor,
    photoLines, ledgerLines, noteFromCounts, MODES, COURAGE, teamCourage, QUESTIONS, MATE_ANSWERS, MATE_ASKS, YOUR_ANSWERS, together, GESTURES, NOTE_MAX };
});
