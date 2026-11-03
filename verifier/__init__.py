from contract import Tool, Task, GameInput, RevealInput, TurnInput, CompareInput, BoardOutput, PlayInput, PlayOutput, CompareOutput
from .checks import result, valid_id, load, replay, visible, play_history, play_order, round_id, opponent_history, comparison, MINES, OPENING

def verify_input(tool, value):
    try:
        name = Tool(tool)
        if name is Tool.PLAY_GAME:
            if not isinstance(value, PlayInput):
                return result(False, 'expected a reveal order')
            play_order(value.order)
            return result(True, 'input is valid')
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
            replay(opponent_history(value.game_id))
        return result(True, 'input is valid')
    except (ValueError, TypeError, AttributeError):
        return result(False, 'invalid game input')

def verify_output(tool, input_value, output_value, workspace):
    try:
        if not verify_input(tool, input_value)['valid']:
            return result(False, 'invalid input')
        name = Tool(tool)
        if name is Tool.PLAY_GAME:
            if not isinstance(output_value, PlayOutput):
                return result(False, 'invalid game output')
            history, status = play_order(input_value.order)
            game_id = output_value.game_id
            nonce = game_id.removeprefix('round-').split('-')[0]
            valid = (
                len(nonce) == 32 and all(char in '0123456789abcdef' for char in nonce)
                and game_id == round_id(nonce, history)
                and output_value.history == history and output_value.status == status
            )
            if valid:
                return result(True, 'completed game verified', mines=[list(cell) for cell in sorted(MINES)], opening=list(OPENING))
            return result(False, 'output does not match the recorded opponent game')
        if name is Tool.COMPARE_SCORES:
            valid = isinstance(output_value, CompareOutput) and output_value == comparison(
                input_value.game_id, input_value.history, opponent_history(input_value.game_id)
            )
        else:
            history = load(workspace, input_value.game_id)
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
    tool = Tool.PLAY_GAME if Task(task) is Task.PLAY_GAME else Tool.COMPARE_SCORES
    return verify_output(tool, arguments, output, workspace)
