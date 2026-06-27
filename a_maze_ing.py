#!/usr/bin/env python3

from src.mazegen.structure import Grid
from src.mazegen.output_maze import put_hex_maze, ascii_display
from src.mazegen.perfect_maze_algo import perfect_algo

# TESTING OUTPUT ###
# run ./a_maze_ing.py and then look in output_maze.txt or cat that file
if __name__ == "__main__":
    grid = Grid(20, 20)
    start_x = 0
    start_y = 0

    perfect_algo(grid, grid.cells[start_y][start_x])
    put_hex_maze(grid)
    ascii_display(grid)
