#!/usr/bin/env python3

from . import perfect_maze_algo as pma
from .structure import Cell, Grid, Walls, get_middle_cell

DIRECTIONS = [Walls.NORTH, Walls.EAST, Walls.SOUTH, Walls.WEST]

STEP_FOR_DIRECTION = {
    Walls.NORTH: (0, -1),
    Walls.EAST: (1, 0),
    Walls.SOUTH: (0, 1),
    Walls.WEST: (-1, 0),
}


def get_neighbor(grid: Grid, cell: Cell, direction: Walls) -> Cell | None:
    """Return the cell next to `cell` in the given direction, or None if
    that would fall outside the grid."""
    change_x, change_y = STEP_FOR_DIRECTION[direction]
    x, y = cell.x + change_x, cell.y + change_y
    if 0 <= x < grid.width and 0 <= y < grid.height:
        return grid.cells[y][x]
    return None


def would_create_2x2_spaces(
    grid: Grid, current: Cell, neighbor: Cell, direction: Walls
) -> bool:
    """Check whether opening this wall would create a fully open 2x2
    block, which the subject forbids."""
    if direction == Walls.WEST:
        current, neighbor, direction = neighbor, current, Walls.EAST
    elif direction == Walls.NORTH:
        current, neighbor, direction = neighbor, current, Walls.SOUTH

    if direction == Walls.EAST:
        for side_wall in (Walls.NORTH, Walls.SOUTH):
            side_cell = get_neighbor(grid, current, side_wall)
            if side_cell is None:
                continue
            if (
                not (current.walls & side_wall)
                and not (neighbor.walls & side_wall)
                and not (side_cell.walls & Walls.EAST)
            ):
                return True

    elif direction == Walls.SOUTH:
        for side_x in (current.x - 1, current.x + 1):
            side_wall = Walls.WEST if side_x < current.x else Walls.EAST
            side_cell = get_neighbor(grid, current, side_wall)
            if side_cell is None:
                continue
            if (
                not (current.walls & side_wall)
                and not (neighbor.walls & side_wall)
                and not (side_cell.walls & Walls.SOUTH)
            ):
                return True

    return False


def safely_open_wall(grid: Grid, cell: Cell, direction: Walls) -> bool:
    """Remove a wall only if it is safe to do so: it must not touch a
    "42" pattern cell, and it must not create an illegal 2x2 open area.
    Returns True if the wall was actually removed."""
    neighbor = get_neighbor(grid, cell, direction)
    if neighbor is None:
        return False
    if cell.blocked or neighbor.blocked:
        return False
    if would_create_2x2_spaces(grid, cell, neighbor, direction):
        return False
    pma.remove_wall_between(cell, neighbor)
    return True


def open_the_four_corners(grid: Grid) -> None:
    """Open a path out of each of the 4 corner cells, safely."""
    corners = [
        (0, 0, Walls.EAST),
        (0, 0, Walls.SOUTH),
        (0, grid.height - 1, Walls.NORTH),
        (0, grid.height - 1, Walls.EAST),
        (grid.width - 1, grid.height - 1, Walls.NORTH),
        (grid.width - 1, grid.height - 1, Walls.WEST),
        (grid.width - 1, 0, Walls.SOUTH),
        (grid.width - 1, 0, Walls.WEST),
    ]
    for x, y, direction in corners:
        safely_open_wall(grid, grid.cells[y][x], direction)


def open_the_center(grid: Grid) -> None:
    """Open the walls right next to the middle of the maze, so the area
    around the "42" pattern connects to the rest of the maze."""
    middle_cell = get_middle_cell(grid)
    for direction in DIRECTIONS:
        safely_open_wall(grid, middle_cell, direction)


def remove_random_interior_walls(grid: Grid, percentage: int) -> None:
    """Randomly open a percentage of the maze's interior walls, safely."""
    interior_walls: list[tuple[Cell, Walls]] = []
    for row in grid.cells:
        for cell in row:
            if cell.x < grid.width - 1 and (cell.walls & Walls.EAST):
                interior_walls.append((cell, Walls.EAST))
            if cell.y < grid.height - 1 and (cell.walls & Walls.SOUTH):
                interior_walls.append((cell, Walls.SOUTH))

    pma.random_instance.shuffle(interior_walls)
    walls_to_remove = len(interior_walls) * percentage // 100

    removed_so_far = 0
    for cell, direction in interior_walls:
        if removed_so_far >= walls_to_remove:
            break
        if safely_open_wall(grid, cell, direction):
            removed_so_far += 1


def remove_dead_ends(grid: Grid) -> None:
    """Open one extra wall on every dead-end cell (a cell with only one
    open side), so the maze has fewer dead ends overall."""
    for row in grid.cells:
        for cell in row:
            if int(cell.walls).bit_count() != 3:
                continue

            closed_directions = [
                direction for direction in DIRECTIONS
                if cell.walls & direction
                and get_neighbor(grid, cell, direction) is not None
            ]
            pma.random_instance.shuffle(closed_directions)

            for direction in closed_directions:
                if safely_open_wall(grid, cell, direction):
                    break


def count_real_dead_ends(grid: Grid) -> int:
    """Count dead-end cells (exactly 3 closed walls) that still have a
    closed wall leading to a real, non-blocked neighbour. Matches the
    "real" vs "42-enclosed" classification maze_analyzer.py itself uses to
    grade the dead-end tolerance in the subject's IV.4 non-perfect mode."""
    real_dead_ends = 0
    for row in grid.cells:
        for cell in row:
            if int(cell.walls).bit_count() != 3:
                continue
            for direction in DIRECTIONS:
                if not (cell.walls & direction):
                    continue
                neighbor = get_neighbor(grid, cell, direction)
                if neighbor is not None and not neighbor.blocked:
                    real_dead_ends += 1
                    break
    return real_dead_ends


def imperfect_algo(grid: Grid, cell: Cell) -> None:
    """Generate a non-perfect maze: start from a perfect maze, then open
    the corners and the center, remove some random interior walls to
    create loops, and finally reduce dead ends. Every wall removal here
    goes through the same safety check, so the "42" pattern always stays
    closed and no 2x2 area ever opens up fully."""
    pma.perfect_algo(grid, cell)
    open_the_four_corners(grid)
    open_the_center(grid)
    remove_random_interior_walls(grid, percentage=10)
    remove_dead_ends(grid)
