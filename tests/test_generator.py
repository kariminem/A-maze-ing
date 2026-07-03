#!/usr/bin/env python3
"""Unit tests for the MazeGenerator reusable class."""

import unittest

from src.mazegen.generator import MazeGenerationError, MazeGenerator


def popcount(value: int) -> int:
    """Count set bits in an int (Python 3.10+ has int.bit_count, kept
    explicit here in case tests run under an older interpreter)."""
    return bin(value).count("1")


class TestMazeGeneratorValidation(unittest.TestCase):
    def test_non_positive_dimensions_raise(self) -> None:
        with self.assertRaises(MazeGenerationError):
            MazeGenerator(width=0, height=5)
        with self.assertRaises(MazeGenerationError):
            MazeGenerator(width=5, height=-1)

    def test_out_of_bounds_entry_raises(self) -> None:
        with self.assertRaises(MazeGenerationError):
            MazeGenerator(width=5, height=5, entry=(5, 0))

    def test_out_of_bounds_exit_raises(self) -> None:
        with self.assertRaises(MazeGenerationError):
            MazeGenerator(width=5, height=5, exit=(0, 5))

    def test_entry_equals_exit_raises(self) -> None:
        with self.assertRaises(MazeGenerationError):
            MazeGenerator(width=5, height=5, entry=(2, 2), exit=(2, 2))

    def test_default_exit_is_bottom_right(self) -> None:
        generator = MazeGenerator(width=4, height=3)
        self.assertEqual(generator.exit, (3, 2))


class TestMazeGeneratorGeneration(unittest.TestCase):
    def test_get_structure_before_generate_raises(self) -> None:
        generator = MazeGenerator(width=5, height=5)
        with self.assertRaises(MazeGenerationError):
            generator.get_structure()

    def test_generate_returns_full_size_grid(self) -> None:
        generator = MazeGenerator(width=6, height=4, seed=1)
        grid = generator.generate()
        self.assertEqual(grid.width, 6)
        self.assertEqual(grid.height, 4)
        self.assertIs(generator.get_structure(), grid)

    def test_same_seed_is_reproducible(self) -> None:
        walls_a = MazeGenerator(width=8, height=8, seed=42).generate()
        walls_b = MazeGenerator(width=8, height=8, seed=42).generate()

        for row_a, row_b in zip(walls_a.cells, walls_b.cells):
            for cell_a, cell_b in zip(row_a, row_b):
                self.assertEqual(cell_a.walls, cell_b.walls)

    def test_perfect_maze_is_a_spanning_tree(self) -> None:
        width, height = 5, 7
        grid = MazeGenerator(width=width, height=height, seed=7).generate()

        # Every wall removal clears one bit on each of the two neighboring
        # cells, so the total number of open (cleared) bits across the grid
        # must equal 2 * (number of edges in a spanning tree of w*h nodes).
        open_bits = sum(
            4 - popcount(int(cell.walls))
            for row in grid.cells
            for cell in row
        )
        self.assertEqual(open_bits, 2 * (width * height - 1))

    def test_get_solution_without_solver_raises_not_implemented(self) -> None:
        generator = MazeGenerator(width=4, height=4, seed=1)
        generator.generate()
        with self.assertRaises(NotImplementedError):
            generator.get_solution()


if __name__ == "__main__":
    unittest.main()
