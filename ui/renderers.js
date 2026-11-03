import {h} from './kit/components.js';
import {game} from './game.js';

function playAgain(send) {
  return h('button', {type: 'button', class: 'button', text: 'Play again', onclick: () => send('Play the game again. Start a fresh round.')});
}

function play(value, {verdict, send}) {
  if (!verdict || !verdict.valid) return h('p', {text: verdict?.message || 'Game verification is unavailable.'});
  const state = game(verdict.details.mines, verdict.details.opening);
  const root = h('section');
  function compareRound() {
    const args = {game_id: value.game_id, history: state.moves};
    send(`Run compare-scores with ${JSON.stringify(args)}. Copy these arguments exactly.`);
  }
  function draw() {
    const cells = [];
    for (let r=0; r<5; r++) for (let c=0; c<5; c++) {
      const clue = state.cell(r,c);
      cells.push(h('button', {class: clue === null ? 'cell covered' : 'cell open', text: clue === null ? '' : String(clue),
        'aria-label': `Row ${r+1}, column ${c+1}: ${clue === null ? 'covered' : clue}`,
        disabled: clue !== null || state.status !== 'playing', onclick: () => {state.reveal(r,c); draw();}}));
    }
    const actions = state.status === 'playing' ? null : h('div', {class: 'game-actions'},
      value.game_id.startsWith('round-')
        ? h('button', {type: 'button', class: 'button', text: 'Compare results', onclick: compareRound})
        : h('p', {text: 'Start a new round to compare scores with this version.'}),
      playAgain(send));
    root.replaceChildren(h('h2', {text:'Your game'}), h('p', {text: state.status === 'playing' ? 'Reveal the safe cells. The AI has finished its round.' : state.status === 'won' ? 'You cleared the board.' : 'You hit a mine.'}), h('div', {class:'board'}, cells),
      actions);
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
function compare(value, {verdict, send}) {
  if (!verdict || !verdict.valid) return h('p', {text:verdict?.message || 'Comparison verification is unavailable.'});
  const label = x => ({human:'Human wins', ai:'Opponent wins', tie:'Tie', 'N/A':'N/A'})[x];
  return h('section', {}, [h('h2', {text:'Verified results'}), h('div', {class:'players'}, [player('Human',value.human), player('Opponent',value.ai)]), h('p', {text:`Game score: ${label(value.game_comparison)}`}), h('p', {text:`Move accuracy: ${label(value.accuracy_comparison)}`}), playAgain(send)]);
}
export default {PlayOutput: play, CompareOutput: compare};
