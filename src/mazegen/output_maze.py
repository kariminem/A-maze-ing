#!/usr/bin/env python3

from .structure import Grid, Walls


def put_hex_maze(
    grid: Grid,
    entry: tuple[int, int],
    exit: tuple[int, int],
    path: list[str],
    filename: str = "output_maze.txt",
) -> None:
    """Write the maze to a file: one hex digit per cell, then a blank
    line, then the entry coordinates, exit coordinates, and solution
    path, exactly as the subject's output file format requires."""
    with open(filename, "w") as f:
        for row in grid.cells:
            for cell in row:
                f.write(f"{cell.walls:X}")
            f.write("\n")

        f.write("\n")
        f.write(f"{entry[0]},{entry[1]}\n")
        f.write(f"{exit[0]},{exit[1]}\n")
        f.write("".join(path) + "\n")


def ascii_display(
    grid: Grid,
    entry: tuple[int, int] | None = None,
    exit: tuple[int, int] | None = None,
    path_cells: set[tuple[int, int]] | None = None,
) -> None:
    """Display the maze as ASCII art in the terminal, marking the entry
    (S), the exit (X), and, if given, the solution path (.)."""
    for row in grid.cells:
        top_line = ""
        for cell in row:
            if cell.walls & Walls.NORTH:
                top_line += "+---"
            else:
                top_line += "+   "
        top_line += "+"
        print(top_line)

        middle_line = ""
        for cell in row:
            if cell.walls & Walls.WEST:
                middle_line += "|"
            else:
                middle_line += " "

            position = (cell.x, cell.y)
            if entry is not None and position == entry:
                middle_line += " S "
            elif exit is not None and position == exit:
                middle_line += " X "
            elif path_cells is not None and position in path_cells:
                middle_line += " . "
            else:
                middle_line += "   "

        if row[-1].walls & Walls.EAST:
            middle_line += "|"
        else:
            middle_line += " "
        print(middle_line)

    bottom_line = ""
    bottom_row = grid.cells[-1]
    for cell in bottom_row:
        if cell.walls & Walls.SOUTH:
            bottom_line += "+---"
        else:
            bottom_line += "+   "
    bottom_line += "+"
    print(bottom_line)
