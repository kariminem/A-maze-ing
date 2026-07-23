#!/usr/bin/env python3

import random

from .structure import OPPOSITE, Cell, Grid, Walls


class MazeAlgoError(Exception):
    """Base class for errors raised by the maze generation algorithm."""
    pass


class InvalidCoordinates(MazeAlgoError):
    """Exception raised when there is a coordinates mismatch."""
    pass


myseed = random.randint(0, 10)
random_instance = random.Random(myseed)


def perfect_algo(grid: Grid, cell: Cell) -> None:
    """Carve a perfect maze using a randomized recursive backtracker."""
    cell.visited = True
    available_neighbors = get_available_neighbors(grid, cell)

    while available_neighbors:
        next_cell = random_instance.choice(available_neighbors)
        remove_wall_between(cell, next_cell)
        perfect_algo(grid, next_cell)
        available_neighbors = get_available_neighbors(grid, cell)


def get_neighbor(grid: Grid, x: int, y: int) -> Cell | None:
    """Return the cell at (x, y), or None if it's outside the grid."""
    if x < 0 or x >= grid.width or y < 0 or y >= grid.height:
        return None
    return grid.cells[y][x]


def get_available_neighbors(grid: Grid, current: Cell) -> list[Cell]:
    """List current's neighbors that are unvisited and not blocked."""
    candidates = [
        get_neighbor(grid, current.x, current.y - 1),
        get_neighbor(grid, current.x + 1, current.y),
        get_neighbor(grid, current.x, current.y + 1),
        get_neighbor(grid, current.x - 1, current.y),
    ]
    return [
        cell for cell in candidates
        if cell is not None and not cell.visited and not cell.blocked
    ]


def remove_wall_between(current: Cell, neighbor: Cell) -> None:
    """Open the shared wall between two adjacent cells, on both sides."""
    if current.y == neighbor.y:
        if neighbor.x == current.x + 1:
            direction_neighbor_wall = Walls.WEST
        elif neighbor.x == current.x - 1:
            direction_neighbor_wall = Walls.EAST
        else:
            raise InvalidCoordinates
    else:
        if neighbor.y == current.y - 1:
            direction_neighbor_wall = Walls.SOUTH
        elif neighbor.y == current.y + 1:
            direction_neighbor_wall = Walls.NORTH
        else:
            raise InvalidCoordinates

    direction_current_wall = OPPOSITE[direction_neighbor_wall]
    current.walls &= ~direction_current_wall
    neighbor.walls &= ~direction_neighbor_wall
