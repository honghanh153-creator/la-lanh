// Game lab 14: case fixtures, solver and judge. Pure functions, no DOM, no storage.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Cases = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  // Six machine-exported attendance records. They are data (ghost holograms in the room), not people
  // anyone plays, so the "extra record" never maps onto a player.
  const profiles = [
    { id: 'an', name: 'An' }, { id: 'binh', name: 'Bình' }, { id: 'chi', name: 'Chi' },
    { id: 'duy', name: 'Duy' }, { id: 'ha', name: 'Hà' }, { id: 'linh', name: 'Linh' }
  ];

  // Playable fictional adult detectives. Each role opens one kind of source; zodiac and tarot are
  // author-assigned archetypes that only colour how they talk.
  const roles = {
    photo: { name: 'Thợ ảnh', spots: ['camera', 'mirror'] },
    route: { name: 'Người đo đường', spots: ['poster', 'door'] },
    records: { name: 'Thủ thư', spots: ['scanner', 'shelf', 'teacher'] },
    seer: { name: 'Người đọc lá', spots: ['tarot'] }
  };
  const detectives = [
    { id: 'hanh', name: 'Hạnh', role: 'records', sign: 'Cự Giải', tarot: 'Temperance', trait: 'Chu đáo, hay hỏi lại cho chắc mọi người cùng hiểu',
      lines: { soft: 'Mình cùng xem lại điều đã thấy nhé, không ai phải vội.', direct: 'Bạn muốn mình mở sổ nào? Nói một chỗ thôi.', joke: 'Hồ sơ thì ghép nhầm được, chứ trà sữa của mình thì không.' },
      help: 'Để mình đi lấy cho, sổ sách là nghề của mình.', hold: 'Mình đứng đây giữ, bạn cứ làm đi.' },
    { id: 'quan', name: 'Quân', role: 'photo', sign: 'Song Tử', tarot: 'The Magician', trait: 'Tò mò, nói nhanh, nảy ý liên tục',
      lines: { soft: 'Ý hay đó! À khoan, còn ý này nữa. Thôi bạn hỏi tiếp đi.', direct: 'Hỏi từng câu nha, tớ hay lạc đề lắm.', joke: 'Tớ chụp ảnh đẹp lắm, chỉ là hay quên tắt đèn flash.' },
      help: 'Máy ảnh hả? Đi liền!', hold: 'Tớ giữ công tắc, nhưng đừng bắt tớ đứng im lâu quá nha.' },
    { id: 'minh', name: 'Minh', role: 'route', sign: 'Thiên Bình', tarot: 'Justice', trait: 'Cẩn thận, thích đo đạc rồi mới nói',
      lines: { soft: 'Đo trước, nói sau. Mình cùng nhìn sơ đồ nhé.', direct: 'Đoạn nào, mấy phút? Nói số đi.', joke: 'Tớ không chậm, tớ chỉ đang cân nhắc từng bước chân.' },
      help: 'Để tớ đi đo, đường xá là phần của tớ.', hold: 'Tớ đứng đây, chính xác từng phân.' },
    { id: 'thao', name: 'Thảo', role: 'seer', sign: 'Bảo Bình', tarot: 'The Star', trait: 'Mơ màng nhưng sắc, thích thử cách nghĩ khác',
      lines: { soft: 'Lá bài không biết đáp án đâu, nó chỉ gợi cách nhìn thôi.', direct: 'Bạn đếm tay chưa, hay mới nhìn lướt?', joke: 'Sao chiếu mệnh hôm nay bảo: đếm lại lần nữa.' },
      help: 'Để mình rút một lá gợi cách kiểm.', hold: 'Mình giữ cho, tiện ngắm trần nhà luôn.' }
  ];
  const roleOfSpot = spot => Object.keys(roles).find(r => roles[r].spots.includes(spot)) || null;
  const ownerOfSpot = spot => detectives.find(d => d.role === roleOfSpot(spot)) || null;

  const ids = profiles.map(p => p.id);
  const nameOf = id => (profiles.find(p => p.id === id) || {}).name || id;

  const fields = {
    badge: { name: 'Huy hiệu', labels: ['Sao', 'Trăng', 'Tam giác'], icons: ['★', '☾', '△'] },
    book: { name: 'Bìa sổ', labels: ['Vàng', 'Xanh'], icons: ['V', 'X'] },
    ticket: { name: 'Mũi tên trên phiếu', labels: ['Trái', 'Phải'], icons: ['←', '→'] }
  };

  // Corridor graph shared by route cases. Node index: 0 T Thư viện, 1 S Sảnh, 2 P Phòng máy, 3 L Lớp.
  const nodes = ['Thư viện', 'Sảnh', 'Phòng máy', 'Lớp'];
  const short = ['T', 'S', 'P', 'L'];
  const linear = [[0, 1, 1], [1, 2, 2], [2, 3, 1]];
  const branched = [[0, 1, 1], [1, 2, 2], [2, 3, 1], [1, 3, 4], [3, 0, 1, 'oneway']];

  const cols = (spec) => ids.map((id, i) => {
    const row = { id };
    for (const k of Object.keys(spec)) row[k] = spec[k][i];
    return row;
  });

  // Seven cases. Each fixture is self-contained and timestamped; later cases never edit earlier facts.
  const cases = [
    { id: 'p1', kind: 'photo', title: 'Chiếc huy hiệu lạc lớp', skill: 'Đếm một loại vật', stamp: 'P1 · 09:10',
      intro: 'Máy điểm danh in ra 6 hồ sơ cho 5 người. Ảnh cận chụp đồ của đúng 5 người thật.',
      sources: ['badge'], rows: cols({ badge: [0, 1, 1, 0, 2, 0] }), proof: { badge: [3, 2, 0] } },
    { id: 'r1', kind: 'route', title: 'Hành lang không có lối tắt', skill: 'Cộng thời gian trên bản đồ', stamp: 'R1 · 08:50',
      intro: 'Mỗi hồ sơ có hai lượt quét thẻ. Năm hành trình là thật, một hồ sơ bị máy ghép sai.',
      sources: ['map', 'scan'], graph: 'linear',
      rows: cols({ trip: [[0, 1, 1], [1, 2, 2], [0, 3, 2], [3, 2, 1], [0, 2, 3], [2, 3, 1]] }) },
    { id: 'p2', kind: 'photo', title: 'Hai ảnh, một giao điểm', skill: 'Đối chiếu hai nguồn', stamp: 'P2 · 10:20',
      intro: 'Hai ảnh cận cùng một lần điểm danh. Một ảnh riêng lẻ không đủ để chốt.',
      sources: ['badge', 'book'], rows: cols({ badge: [0, 0, 1, 1, 0, 1], book: [1, 0, 0, 1, 1, 0] }),
      proof: { badge: [2, 3, 0], book: [2, 3] } },
    { id: 'r2', kind: 'route', title: 'Phải ghé phòng máy', skill: 'Đi vòng qua checkpoint', stamp: 'R2 · 09:40',
      intro: 'Bản ghi phòng máy xác nhận cả 5 hành trình thật đều ghé P giữa hai lượt quét.',
      sources: ['map', 'scan', 'checkpoint'], graph: 'linear', checkpoint: 2,
      rows: cols({ trip: [[0, 1, 5], [1, 3, 3], [2, 0, 3], [1, 0, 4], [3, 1, 3], [0, 3, 4]] }) },
    { id: 'p4', kind: 'photo', title: 'Ảnh chụp qua gương', skill: 'Đọc dấu nguồn của ảnh', stamp: 'P4 · 11:05',
      intro: 'Ba ảnh cận. Một ảnh được chụp qua gương tủ đồ, dấu nguồn có ghi.',
      sources: ['badge', 'book', 'ticket'], mirrored: ['ticket'], plate: { spot: 'mirror', at: [13, 8] },
      rows: cols({ badge: [1, 0, 1, 1, 0, 0], book: [0, 0, 0, 1, 0, 1], ticket: [1, 1, 0, 1, 0, 1] }),
      proof: { badge: [3, 2, 0], book: [3, 2], ticket: [2, 3] } },
    { id: 'r4', kind: 'route', title: 'Cửa thoát hiểm một chiều', skill: 'Chọn đường, tôn trọng cửa một chiều', stamp: 'R4 · 13:15',
      intro: 'Tầng này có thêm hành lang dài S–L và một cửa thoát hiểm chỉ mở từ Lớp ra Thư viện.',
      sources: ['map', 'scan', 'door'], graph: 'branched', plate: { spot: 'door', at: [1, 5] },
      rows: cols({ trip: [[3, 1, 2], [3, 0, 1], [1, 3, 3], [2, 1, 2], [0, 1, 2], [0, 3, 3]] }) },
    { id: 'x1', kind: 'timeline', title: 'Ảnh phòng máy lúc 09:04', skill: 'Ghép hành trình với ảnh có giờ', stamp: 'X1 · 09:04',
      intro: 'Sáu hồ sơ hành trình đều đi kịp. Nhưng có một ảnh toàn cảnh phòng máy lúc 09:04.',
      sources: ['map', 'scan', 'roomphoto'], graph: 'linear', photoAt: 4, photoNode: 2, plate: { spot: 'camera', at: [1, 5] },
      // trip: [from, startMinute, to, endMinute] in minutes after 09:00; badge 0 Sao, 1 Trăng
      rows: cols({ trip: [[0, 1, 3, 5], [3, 0, 2, 6], [0, 0, 1, 7], [3, 0, 2, 7], [0, 1, 3, 5], [0, 3, 3, 8]], badge: [1, 1, 1, 1, 0, 1] }),
      proof: { badge: [0, 3, 0] } }
  ];

  const graphs = { linear, branched };
  const edgesOf = c => graphs[c.graph] || linear;

  function counts(rows, key) {
    const out = fields[key].labels.map(() => 0);
    for (const r of rows) out[r[key]] += 1;
    return out;
  }

  function sameCounts(a, b) { return a.length === b.length && a.every((v, i) => v === b[i]); }

  // Earliest arrival on the corridor graph, with optional mandatory checkpoint node.
  function earliest(c, from, to) {
    const edges = edgesOf(c);
    const need = c.checkpoint;
    const start = [0, from, need === undefined || from === need];
    const best = new Map();
    const queue = [start];
    while (queue.length) {
      queue.sort((a, b) => a[0] - b[0]);
      const [t, n, passed] = queue.shift();
      const key = n + ':' + passed;
      if (best.has(key)) continue;
      best.set(key, t);
      if (n === to && passed) return t;
      for (const [a, b, w, one] of edges) {
        const steps = one ? [[a, b]] : [[a, b], [b, a]];
        for (const [u, v] of steps) if (u === n) queue.push([t + w, v, passed || v === need]);
      }
    }
    return Infinity;
  }

  function shortestFrom(c, from) {
    return nodes.map((_, to) => earliest({ graph: c.graph }, from, to));
  }

  // Can a timeline traveller be inside node P / outside it at minute t? Waiting allowed anywhere.
  function presence(c, row, t) {
    const [a, t0, b, t1] = row.trip;
    const d = (u, v) => earliest({ graph: c.graph }, u, v);
    const P = c.photoNode;
    if (d(a, b) > t1 - t0) return null;
    const canIn = d(a, P) <= t - t0 && d(P, b) <= t1 - t;
    let canOut = nodes.some((_, n) => n !== P && d(a, n) <= t - t0 && d(n, b) <= t1 - t);
    for (const [u, v, w] of edgesOf(c)) {
      for (const [s, e] of [[u, v], [v, u]]) {
        for (let dep = t0 + d(a, s); dep < t; dep++) if (dep + w > t && dep + w + d(e, b) <= t1) canOut = true;
      }
    }
    return { canIn, canOut };
  }

  // Candidates explained by ALL listed sources. Hidden answer is never stored: it is derived from sources.
  function candidates(c) {
    if (c.kind === 'photo') {
      return ids.filter(x => c.sources.every(k => sameCounts(counts(c.rows.filter(r => r.id !== x), k), c.proof[k])));
    }
    if (c.kind === 'route') return c.rows.filter(r => earliest(c, r.trip[0], r.trip[1]) > r.trip[2]).map(r => r.id);
    return ids.filter(x => {
      const rest = c.rows.filter(r => r.id !== x);
      const states = rest.map(r => presence(c, r, c.photoAt));
      if (states.some(s => s === null)) return false;
      const options = states.map(s => (s.canIn && s.canOut ? [true, false] : s.canIn ? [true] : s.canOut ? [false] : []));
      if (options.some(o => !o.length)) return false;
      const walk = (i, tally) => {
        if (i === rest.length) return sameCounts(tally, c.proof.badge);
        return options[i].some(inside => {
          const next = tally.slice();
          if (inside) next[rest[i].badge] += 1;
          return walk(i + 1, next);
        });
      };
      return walk(0, [0, 0, 0]);
    });
  }

  // What a seen photo shows. Mirrored arrows read reversed.
  function seenProof(c, key) {
    const p = c.proof[key];
    return (c.mirrored || []).includes(key) ? p.slice().reverse() : p.slice();
  }

  // The reason a correct submission must state, derived from data.
  function expectedReason(c, id) {
    if (c.kind === 'photo') {
      const out = {};
      for (const k of c.sources) {
        const total = counts(c.rows, k);
        out[k] = total.findIndex((v, i) => v !== c.proof[k][i]);
      }
      return out;
    }
    if (c.kind === 'route') {
      const row = c.rows.find(r => r.id === id);
      return { minutes: earliest(c, row.trip[0], row.trip[1]) };
    }
    const row = c.rows.find(r => r.id === id);
    const s = presence(c, row, c.photoAt);
    return { presence: s && s.canIn && !s.canOut ? 'must' : 'cannot', badge: row.badge };
  }

  function reasonFields(c) {
    if (c.kind === 'photo') return c.sources.map(k => ({ key: k, type: 'label', label: 'Ảnh ' + fields[k].name.toLowerCase() + ' cho thấy hồ sơ thừa mang', options: fields[k].labels }));
    if (c.kind === 'route') return [{ key: 'minutes', type: 'number', label: 'Hành trình đó cần ít nhất bao nhiêu phút?', min: 0, max: 30 }];
    return [
      { key: 'presence', type: 'choice', label: 'Lúc 09:04, hồ sơ đó', options: [['must', 'bắt buộc đang ở phòng máy'], ['cannot', 'không thể ở phòng máy']] },
      { key: 'badge', type: 'label', label: 'Huy hiệu của hồ sơ đó', options: fields.badge.labels }
    ];
  }

  // Judge: needs all sources earned, one candidate, the right record AND the right reason. No partial hints.
  function judge(c, earned, id, reason) {
    if (!c.sources.every(s => earned.includes(s))) return { status: 'insufficient', text: 'Còn nguồn chưa khám. Máy chưa nhận lập luận.' };
    if (!ids.includes(id)) return { status: 'invalid', text: 'Chọn một hồ sơ trước.' };
    const sol = candidates(c);
    if (sol.length !== 1) return { status: 'ambiguous', text: 'Nguồn không cho đúng một nghiệm.' };
    const exp = expectedReason(c, sol[0]);
    const reasonOk = reason && Object.keys(exp).every(k => String(reason[k]) === String(exp[k]));
    if (sol[0] === id && reasonOk) return { status: 'solved', text: 'Lập luận khớp mọi nguồn.' };
    return { status: 'retry', text: 'Lập luận chưa khớp. Máy không nói phần nào sai. Thử lại không mất gì.' };
  }

  // Observation check when collecting a source. Never asks about the answer's own row or path.
  function sourceCheck(c, key) {
    if (fields[key]) return { type: 'tally', key, labels: fields[key].labels, answer: seenProof(c, key), prompt: 'Ghi lại số vật mỗi loại bạn thấy trong ảnh.' };
    if (key === 'roomphoto') return { type: 'tally', key: 'badge', labels: fields.badge.labels, answer: c.proof.badge.slice(), prompt: 'Ghi lại số huy hiệu mỗi loại trong ảnh toàn cảnh.' };
    if (key === 'map') return { type: 'number', prompt: 'Đoạn Sảnh ↔ Phòng máy mất mấy phút?', answer: 2, min: 0, max: 9 };
    if (key === 'scan') {
      const sol = candidates(c)[0];
      const row = c.rows.find(r => r.id !== sol && r.id !== 'an') || c.rows[0];
      const minutes = c.kind === 'timeline' ? row.trip[3] - row.trip[1] : row.trip[2];
      return { type: 'number', prompt: 'Hồ sơ ' + nameOf(row.id) + ' có mấy phút giữa hai lượt quét?', answer: minutes, min: 0, max: 30 };
    }
    if (key === 'checkpoint') return { type: 'choice', prompt: 'Năm hành trình thật đều phải ghé khu nào?', options: nodes.map((n, i) => [String(i), n]), answer: '2' };
    if (key === 'door') return { type: 'choice', prompt: 'Cửa thoát hiểm cho đi theo chiều nào?', options: [['LT', 'Lớp → Thư viện'], ['TL', 'Thư viện → Lớp'], ['both', 'Cả hai chiều']], answer: 'LT' };
    return null;
  }

  function checkSource(check, value) {
    if (check.type === 'tally') return Array.isArray(value) && sameCounts(value.map(Number), check.answer);
    return String(value) === String(check.answer);
  }

  // Progress: in-memory only. Next case unlocks after a solved judge result.
  function createProgress() { return { unlocked: 0, solved: [] }; }
  function complete(progress, index, result) {
    if (!result || result.status !== 'solved' || index > progress.unlocked || index < 0 || index >= cases.length) return false;
    if (!progress.solved.includes(index)) progress.solved.push(index);
    progress.unlocked = Math.min(Math.max(progress.unlocked, index + 1), cases.length - 1);
    return true;
  }

  // Method cards: tarot suggests HOW to check. It never names a record or opens a source.
  const methods = {
    photo: { card: 'The Moon', glyph: '☾', text: 'Tách điều bạn đã đếm khỏi điều bạn đoán. Đếm lại bằng tay từng hồ sơ.' },
    route: { card: 'Wheel of Fortune', glyph: '☸', text: 'Thời gian chỉ chạy một chiều. Có thể chờ, không thể nhanh hơn đường ngắn nhất.' },
    p2: { card: 'Justice', glyph: '⚖', text: 'Một hồ sơ phải giải thích được mọi bảng cùng lúc, không chỉ một bảng.' },
    p4: { card: 'The Hermit', glyph: '✧', text: 'Hỏi ảnh được chụp thế nào trước khi tin điều nó cho thấy.' },
    r4: { card: 'The Chariot', glyph: '➶', text: 'Có đường nhanh hơn chưa chắc đi được theo cả hai chiều.' },
    x1: { card: 'Temperance', glyph: '⚗', text: 'Pha hai loại nguồn: ai bắt buộc ở đâu lúc đó, ai thì có thể.' }
  };
  const methodFor = c => methods[c.id] || methods[c.kind === 'photo' ? 'photo' : 'route'];

  return { profiles, detectives, roles, roleOfSpot, ownerOfSpot, ids, nameOf, fields, nodes, short, graphs, edgesOf, cases, counts, earliest, shortestFrom,
    presence, candidates, seenProof, expectedReason, reasonFields, judge, sourceCheck, checkSource,
    createProgress, complete, methodFor };
});
