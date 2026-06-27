#!/usr/bin/env python3

from enum import IntFlag


# This is already the bit representation of the walls as we will need it for the output.
class Walls(IntFlag):
    NORTH = 1   # Bit 0
    EAST = 2    # Bit 1
    SOUTH = 4   # Bit 2
    WEST = 8    # Bit 3


# dictionary for directly getting the opposite direction
OPPOSITE = {
    Walls.NORTH: Walls.SOUTH,
    Walls.EAST: Walls.WEST,
    Walls.SOUTH: Walls.NORTH,
    Walls.WEST: Walls.EAST,
}


class Cell:
    def __init__(self, x: int, y: int):
        # cells have to have their coordinates to know where they are in the
        # grid so its easier to work with cells instead of having to
        # communicate coordinates
        self.x = x
        self.y = y
        # setting all walls to closed using bit operations -> (1111)
        self.walls: Walls = Walls.NORTH | Walls.EAST | Walls.SOUTH | Walls.WEST
        self.visited = False
        self.blocked = False  # set True for the cells that make 42 pattern


class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: list[list[Cell]] = []  # create empty double array
        # have to loop through it to set the x and y coordinates
        for y in range(height):
            row: list[Cell] = []
            for x in range(width):
                row.append(Cell(x, y))
            self.cells.append(row)
        # self.cells = [[Cell() for _ in range(self.width)] for _ in range(self.height)]  # creating 2D Array/List for Grid each element is a Cell() Object which Walls are closed



# ================= TESTING =================

# test_grid = Grid(5, 5)
# # random test if all walls are closed. Should display 15 if closed since 8 + 4 + 2 + 1 = 15
# print(test_grid.cells[0][0].walls)
# print(test_grid.cells[2][1].walls)
# print(test_grid.cells[4][4].walls)

# # for testing this Grid representation change the Cell() in self.cells = … to f.ex 1
# print(test_grid.cells[0])
# print(test_grid.cells[1])
# print(test_grid.cells[2])
# print(test_grid.cells[3])

# # for testing the coordinates
# print(test_grid.cells[0][0].x)
# print(test_grid.cells[0][0].y)
# print(test_grid.cells[1][1].x)
# print(test_grid.cells[1][1].y)
# print(test_grid.cells[2][2].x)
# print(test_grid.cells[2][2].y)
# print(test_grid.cells[4][3].x)
# print(test_grid.cells[4][3].y)
