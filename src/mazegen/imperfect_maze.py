#!/usr/bin/env python3

import random
from .perfect_maze_algo import perfect_algo, remove_wall_between, InvalidCoordinates
from .structure import Grid, Cell, Walls

# def check_open_spaces()

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
    >>> making each corridor is reachable
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
        if current_cell.blocked or neighbor.blocked:
            continue
        else:
            remove_wall_between(current_cell, neighbor)
            walls_to_remove -= 1


    # STIL OPEN:
    # check if a 3x3 open field would be created before breaking walls


