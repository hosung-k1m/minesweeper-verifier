import itertools
import json
import re
from pathlib import Path
from contract import BoardOutput, Move, PlayerResult, CompareOutput

MINES = {(0, 3), (1, 4), (3, 2), (4, 4)}
OPENING = (0, 0)
CELLS = {(r, c) for r in range(5) for c in range(5)}

def result(valid, message, **details):
    return {'valid': valid, 'score': float(valid), 'message': message, 'details': details}

def valid_id(game_id):
    return bool(re.fullmatch(r'[A-Za-z0-9_-]{1,64}', game_id))

def neighbors(cell):
    r, c = cell
    return {(rr, cc) for rr in range(max(0, r-1), min(5, r+2)) for cc in range(max(0, c-1), min(5, c+2)) if (rr, cc) != cell}

def clue(cell):
    return len(neighbors(cell) & MINES)

def reveal(opened, cell):
    if cell not in CELLS or cell in opened:
        raise ValueError('cell is out of range or already revealed')
    if cell in MINES:
        return 'lost'
    pending = [cell]
    while pending:
        current = pending.pop()
        if current in opened:
            continue
        opened.add(current)
        if clue(current) == 0:
            pending.extend(neighbors(current) - opened - MINES)
    return 'won' if len(opened) == 21 else 'playing'

def initial():
    opened = set()
    status = reveal(opened, OPENING)
    return opened, status

def risks(opened):
    covered = sorted(CELLS - opened)
    counts = {cell: 0 for cell in covered}
    total = 0
    for placement in itertools.combinations(covered, len(MINES)):
        mines = set(placement)
        if all(len(neighbors(cell) & mines) == clue(cell) for cell in opened):
            total += 1
            for cell in placement:
                counts[cell] += 1
    if not total:
        raise ValueError('no mine placements match the visible board')
    return counts

def replay(history, grade=False):
    opened, status = initial()
    optimal = 0
    hit = None
    for move in history:
        cell = (move.row, move.col)
        if status != 'playing':
            raise ValueError('move after game over')
        if cell not in CELLS or cell in opened:
            raise ValueError('cell is out of range or already revealed')
        if grade:
            counts = risks(opened)
            optimal += counts[cell] == min(counts.values())
        status = reveal(opened, cell)
        if status == 'lost':
            hit = cell
    return opened, status, hit, optimal

def play_history(history, guess):
    opened, status, _, _ = replay(history)
    if guess is not None:
        if status != 'playing' or 0 in risks(opened).values():
            raise ValueError('guess only when there are no guaranteed safe moves')
        status = reveal(opened, (guess.row, guess.col))
        history = [*history, guess]
    else:
        history = list(history)
    while status == 'playing':
        safe = min((cell for cell, count in risks(opened).items() if count == 0), default=None)
        if safe is None:
            break
        status = reveal(opened, safe)
        history.append(Move(*safe))
    return history


def opponent_game(game_id):
    if not re.fullmatch(r'[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}', game_id):
        raise ValueError('invalid opponent game identifier')
    seed = int(game_id, 16)
    history = play_history([], None)
    opened, status, _, _ = replay(history)
    while status == 'playing':
        counts = risks(opened)
        lowest = min(counts.values())
        choices = sorted(cell for cell, count in counts.items() if count == lowest)
        history = play_history(history, Move(*choices[seed % len(choices)]))
        opened, status, _, _ = replay(history)
    return history, status


def visible(game_id, history):
    opened, status, _, _ = replay(history)
    board = [[clue((r,c)) if (r,c) in opened else None for c in range(5)] for r in range(5)]
    return BoardOutput(game_id, board, status, history, len(MINES))

def load(workspace, game_id):
    if not valid_id(game_id):
        raise ValueError('invalid game identifier')
    data = json.loads((Path(workspace) / ('game-' + game_id + '.json')).read_text(encoding='utf-8'))
    if not isinstance(data, list):
        raise ValueError('invalid history')
    return [Move(**move) for move in data]

def player(history):
    opened, status, hit, optimal = replay(history, True)
    if status == 'playing':
        raise ValueError('game is incomplete')
    board = [[('hit' if (r,c) == hit else 'mine' if (r,c) in MINES else str(clue((r,c))) if (r,c) in opened else 'covered') for c in range(5)] for r in range(5)]
    return PlayerResult(board, status, len(opened), optimal, len(history))

def comparison(game_id, human_history, ai_history):
    human, ai = player(human_history), player(ai_history)
    def compare(a, b):
        return 'human' if a > b else 'ai' if a < b else 'tie'
    accuracy = compare(human.optimal_moves * ai.decisions, ai.optimal_moves * human.decisions) if human.decisions and ai.decisions else 'N/A'
    return CompareOutput(game_id, human, ai, compare(human.game_score, ai.game_score), accuracy)
