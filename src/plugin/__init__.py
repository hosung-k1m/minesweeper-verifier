import json
from dataclasses import asdict
from uuid import uuid4
from verifier.checks import valid_id, load, visible, replay, comparison, play_history, play_order
from contract import Move, PlayOutput

def path_for(workspace, game_id):
    if not valid_id(game_id):
        raise ValueError('invalid game identifier')
    return workspace / ('game-' + game_id + '.json')

def get_board(value, workspace):
    path = path_for(workspace, value.game_id)
    if not path.exists():
        path.write_text('[]', encoding='utf-8')
    return visible(value.game_id, load(workspace, value.game_id))

def reveal_cell(value, workspace):
    history = load(workspace, value.game_id)
    history.append(Move(value.row, value.col))
    replay(history)
    save(path_for(workspace, value.game_id), history)
    return visible(value.game_id, history)

def save(path, history):
    path.write_text(json.dumps([asdict(move) for move in history]), encoding='utf-8')


def play_turn(value, workspace):
    path = path_for(workspace, value.game_id)
    if value.guess is None:
        history = play_history([], None)
        if path.exists() and load(workspace, value.game_id) not in ([], history):
            raise ValueError('game already advanced; use a new game identifier')
    else:
        history = play_history(load(workspace, value.game_id), value.guess)
    save(path, history)
    return visible(value.game_id, history)


def play_game(value, workspace):
    game_id = uuid4().hex
    history, status = play_order(value.order)
    return PlayOutput(game_id, history, status)


def compare_scores(value, workspace):
    return comparison(value.game_id, value.history, value.ai_history)
