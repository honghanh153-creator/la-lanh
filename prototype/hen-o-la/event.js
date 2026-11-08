// Hẹn ở Lá: the rules of one matchmaking evening, kept pure so node tests can check them.
// Everyone here is a fictional adult. Nothing is stored or sent anywhere.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Hen = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  // Small seeded RNG so a given evening replays the same way.
  function rng(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function shuffle(list, rand) {
    const a = list.slice();
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    return a;
  }

  const PHASES = [
    { id: 'loivao', label: 'Lối vào' },
    { id: 'tudo', n: 1, label: 'Tự do' },
    { id: 'xoayban', n: 2, label: 'Xoay bàn' },
    { id: 'thu', n: 3, label: 'Thư giữa giờ' },
    { id: 'thaden', n: 4, label: 'Thả đèn' },
    { id: 'lycuoi', n: 5, label: 'Ly cuối' },
    { id: 'het', label: 'Hết buổi' }
  ];

  const LANTERNS = {
    thuong: { icon: '🌸', label: 'tìm người thương' },
    ban: { icon: '🍃', label: 'tìm bạn' },
    choi: { icon: '☕', label: 'ghé chơi cho vui' }
  };

  // Things you can do. Acts with `at` need you to stand by that kind of spot (World.SPOTS[..].act).
  const ACTS = {
    nhay: { label: 'Nhảy', verb: 'nhảy một điệu giữa quán', icon: '💃' },
    mathe: { label: 'Làm mặt hề', verb: 'làm mặt hề', icon: '🤪' },
    ngugat: { label: 'Ngủ gật', verb: 'ngủ gật', icon: '💤' },
    vaytay: { label: 'Vẫy tay', verb: 'vẫy tay chào cả quán', icon: '👋' },
    chaptay: { label: 'Chắp tay', verb: 'chắp tay chào', icon: '🙏' },
    docsach: { label: 'Đọc sách', verb: 'đọc sách ở kệ', icon: '📖', at: true },
    tuoicay: { label: 'Tưới cây', verb: 'tưới cây', icon: '🪴', at: true },
    vuotmeo: { label: 'Vuốt mèo', verb: 'vuốt mèo Mướp', icon: '🐈', at: true },
    ngammua: { label: 'Ngắm mưa', verb: 'ngắm mưa bên cửa sổ', icon: '🌧', at: true },
    danhdan: { label: 'Đánh đàn', verb: 'đánh đàn', icon: '🎵', at: true },
    goido: { label: 'Gọi đồ uống', verb: 'gọi đồ uống ở quầy', icon: '🧋', at: true },
    // place acts: they happen at a window bench, the reading nook, beside Bơ the dog, or with a drink in hand
    uong: { label: 'Uống một ngụm', verb: 'nhâm nhi ly của mình', icon: '☕', place: true },
    cuaso: { label: 'Ngồi cạnh cửa sổ', verb: 'ngồi cạnh cửa sổ', icon: '🪟', place: true },
    nam: { label: 'Nằm đọc sách', verb: 'nằm đọc sách ở góc gối lười', icon: '📚', place: true },
    vuotcho: { label: 'Chơi với Bơ', verb: 'chơi với chó Bơ', icon: '🐶', place: true },
    ngoi: { label: 'Ngồi vào bàn', verb: 'ngồi vào bàn', icon: '🪑', place: true },
    layra: { label: 'Lấy đồ ra', verb: 'bày đồ mang theo lên bàn', icon: '🎒', place: true },
    catdo: { label: 'Cất đồ', verb: 'cất đồ', icon: '👜', place: true }
  };
  const FREE_ACTS = Object.keys(ACTS).filter(k => !ACTS[k].at && !ACTS[k].place);
  const PLACE_ACTS = Object.keys(ACTS).filter(k => ACTS[k].place);
  // What a guest says when they turn to you. Short, no questions about where you live or how to reach you.
  // What someone's carried item looks like when they take it out on a table (Room.tableThing kinds).
  const ITEM_THINGS = [[/sổ/, 'sove'], [/máy ảnh/, 'mayanh'], [/len/, 'len'], [/sách/, 'sach'], [/tai nghe/, 'tainghe'], [/bánh/, 'banh'], [/xương rồng/, 'xuongrong'], [/ukulele|đàn/, 'ukulele'], [/diều/, 'dieu']];
  function itemThing(item) { const hit = ITEM_THINGS.find(([re]) => re.test(String(item || ''))); return hit ? hit[1] : 'sach'; }
  const OPENERS = ['Bạn cũng thích nghe mưa hả?', 'Hồi nãy thấy bạn vui ghê.', 'Bạn mang theo gì vậy?', 'Quán này ấm ha?', 'Bạn thích uống gì nhất?', 'Bơ có vẻ quý bạn đó.'];
  // A guest's short reply when you say something that is not a question.
  const REACTIONS = ['Haha thật hả?', 'Mình cũng vậy nè.', 'Ồ, hay ghê.', 'Kể thêm đi!', 'Nghe dễ thương ghê.', '🙂'];

  const INGREDIENTS = {
    caphe: 'Cà phê', sua: 'Sữa đặc', gung: 'Gừng', trala: 'Trà lài',
    muoi: 'Kem muối', dua: 'Cốt dừa', cam: 'Vỏ cam', que: 'Quế'
  };
  function drinkName(a, b) {
    if (a === b) return INGREDIENTS[a] + ' gấp đôi';
    return INGREDIENTS[a] + ' ' + INGREDIENTS[b].toLowerCase();
  }

  const QUESTIONS = [
    'Lần gần nhất bạn cười tới chảy nước mắt là vì gì?',
    'Một nơi bạn muốn quay lại khi trời mưa?',
    'Món ăn nào làm bạn nhớ nhà?',
    'Được nghỉ một ngày bất ngờ, bạn làm gì đầu tiên?',
    'Bài hát bạn hay hát khi không ai nghe?',
    'Điều nhỏ nhất làm bạn vui tuần này?'
  ];

  // Lock-and-key, Lá style: everyone holds half a tarot card. Cards set a topic, never a prediction.
  const TAROT = [
    { card: 'The Star', q: 'Điều bạn đang âm thầm hy vọng là gì?' },
    { card: 'The Sun', q: 'Kể một chuyện làm bạn cười cả ngày.' },
    { card: 'The Moon', q: 'Một giấc mơ lạ bạn còn nhớ?' },
    { card: 'Temperance', q: 'Bạn thường làm gì để bình tĩnh lại?' },
    { card: 'Strength', q: 'Một lần bạn dũng cảm theo kiểu nhỏ xíu?' },
    { card: 'Wheel of Fortune', q: 'Một ngã rẽ tình cờ hoá ra hay ho?' }
  ];

  const ADJECTIVES = ['dễ thương ghê', 'vui lây', 'bình yên lạ', 'muốn làm quen'];

  // Nine fictional guests. look feeds Engine.buildSheet from game lab 14.
  const GUESTS = [
    { id: 'me', name: 'Lá Me', item: 'sổ vẽ', lantern: 'thuong', does: ['docsach', 'ngammua', 'vuotmeo', 'cuaso'], loves: ['danhdan', 'tuoicay', 'mathe', 'nam'], taste: ['trala', 'dua', 'cam'],
      look: { H: '#3b2420', T: '#c0605a', C: '#ef9a8a', P: '#3a3550', B: '#1d1b26', longHair: true },
      idle: ['Mưa thế này hợp vẽ tranh ghê.', 'Mèo Mướp ngủ giỏi hơn mình.', 'Có ai vẽ cùng không?'],
      answer: ['Chắc là hôm mình vẽ con mèo mà ra con heo.', 'Mình nghĩ hoài mới ra… chắc là chiều mưa ở Hội An.'],
      last: ['Hôm nay vui thật đó.', 'Lần sau mình vẽ bạn nha, vẽ xấu thôi.'] },
    { id: 'phong', name: 'Lá Phong', item: 'máy ảnh film', lantern: 'thuong', does: ['ngammua', 'nhay', 'goido'], loves: ['docsach', 'vuotmeo', 'ngammua'], taste: ['caphe', 'muoi', 'que'],
      look: { H: '#1f1c1c', T: '#c08a2a', C: '#e3b23c', P: '#2e3a5c', B: '#1d1b26', glasses: true },
      idle: ['Ánh đèn quán này chụp film đẹp lắm.', 'Còn đúng ba kiểu phim thôi.', 'Ai đứng yên cho mình chụp với?'],
      answer: ['Hôm mình chụp nhầm ngón tay cả cuộn phim.', 'Một quán nhỏ ở Đà Lạt, mưa mà ấm.'],
      last: ['Mình chưa kịp chụp bạn, tiếc ghê.', 'Ngồi đây nghe mưa thêm chút nữa nhé.'] },
    { id: 'sen', name: 'Lá Sen', item: 'khăn len', lantern: 'ban', does: ['tuoicay', 'vuotmeo', 'ngugat', 'nam'], loves: ['tuoicay', 'ngugat', 'vaytay', 'vuotcho'], taste: ['trala', 'gung', 'sua'],
      look: { H: '#4a3028', T: '#3d9a96', C: '#3d9a96', P: '#2f2f38', B: '#1d1b26', longHair: true },
      idle: ['Cây này cần nắng hơn một chút.', 'Đan xong cái khăn là hết mùa lạnh mất.', 'Ngủ gật ở quán cũng là một kỹ năng.'],
      answer: ['Đan sai một mũi mà ra hình trái tim.', 'Một ly trà gừng lúc mất điện.'],
      last: ['Mai mình mang khăn cho bạn xem.', 'Ngồi im thế này cũng vui.'] },
    { id: 'tre', name: 'Lá Tre', item: 'đàn ukulele', lantern: 'thuong', does: ['danhdan', 'nhay', 'mathe', 'vuotcho'], loves: ['nhay', 'mathe', 'danhdan'], taste: ['caphe', 'sua', 'dua'],
      look: { H: '#26201c', T: '#3f6b55', C: '#7fc8a0', P: '#30303a', B: '#1d1b26', hat: true },
      idle: ['Ai biết hợp âm Đô trưởng không?', 'Đàn hơi lạc dây nhưng tim không lạc.', 'Nhảy chung đi, ngại gì!'],
      answer: ['Mình hát sai lời trước cả lớp, cả lớp hát theo.', 'Cơm mẹ nấu, nghĩ tới là đói.'],
      last: ['Bài vừa nãy là mình chế đó.', 'Lần sau mình đàn bạn hát nhé.'] },
    { id: 'lot', name: 'Lá Lốt', item: 'hộp bánh', lantern: 'choi', does: ['goido', 'vaytay', 'nhay', 'uong'], loves: ['goido', 'vaytay', 'nhay', 'vuotcho'], taste: ['sua', 'dua', 'cam'],
      look: { H: '#211d24', T: '#c0605a', C: '#f2b45a', P: '#3a3550', B: '#1d1b26' },
      idle: ['Ai ăn bánh bông lan không?', 'Mình tới vì nghe nói quán có mèo.', 'Ly này ngọt vừa ghê.'],
      answer: ['Lần mình làm bánh quên bỏ đường.', 'Ly sữa nóng lúc ba giờ sáng.'],
      last: ['Còn hai miếng bánh, chia nhau nhé.', 'Vui ghê, lần sau mình lại ghé.'] },
    { id: 'che', name: 'Lá Chè', item: 'cuốn sách cũ', lantern: 'thuong', does: ['docsach', 'ngugat', 'tuoicay', 'nam'], loves: ['docsach', 'ngammua', 'danhdan', 'cuaso'], taste: ['trala', 'gung', 'que'],
      look: { H: '#2b2230', T: '#6a4fa0', C: '#a995d8', P: '#2f2f38', B: '#1d1b26', longHair: true, glasses: true },
      idle: ['Trang này có người gạch chân trước mình.', 'Đọc tới đoạn hay thì mưa tạnh.', 'Bạn đang đọc gì vậy?'],
      answer: ['Một câu thơ dở tới mức buồn cười.', 'Thư viện cũ ở quê, mùi giấy ẩm.'],
      last: ['Mình cho bạn mượn cuốn này nhé.', 'Nói chuyện với bạn dễ chịu thật.'] },
    { id: 'bang', name: 'Lá Bàng', item: 'diều giấy', lantern: 'ban', does: ['nhay', 'vaytay', 'vuotmeo', 'vuotcho'], loves: ['mathe', 'vuotmeo', 'nhay', 'vuotcho'], taste: ['caphe', 'cam', 'muoi'],
      look: { H: '#3a2a22', T: '#3f6b55', C: '#4f8a6b', P: '#2f3b4a', B: '#1d1b26', hat: true },
      idle: ['Mưa thế này thả diều hơi khó.', 'Con mèo nhìn mình như chủ nợ.', 'Có ai chơi oẳn tù tì không?'],
      answer: ['Diều mắc lên cây, mình leo lên rồi kẹt luôn.', 'Bánh tráng nướng đầu hẻm.'],
      last: ['Cuối tuần đi thả diều không?', 'Vui thiệt, kết bạn nha.'] },
    { id: 'oi', name: 'Lá Ổi', item: 'chậu xương rồng', lantern: 'thuong', does: ['tuoicay', 'mathe', 'goido'], loves: ['tuoicay', 'docsach', 'goido'], taste: ['gung', 'dua', 'muoi'],
      look: { H: '#3b2420', T: '#c08a2a', C: '#ef7b6a', P: '#26252b', B: '#1d1b26', longHair: true },
      idle: ['Xương rồng của mình tên là Gai.', 'Tưới ít thôi, nó dễ dỗi.', 'Bạn có nuôi cây không?'],
      answer: ['Cây chết mà mình vẫn tưới thêm một tuần.', 'Gỏi cuốn của bà ngoại.'],
      last: ['Gai gửi lời chào bạn.', 'Hôm nay nhẹ lòng ghê.'] },
    { id: 'duala', name: 'Lá Dứa', item: 'tai nghe', lantern: 'thuong', does: ['ngammua', 'danhdan', 'ngugat', 'cuaso'], loves: ['ngammua', 'danhdan', 'ngugat', 'cuaso'], taste: ['muoi', 'caphe', 'que'],
      look: { H: '#1f1c1c', T: '#3f6b55', C: '#9fd3bd', P: '#30303a', B: '#1d1b26' },
      idle: ['Tiếng mưa nghe hay hơn playlist.', 'Đàn này còn phím La bị kẹt.', 'Mình hay ngồi một mình, hôm nay thử khác.'],
      answer: ['Bài hát chế về con mèo nhà hàng xóm.', 'Một bến xe lúc mưa, chả hiểu sao.'],
      last: ['Bạn nghe thử bài này không?', 'Mình ít nói, nhưng hôm nay vui.'] }
  ];

  const NICKNAMES = ['Lá Mít', 'Lá Hẹ', 'Lá Trầu', 'Lá Sung'];
  const ITEMS = ['sổ tay', 'máy ảnh film', 'hộp bánh', 'cuốn sách cũ', 'đàn ukulele', 'cây xương rồng', 'khăn len'];
  const LOOKS = [
    { H: '#3a2a22', T: '#3f6b55', C: '#4f8a6b', P: '#2f3b4a', B: '#1d1b26', hat: true },
    { H: '#3b2420', T: '#c0605a', C: '#ef9a8a', P: '#3a3550', B: '#1d1b26', longHair: true },
    { H: '#1f1c1c', T: '#c08a2a', C: '#e3b23c', P: '#2e3a5c', B: '#1d1b26', glasses: true },
    { H: '#2b2230', T: '#6a4fa0', C: '#a995d8', P: '#2f2f38', B: '#1d1b26', longHair: true }
  ];

  // Circle-method round robin. Nobody meets the same person twice; with an odd count one sits out.
  function rotation(ids, rounds) {
    const arr = ids.slice();
    if (arr.length % 2) arr.push(null);
    const n = arr.length, out = [];
    for (let r = 0; r < Math.min(rounds, n - 1); r++) {
      const pairs = [];
      for (let i = 0; i < n / 2; i++) if (arr[i] !== null && arr[n - 1 - i] !== null) pairs.push([arr[i], arr[n - 1 - i]]);
      out.push(pairs);
      arr.splice(1, 0, arr.pop());
    }
    return out;
  }

  function sanitizeBubble(text, max) {
    const clean = String(text == null ? '' : text).replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/\s+/g, ' ').trim();
    return Array.from(clean).slice(0, max || 40).join('');
  }

  function guest(id) { return GUESTS.find(g => g.id === id) || null; }

  // One evening. `you` is the player's chosen nickname, look, item and lantern.
  function createEvening(seed, you) {
    const rand = rng(seed);
    const people = [Object.assign({ id: 'you', npc: false }, you)].concat(shuffle(GUESTS, rand).map(g => Object.assign({ npc: true }, g)));
    const ids = people.map(p => p.id);
    const aff = {}, seen = {};
    for (const a of ids) { aff[a] = {}; seen[a] = {}; for (const b of ids) if (a !== b) { aff[a][b] = 0; seen[a][b] = new Set(); } }
    const deck = shuffle(TAROT, rand), order = shuffle(ids, rand), halves = {};
    for (let i = 0; i + 1 < order.length; i += 2) {
      const t = deck[(i / 2) % deck.length];
      halves[order[i]] = { card: t.card, q: t.q, side: 'trái', mate: order[i + 1] };
      halves[order[i + 1]] = { card: t.card, q: t.q, side: 'phải', mate: order[i] };
    }
    return {
      seed, rand, people, ids, aff, seen, halves,
      tarotFound: new Set(), waved: new Set(),
      leaves: Object.fromEntries(ids.map(id => [id, 0])), leafSent: Object.fromEntries(ids.map(id => [id, new Set()])),
      letters: Object.fromEntries(ids.map(id => [id, []])), letterSent: Object.fromEntries(ids.map(id => [id, new Set()])),
      rounds: rotation(ids, 4)
    };
  }
  function person(ev, id) { return ev.people.find(p => p.id === id) || null; }
  function bump(ev, from, to, by) { if (from !== to && person(ev, from).npc) ev.aff[from][to] += by; }

  // viewer saw actor doing act. First sight of each act counts; a loved act counts more.
  function observe(ev, viewer, actor, act) {
    if (viewer === actor || !ACTS[act]) return false;
    const s = ev.seen[viewer][actor];
    if (s.has(act)) return false;
    s.add(act);
    const v = person(ev, viewer);
    if (v.npc) bump(ev, viewer, actor, v.loves.includes(act) ? 2 : 0.5);
    return true;
  }

  function wave(ev, from, to) {
    const k = from + '>' + to;
    if (ev.waved.has(k)) return false;
    ev.waved.add(k);
    bump(ev, to, from, 0.5);
    return true;
  }

  // Asking someone for their half card. A match is a shared topic, not a match of people.
  function compareHalves(ev, a, b) {
    const ha = ev.halves[a], hb = ev.halves[b];
    if (!ha || !hb || ha.mate !== b) return { match: false, card: hb ? hb.card : null };
    const key = [a, b].sort().join('+');
    const first = !ev.tarotFound.has(key);
    if (first) { ev.tarotFound.add(key); bump(ev, a, b, 1.5); bump(ev, b, a, 1.5); }
    return { match: true, first, card: ha.card, q: ha.q };
  }

  // Anonymous leaf. It never changes how anyone feels about the sender, because nobody knows who sent it.
  const LEAF_LIMIT = 5;
  function dropLeaf(ev, from, to) {
    if (from === to || ev.leafSent[from].has(to) || ev.leafSent[from].size >= LEAF_LIMIT) return false;
    ev.leafSent[from].add(to);
    ev.leaves[to] += 1;
    return true;
  }
  function npcLeafTargets(ev, id) {
    return ev.ids.filter(o => o !== id && ev.aff[id][o] >= 4 && !ev.leafSent[id].has(o));
  }

  // One table round between a and b. Each picks an ingredient; answered = they talked about the card.
  function tableRound(ev, a, b, ingA, ingB, answeredA, answeredB) {
    for (const [self, other, otherIng, otherAnswered, ownIng] of [[a, b, ingB, answeredB, ingA], [b, a, ingA, answeredA, ingB]]) {
      const p = person(ev, self);
      if (!p.npc) continue;
      if (p.taste.includes(otherIng)) bump(ev, self, other, 2);
      if (otherIng === ownIng) bump(ev, self, other, 1);
      if (otherAnswered) bump(ev, self, other, 1);
    }
    return drinkName(ingA, ingB);
  }
  function npcIngredient(ev, id, offered) {
    const p = person(ev, id);
    return offered.find(i => p.taste.includes(i)) || offered[0];
  }

  // Mid-event letters: compliment one thing you actually saw. The sender is never stored with the letter.
  const LETTER_LIMIT = 3;
  function writeLetter(ev, from, to, act, adj) {
    if (from === to || !ev.seen[from][to] || !ev.seen[from][to].has(act)) return false;
    if (ev.letterSent[from].has(to) || ev.letterSent[from].size >= LETTER_LIMIT) return false;
    ev.letterSent[from].add(to);
    ev.letters[to].push({ act, adj: ADJECTIVES.includes(adj) ? adj : ADJECTIVES[0] });
    return true;
  }
  function letterText(l) { return 'Có người thấy bạn ' + ACTS[l.act].verb + ', và thấy ' + l.adj + '.'; }
  function npcLetters(ev) {
    for (const p of ev.people) {
      if (!p.npc) continue;
      const targets = ev.ids.filter(o => o !== p.id && ev.seen[p.id][o].size).sort((x, y) => ev.aff[p.id][y] - ev.aff[p.id][x]).slice(0, 2);
      for (const t of targets) {
        const acts = [...ev.seen[p.id][t]];
        const act = acts.find(a => p.loves.includes(a)) || acts[0];
        writeLetter(ev, p.id, t, act, p.loves.includes(act) ? 'dễ thương ghê' : 'vui lây');
      }
    }
  }

  // Final lantern vote: up to three, in order. Guests who came "ghé chơi" need a stronger pull.
  function npcPicks(ev, id) {
    const p = person(ev, id), need = p.lantern === 'choi' ? 5 : 3;
    return ev.ids.filter(o => o !== id && ev.aff[id][o] >= need).sort((x, y) => ev.aff[id][y] - ev.aff[id][x] || (x < y ? -1 : 1)).slice(0, 3);
  }
  // Mutual picks become pairs; each person ends in at most one pair, best combined rank first.
  function couples(ev, picks) {
    const mutual = [];
    for (let i = 0; i < ev.ids.length; i++) for (let j = i + 1; j < ev.ids.length; j++) {
      const a = ev.ids[i], b = ev.ids[j];
      const ra = (picks[a] || []).indexOf(b), rb = (picks[b] || []).indexOf(a);
      if (ra >= 0 && rb >= 0) mutual.push({ a, b, score: ra + rb, best: Math.min(ra, rb) });
    }
    mutual.sort((x, y) => x.score - y.score || x.best - y.best || (x.a + x.b < y.a + y.b ? -1 : 1));
    const taken = new Set(), out = [];
    for (const m of mutual) {
      if (taken.has(m.a) || taken.has(m.b)) continue;
      taken.add(m.a); taken.add(m.b);
      const both = person(ev, m.a).lantern === 'thuong' && person(ev, m.b).lantern === 'thuong';
      out.push({ a: m.a, b: m.b, kind: both ? 'hen' : 'ban' });
    }
    return out;
  }

  return { itemThing, rng, shuffle, PHASES, LANTERNS, ACTS, FREE_ACTS, PLACE_ACTS, OPENERS, REACTIONS, INGREDIENTS, drinkName, QUESTIONS, TAROT, ADJECTIVES, GUESTS, NICKNAMES, ITEMS, LOOKS,
    rotation, sanitizeBubble, guest, createEvening, person, observe, wave, compareHalves, LEAF_LIMIT, dropLeaf, npcLeafTargets,
    tableRound, npcIngredient, LETTER_LIMIT, writeLetter, letterText, npcLetters, npcPicks, couples };
});
