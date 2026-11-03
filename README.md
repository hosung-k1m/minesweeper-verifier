# Minesweeper

Play a fixed 5×5 Minesweeper puzzle after the automated opponent has played it. Ask the plugin to start a new game, reveal cells, then choose Compare results. The result shows both boards and independently verified scores.

## Tools

`play_game` executes a fresh reveal order chosen by the AI from the opening clues. It stops at a mine or when the board is clear. `compare_scores` replays the two histories from the current round and calculates their scores. Neither task reads or writes saved game files. The separate `get_board`, `reveal_cell`, and `play_turn` tools support inspecting and stepping through a game.

`play-game` starts a fresh round. `compare-scores` compares the finished games. Scores count safe cells revealed, including the opening. Move accuracy counts choices with the lowest immediate mine probability among all placements consistent with the visible clues.

## Layout

The game rules and verifier live in `verifier/`, the tools in `src/plugin/`, and the local board in `ui/`.

## Develop and run

Run `uv sync`, `uv run pytest`, `nanoagent plugin inspect .`, and `nanoagent plugin pack . <package.tar.gz>`. The renderer receives the puzzle after the opponent's game is verified. Human play runs locally; refreshing restarts it. The comparison trusts neither the displayed board nor client scores.
