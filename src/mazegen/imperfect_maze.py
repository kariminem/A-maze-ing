#!/usr/bin/env python3

import random
from .perfect_maze_algo import perfect_algo, get_available_neighbors, remove_wall_between
from .structure import Grid, Cell, Walls

# def check_open_spaces()

def imperfect_algo(grid: Grid, cell: Cell) -> None:
    perfect_algo(grid, cell)

    # percentage_to_break_in = 10
    # amount_cells = grid.width * grid.height
    # walls_to_break = int(amount_cells * percentage_to_break_in / 100)
    # open 4 corners
    remove_wall_between(grid.cells[0][0], grid.cells[0][1])
    remove_wall_between(grid.cells[0][0], grid.cells[1][0])
    remove_wall_between(grid.cells[grid.height - 1][0], grid.cells[grid.height - 2][0])
    remove_wall_between(grid.cells[grid.height - 1][0], grid.cells[grid.height - 1][1])
    remove_wall_between(grid.cells[grid.height - 1][grid.width - 1], grid.cells[grid.height - 2][grid.width - 1])
    remove_wall_between(grid.cells[grid.height - 1][grid.width - 1], grid.cells[grid.height - 1][grid.width - 2])


    # for _ in range(walls_to_break):
    #     chosen_cell = random.choice(grid.cells)
    #     unblocked_neighbors = get_available_neighbors(grid, chosen_cell, "imperfect")
    #     chosen_neighbor = random.choice(unblocked_neighbors)
    #     # check if a 3x3 open field would be created before breaking walls


