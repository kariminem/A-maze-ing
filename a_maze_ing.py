#!/usr/bin/env python3

import random
import sys
from typing import cast

from config import AmazingExceptions, load_config
from src.mazegen.generator import MazeGenerationError, MazeGenerator
from src.mazegen.output_maze import ascii_display, put_hex_maze

WALL_COLORS = ["\033[37m", "\033[33m", "\033[32m", "\033[36m", "\033[35m"]
RESET_COLOR = "\033[0m"

STEP_FOR_LETTER = {
    "N": (0, -1),
    "E": (1, 0),
    "S": (0, 1),
    "W": (-1, 0),
}


def path_to_cells(
    entry: tuple[int, int], path: list[str]
) -> set[tuple[int, int]]:
    """Turn a list of N/E/S/W letters into the set of (x, y) cells the
    path passes through, starting at entry."""
    x, y = entry
    cells = {(x, y)}
    for letter in path:
        change_x, change_y = STEP_FOR_LETTER[letter]
        x, y = x + change_x, y + change_y
        cells.add((x, y))
    return cells


def save_maze(generator: MazeGenerator, output_file: str) -> list[str]:
    """Write the current maze to the output file and return its
    solution path."""
    try:
        path = generator.get_solution()
    except (NotImplementedError, ValueError) as exc:
        print(f"Warning: could not compute a solution path: {exc}")
        path = []

    put_hex_maze(
        generator.get_structure(),
        generator.entry,
        generator.exit,
        path,
        output_file,
    )
    return path


def show_maze(
    generator: MazeGenerator,
    path: list[str],
    show_path: bool,
    color_index: int,
) -> None:
    """Print the maze to the terminal, in the current wall color, with
    the solution path shown if requested."""
    path_cells = path_to_cells(generator.entry, path) if show_path else None
    print(WALL_COLORS[color_index], end="")
    ascii_display(
        generator.get_structure(), generator.entry, generator.exit,
        path_cells,
    )
    print(RESET_COLOR, end="")


def run_menu(
    generator: MazeGenerator, output_file: str, path: list[str]
) -> None:
    """The required user interactions: regenerate, show/hide the
    solution path, and change the wall color."""
    show_path = False
    color_index = 0

    while True:
        print("1) Regenerate maze")
        print(f"2) {'Hide' if show_path else 'Show'} solution path")
        print("3) Change wall color")
        print("4) Quit")

        try:
            choice = input("Choice? (1-4): ").strip()
        except EOFError:
            break

        if choice == "1":
            generator.seed = random.randrange(2**32)
            generator.generate()
            path = save_maze(generator, output_file)
        elif choice == "2":
            show_path = not show_path
        elif choice == "3":
            color_index = (color_index + 1) % len(WALL_COLORS)
        elif choice == "4":
            break
        else:
            print("Invalid choice, please pick 1-4.")
            continue

        show_maze(generator, path, show_path, color_index)


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
    entry = cast(list[int], cfg["ENTRY"])
    exit_coords = cast(list[int], cfg["EXIT"])
    perfect = cast(bool, cfg["PERFECT"])
    output_file = cast(str, cfg["OUTPUT_FILE"])
    seed = cast("int | None", cfg["SEED"])

    try:
        generator = MazeGenerator(
            width=width,
            height=height,
            entry=(entry[0], entry[1]),
            exit=(exit_coords[0], exit_coords[1]),
            seed=seed,
            perfect=perfect,
        )
        generator.generate()
    except MazeGenerationError as exc:
        print(f"Invalid maze parameters: {exc}")
        sys.exit(1)

    path = save_maze(generator, output_file)
    show_maze(generator, path, show_path=False, color_index=0)
    run_menu(generator, output_file, path)


if __name__ == "__main__":
    main()
