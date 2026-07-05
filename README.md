*This project has been created as part of the 42 curriculum by casgarna, ktaher.*

# A-maze-ing

## Description

A-maze-ing is a Python maze generator and solver built for the 42 curriculum. Given a
plain-text configuration file, it generates a maze (perfect by default, meaning exactly
one path between the entry and the exit), writes it to a file using a hexadecimal wall
representation, and displays it — either as ASCII art in the terminal, or as an
interactive graphical window using MiniLibX (MLX). The maze always contains a visible
"42" shape made of permanently closed cells, unless the maze is too small to fit it, in
which case an error is printed and generation continues without it.

The maze-generation logic is also packaged as a standalone, pip-installable module
(`mazegen`) so it can be reused in other projects independently of this CLI.

## Instructions

Requirements: Python 3.10 or later. `flake8`, `mypy`, and `build` are only needed for
linting and packaging, not for running the maze generator itself.

```bash
git clone <this repository>
cd A-maze-ing
make install        # installs flake8, mypy, build (dev tools only)
make run             # runs: python3 a_maze_ing.py config.txt
make debug            # same, through Python's pdb debugger
make lint             # flake8 . and the subject's mandatory mypy flags
make lint-strict       # flake8 . and mypy --strict (optional, stronger)
make clean              # removes __pycache__ and .mypy_cache
```

Two extra, non-mandatory targets:
```bash
make visualize   # opens the interactive MLX graphical window instead of ASCII
make package     # rebuilds mazegen-0.1.0-py3-none-any.whl from source
```

It's recommended to use a virtual environment during development
(`python3 -m venv venv && source venv/bin/activate`), per the subject's own guidelines.

## Configuration File

One `KEY=VALUE` pair per line; lines starting with `#` are comments and are ignored.

```
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
```

| Key | Description |
|---|---|
| `WIDTH` | Maze width, in cells |
| `HEIGHT` | Maze height, in cells |
| `ENTRY` | Entry coordinates, as `x,y` |
| `EXIT` | Exit coordinates, as `x,y` |
| `OUTPUT_FILE` | Path to write the generated maze to |
| `PERFECT` | `True` for exactly one path between entry and exit; `False` is accepted but not yet implemented (falls back to a perfect maze with a printed note) |

A default `config.txt` matching this exact format is included at the repository root.

## Chosen Maze Algorithm

**Generation**: a randomized recursive backtracker (a seeded depth-first search). Chosen
because it directly guarantees a *perfect* maze — a spanning tree — as a natural
consequence of how it works (exactly one wall removed per newly visited cell), rather
than needing extra logic bolted on afterward. That same spanning-tree property also
automatically satisfies two other subject requirements for free: no fully open 2x2 area
can ever exist (that would require a cycle, which a tree cannot contain), and every
reachable cell is guaranteed connected with no isolated cells.

**Solving**: a flood fill (breadth-first search) from the entry to the exit. Since a
perfect maze has exactly one path between any two cells, a flood fill finds that one
path directly, and it is automatically the shortest one, in time proportional to the
number of cells.

## Reusable Package (`mazegen`)

The generation (and, since it's bundled in the same package, the graphical
visualization) logic lives in a standalone module, installable via
`mazegen-0.1.0-py3-none-any.whl` (built from `src/mazegen/`, see `make package` above).

```python
from mazegen import MazeGenerator

generator = MazeGenerator(width=20, height=15, entry=(0, 0), exit=(19, 14), seed=42)
grid = generator.generate()             # a Grid of Cell objects (walls, x, y, blocked)
path = generator.get_solution()         # e.g. ["N", "E", "E", "S", ...]
generator.visualize()                   # optional: opens the MLX graphical window
```

`seed` is optional; passing the same one always reproduces the identical maze.
`get_structure()` returns the generated `Grid` without needing to call `generate()`
again.

## Visual Representation

- **ASCII** (`ascii_display`, always available, no extra setup): prints the maze using
  `+`/`-`/`|` characters directly in the terminal.
- **MLX** (bonus, `make visualize` or `generator.visualize()`): an interactive window
  showing walls, a colored entry/exit, the "42" pattern, and (toggleable) the solution
  path, with keyboard controls: `1` regenerate, `2` show/hide path, `3` rotate wall
  colors, `4`/Esc quit. Needs the vendored MiniLibX source compiled first
  (`sh vendor/build_mlx.sh`) — see `WALKTHROUGH.md` for the full story of how that works
  and why.

## Team & Project Management

**Roles**:
- **Casie Lynn Garnatz** — the core maze data model (`Grid`/`Cell`/`Walls`), the
  recursive-backtracker generation algorithm, and placing the "42" pattern.
- **Karim Taher** — configuration parsing and validation, the `MazeGenerator` wrapper
  class and packaging, CLI wiring (`a_maze_ing.py`), the flood-fill solver, and the MLX
  graphical visualizer.

**Planning & evolution**: work started with config parsing (nothing else needs the maze
itself yet), then the core data model and generation algorithm, then the reusable
`MazeGenerator` class and `.whl` packaging, then wiring it all into the CLI. The "42"
pattern and a real solver came next, and the MLX visualizer was added afterward as a
bonus once the ASCII/ text pipeline was already fully working.

**What worked well**: splitting ownership by file (data model and algorithm vs.
config/packaging/CLI) meant both halves could be built and tested independently before
being wired together, which is also what caught two real bugs early (a stale import
depending on a file outside the installable package, and a `src`/`mazegen` naming clash
that only `mypy .` run across the whole project surfaced).

**What could be improved**: `SEED` isn't yet exposed through `config.txt` itself (only
through the `MazeGenerator(seed=...)` Python API) — the CLI always generates a fresh maze
rather than a reproducible one from the config file. The mandatory output-file format
(Chapter IV.5) is also still missing its trailing entry/exit/solution-path block. The
non-perfect (braided) maze mode described by `PERFECT=False` isn't implemented yet either.

**Tools used**: Python 3.10+, `flake8`, `mypy`, `Makefile`-based task automation, `git`,
and MiniLibX (bonus, graphical visualization only).

## Resources

- [Writing your pyproject.toml — Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Python Bitwise Operators — W3Schools](https://www.w3schools.com/python/python_operators_bitwise.asp)
- [Python 2D Arrays/Lists the Right Way — GeeksforGeeks](https://www.geeksforgeeks.org/python/python-using-2d-arrays-lists-the-right-way/)
- [Python random module — W3Schools](https://www.w3schools.com/python/module_random.asp)
- [MiniLibX documentation (Gontjarow)](https://gontjarow.github.io/MiniLibX/)

**How AI was used**: AI assistance (Claude) was used specifically for two things —
building the MLX/`ctypes` graphical visualizer (vendoring and cross-platform-building
MiniLibX, and writing the Python-to-C ctypes bridge, an area neither of us had prior
experience with) and structuring/writing this README. The maze generation algorithm,
the solver, configuration parsing, and packaging were designed and written by the team
directly.
