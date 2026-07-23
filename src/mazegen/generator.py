#!/usr/bin/env python3

import random
from typing import cast

from . import perfect_maze_algo as pma
from . import imperfect_maze as ipma
from .structure import Grid


class MazeGenerationError(Exception):
    """Raised when maze parameters are invalid or used out of order."""


class MazeGenerator:
    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] | None = None,
        seed: int | None = None,
        perfect: bool = True,
    ) -> None:
        if width <= 0 or height <= 0:
            raise MazeGenerationError("width and height must be positive")

        resolved_exit = exit if exit is not None else (width - 1, height - 1)

        for label, (x, y) in (("entry", entry), ("exit", resolved_exit)):
            if not (0 <= x < width and 0 <= y < height):
                raise MazeGenerationError(f"{label} {(x, y)} is out of bounds")

        if entry == resolved_exit:
            raise MazeGenerationError("entry and exit must be different cells")

        self.width = width
        self.height = height
        self.entry = entry
        self.exit = resolved_exit
        self.seed = seed
        self.perfect = perfect
        self._grid: Grid | None = None

    def generate(self) -> Grid:
        if self.seed is not None:
            pma.random_instance = random.Random(self.seed)

        grid = Grid(self.width, self.height)
        entry_x, entry_y = self.entry

        if self.perfect:
            pma.perfect_algo(grid, grid.cells[entry_y][entry_x])
        elif not self.perfect:
            ipma.imperfect_algo(grid, grid.cells[entry_y][entry_x])

        self._grid = grid
        return grid

    def get_structure(self) -> Grid:
        if self._grid is None:
            raise MazeGenerationError(
                "call generate() before accessing the structure"
            )
        return self._grid

    def get_solution(self) -> list[str]:
        grid = self.get_structure()

        try:
            # NOTE: solve_perfect_maze.py also exists (Casie's "starting
            # BFS" stub) but solve_floodfill.py is the file that actually
            # has a working solve() -- see WALKTHROUGH.md, Part 3, for the
            # discrepancy between the two files.
            from .solve_floodfill import solve
        except ImportError as exc:
            raise NotImplementedError(
                "solve_floodfill.solve() is not implemented yet"
            ) from exc

        return cast(list[str], solve(grid, self.entry, self.exit))

    def visualize(self, cell_size: int = 20) -> None:
        """Open an interactive MLX window showing the generated maze."""
        from .visualizer import MlxVisualizer

        MlxVisualizer(self, cell_size=cell_size).run()
