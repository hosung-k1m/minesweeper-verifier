from contract import Tool, Task, GameInput, RevealInput, TurnInput, CompareInput, BoardOutput, PlayOutput, CompareOutput
from .checks import result, valid_id, load, replay, visible, play_history, comparison, MINES, OPENING

def verify_input(tool, value):
    try:
        name = Tool(tool)
        expected = {Tool.GET_BOARD: GameInput, Tool.REVEAL_CELL: RevealInput, Tool.PLAY_TURN: TurnInput, Tool.COMPARE_SCORES: CompareInput}[name]
        if not isinstance(value, expected) or not valid_id(value.game_id):
            return result(False, 'invalid game input or identifier')
        if name is Tool.REVEAL_CELL and (not 0 <= value.row < 5 or not 0 <= value.col < 5):
            return result(False, 'coordinates must be between 0 and 4')
        if name is Tool.PLAY_TURN and value.guess is not None:
            if not 0 <= value.guess.row < 5 or not 0 <= value.guess.col < 5:
                return result(False, 'coordinates must be between 0 and 4')
        if name is Tool.COMPARE_SCORES:
            replay(value.history)
        return result(True, 'input is valid')
    except (ValueError, TypeError, AttributeError):
        return result(False, 'invalid game input')

def verify_output(tool, input_value, output_value, workspace):
    try:
        if not verify_input(tool, input_value)['valid']:
            return result(False, 'invalid input')
        name = Tool(tool)
        history = load(workspace, input_value.game_id)
        if name is Tool.COMPARE_SCORES:
            valid = isinstance(output_value, CompareOutput) and output_value == comparison(input_value.game_id, input_value.history, history)
        else:
            if not isinstance(output_value, BoardOutput):
                return result(False, 'output does not match replay')
            # Later reveals can be saved before the host verifies this response.
            snapshot = output_value.history
            valid = snapshot == history[:len(snapshot)] and output_value == visible(input_value.game_id, snapshot)
            if name is Tool.REVEAL_CELL:
                valid = valid and bool(snapshot) and snapshot[-1].row == input_value.row and snapshot[-1].col == input_value.col
            if valid and name is Tool.PLAY_TURN:
                guess = input_value.guess
                before = [] if guess is None else snapshot[:snapshot.index(guess)]
                valid = snapshot == play_history(before, guess)
        return result(valid, 'output matches replay' if valid else 'output does not match replay')
    except (ValueError, TypeError, AttributeError, KeyError, OSError):
        return result(False, 'invalid or missing game evidence')

def verify_task(task, arguments, output, reference, workspace):
    if Task(task) is Task.COMPARE_SCORES:
        return verify_output(Tool.COMPARE_SCORES, arguments, output, workspace)
    try:
        history = load(workspace, arguments.game_id)
        _, status, _, _ = replay(history)
        valid = isinstance(arguments, GameInput) and isinstance(output, PlayOutput) and output.game_id == arguments.game_id and output.history == history and output.status == status and status in ('won', 'lost')
        return result(valid, 'completed game verified' if valid else 'game is incomplete or does not match history', mines=[list(cell) for cell in sorted(MINES)], opening=list(OPENING)) if valid else result(False, 'game is incomplete or does not match history')
    except (ValueError, TypeError, AttributeError, KeyError, OSError):
        return result(False, 'invalid or missing game evidence')
