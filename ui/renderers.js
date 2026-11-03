import {h} from './kit/components.js';
import {game} from './game.js';

function play(value, {verdict, send}) {
  if (!verdict || !verdict.valid) return h('p', {text: verdict?.message || 'Game verification is unavailable.'});
  const state = game(verdict.details.mines, verdict.details.opening);
  const root = h('section');
  function draw() {
    const cells = [];
    for (let r=0; r<5; r++) for (let c=0; c<5; c++) {
      const clue = state.cell(r,c);
      cells.push(h('button', {class: clue === null ? 'cell covered' : 'cell open', text: clue === null ? '' : String(clue),
        'aria-label': `Row ${r+1}, column ${c+1}: ${clue === null ? 'covered' : clue}`,
        disabled: clue !== null || state.status !== 'playing', onclick: () => {state.reveal(r,c); draw();}}));
    }
    root.replaceChildren(h('h2', {text:'Your game'}), h('p', {text: state.status === 'playing' ? 'Reveal the safe cells. The automated opponent has finished its game.' : state.status === 'won' ? 'You cleared the board.' : 'You hit a mine.'}), h('div', {class:'board'}, cells),
      ...(state.status === 'playing' ? [] : [h('button', {text:'Compare results', onclick: () => send(`Run compare-scores with game_id ${JSON.stringify(value.game_id)} and human history ${JSON.stringify(state.moves)}.`)})]));
  }
  draw();
  return root;
}

function player(title, value) {
  const symbols = {covered:'', mine:'✹', hit:'✹'};
  return h('section', {}, [h('h3', {text:title}), h('div', {class:'board'}, value.board.flat().map(cell => h('div', {class:`cell ${cell === 'covered' ? 'covered' : cell === 'hit' ? 'hit' : 'open'}`, text: symbols[cell] ?? cell}))),
    h('p', {text: value.status === 'won' ? 'Won' : 'Hit a mine'}), h('p', {text:`Safe cells revealed: ${value.game_score}`}),
    h('p', {text:`Optimal moves: ${value.optimal_moves} / ${value.decisions} (${value.decisions ? (100 * value.optimal_moves / value.decisions).toFixed(1) + '%' : 'N/A'})`})]);
}
function compare(value, {verdict}) {
  if (!verdict || !verdict.valid) return h('p', {text:verdict?.message || 'Comparison verification is unavailable.'});
  const label = x => ({human:'Human wins', ai:'Opponent wins', tie:'Tie', 'N/A':'N/A'})[x];
  return h('section', {}, [h('h2', {text:'Verified results'}), h('div', {class:'players'}, [player('Human',value.human), player('Opponent',value.ai)]), h('p', {text:`Game score: ${label(value.game_comparison)}`}), h('p', {text:`Move accuracy: ${label(value.accuracy_comparison)}`})]);
}
export default {PlayOutput: play, CompareOutput: compare};
