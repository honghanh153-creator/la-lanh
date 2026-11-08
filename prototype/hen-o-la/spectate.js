// Khách quán: watch a matchmaking evening from the mezzanine, for the vibe. Pure rules for node tests.
// Guests cheer for shared moments only: never for, at or about one person. Nobody sees who chose whom.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Xem = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const SEATS = 40;
  // Seats taken when you arrive, and how a short queue moves when people leave.
  function arrive(rand) {
    const taken = 34 + Math.floor(rand() * 10); // 34..43
    return taken < SEATS ? { seated: true, free: SEATS - taken, ahead: 0 } : { seated: false, free: 0, ahead: taken - SEATS + 1 };
  }
  function queueStep(state) {
    if (state.seated) return state;
    const ahead = Math.max(0, state.ahead - 1);
    return ahead === 0 ? { seated: true, free: 0, ahead: 0 } : { seated: false, free: 0, ahead };
  }

  // The shared moments guests may watch. Private ones (duo rooms, tables, last drink, picks) are never shown.
  const MOMENTS = [
    { id: 'tudo', title: 'Tự do', text: 'Người hẹn đi lại, làm trò, đọc sách, vuốt mèo.', secs: 40 },
    { id: 'thaden', title: 'Thả đèn', text: 'Những đôi đèn bay lên mái quán. Không ai biết ai chọn ai.', secs: 22 },
    { id: 'taihien', title: 'Tái hiện', text: 'Cô Lá kể lại vụ án của tối nay cho cả quán.', secs: 22 }
  ];
  const PRIVATE = ['xoayban', 'thu', 'lycuoi', 'doi'];

  // Cheering is for the moment, never for a person: the function takes no target at all.
  const CHEERS = { votay: { label: 'Vỗ tay', icon: '👏' }, la: { label: 'Thả lá cổ vũ', icon: '🍃' } };
  function cheer(kind) { return CHEERS[kind] ? { kind, forMoment: true } : null; }

  // Cô Lá's notebook: kind moments told without saying who. No names, no looks, no numbers.
  const HOST_NOTES = [
    'Có người hỏi đúng về cuốn sách người kia mang theo, thế là hai người nói chuyện mãi.',
    'Có hai người cùng chọn gừng cho ly chung, rồi cùng cười vì ly cay quá.',
    'Có người lỡ đổ nước tưới cây, người bên cạnh lấy khăn lau giúp, không nói gì.',
    'Có người kể chuyện con mèo nhà mình, cả bàn kể tiếp chuyện mèo nhà ai cũng có.',
    'Có người ngại nói nên vẫy tay trước, người kia vẫy lại ngay.',
    'Có người hỏi "hôm nay bạn mệt không", người kia nói đó là câu dễ chịu nhất trong tuần.',
    'Có hai người đếm sai cùng một chỗ, rồi đếm lại cùng nhau và cười.'
  ];
  function hostNotes(rand, n) {
    const pool = HOST_NOTES.slice(), out = [];
    while (out.length < (n || 3) && pool.length) out.push(pool.splice(Math.floor(rand() * pool.length), 1)[0]);
    return out;
  }

  // How many pairs of lanterns rise. Only a count, never who.
  function lanternPairs(rand) { return 1 + Math.floor(rand() * 3); }

  return { SEATS, arrive, queueStep, MOMENTS, PRIVATE, CHEERS, cheer, HOST_NOTES, hostNotes, lanternPairs };
});
