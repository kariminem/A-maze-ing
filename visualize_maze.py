#!/usr/bin/env python3

import sys
from typing import cast

from config import AmazingExceptions, load_config
from src.mazegen.generator import MazeGenerationError, MazeGenerator


def main() -> None:
    """Parse the config file, generate the maze, then open the MLX window."""
    if len(sys.argv) != 2:
        print("Usage: python3 visualize_maze.py <config_file>")
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

    try:
        generator = MazeGenerator(
            width=width,
            height=height,
            entry=(entry[0], entry[1]),
            exit=(exit_coords[0], exit_coords[1]),
            perfect=perfect,
        )
        generator.generate()
    except MazeGenerationError as exc:
        print(f"Invalid maze parameters: {exc}")
        sys.exit(1)

    generator.visualize()


if __name__ == "__main__":
    main()
