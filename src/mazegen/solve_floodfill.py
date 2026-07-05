#!/usr/bin/env python3

from __future__ import annotations

from collections import deque

from .structure import Cell, Grid, Walls


# Each entry stores:
#   - how far to move on the x-axis (dx)
#   - how far to move on the y-axis (dy)
#   - which wall bit must be OPEN on the current cell to be allowed to
#     step that way
# The single-letter path codes this project writes to the output file
# (N, E, S, W) are simply the first letter of each of these names.
DIRECTIONS: dict[str, tuple[int, int, Walls]] = {
    "North": (0, -1, Walls.NORTH),
    "East": (1, 0, Walls.EAST),
    "South": (0, 1, Walls.SOUTH),
    "West": (-1, 0, Walls.WEST),
}


def get_walkable_neighbors(grid: Grid, cell: Cell) -> list[tuple[Cell, str]]:
    """Find every neighboring cell we are allowed to walk into from here."""
    walkable_neighbors = []

    for direction_name, (dx, dy, wall) in DIRECTIONS.items():
        wall_is_closed = cell.walls & wall
        if wall_is_closed:
            # There is a wall in this direction, so we cannot walk
            # through it. Move on and check the next direction instead.
            continue

        neighbor_x = cell.x + dx
        neighbor_y = cell.y + dy

        # Make sure this neighbor is actually still inside the maze,
        # and that we have not accidentally stepped off the edge of
        # the grid.
        is_inside_grid = (
            0 <= neighbor_x < grid.width and 0 <= neighbor_y < grid.height
        )
        if is_inside_grid:
            neighbor_cell = grid.cells[neighbor_y][neighbor_x]
            direction_letter = direction_name[0]  # "North" becomes "N"
            walkable_neighbors.append((neighbor_cell, direction_letter))

    return walkable_neighbors


def solve(
    grid: Grid, entry: tuple[int, int], exit: tuple[int, int]
) -> list[str]:
    """Find the path from the entry to the exit, one step at a time.

    Returns the path as a list of single-letter directions (for example
    ["N", "N", "E", "S"]) describing how to walk from the entry all the
    way to the exit, one cell at a time.
    """
    entry_x, entry_y = entry
    exit_x, exit_y = exit
    start_cell = grid.cells[entry_y][entry_x]
    goal_cell = grid.cells[exit_y][exit_x]

    # The "breadcrumb trail": the first time we ever step into a new
    # cell, we drop a breadcrumb pointing back at the cell we came from
    # (and which direction we walked to get here). Once we reach the
    # goal, we can follow these breadcrumbs backwards, cell by cell, all
    # the way back to the start, to reconstruct the full path.
    breadcrumb_trail: dict[Cell, tuple[Cell, str]] = {}

    # Every cell we have already visited, so we never walk into the same
    # cell twice and end up going around in circles.
    visited_cells = {start_cell}

    # The "todo list" of cells we still need to explore, kept in the
    # order we discovered them. This is what makes it a flood fill: we
    # always explore the oldest, closest cells first, one whole ring at
    # a time -- exactly like water spreading out evenly from the
    # entrance, rather than rushing off down one single corridor first.
    todo_list: deque[Cell] = deque([start_cell])

    reached_the_goal = False

    while todo_list:
        # Take the next cell off the front of the todo list, and
        # explore outward from there.
        current_cell = todo_list.popleft()

        if current_cell is goal_cell:
            # We just reached the exit! We can stop exploring now.
            reached_the_goal = True
            break

        for neighbor_cell, direction_letter in get_walkable_neighbors(
            grid, current_cell
        ):
            if neighbor_cell in visited_cells:
                # We have already been to this cell before, so there is
                # no need to visit it again.
                continue

            visited_cells.add(neighbor_cell)

            # Drop a breadcrumb here: "to reach neighbor_cell, you came
            # from current_cell by walking in this direction."
            breadcrumb_trail[neighbor_cell] = (
                current_cell, direction_letter,
            )

            # Add this newly found cell to the end of the todo list, so
            # it gets explored later, only after all the cells that are
            # closer to the entrance have been explored first.
            todo_list.append(neighbor_cell)

    if not reached_the_goal:
        # This should never happen in a valid perfect maze (every cell
        # is reachable from every other cell), but we check for it
        # anyway rather than silently returning a broken path.
        raise ValueError("no path exists between entry and exit")

    # Now walk the breadcrumb trail backwards: start at the exit, and
    # keep following each breadcrumb back towards the entrance, one
    # step at a time, until we arrive back at the very first cell.
    path_steps: list[str] = []
    cell_we_are_looking_at = goal_cell

    while cell_we_are_looking_at is not start_cell:
        previous_cell, direction_letter = breadcrumb_trail[
            cell_we_are_looking_at
        ]
        path_steps.append(direction_letter)
        cell_we_are_looking_at = previous_cell

    # We built the path backwards (from the exit back to the entry), so
    # reverse it now to get the correct entry-to-exit order before
    # handing it back.
    path_steps.reverse()

    return path_steps
