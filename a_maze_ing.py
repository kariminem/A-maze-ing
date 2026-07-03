#!/usr/bin/env python3

import sys
from typing import cast

from config import AmazingExceptions, load_config
from src.mazegen.generator import MazeGenerationError, MazeGenerator
from src.mazegen.output_maze import ascii_display, put_hex_maze


def main() -> None:
    """Parse the config file given on the command line, generate the maze
    it describes, write it to the configured output file, and display it.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        cfg = load_config(config_file)
    except FileNotFoundError:
        print(f"Config file not found: {config_file}")
        sys.exit(1)
    except AmazingExceptions as exc:
        print(f"Invalid configuration: {exc}")
        sys.exit(1)

    width = cast(int, cfg["WIDTH"])
    height = cast(int, cfg["HEIGHT"])
    entry = cast(list, cfg["ENTRY"])
    exit_coords = cast(list, cfg["EXIT"])
    perfect = cast(bool, cfg["PERFECT"])
    output_file = cast(str, cfg["OUTPUT_FILE"])

    if not perfect:
        print(
            "Note: non-perfect maze generation isn't implemented yet; "
            "generating a perfect maze instead."
        )

    try:
        generator = MazeGenerator(
            width=width,
            height=height,
            entry=(entry[0], entry[1]),
            exit=(exit_coords[0], exit_coords[1]),
            perfect=perfect,
        )
        grid = generator.generate()
    except MazeGenerationError as exc:
        print(f"Invalid maze parameters: {exc}")
        sys.exit(1)

    put_hex_maze(grid, output_file)
    ascii_display(grid)


if __name__ == "__main__":
    main()
