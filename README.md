# Minesweeper

Play a fixed 5×5 Minesweeper puzzle after the automated opponent has played it. Ask the plugin to start a new game, reveal cells, then choose Compare results. The result shows both boards and independently verified scores.

## Tools

`get_board` and `reveal_cell` expose only visible clues. `play_turn` reveals guaranteed safe cells and accepts a guess. `play_game` runs the automated opponent to completion. `compare_scores` replays both games and calculates results. Each game uses a unique identifier and the opponent’s history is stored in the plugin workspace.

`play-game` runs the automated opponent in one tool call. It opens provably safe cells, then chooses a lowest-risk guess from the visible clues, using a fresh game ID to break ties. All reveals count toward the opponent's score. `compare-scores` checks the human history against the recorded opponent game. Scores count safe cells revealed including the opening. Move accuracy counts explicit choices with the lowest immediate mine probability among all placements consistent with visible clues. An accuracy with no decisions is N/A.

## Layout

The game rules and verifier live in `verifier/`, the tools in `src/plugin/`, and the local board in `ui/`.

## Develop and run

Run `uv sync`, `uv run pytest`, `nanoagent plugin inspect .`, and `nanoagent plugin pack . <package.tar.gz>`. The renderer receives the puzzle after the opponent's game is verified. Human play runs locally; refreshing restarts it. The comparison trusts neither the displayed board nor client scores.
