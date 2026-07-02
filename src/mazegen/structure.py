#!/usr/bin/env python3

from enum import IntFlag


# This is already the bit representation of the walls as we will need it
# for the output.
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
        forty_two_pattern(self)  # may remove that here if we use it generator.py


# 42 LOGO in Maze

######### STILL OPEN ##############
# print error message if maze is to small to display the 42 pattern
# should the maze then still be displayed just without the 42 pattern??

def forty_two_pattern(grid: Grid):
    """setting the 42 cells as blocked when creating the grid"""
    # find horizontal middle of maze
    # you may ask what happens if there is no ONE middle cell but 4
    # We will not care! Since I'm rounding to an int, we will just take the
    # left one
    horizontal_middle = int(grid.width / 2)
    vertical_middle = int(grid.height / 2)
    middle_cell: Cell = grid.cells[vertical_middle][horizontal_middle]

    # so now the blocking the pattern part

    # doing the 4 first
    # three left from the middle (four's horizontal line)
    grid.cells[middle_cell.y][middle_cell.x - 1].blocked = True
    grid.cells[middle_cell.y][middle_cell.x - 2].blocked = True
    grid.cells[middle_cell.y][middle_cell.x - 3].blocked = True

    # vertical upper 2 cells for the top of 4
    grid.cells[middle_cell.y - 1][middle_cell.x - 3].blocked = True
    grid.cells[middle_cell.y - 2][middle_cell.x - 3].blocked = True

    # vertical lower 2 cells of the 4
    grid.cells[middle_cell.y + 1][middle_cell.x - 1].blocked = True
    grid.cells[middle_cell.y + 2][middle_cell.x - 1].blocked = True

    # now the 2
    # three right from the middle
    grid.cells[middle_cell.y][middle_cell.x + 1].blocked = True
    grid.cells[middle_cell.y][middle_cell.x + 2].blocked = True
    grid.cells[middle_cell.y][middle_cell.x + 3].blocked = True

    # upper half of 2
    # horizontal line
    grid.cells[middle_cell.y - 2][middle_cell.x + 1].blocked = True
    grid.cells[middle_cell.y - 2][middle_cell.x + 2].blocked = True
    grid.cells[middle_cell.y - 2][middle_cell.x + 3].blocked = True
    # vertical one
    grid.cells[middle_cell.y - 1][middle_cell.x + 3].blocked = True

    # lower half of 2
    # horizontal line
    grid.cells[middle_cell.y + 2][middle_cell.x + 1].blocked = True
    grid.cells[middle_cell.y + 2][middle_cell.x + 2].blocked = True
    grid.cells[middle_cell.y + 2][middle_cell.x + 3].blocked = True
    # vertical one
    grid.cells[middle_cell.y + 1][middle_cell.x + 1].blocked = True
