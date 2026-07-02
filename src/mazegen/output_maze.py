#!/usr/bin/env python3

from .structure import Grid, Walls


def put_hex_maze(grid: Grid) -> None:
    """print hexa putput in output_maze.txt"""
    with open("output_maze.txt", "w") as f:
        for row in grid.cells:
            for cell in row:
                f.write(f"{cell.walls:X}")  # :X -> format specifiyer: display in uppercase hex
            f.write("\n")


def ascii_display(grid: Grid) -> None:
    """displaying the maze with Terminal ASCII rendering"""
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
