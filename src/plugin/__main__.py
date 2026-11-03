import os
from pathlib import Path
import anyio
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from slimconfig import build_output, output_schema, plain_output
from contract import TOOLS, Tool
from plugin import get_board, reveal_cell, play_turn, compare_scores

server = Server('minesweeper-verifier')
IMPLEMENTATIONS = {Tool.GET_BOARD: get_board, Tool.REVEAL_CELL: reveal_cell, Tool.PLAY_TURN: play_turn, Tool.COMPARE_SCORES: compare_scores}

@server.list_tools()
async def list_tools():
    return [types.Tool(name=tool.value, inputSchema=output_schema(given), outputSchema=output_schema(made)) for tool, (given, made) in TOOLS.items()]

@server.call_tool()
async def call_tool(name, arguments):
    tool = Tool(name)
    given, made = TOOLS[tool]
    output = IMPLEMENTATIONS[tool](build_output(arguments, given), Path(os.environ['NANOAGENT_WORKSPACE']))
    if not isinstance(output, made):
        raise TypeError('wrong output type')
    return plain_output(output)

async def run():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == '__main__':
    anyio.run(run)
