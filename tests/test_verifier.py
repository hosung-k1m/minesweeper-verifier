import json
import subprocess
from dataclasses import replace
from pathlib import Path
import pytest
from contract import GameInput, RevealInput, TurnInput, CompareInput, Move, PlayInput
from plugin import get_board, reveal_cell, play_turn, play_game, compare_scores
from verifier import verify_input, verify_output, verify_task
from verifier.checks import initial, replay, risks, visible, MINES, OPENING


def test_tools_and_task_reject_forgery(tmp_path):
    game = GameInput('test')
    board = get_board(game, tmp_path)
    assert verify_output('get_board', game, board, tmp_path)['valid']
    assert not verify_output('get_board', game, replace(board, board=[[9]*5]*5), tmp_path)['valid']
    assert not verify_input('reveal_cell', RevealInput('test', 5, 0))['valid']
    move = RevealInput('test', 0, 3)
    board = reveal_cell(move, tmp_path)
    assert board.status == 'lost'
    assert verify_output('reveal_cell', move, board, tmp_path)['valid']
    with pytest.raises(ValueError):
        reveal_cell(RevealInput('test', 1, 1), tmp_path)
    human = CompareInput('test', [Move(0, 3)], board.history)
    compared = compare_scores(human, tmp_path)
    assert verify_output('compare_scores', human, compared, tmp_path)['valid']
    assert not verify_task('compare-scores', human, replace(compared, game_comparison='ai'), None, tmp_path)['valid']
    assert not verify_task('compare-scores', replace(human, ai_history=[]), compared, None, tmp_path)['valid']
    with pytest.raises(ValueError):
        compare_scores(replace(human, history=[]), tmp_path)


def test_board_responses_verify_after_later_reveals(tmp_path):
    game = GameInput('game_002')
    opening = get_board(game, tmp_path)
    moves = [RevealInput(game.game_id, row, col) for row, col in [(1, 3), (2, 3), (3, 3), (4, 2)]]
    responses = [reveal_cell(move, tmp_path) for move in moves]

    assert verify_output('get_board', game, opening, tmp_path)['valid']
    for move, board in zip(moves, responses):
        assert verify_output('reveal_cell', move, board, tmp_path)['valid']

    board = responses[2]
    assert not verify_output('reveal_cell', moves[1], board, tmp_path)['valid']
    assert not verify_output('reveal_cell', moves[2], replace(board, status='won'), tmp_path)['valid']
    reordered = visible(game.game_id, [board.history[1], board.history[0], board.history[2]])
    assert not verify_output('reveal_cell', moves[2], reordered, tmp_path)['valid']


def test_every_guess_finishes_in_two_turn_calls(tmp_path):
    start = TurnInput('probe', None)
    opening = play_turn(start, tmp_path)
    assert opening.status == 'playing'
    opened, _, _, optimal = replay(opening.history, grade=True)
    assert optimal == len(opening.history)
    assert all(count > 0 for count in risks(opened).values())

    for row, col in sorted(risks(opened)):
        game = GameInput(f'guess-{row}-{col}')
        start = TurnInput(game.game_id, None)
        opening = play_turn(start, tmp_path)
        guess = TurnInput(game.game_id, Move(row, col))
        final = play_turn(guess, tmp_path)
        assert final.status == ('lost' if (row, col) in MINES else 'won')
        assert verify_output('play_turn', start, opening, tmp_path)['valid']
        assert verify_output('play_turn', guess, final, tmp_path)['valid']
        assert not verify_output('play_turn', guess, opening, tmp_path)['valid']
        assert not verify_output('play_turn', start, final, tmp_path)['valid']


