*This project has been created as part of the 42 curriculum by ktaher, casgarna.*

# A-maze-ing

## Description

A-maze-ing is a Python maze generator and solver built for the 42 curriculum. Given a
plain-text configuration file, it generates a maze — perfect (exactly one path between
entry and exit) or non-perfect (looped, with multiple routes) — writes it to a file
using a hexadecimal wall representation, and displays it, either as ASCII art in the
terminal, or as an interactive graphical window using MiniLibX (MLX). The maze always
contains a visible "42" shape made of permanently closed cells, unless the maze is too
small to fit it, in which case an error is printed and generation continues without it.

The maze-generation logic is also packaged as a standalone, pip-installable module
(`mazegen`) so it can be reused in other projects independently of this CLI.

## Instructions

Requirements: Python 3.10 or later. `flake8`, `mypy`, and `build` are only needed for
linting and packaging, not for running the maze generator itself.

```bash
git clone <this repository>
cd A-maze-ing
make install        # installs flake8, mypy, build, and the mlx package (Linux only)
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

`maze_analyzer.py`, provided with the subject, checks an output file's wall coherence
and whether it's a genuine perfect/non-perfect maze:
```bash
python3 maze_analyzer.py maze.txt
```

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
| `PERFECT` | `True` for exactly one path between entry and exit; `False` for a looped maze with multiple routes |

A default `config.txt` matching this exact format is included at the repository root.
`SEED` is not yet a config-file key — reproducibility is available through the
`MazeGenerator(seed=...)` Python API, but not through the CLI's config file yet (see
"What could be improved" below).

## Chosen Maze Algorithm

**Generation (perfect)**: a randomized recursive backtracker (a seeded depth-first
search). Chosen because it directly guarantees a *perfect* maze — a spanning tree — as a
natural consequence of how it works (exactly one wall removed per newly visited cell),
rather than needing extra logic bolted on afterward. That same spanning-tree property
also automatically satisfies two other subject requirements for free: no fully open 2x2
area can ever exist (that would require a cycle, which a tree cannot contain), and every
reachable cell is guaranteed connected with no isolated cells.

**Generation (non-perfect)**: starts from the same perfect maze, then opens the four
corners and the center, randomly removes a percentage of the remaining interior walls
(skipping any that would touch the "42" pattern or create a 2x2 open block), and finally
removes real dead-ends. This produces a maze with loops and multiple valid routes
between entry and exit, as the subject describes for `PERFECT=False`.

**Solving**: a flood fill (breadth-first search) from the entry to the exit. This finds
the shortest path regardless of whether the maze is perfect or has loops, in time
proportional to the number of cells.

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
again. `visualize()` needs the `mlx` package installed (`make install` on Linux); the
rest of the module has no such dependency.

## Visual Representation

- **ASCII** (`ascii_display`, always available, no extra setup): prints the maze using
  `+`/`-`/`|` characters directly in the terminal.
- **MLX** (bonus, `make visualize` or `generator.visualize()`): an interactive window
  showing walls, a colored entry/exit, the "42" pattern, and (toggleable) the solution
  path, with keyboard controls: `1` regenerate, `2` show/hide path, `3` rotate wall
  colors, `4`/Esc quit. Uses the official `mlx` package provided with the subject
  (`vendor/mlx-2.2.tgz`; `make install` or `sh vendor/install_mlx.sh` installs the
  right prebuilt wheel for Ubuntu/Fedora — Linux only, no macOS build).

## Team & Project Management

**Roles**:
- **Casie Lynn Garnatz** — the core maze data model (`Grid`/`Cell`/`Walls`), the
  recursive-backtracker generation algorithm, the "42" pattern, and the non-perfect
  (looped) generation mode.
- **Karim Taher** — configuration parsing and validation, the `MazeGenerator` wrapper
  class and packaging, CLI wiring, the flood-fill solver, and the MLX graphical
  visualizer.

**Planning & evolution**: work started with config parsing (nothing else needs the maze
itself yet), then the core data model and generation algorithm, then the reusable
`MazeGenerator` class and `.whl` packaging, then wiring it all into the CLI. The "42"
pattern and a real solver came next, then the MLX visualizer, and finally the non-perfect
generation mode.

**What worked well**: splitting ownership by file (data model and algorithms vs.
config/packaging/CLI/visualizer) let both halves be built and tested independently
before being wired together, which is also what caught several real bugs early —
a stale import depending on a file outside the installable package, a `src`/`mazegen`
mypy naming clash, and a stale `.whl` that didn't match current source.

**What could be improved** (known gaps, being tracked, not yet fixed):
- The output file's mandatory trailing block (entry coordinates, exit coordinates,
  solution path) isn't written yet — `put_hex_maze()` currently only writes the hex
  grid.
- `SEED` isn't exposed through `config.txt`/the CLI, only through the `MazeGenerator`
  Python API — every CLI run currently generates a fresh, non-reproducible maze.
- Nothing validates that `ENTRY`/`EXIT` don't land on a "42" pattern cell.
- The non-perfect mode's corner- and center-opening steps don't apply the same 2x2-open
  check the interior-wall-removal step uses, so a generated non-perfect maze can
  currently contain an illegal fully-open 2x2 block near those specific cells.
- The regenerate/show-path/change-color interactions currently only exist behind the
  optional MLX path (`make visualize`); the mandated `python3 a_maze_ing.py config.txt`
  command itself has no interactive loop.
- `ascii_display()` shows walls only — no entry/exit/path markers in the always-available
  fallback display.
- No automated test suite exists yet (not graded per the subject, but recommended).

**Tools used**: Python 3.10+, `flake8`, `mypy`, `Makefile`, `git`, and the official `mlx`
package (bonus, graphical visualization only).

## Resources

- [Writing your pyproject.toml — Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Python Bitwise Operators — W3Schools](https://www.w3schools.com/python/python_operators_bitwise.asp)
- [Python 2D Arrays/Lists the Right Way — GeeksforGeeks](https://www.geeksforgeeks.org/python/python-using-2d-arrays-lists-the-right-way/)
- [Python random module — W3Schools](https://www.w3schools.com/python/module_random.asp)

**How AI was used**: AI assistance was used for two specific, scoped tasks — integrating
the MLX graphical visualizer (wiring the provided `mlx` package into the project), and
structuring/writing this README. The maze generation and solving algorithms,
configuration parsing, and packaging were designed and written by the team directly.
