#!/usr/bin/env python3

import random

from . import perfect_maze_algo as pma
from . import imperfect_maze as ipma
from .structure import Grid


class MazeGenerationError(Exception):
    """Raised when maze parameters are invalid or used out of order."""


class MazeGenerator:
    """Builds, stores, and solves one maze.

    Basic usage:
        >>> generator = MazeGenerator(width=10, height=10, seed=42)
        >>> grid = generator.generate()
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] | None = None,
        seed: int | None = None,
        perfect: bool = True,
    ) -> None:
        """Validate the maze parameters and store them for generate().

        Args:
            width: Maze width, in cells.
            height: Maze height, in cells.
            entry: Entry coordinates as (x, y). Defaults to (0, 0).
            exit: Exit coordinates as (x, y). Defaults to the bottom-right
                cell.
            seed: Optional; the same seed always reproduces the same maze.
            perfect: True for exactly one path between entry and exit,
                False for a looped maze with multiple routes.

        Raises:
            MazeGenerationError: Width/height aren't positive, entry/exit
                are out of bounds, or entry and exit are the same cell.
        """
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
        """Generate a new maze and store it as this generator's structure.

        Returns:
            The generated Grid.

        Raises:
            MazeGenerationError: The entry or exit falls on a "42"
                pattern cell.
        """
        if self.seed is not None:
            pma.random_instance = random.Random(self.seed)

        grid = Grid(self.width, self.height)
        entry_x, entry_y = self.entry
        exit_x, exit_y = self.exit

        if grid.cells[entry_y][entry_x].blocked:
            raise MazeGenerationError("entry falls on the '42' pattern")
        if grid.cells[exit_y][exit_x].blocked:
            raise MazeGenerationError("exit falls on the '42' pattern")

        if self.perfect:
            pma.perfect_algo(grid, grid.cells[entry_y][entry_x])
        elif not self.perfect:
            ipma.imperfect_algo(grid, grid.cells[entry_y][entry_x])

        self._grid = grid
        return grid

    def get_structure(self) -> Grid:
        """Return the generated Grid.

        Raises:
            MazeGenerationError: generate() hasn't been called yet.
        """
        if self._grid is None:
            raise MazeGenerationError(
                "call generate() before accessing the structure"
            )
        return self._grid

    def get_solution(self) -> list[str]:
        """Return the shortest path from entry to exit, as N/E/S/W steps."""
        grid = self.get_structure()

        try:
            from .solve_floodfill import solve
        except ImportError as exc:
            raise NotImplementedError(
                "solve_floodfill.solve() is not implemented yet"
            ) from exc

        return solve(grid, self.entry, self.exit)

    def visualize(self, cell_size: int = 20) -> None:
        """Open an interactive MLX window showing the generated maze."""
        from .visualizer import MlxVisualizer

        MlxVisualizer(self, cell_size=cell_size).run()
