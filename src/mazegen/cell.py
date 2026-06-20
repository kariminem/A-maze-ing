#!/usr/bin/env python3

from enum import IntFlag


# This is already the bit representation of the walls as we will need it for the output. 
class Walls(IntFlag):
    NORTH = 1   # Bit 0
    EAST = 2    # Bit 1
    SOUTH = 4   # Bit 2
    WEST = 8    # Bit 3


class Cell:
    def __init__(self):
        # setting all walls to closed using bit operations -> (1111)
        self.walls: Walls = Walls.NORTH | Walls.EAST | Walls.SOUTH | Walls.WEST


class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells = [[Cell() for _ in range(self.width)] for _ in range(self.height)]




# ================= TESTING =================

# test_grid = Grid(5, 5)
# random test if all walls are closed. Should display 15 if closed since 8 + 4 + 2 + 1 = 15
# print(test_grid.cells[0][0].walls)
# print(test_grid.cells[2][1].walls)
# print(test_grid.cells[4][4].walls)

# for testing this Grid representation change the Cell() in self.cells = … to f.ex 1
# print(test_grid.cells[0])
# print(test_grid.cells[1])
# print(test_grid.cells[2])
# print(test_grid.cells[3])
