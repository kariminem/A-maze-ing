#!/usr/bin/env python3

from enum import IntFlag


# This is already the bit representation of the walls as we will need it for the output. 
class Walls(IntFlag):
    NORTH = 1   # Bit 0
    EAST = 2    # Bit 1
    SOUTH = 4   # Bit 2
    WEST = 8    # Bit 3


class Cell:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        # setting all walls to closed using bit operations -> (1111)
        self.walls: Walls = Walls.NORTH | Walls.EAST | Walls.SOUTH | Walls.WEST
        self.visited = False


class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: list[list[Cell]] = []
        for y in range(height):
            row: list[Cell] = []
            for x in range(width):
                row.append(Cell(x, y))
            self.cells.append(row)
        # self.cells = [[Cell() for _ in range(self.width)] for _ in range(self.height)]  # creating 2D Array/List for Grid each element is a Cell() Object which Walls are closed


## NEW HELPER FOR CHECKING IF COORDINATES ARE OUT OUF BOUNDS 
# STILL HAVE TO CALL IT IN def get_unvisited_neighbors !!!!!!!!!!!!!
def get_neighbors(grid: Grid, x: int, y: int):
    if x < 0 or x >= grid.width or y < 0 or y >= grid.height:
        return None
    else:
        return grid.cells[y][x]


def get_unvisited_neighbors(grid: Grid, current: Cell):
    # defining each neighbor as the direction they're in
    north: Cell = grid.cells[current.y - 1][current.x]
    east: Cell = grid.cells[current.y][current.x + 1]
    south: Cell = grid.cells[current.y + 1][current.x]
    west: Cell = grid.cells[current.y][current.x - 1]

    # creating a list for all the unvisited neighbors
    unvisited_neighbors: list[Cell] = []
    if north and not north.visited:
        unvisited_neighbors.append(north)
    if not east.visited:
        unvisited_neighbors.append(east)
    if not south.visited:
        unvisited_neighbors.append(south)
    if not west.visited:
        unvisited_neighbors.append(west)

    return unvisited_neighbors


def remove_wall_between(current: Cell, neighbor: Cell, direction: Walls):
    # get the direction if the neighbors wall
    if direction == Walls.NORTH:
        opposite = Walls.SOUTH
    elif direction == Walls.EAST:
        opposite = Walls.WEST
    elif direction == Walls.SOUTH:
        opposite = Walls.NORTH
    elif direction == Walls.WEST:
        opposite = Walls.EAST
    else:
        raise ValueError(f"{direction} is Invalid. Valid options: NORTH, EAST, SOUTH, WEST")

    # we do a bit operation by inverting the bits of the direction (with ~)
    # and using the & which will only set bits to 1 if both bits (current
    # wall and direction) are 1. Since we inverted direction bits, the only 1
    # bit of that direction, will be zero and only this bit will be deducted
    # So it is simply the way of setting that wall to "open"
    current.walls &= ~direction
    neighbor.walls &= ~opposite

# ======== NEXT UP ========

# - list for tracking the path
# - backtracking algo:
#   - get_unvisited_neighbours()
# 	- try: randomly choose one with random.choice(unvisited_neigbours) and call backtracking function recursively with next cell
#   - except NoUnvisitedNeighbour/EmptyList or whatever: go back one step using the path list and call backtracking function recursively with this cell
#   - 


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
