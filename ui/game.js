export function game(mines, opening) {
  const key = (r, c) => `${r},${c}`;
  const bombs = new Set(mines.map(([r,c]) => key(r,c)));
  const opened = new Set();
  const moves = [];
  let status = 'playing';
  const neighbors = (r,c) => {
    const result = [];
    for (let rr = Math.max(0,r-1); rr <= Math.min(4,r+1); rr++)
      for (let cc = Math.max(0,c-1); cc <= Math.min(4,c+1); cc++)
        if (rr !== r || cc !== c) result.push([rr,cc]);
    return result;
  };
  const clue = (r,c) => neighbors(r,c).filter(([rr,cc]) => bombs.has(key(rr,cc))).length;
  function reveal(r,c, record = true) {
    if (status !== 'playing' || r < 0 || r > 4 || c < 0 || c > 4 || opened.has(key(r,c))) throw new Error('Invalid reveal');
    if (record) moves.push({row:r,col:c});
    if (bombs.has(key(r,c))) { status = 'lost'; return; }
    const pending = [[r,c]];
    while (pending.length) {
      const [rr,cc] = pending.pop(), cell = key(rr,cc);
      if (opened.has(cell)) continue;
      opened.add(cell);
      if (clue(rr,cc) === 0) pending.push(...neighbors(rr,cc).filter(([y,x]) => !opened.has(key(y,x)) && !bombs.has(key(y,x))));
    }
    if (opened.size === 21) status = 'won';
  }
  reveal(...opening, false);
  return {reveal, moves, get status() { return status; }, cell(r,c) { return opened.has(key(r,c)) ? clue(r,c) : null; }};
}
