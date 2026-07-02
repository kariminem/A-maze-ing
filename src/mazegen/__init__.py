"""mazegen: a reusable maze generation library.

Basic usage:
    >>> from mazegen import MazeGenerator
    >>> generator = MazeGenerator(width=10, height=10, seed=42)
    >>> grid = generator.generate()

Custom parameters (size, seed, entry/exit, perfect mode):
    >>> generator = MazeGenerator(
    ...     width=20,
    ...     height=15,
    ...     entry=(0, 0),
    ...     exit=(19, 14),
    ...     seed=123,
    ...     perfect=True,
    ... )

Accessing the generated structure and a solution:
    >>> generator.generate()
    >>> grid = generator.get_structure()          # Grid of Cell objects
    >>> path = generator.get_solution()           # e.g. ["N", "E", "E", "S"]
"""

from .generator import MazeGenerationError, MazeGenerator

__all__ = ["MazeGenerator", "MazeGenerationError"]
__version__ = "0.1.0"
