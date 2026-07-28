*This project has been created as part of the 42 curriculum by ktaher, casgarna.*

# A-maze-ing

## Description

A-maze-ing is a Python maze generator and solver built for the 42 curriculum. Given a
plain-text configuration file, it generates a maze, either perfect (exactly one path
between entry and exit) or non-perfect (looped, with multiple routes), writes it to a
file using a hexadecimal wall representation plus the entry, exit, and solution path,
and displays it interactively, either as colored ASCII art in the terminal, or as a
graphical MLX window. The maze always contains a visible "42" shape made of permanently
closed cells, unless the maze is too small to fit it, in which case an error is printed
and generation continues without it.

The maze-generation logic is also packaged as a standalone, pip-installable module
(`mazegen`) so it can be reused in other projects independently of this CLI.

## Instructions

How to run and test this, step by step. This section assumes no prior coding
experience. Every command below is meant to be
typed exactly as written, into a program called "Terminal" (on macOS) or a terminal
application on Linux.

**1. Open a terminal and go to the project folder.**
```bash
cd A-maze-ing
```

**2. Check your Python version (must be 3.10 or later).**
```bash
python3 --version
```
If this prints something below `3.10` (this can happen on some Macs, where the
built-in `python3` is older than that), install a newer Python (e.g.
[python.org](https://www.python.org/downloads/) or `brew install python@3.11`), then
create and activate a virtual environment with it before continuing:
```bash
python3.11 -m venv venv
source venv/bin/activate
```

**3. Install the project's dependencies.**
```bash
make install
```
This creates a `venv/` folder (a self-contained space for installing tools, so they
don't interfere with anything else already on your machine; the subject itself
recommends this) and installs `flake8`/`mypy` (checks the code for mistakes), `build`
(packages the project), and, on Linux only, the graphical `mlx` library (see "Visual
Representation" below for why Mac is different) into it. This is also why plain
`pip install ...` typically fails on a fresh Ubuntu/Debian machine (including WSL) with
an "externally-managed-environment" error: modern Linux blocks installing Python
packages system-wide by default, so `make install` avoids that entirely by using its own
`venv/` instead. You don't need to activate it yourself, since every `make` command
already knows to use it.

**4. Run the maze generator.**
```bash
make run
```
This is identical to running `python3 a_maze_ing.py config.txt` directly. `config.txt`,
already included in this folder, is the settings file it reads. A maze appears in the
terminal immediately, followed by a small numbered menu:
```
1) Regenerate maze
2) Show solution path
3) Change wall color
4) Quit
Choice? (1-4):
```
Type a number and press Enter to try each option. Type `4` and press Enter to stop.

**5. Look at the file it produced.**
```bash
cat maze.txt
```
This is the actual result of the program: one line of letters/numbers per row of the
maze (its walls, in hexadecimal), then a blank line, then the entry coordinates, the
exit coordinates, and the solution path. This is explained in full further down.

**6. Check the maze is actually valid**, using the checker tool provided with this
project's assignment:
```bash
python3 maze_analyzer.py maze.txt
```
This prints a report confirming the maze has no broken walls, is fully reachable, and
(if `PERFECT=True` in `config.txt`) has exactly one solution.

**7. Run the code-quality checks.**
```bash
make lint
```
This should finish with no errors printed at all. If you see error messages, something
in the code doesn't meet the project's requirements.

**8. Test the reusable package, in total isolation**:
```bash
python3 -m venv /tmp/test_environment
source /tmp/test_environment/bin/activate
pip install build
python3 -m build
pip install dist/mazegen-0.1.0-py3-none-any.whl
python3 -c "from mazegen import MazeGenerator; g = MazeGenerator(width=10, height=10, seed=1); g.generate(); print('It works:', g.get_solution())"
deactivate
```

**9. Optional: the graphical version (Linux only).**
```bash
make visualize
```
Opens an interactive window instead of the terminal display, with the same 4 controls.
This only works on Linux (see "Visual Representation" below). Running it on macOS will
show a "No module named mlx" error, which is expected, not a bug.

**10. Clean up afterward.**
```bash
make clean
```
Removes temporary files Python created while running (`__pycache__`, `.mypy_cache`).
Safe to run any time; nothing important is deleted.

## Configuration File

One `KEY=VALUE` pair per line; lines starting with `#` are comments and are ignored.

```
WIDTH=15
HEIGHT=19
ENTRY=0,0
EXIT=13,4
OUTPUT_FILE=maze.txt
PERFECT=False
#SEED=42
```

| Key | Description |
|---|---|
| `WIDTH` | Maze width, in cells |
| `HEIGHT` | Maze height, in cells |
| `ENTRY` | Entry coordinates, as `x,y` |
| `EXIT` | Exit coordinates, as `x,y` |
| `OUTPUT_FILE` | Path to write the generated maze to |
| `PERFECT` | `True` for exactly one path between entry and exit; `False` for a looped maze with multiple routes |
| `SEED` | Optional. Any whole number always reproduces the exact same maze; leave it out for a fresh maze every run |

A default `config.txt` matching this exact format is included at the repository root.

## Output File Format

```
D539553955553D517913
97C693C69553C53C56AA
...one line of hex digits per maze row...

0,0
19,14
EESENEEESENEEEEESEESSENEEENNESSSSWWWSWNWSSSENESSSWSESSESSENNNESSS
```
Each hex digit is one cell's walls, as a 4-bit number: bit 0 (North), bit 1 (East),
bit 2 (South), bit 3 (West). A set bit means that wall is closed. After a blank line:
the entry coordinates, the exit coordinates, and the shortest path from entry to exit as
a string of `N`/`E`/`S`/`W` letters.

## Chosen Maze Algorithm

**Generation (perfect)**: a randomized recursive backtracker (a seeded depth-first
search). Chosen because it directly guarantees a *perfect* maze, a spanning tree, as a
natural consequence of how it works (exactly one wall removed per newly visited cell),
rather than needing extra logic bolted on afterward. That same spanning-tree property
also automatically satisfies two other subject requirements for free: no fully open 2x2
area can ever exist (that would require a cycle, which a tree cannot contain), and every
reachable cell is guaranteed connected with no isolated cells.

**Generation (non-perfect)**: starts from the same perfect maze, then opens the four
corners and the center, randomly removes a percentage of the remaining interior walls,
and finally reduces dead-ends. Every single one of those wall removals is checked first
(no touching the "42" pattern, no creating an illegal 2x2 open block) before being
applied. This produces a maze with loops and multiple valid routes between entry and
exit, as the subject describes for `PERFECT=False`.

**Solving**: a flood fill (breadth-first search) from the entry to the exit. This finds
the shortest path regardless of whether the maze is perfect or has loops, in time
proportional to the number of cells.

## Reusable Package (`mazegen`)

The generation (and, since it's bundled in the same package, the graphical
visualization) logic lives in a standalone module, installable via
`mazegen-0.1.0-py3-none-any.whl` (built from `src/mazegen/`, see step 8 above, or
`make package`).

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

- **ASCII** (always available, no extra setup): `make run` prints the maze directly in
  the terminal, marking the entry (`S`), the exit (`X`), and, when toggled on, the
  solution path (`.`), in a rotating choice of colors, with a menu to regenerate,
  toggle the path, and change color, right there in the same command the subject
  mandates (`python3 a_maze_ing.py config.txt`).
- **MLX** (bonus, `make visualize` or `generator.visualize()`): the same controls in a
  graphical window instead. Uses the official `mlx` package provided with the subject
  (`vendor/mlx-2.2.tgz`; `make install` or `sh vendor/install_mlx.sh` installs the
  right prebuilt wheel for Ubuntu/Fedora). **Linux only**, since there is no macOS build
  in what was provided, so this specific feature can't be tested on a Mac. The terminal
  version above already fully satisfies the requirement on its own, on any platform.

## Bonuses

- **No dead-end at all in the default (`PERFECT=False`) mode**: the non-perfect
  generator is tuned to leave zero real dead-ends (only the "42" pattern's two
  enclosed cells remain, which are tolerated by design). Verify it with:
  `python3 maze_analyzer.py maze.txt --max-dead-ends 0`.
- **MLX graphical visualizer**: an interactive graphical window (see "Visual
  Representation" above), on top of the always-available ASCII terminal display.

## Team & Project Management

**Roles**:
- **Casie Lynn Garnatz**: the core maze data model (`Grid`/`Cell`/`Walls`), the
  recursive-backtracker generation algorithm, the "42" pattern, and the non-perfect
  (looped) generation mode.
- **Karim Taher**: configuration parsing and validation, the `MazeGenerator` wrapper
  class and packaging, CLI wiring and interactivity, the flood-fill solver, and the MLX
  graphical visualizer.

**Planning & evolution**: work started with config parsing (nothing else needs the maze
itself yet), then the core data model and generation algorithm, then the reusable
`MazeGenerator` class and `.whl` packaging, then wiring it all into the CLI. The "42"
pattern and a real solver came next, then the MLX visualizer, then the non-perfect
generation mode, and finally a full pass against the subject to close every remaining
gap: the output file's footer, seed support in the config file, the terminal
interactivity, and a real bug in the non-perfect mode that could produce an illegal
open area.

**What worked well**: splitting ownership by file (data model and algorithms vs.
config/packaging/CLI/visualizer) let both halves be built and tested independently
before being wired together, which is also what caught several real bugs early: a
stale import depending on a file outside the installable package, a `src`/`mazegen`
mypy naming clash, and a stale `.whl` that didn't match current source.

**What could be improved**: no automated test suite exists yet.

**Tools used**: Python 3.10+, `flake8`, `mypy`, `Makefile`, `git`, and the official `mlx`
package (bonus, graphical visualization only).

## Resources

- [Writing your pyproject.toml — Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Python Bitwise Operators — W3Schools](https://www.w3schools.com/python/python_operators_bitwise.asp)
- [Python 2D Arrays/Lists the Right Way — GeeksforGeeks](https://www.geeksforgeeks.org/python/python-using-2d-arrays-lists-the-right-way/)
- [Python random module — W3Schools](https://www.w3schools.com/python/module_random.asp)

**How AI was used**: AI assistance was used for two specific, scoped tasks: integrating
the MLX graphical visualizer (wiring the provided `mlx` package into the project), and
structuring/writing this README. The maze generation and solving algorithms,
configuration parsing, and packaging were designed and written by the team directly.
