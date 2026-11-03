from dataclasses import dataclass
from enum import Enum
from typing import Annotated
from slimconfig import Output

class Tool(Enum):
    GET_BOARD = 'get_board'
    REVEAL_CELL = 'reveal_cell'
    PLAY_TURN = 'play_turn'
    PLAY_GAME = 'play_game'
    COMPARE_SCORES = 'compare_scores'

class Task(Enum):
    PLAY_GAME = 'play-game'
    COMPARE_SCORES = 'compare-scores'

@dataclass
class GameInput(Output):
    game_id: Annotated[str, 'Unique game identifier, letters, digits, hyphens and underscores']

@dataclass
class Move(Output):
    row: Annotated[int, 'Zero-based row, 0 to 4']
    col: Annotated[int, 'Zero-based column, 0 to 4']

@dataclass
class RevealInput(Output):
    game_id: Annotated[str, 'Game identifier']
    row: Annotated[int, 'Zero-based row']
    col: Annotated[int, 'Zero-based column']

@dataclass
class TurnInput(Output):
    game_id: Annotated[str, 'Game identifier']
    guess: Annotated[Move | None, 'Null to start, or one covered cell to guess']

@dataclass
class BoardOutput(Output):
    game_id: Annotated[str, 'Game identifier']
    board: Annotated[list[list[int | None]], 'Visible clues; null is covered or the hit mine']
    status: Annotated[str, 'playing, won, or lost']
    history: Annotated[list[Move], 'Explicit reveals in order']
    mine_count: Annotated[int, 'Total mines']

@dataclass
class PlayInput(Output):
    order: Annotated[list[int], 'Fresh reveal order, containing each covered cell index once']

@dataclass
class PlayOutput(Output):
    game_id: Annotated[str, 'Game identifier assigned by the plugin']
    history: Annotated[list[Move], 'All explicit reveals in order']
    status: Annotated[str, 'Terminal status: won or lost']

@dataclass
class CompareInput(Output):
    game_id: Annotated[str, 'Identifier of the completed AI game']
    history: Annotated[list[Move], 'Human explicit reveals in order']

@dataclass
class PlayerResult(Output):
    board: Annotated[list[list[str]], 'Final board: covered, mine, hit, or a clue digit']
    status: Annotated[str, 'won or lost']
    game_score: Annotated[int, 'Safe cells revealed']
    optimal_moves: Annotated[int, 'Number of lowest-risk decisions']
    decisions: Annotated[int, 'Number of explicit decisions']

@dataclass
class CompareOutput(Output):
    game_id: Annotated[str, 'Game identifier']
    human: Annotated[PlayerResult, 'Verified human result']
    ai: Annotated[PlayerResult, 'Verified AI result']
    game_comparison: Annotated[str, 'human, ai, or tie']
    accuracy_comparison: Annotated[str, 'human, ai, tie, or N/A']

TOOLS = {Tool.GET_BOARD: (GameInput, BoardOutput), Tool.REVEAL_CELL: (RevealInput, BoardOutput), Tool.PLAY_TURN: (TurnInput, BoardOutput), Tool.PLAY_GAME: (PlayInput, PlayOutput), Tool.COMPARE_SCORES: (CompareInput, CompareOutput)}
TASKS = {Task.PLAY_GAME: TOOLS[Tool.PLAY_GAME], Task.COMPARE_SCORES: (CompareInput, CompareOutput)}
