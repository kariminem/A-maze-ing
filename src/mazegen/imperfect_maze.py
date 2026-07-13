#!/usr/bin/env python3

import random
from .perfect_maze_algo import perfect_algo, remove_wall_between, InvalidCoordinates
from .structure import Grid, Cell, Walls
from .structure import get_middle_cell


def get_all_interior_walls(grid: Grid) -> list[tuple[Cell, Walls]]:
    """creata a list of all standing walls inside the grid
    and give them back as tuple consisting of the cell and direction"""

    interior_walls: list[tuple[Cell, Walls]] = []
    for y in range(grid.height):
        for x in range(grid.width):
            # go through each cell
            cell = grid.cells[y][x]

            # only if we're not at the outer border check for a wall in the direction
            # that we add to our list of possible breaking-downs
            if x < grid.width - 1:
                if cell.walls & Walls.EAST:
                    interior_walls.append((cell, Walls.EAST))

            if y < grid.height - 1:
                if cell.walls & Walls.SOUTH:
                    interior_walls.append((cell, Walls.SOUTH))
            # only counting east and south since if we break a south we're
            # breaking a nother cells north wall
    return interior_walls


def imperfect_algo(grid: Grid, cell: Cell) -> None:
    """
    >>> opening up the edges and centre
    >>> making each corridor reachable
    >>> breaking in some walls to make the maze imperfect
    >>> removing dead-ends
    """

    perfect_algo(grid, cell)

    # open 4 corners
    remove_wall_between(grid.cells[0][0], grid.cells[0][1])
    remove_wall_between(grid.cells[0][0], grid.cells[1][0])
    remove_wall_between(grid.cells[grid.height - 1][0], grid.cells[grid.height - 2][0])
    remove_wall_between(grid.cells[grid.height - 1][0], grid.cells[grid.height - 1][1])
    remove_wall_between(grid.cells[grid.height - 1][grid.width - 1], grid.cells[grid.height - 2][grid.width - 1])
    remove_wall_between(grid.cells[grid.height - 1][grid.width - 1], grid.cells[grid.height - 1][grid.width - 2])
    remove_wall_between(grid.cells[0][grid.width - 1], grid.cells[1][grid.width - 1])
    remove_wall_between(grid.cells[0][grid.width - 1], grid.cells[0][grid.width - 2])

    # open center (just the one line between the 4 and the 2, I guess?)
    middle_cell = get_middle_cell(grid)

    # first random try of opening up the center (because I DON'T KNOW WHAT THEY MEAN BY THAT)
    # if current (middle) cell has a wall bewol, remove it
    if grid.cells[middle_cell.y][middle_cell.x].walls & Walls.SOUTH:
        remove_wall_between(grid.cells[middle_cell.y][middle_cell.x], grid.cells[middle_cell.y + 1][middle_cell.x])
    if grid.cells[middle_cell.y + 1][middle_cell.x].walls & Walls.SOUTH:
        remove_wall_between(grid.cells[middle_cell.y + 1][middle_cell.x], grid.cells[middle_cell.y + 2][middle_cell.x])
    # does the middle cell have a north wall, remove it
    if grid.cells[middle_cell.y][middle_cell.x].walls & Walls.NORTH:
        remove_wall_between(grid.cells[middle_cell.y][middle_cell.x], grid.cells[middle_cell.y - 1][middle_cell.x])
    if grid.cells[middle_cell.y - 1][middle_cell.x].walls & Walls.WEST:
        remove_wall_between(grid.cells[middle_cell.y - 1][middle_cell.x], grid.cells[middle_cell.y - 1][middle_cell.x - 1])
    if grid.cells[middle_cell.y - 1][middle_cell.x - 1].walls & Walls.NORTH:
        remove_wall_between(grid.cells[middle_cell.y - 1][middle_cell.x - 1], grid.cells[middle_cell.y - 2][middle_cell.x - 1])

    interior_walls = get_all_interior_walls(grid)
    random.shuffle(interior_walls)

    # here you can adjust the intensity -> how many walls we're destroying 
    intensity = 10  # f.ex. 10 percent of the walls
    walls_to_remove = int(len(interior_walls) * intensity / 100)

    while walls_to_remove > 0:
        chosen_wall = interior_walls.pop()
        current_cell, direction = chosen_wall
        if direction == Walls.NORTH:
            neighbor = grid.cells[current_cell.y - 1][current_cell.x]
        elif direction == Walls.EAST:
            neighbor = grid.cells[current_cell.y][current_cell.x + 1]
        elif direction == Walls.SOUTH:
            neighbor = grid.cells[current_cell.y + 1][current_cell.x]
        elif direction == Walls.WEST:
            neighbor = grid.cells[current_cell.y][current_cell.x - 1]
        else:
            raise InvalidCoordinates

        # protect 42 pattern
        if current_cell.blocked or neighbor.blocked or would_create_2x2_spaces(grid, current_cell, neighbor, direction):
            continue
        else:
            remove_wall_between(current_cell, neighbor)
            walls_to_remove -= 1


def would_create_2x2_spaces(grid: Grid, current: Cell, neighbor: Cell, direction_current_wall: Walls) -> bool:
    """function for avoiding creating 2x2 grids"""
    # checking for a vertical wall
    if direction_current_wall == Walls.EAST:
        # looking at the 2 cells above us only if we're not row 0
        if current.y > 0:
            if (not (current.walls & Walls.NORTH)) and \
               (not (neighbor.walls & Walls.NORTH)) and \
               (not (grid.cells[current.y - 1][current.x].walls & Walls.EAST)):
                return True
    # looking at the 2 cells below us
        if current.y < grid.height - 1:
            if (not (current.walls & Walls.SOUTH)) and \
               (not (neighbor.walls & Walls.SOUTH)) and \
               (not (grid.cells[current.y + 1][current.x].walls & Walls.EAST)):
                return True

    # checking for a horizontal wall
    elif direction_current_wall == Walls.SOUTH:
        # looking at the 2 cells left of us only if we're not collumn 0
        if current.x > 0:
            if (not (current.walls & Walls.WEST)) and \
               (not (neighbor.walls & Walls.WEST)) and \
               (not (grid.cells[current.y][current.x - 1].walls & Walls.SOUTH)):
                return True
    # looking at the 2 cells right of us
        if current.y < grid.width - 1:
            if (not (current.walls & Walls.EAST)) and \
               (not (neighbor.walls & Walls.EAST)) and \
               (not (grid.cells[current.y][current.x + 1].walls & Walls.SOUTH)):
                return True

    return False