def test_play_game_allocates_and_verifies_complete_games(tmp_path):
    request = PlayInput([8, 13, 18, 14, 22, 23, 4, 19, 3, 9, 17, 24])
    other = PlayInput([3, *[cell for cell in request.order if cell != 3]])
    assert not verify_input('play_game', PlayInput(request.order[:-1]))['valid']
    get_board(GameInput('game-001'), tmp_path)
    first = play_game(request, tmp_path)
    second = play_game(other, tmp_path)
    assert first.status == 'won'
    assert second.status == 'lost'
    assert sorted(path.name for path in tmp_path.iterdir()) == ['game-game-001.json']
    independent = tmp_path / 'independent'
    independent.mkdir()
    assert first.game_id != second.game_id
    for plan, output in ((request, first), (other, second)):
        assert output.status in ('won', 'lost')
        verdict = verify_task('play-game', plan, output, None, tmp_path)
        assert verdict['valid'] and verdict == verify_task('play-game', plan, output, None, tmp_path)
        assert not verify_output('play_game', plan, replace(output, history=output.history[:-1]), tmp_path)['valid']
        assert not verify_output('play_game', plan, replace(output, status='playing'), tmp_path)['valid']
        compared = compare_scores(CompareInput(output.game_id, [Move(0, 3)], output.history), independent)
        assert compared.ai.status == output.status
    assert get_board(GameInput('game-001'), tmp_path).history == []


def test_risks_and_invalid_moves():
    opened, _ = initial()
    counts = risks(opened)
    assert len(set(counts.values())) > 1
    safest = min(counts.values())
    assert sum(value == safest for value in counts.values()) > 1
    lucky = next(cell for cell, risk in counts.items() if cell not in MINES and risk > safest)
    assert replay([Move(*lucky)], True)[3] == 0
    with pytest.raises(ValueError):
        replay([Move(*OPENING)])
    with pytest.raises(ValueError):
        replay([Move(0,3), Move(0,4)])


def test_javascript_and_python_agree():
    cases = [[(0,3)], [(0,4)], [(2,4), (0,3)], [(3,4), (4,4)]]
    script = '''import {game} from './ui/game.js';
const cases = JSON.parse(process.argv[1]);
const result = cases.map(moves => { const g=game([[0,3],[1,4],[3,2],[4,4]],[0,0]);
try {for (const [r,c] of moves) g.reveal(r,c); return {status:g.status,board:Array.from({length:5},(_,r)=>Array.from({length:5},(_,c)=>g.cell(r,c)))};} catch(e) {return {error:true};}});
console.log(JSON.stringify(result));'''
    root = Path(__file__).resolve().parents[1]
    actual = json.loads(subprocess.check_output(['node', '--experimental-default-type=module', '--input-type=module', '-e', script, json.dumps(cases)], cwd=root, text=True))
    for moves, js in zip(cases, actual):
        try:
            output = visible('test', [Move(*cell) for cell in moves])
            assert js == {'status': output.status, 'board': output.board}
        except ValueError:
            assert js == {'error': True}


def test_optimal_guess_can_lose():
    history = [Move(*cell) for cell in [(1,3), (2,3), (2,4), (3,3), (4,2), (4,3)]]
    opened, status, _, _ = replay(history)
    assert status == 'playing'
    counts = risks(opened)
    assert counts[(4,4)] == min(counts.values()) > 0
    _, status, hit, optimal = replay(history + [Move(4,4)], True)
    assert status == 'lost' and hit == (4,4)
    assert optimal == replay(history, True)[3] + 1


def test_win_and_duplicate_reveal(tmp_path):
    get_board(GameInput('win'), tmp_path)
    sequence = []
    for row in range(5):
        for col in range(5):
            opened, status, _, _ = replay(sequence)
            if status != 'playing':
                break
            if (row, col) not in opened and (row, col) not in MINES:
                move = Move(row, col)
                sequence.append(move)
                board = reveal_cell(RevealInput('win', row, col), tmp_path)
                if board.status == 'playing':
                    with pytest.raises(ValueError):
                        reveal_cell(RevealInput('win', row, col), tmp_path)
    assert board.status == 'won'
    assert get_board(GameInput('win'), tmp_path).history == sequence
