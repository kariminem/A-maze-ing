# A-maze-ing — Code Walkthrough

Working notes for the team meeting: what every file does, why it's written the
way it is, and who's responsible for which part. Meant to be detailed enough
that either of you could explain any single line of it if asked.

---

## Data flow: what actually happens now

This used to be two disconnected islands (`config.py` printing a dict to
itself, `a_maze_ing.py` hardcoding a 3×3 test grid). That's now wired end to
end — `python3 a_maze_ing.py config.txt` really works:

```
config.txt  →  config.py: load_config()  →  validated dict
                                                    │
                                                    ▼
                              a_maze_ing.py reads cfg["WIDTH"], cfg["HEIGHT"],
                              cfg["ENTRY"], cfg["EXIT"], cfg["PERFECT"] and
                              constructs:
                                  MazeGenerator(
                                      width=width,
                                      height=height,
                                      entry=(entry[0], entry[1]),
                                      exit=(exit_coords[0], exit_coords[1]),
                                      perfect=perfect,
                                  )
                                                    │
                                                    ▼
                              generator.generate() → Grid
                                                    │
                                                    ▼
                    put_hex_maze(grid, cfg["OUTPUT_FILE"])  +  ascii_display(grid)
```

`config.py`'s validated dict is the bridge between "the file format the
subject demands" and "the plain arguments `MazeGenerator` wants." Verified
live: running with `config.txt` (20×15) renders correctly; swapping in an
8×5 config produces a correctly different-sized maze and a matching output
file; a bad value (`WIDTH=abc`) or a missing file both print a clear message
and exit cleanly instead of crashing.

**Still missing from this pipeline:** the entry/exit/solution-path block the
subject requires after the hex grid in the output file — that depends on
Casie's BFS solver, which doesn't exist yet (`get_solution()` still raises
`NotImplementedError`), so it's intentionally left out rather than crash the
whole CLI on it.

---

## Part 1 — Casie's maze core (`src/mazegen/`)

### 1.1 `structure.py` — the data model

```python
class Walls(IntFlag):
    NORTH = 1   # Bit 0
    EAST = 2    # Bit 1
    SOUTH = 4   # Bit 2
    WEST = 8    # Bit 3
```
`IntFlag` is a stdlib enum variant built for exactly this: values that behave
like plain ints (so `f"{walls:X}"` works directly), but that also support
bitwise `|` (combine) and `&` (test/mask). The four values (1, 2, 4, 8) are
each a single bit, so any combination of walls is a unique number 0–15 — one
hex digit. This isn't an arbitrary choice: it's written to match the
subject's required bit table exactly (bit 0=North, 1=East, 2=South, 3=West),
which is what lets the *entire* hex-output requirement collapse into one
`f"{cell.walls:X}"` call later in `output_maze.py` — no separate encoding
step needed anywhere.

```python
OPPOSITE = {Walls.NORTH: Walls.SOUTH, Walls.EAST: Walls.WEST, ...}
```
A lookup table for "the wall on the other side." Needed because knocking
down a wall between two cells means clearing a bit on *both* cells, and each
cell names that same physical wall from its own local direction (my EAST
wall is your WEST wall).

```python
class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = Walls.NORTH | Walls.EAST | Walls.SOUTH | Walls.WEST  # 1111 = 15
        self.visited = False
        self.blocked = False  # reserved for the "42" pattern
```
Every cell starts as a fully sealed box (all 4 bits set = 15 = hex `F`).
`visited` is bookkeeping for the generation algorithm (section 1.2).
`blocked` is a placeholder for later: cells forced to stay permanently
closed to draw the required "42" shape — nothing uses it yet.

```python
class Grid:
    def __init__(self, width, height):
        self.cells: list[list[Cell]] = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(Cell(x, y))
            self.cells.append(row)
```
`cells` is indexed **`[y][x]`** — row-major, i.e. `cells[0]` is the whole top
row, not the leftmost column. This matches how the maze needs to be *read
out* later (the output file is written "one row per line"), and it's why
every place that walks the grid loops `for row in grid.cells: for cell in
row`, not the other way round. Each `Cell` is stamped with its own `(x, y)`
at construction time so nothing downstream has to track coordinates
separately from the cell object itself.

### 1.2 `perfect_maze_algo.py` — the generation algorithm

This implements a **recursive backtracker** (a randomized depth-first
search), one of the classic algorithms named in the subject's foreword.

```python
myseed = 42
random_instance = random.Random(myseed)
```
The key detail: this uses `random.Random(seed)` — its own independent
generator object — instead of the global `random` module. That's what makes
the "reproducibility via a seed" requirement possible: a `Random` instance's
sequence of choices is 100% deterministic for a given seed, so re-running
with the same seed reproduces the identical maze bit-for-bit. (Right now
`myseed` is hardcoded — more on that in section 2.2.)

```python
def perfect_algo(grid, cell):
    cell.visited = True
    unvisited_neighbors = get_unvisited_neighbors(grid, cell)
    while unvisited_neighbors:
        next_cell = random_instance.choice(unvisited_neighbors)
        remove_wall_between(cell, next_cell)
        perfect_algo(grid, next_cell)          # recurse into it
        unvisited_neighbors = get_unvisited_neighbors(grid, cell)  # re-check
```
Walk through it as a story: stand on `cell`, mark it visited, and look at
its unvisited neighbors. Pick one at random, knock the wall down between you
and it, then **recurse — become that neighbor** and repeat the whole process
from there. Eventually you'll reach a cell whose every neighbor is already
visited: the `while` loop there is immediately false, and the function
simply `return`s. That return doesn't end the whole algorithm — it pops back
up to whichever earlier call was waiting on it (Python's own call stack *is*
the backtracking stack — nothing explicit is maintained), which then
re-runs `get_unvisited_neighbors` for *its* cell (some neighbors may have
been claimed by the branch that just finished) and continues from there if
there's anything left, or itself returns if not, popping up another level.
This is why it's called *backtracking*: dead ends unwind naturally through
recursion.

Why this guarantees a **perfect maze**: every cell gets visited exactly
once, and exactly one wall gets removed per new cell visited — that's
`width*height - 1` removed walls total, connecting all `width*height` cells
with the minimum possible number of connections and zero cycles. In graph
theory that's a *spanning tree*. A tree has no cycles, so there is
necessarily exactly one path between any two cells — precisely the
subject's own definition of "perfect." It also means a fully open 2×2 block
can never occur: that would need 4 connections among 4 cells, which forms a
cycle, which a tree structure cannot contain. So the subject's "no open
area wider than 2 cells" rule is automatically satisfied for perfect mazes,
for free, as a side effect of the algorithm — not something enforced
separately.

```python
def get_neighbor(grid, x, y):
    if x < 0 or x >= grid.width or y < 0 or y >= grid.height:
        return None
    return grid.cells[y][x]
```
Pure bounds check. This one function is also, quietly, what guarantees the
subject's "closed external border" requirement: a border cell's
off-grid side always returns `None` here, so that direction is never even
offered as a candidate neighbor, so that wall bit is never touched by
`remove_wall_between` — it stays permanently 1 (closed) from `Cell.__init__`
onward, with no extra code needed to enforce it.

```python
def get_unvisited_neighbors(grid, current):
    north = get_neighbor(grid, current.x, current.y - 1)
    east  = get_neighbor(grid, current.x + 1, current.y)
    south = get_neighbor(grid, current.x, current.y + 1)
    west  = get_neighbor(grid, current.x - 1, current.y)
    ...filters to the ones that exist (not None) and aren't visited yet...
```
Builds the 4 candidate neighbors, keeps only the ones that are both real
(in-bounds) and not yet visited, returns them as a plain list for
`random_instance.choice()` to pick from.

```python
def remove_wall_between(current, neighbor):
    if current.y == neighbor.y:            # same row -> horizontal (E/W) pair
        if neighbor.x == current.x + 1:
            direction_neighbor_wall = Walls.WEST   # neighbor is to our right
        elif neighbor.x == current.x - 1:
            direction_neighbor_wall = Walls.EAST   # neighbor is to our left
        else:
            raise InvalidCoordinates                # not actually adjacent
    else:                                    # different row -> vertical (N/S) pair
        if neighbor.y == current.y - 1:
            direction_neighbor_wall = Walls.SOUTH  # neighbor is above us
        elif neighbor.y == current.y + 1:
            direction_neighbor_wall = Walls.NORTH  # neighbor is below us
        else:
            raise InvalidCoordinates

    direction_current_wall = OPPOSITE[direction_neighbor_wall]
    current.walls  &= ~direction_current_wall
    neighbor.walls &= ~direction_neighbor_wall
```
This is the fiddliest function, so walk it through carefully:
1. First it figures out, purely from comparing `(x, y)` pairs, which
   physical side `neighbor` sits on relative to `current` — and names the
   wall **from the neighbor's own point of view** (`direction_neighbor_wall`).
   E.g. if `neighbor.x == current.x + 1`, the neighbor is one cell to the
   right, so the shared wall, as seen from the neighbor looking back at
   `current`, is the neighbor's **WEST** wall.
2. `direction_current_wall = OPPOSITE[direction_neighbor_wall]` mirrors that
   to get the same physical wall as seen from `current`'s side — if the
   neighbor's side of it is WEST, `current`'s side of the exact same wall is
   EAST. (Same wall, two doors, two names — like a shared apartment wall.)
3. The actual clearing is a bit trick:
   `current.walls &= ~direction_current_wall`. Take `EAST` (binary `0010`),
   invert every bit with `~` → a mask that's `1` everywhere *except* the
   EAST bit. ANDing `current.walls` against that mask leaves every other
   wall untouched but forces the EAST bit specifically to `0` (open),
   regardless of what it was. The same operation runs on `neighbor.walls`
   with the opposite direction, so **both** sides of the shared wall open
   together, in one call — which is exactly the subject's "coherent
   neighboring walls" rule (a wall must be identically open/closed from
   both adjacent cells), satisfied by construction rather than checked
   afterward.
4. The `else: raise InvalidCoordinates` branches (lines 86–90 in the
   current file) are a defensive sanity check for "these two cells aren't
   actually adjacent" — should never trigger in normal use. There are also
   a few leftover debug `print()` statements in that branch (and the
   function is missing a return-type hint) — small cleanup items for later,
   not urgent, but worth flagging as a "still to polish" item rather than
   pretending it's finished.

### 1.3 `output_maze.py` — turning a Grid into visible output

```python
def put_hex_maze(grid):
    with open("output_maze.txt", "w") as f:
        for row in grid.cells:
            for cell in row:
                f.write(f"{cell.walls:X}")
            f.write("\n")
```
Because `Walls` was defined to match the subject's bit table exactly, the
*entire* "write the maze as one hex digit per cell" requirement is this one
line: `:X` formats an int straight into an uppercase hex digit. No separate
encoding step exists (or is needed) anywhere else.

```python
def ascii_display(grid):
    ...
```
Prints the maze using a classic 3-line-per-row ASCII trick:
- **top_line**: for each cell, `"+---"` if its NORTH wall bit is set, else
  `"+   "` (blank) — the `+` marks a corner post, the following 3 chars are
  either a wall dash or empty space. One trailing `+` closes off the row.
- **middle_line**: for each cell, `"|"` if its WEST wall bit is set else
  `" "`, then 3 spaces for the cell's interior — drawing the left edge of
  every cell across the row. After the loop, one extra check on the *last*
  cell's EAST wall draws the row's final right-hand boundary.
- A **bottom_line** is only printed once, after all rows, using the SOUTH
  walls of the very last row. Every other row's bottom edge doesn't need
  its own line because it's already drawn by the *next* row's top_line —
  a cell's SOUTH wall and the cell below it's NORTH wall are the same
  physical wall, guaranteed identical by `remove_wall_between`'s coherence
  guarantee (section 1.2), so printing it twice would be redundant.

### 1.4 `a_maze_ing.py` — now the real CLI entry point

Used to be a hardcoded 3×3 test harness ("TESTING OUTPUT"). It's now the
actual wired-up program (see section 2.4 for the wiring details): reads
`sys.argv[1]`, validates the config via `config.py`, builds a `MazeGenerator`
from it, generates, writes the hex file to the configured `OUTPUT_FILE`, and
calls `ascii_display`. Still calls into Casie's `Grid`/`perfect_algo` the
same way — nothing about her actual generation logic changed, only how it
gets invoked.

---

## Part 2 — Karim's parts

### 2.1 `config.py` — config file parsing & validation

```python
class AmazingExceptions(Exception):
    """base class for handling all exceptions"""

class InvalidWidthInput(AmazingExceptions): ...
class InvalidHeightInput(AmazingExceptions): ...
class MissingConfigInputs(AmazingExceptions): ...
# ...one subclass per failure mode
```
One shared base class, one specific subclass per way the config file can be
wrong. This lets `__main__` catch each failure mode separately and print a
tailored, human-readable message — directly satisfying the subject's
"handle all errors gracefully... always provide a clear error message"
requirement, instead of one generic catch-all that hides *what* went wrong.

```python
def dict_validate(config_dict: dict) -> dict:
    input_params = ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"]
    for i in input_params:
        if i in config_dict.keys():
            continue
        raise MissingConfigInputs
```
**Pass 1**: fail fast — confirm all 6 mandatory keys are present *before*
trying to parse any values, so a missing key is reported as "missing," not
as some confusing downstream type error.

**Pass 2** (the main loop) converts and validates each key according to its
expected shape:
- `WIDTH`/`HEIGHT` → must parse as a positive int.
- `ENTRY`/`EXIT` → split on `","`, both halves converted to int, wrapped in
  `try/except` so any malformed value (missing comma, non-numeric part)
  funnels into `InvalidEntryInput`/`InvalidExitInput` instead of a raw
  crash.
- `OUTPUT_FILE` → just needs to be non-empty.
- `PERFECT` → accepts the literal strings `"True"`/`"False"` (or `1`/`0`)
  and turns them into real Python `bool`s.

**Final check**, after the loop (needs both WIDTH/HEIGHT *and* ENTRY/EXIT
already parsed, hence it's outside the per-key loop): entry/exit coordinates
must fall inside `[0, WIDTH) x [0, HEIGHT)`, else `ExceedingMazeLimit`.

```python
def load_config(config_file: str) -> dict[str, ConfigValue]:
    config_dict: dict[str, str] = {}
    with open(config_file, "r") as f:
        lines = [
            line.strip() for line in f
            if line.strip() != "" and line.strip()[0] != "#"
        ]
        for line in lines:
            key, value = line.split("=", 1)
            config_dict[key.strip()] = value.strip()
    return dict_validate(config_dict)
```
This is the piece that used to only exist inline inside `__main__` (so
nothing else could reuse it). Reads the file through a context manager
(auto-closes it — required by the subject's "resource management" rule),
strips blank lines and `#` comment lines, splits each `KEY=VALUE` line, and
hands the raw dict to `dict_validate`. Extracting this into its own function
is what let `a_maze_ing.py` import and call it directly (section 2.4) instead
of duplicating the file-reading logic.

**Fixed**: `int(value)` inside `dict_validate` used to be able to raise a
bare `ValueError` *before* any of the custom exceptions got a chance to fire
(e.g. `WIDTH=abc` bypassed `InvalidWidthInput` entirely). `WIDTH`/`HEIGHT`
parsing now wraps `int(value)` in its own `try/except ValueError` and raises
the correct custom exception. Every exception in the file now also carries
a real message (e.g. `raise InvalidWidthInput("Invalid Width Input")`
instead of a bare `raise InvalidWidthInput`), so any caller can just do
`except AmazingExceptions as exc: print(exc)` and get a correct, specific
message — instead of duplicating an 8-branch except-chain wherever the
config needs to be loaded (now only written once, reused by both
`config.py`'s own `__main__` and `a_maze_ing.py`).

### 2.2 `generator.py` — the `MazeGenerator` wrapper class

**What it is not**: a second implementation of maze generation. It contains
zero recursive-backtracker logic. Every call that actually builds a maze
delegates straight to Casie's code:
```python
grid = Grid(self.width, self.height)                      # her class
pma.perfect_algo(grid, grid.cells[entry_y][entry_x])       # her function
```

**What it is**: the subject (Chapter VI, "Code reusability requirements")
requires the generation logic to be wrapped in *one class* (their example
name is literally `MazeGenerator`) inside a standalone, pip-installable
module — a clean, documented, validated interface, separate from the raw
internal functions. Casie's code is organized as free functions plus two
data classes; this class is the "front door" placed on top of that for
whoever (or whatever future project) wants to reuse the generator without
learning its internals. Think: her code is the engine, this is the
dashboard.

What it adds beyond just calling her functions:

- **Validation that doesn't exist upstream**: `Grid(0, 5)` or an
  out-of-bounds `entry` currently just misbehaves silently in her code —
  `MazeGenerator.__init__` checks width/height > 0, entry/exit in bounds,
  and entry != exit, raising a clear `MazeGenerationError` (its own local
  exception — deliberately *not* imported from the top-level `config.py`,
  because this package has to remain installable into some other,
  unrelated project later, where `config.py` won't exist).
- **Configurable seeds**: her `perfect_maze_algo.py` currently hardcodes
  `myseed = 42` at module level, so nobody could actually change it. Before
  calling her function, `generate()` does:
  ```python
  if self.seed is not None:
      pma.random_instance = random.Random(self.seed)
  ```
  — reassigning *her module's* `random_instance` attribute from outside,
  without editing her file at all, so a caller-supplied seed takes effect.
  (Flag to Casie: a real fix later would be to add a `seed` parameter to
  `perfect_algo` itself; this is a working stand-in until then.)
- **`get_structure()`**: just returns the generated `Grid`, raising
  `MazeGenerationError` if `generate()` hasn't run yet — a clean read
  accessor instead of reaching into a private attribute.
- **`get_solution()`**: deliberately does *not* implement solving. It tries
  to import a `solve(grid, entry, exit) -> list[str]` function from
  `solve_perfect_maze.py` (Casie's file — currently just a comment stub for
  her planned BFS work) and raises `NotImplementedError` if it's not there
  yet. This is a placeholder honoring an agreed contract, not a competing
  solver — **action item: confirm this exact function signature with Casie**
  so her BFS slots in later without either of us touching the other's file.

**The one edit made to her file**: `perfect_maze_algo.py` originally had
`from config import AmazingExceptions` — importing the *root-level*
`config.py` script. That only worked by accident, because it happened to
sit next to her file in this repo. The moment the package was built and
installed into a totally separate, clean virtualenv (see below), it crashed
with `ModuleNotFoundError: No module named 'config'` — because a pip
package can't assume anything about the folder it gets installed into. The
fix: replaced that import with a small locally-defined
`MazeAlgoError(Exception)` base class in the same file, so the package
no longer depends on anything outside itself. One import line and one new
5-line class — nothing else in her file touched.

### 2.3 The `.whl` package — what it is and how it was built

A `.whl` ("wheel") is Python's standard binary package format — literally a
zip file containing your source code plus metadata, structured so `pip
install some_file.whl` knows how to unpack it into `site-packages`. It's the
exact same kind of file you get transparently whenever you `pip install
requests` — pip is just fetching someone else's pre-built wheel.

**How ours gets built, step by step:**

1. `pyproject.toml` (already existed at the repo root) declares the
   package's identity and where its source lives:
   ```toml
   [project]
   name = "mazegen"
   version = "0.1.0"
   requires-python = ">=3.10"

   [tool.setuptools.packages.find]
   where = ["src"]
   ```
   That `where = ["src"]` line is what tells the build tool "the actual
   importable package is under `src/`" — this is called a *src-layout*, a
   common convention specifically to keep the installable package cleanly
   separated from repo-only files like `a_maze_ing.py`, `config.py`, tests,
   etc. (which do *not* get bundled into the wheel).
2. `pip install build` — installs Python's standard `build` tool (not
   something we wrote; a normal packaging utility).
3. `python -m build`, run from the repo root. It reads `pyproject.toml`,
   gathers everything under `src/mazegen/` (`__init__.py`, `generator.py`,
   `structure.py`, `perfect_maze_algo.py`, `output_maze.py`), and writes two
   files into a new `dist/` folder:
   - `mazegen-0.1.0.tar.gz` (the raw source distribution)
   - `mazegen-0.1.0-py3-none-any.whl` (the wheel). Name breakdown:
     `{name}-{version}-{python tag}-{abi tag}-{platform tag}` → `py3` = any
     Python 3, `none` = no compiled C-extension requirement, `any` = pure
     Python, works on any OS.
4. The `.whl` gets copied from `dist/` to the **repo root** and committed
   there — the subject specifically requires the built artifact to live at
   the repo root, not just be buildable. `dist/`, `build/`, and
   `*.egg-info/` (the intermediate working folders `build` creates) are
   gitignored — only the final `.whl` is tracked.
5. **Proof it actually works standalone** — this is the exact test an
   evaluator will run per the subject ("in a virtualenv... install... and
   build your package again from your sources"): a brand-new virtualenv was
   created completely outside this repo, `pip install
   mazegen-0.1.0-py3-none-any.whl` was run there, and `from mazegen import
   MazeGenerator` was confirmed to work with zero access to any other file
   in this project. That test is exactly what caught the `config.py` import
   bug above — it only surfaced once isolated from the repo, not when
   running from inside it.

**To rebuild/verify it yourselves** (from the repo root, Python 3.10+):
```bash
pip install build
python -m build
cp dist/mazegen-0.1.0-py3-none-any.whl .
```

**A packaging/lint wrinkle that got found and fixed**: once `src/mazegen/`
had its own `__init__.py`, running `mypy .` (the subject's exact mandatory
lint command) started failing *before it could check anything*, with
`Source file found twice under different module names: "mazegen.generator"
and "src.mazegen.generator"`. Reason: with `src/mazegen/__init__.py`
present but no `src/__init__.py`, mypy's root-finding walks up from
`generator.py` until it hits a directory *without* an `__init__.py` — that's
`src/` — so it names the module `mazegen.generator`. But `a_maze_ing.py`
imports it as `src.mazegen.generator`, so mypy sees the same physical file
reachable under two different names and refuses to continue. Fix: added an
empty `src/__init__.py`, which makes mypy keep walking up one more level and
settle on the one consistent name (`src.mazegen.generator`) everywhere.
Verified this doesn't change what ships in the wheel — `setuptools` only
looks for packages *inside* `src/` (per `where = ["src"]`), not `src` itself,
so the wheel's contents (`mazegen/*.py`) are identical before and after.

### 2.4 `sys.argv` wiring — connecting `config.py` to `MazeGenerator`

This is what turned the two islands in the "Data flow" section at the top
into a real pipeline. `sys.argv` is just the list Python gives a script of
what was typed on the command line — `sys.argv[1]` is `"config.txt"` when
you run `python3 a_maze_ing.py config.txt`. `a_maze_ing.py`'s new `main()`:
reads `sys.argv[1]`, calls `config.load_config()` on it (catching
`FileNotFoundError` and the whole `AmazingExceptions` family with clear
messages), builds a `MazeGenerator` from the validated values, calls
`.generate()` (catching `MazeGenerationError`), then calls `put_hex_maze`
(now given the config's `OUTPUT_FILE` instead of a hardcoded name) and
`ascii_display`. Two small supporting fixes were needed for this to actually
work end to end:
- `output_maze.py`'s `put_hex_maze` gained a `filename` parameter
  (defaulting to the old hardcoded `"output_maze.txt"` so nothing else
  breaks) so `OUTPUT_FILE` from the config can actually control where the
  maze gets written.
- `config.py` gained real messages on every exception (see section 2.1), so
  `a_maze_ing.py` can catch the whole family in one place instead of
  duplicating the message-per-exception chain.

---

## Everything done so far (running summary)

- **Config parsing** (`config.py`): mandatory-key check, per-field
  validation/conversion, entry/exit bounds check — all with real,
  per-exception messages now. Extracted a reusable `load_config(path)`
  (file-read + validate in one call) so it isn't only usable via
  `python3 config.py`.
- **Maze core** (`src/mazegen/`, Casie): `Walls`/`Cell`/`Grid` data model,
  seeded recursive-backtracker (`perfect_maze_algo.py`), hex file + ASCII
  output (`output_maze.py`) — all unchanged in behavior, see Part 1 above.
- **`MazeGenerator` reusable class** (`src/mazegen/generator.py`,
  `src/mazegen/__init__.py`, new): validated, class-based wrapper around
  the core above; configurable seed via a non-invasive workaround; a
  `get_solution()` slot waiting on Casie's BFS.
- **`mazegen-0.1.0-py3-none-any.whl`** at the repo root: builds from
  `pyproject.toml`, verified to install and run in a completely isolated
  virtualenv outside this repo.
- **`sys.argv` wiring** (`a_maze_ing.py`): the full
  `config.txt → load_config → MazeGenerator → hex file + ASCII display`
  pipeline now actually runs, with graceful handling of bad config values,
  missing files, and invalid maze parameters.
- **Two file-boundary bugs found and fixed** (both because the wheel was
  tested standalone, outside the repo, which is what exposed them):
  `perfect_maze_algo.py`'s `from config import AmazingExceptions` (broke
  standalone install) and the `src`/`mazegen` mypy double-naming conflict
  (broke `mypy .`, the subject's exact mandatory lint command) — fixed with
  a locally-defined exception class and an empty `src/__init__.py`,
  respectively.
- **Project-wide flake8 cleanup**: every file in the repo (`config.py`,
  `a_maze_ing.py`, and all of `src/mazegen/`) now passes `flake8 .` with
  zero errors — comment style, line length, blank-line spacing, trailing
  whitespace, all resolved without changing any logic.
- **Tests** (`tests/test_generator.py`, stdlib `unittest`, 10 cases):
  validation errors, seed reproducibility, spanning-tree/connectivity
  invariant, the solver-not-implemented contract.

## Open items (not done yet, for awareness)

- **Casie**: BFS solver (`solve_perfect_maze.py`) — needs a
  `solve(grid, entry, exit) -> list[str]` function to satisfy
  `MazeGenerator.get_solution()`'s contract.
- **Casie**: `perfect_maze_algo.py` — two functions still missing
  return-type hints (`mypy` flags both under the subject's mandatory flags,
  independent of the flake8 cleanup above), hardcoded seed (workaround
  exists on the `MazeGenerator` side, real fix would be a `seed` parameter).
- **`generator.py`'s docstrings**: were removed in a hand-edit after the
  class was first written (flake8/mypy/tests still pass either way — this
  is a documentation-only gap, PEP257 requires them back before submission).
- **Joint / unclaimed**: the entry/exit/solution-path block in the output
  file (blocked on Casie's BFS above); the "42" pattern; non-perfect
  (braided) maze + corridor-width validation; interactive display
  (regenerate / show-hide path / change colors); Makefile rules; README.md
  per the subject's required format.
- `default_config.txt` (required by the subject) was deleted in the working
  tree while only `config.txt` remains — worth a quick sync on whether that
  was intentional.

---

## Chronological build order of the whole project

Not the order files happen to sit in the repo — the order each piece
*had to* exist before the next one could be built on top of it, and why.

1. **`config.py` — config file parsing & validation.** Nothing else needs
   the maze at all yet; this only needs to know the *shape* of a config
   file (six `KEY=VALUE` lines) straight from the subject text. Built and
   tested completely standalone (`python3 config.py` just prints a dict) —
   correctly, since there was nothing yet to wire it into.
2. **`src/mazegen/structure.py` — `Walls`, `Cell`, `Grid`.** The foundational
   data model everything else depends on. Had to come before any generation
   algorithm because the algorithm needs somewhere to carve walls *into*.
   The bit-flag values were fixed to match the subject's hex table from the
   start, since every later piece (hex output, ASCII display) leans on that.
3. **`src/mazegen/perfect_maze_algo.py` — the generation algorithm.**
   Depends on step 2 (needs `Grid`/`Cell`/`Walls` to exist first). This is
   the first point the project produces an actual maze, even if nothing
   displays it yet.
4. **`src/mazegen/output_maze.py` — hex file + ASCII display.** Depends on
   step 3 (needs a generated `Grid` to render). This is the first point the
   maze becomes visible/verifiable by a human instead of just existing in
   memory — `a_maze_ing.py`'s original hardcoded `Grid(3, 3)` test harness
   (steps 2–4 wired together manually, no config yet) is what proved steps
   2–4 worked together at all.
5. **`src/mazegen/generator.py` + `__init__.py` — the reusable
   `MazeGenerator` class.** Only makes sense once steps 2–3 exist to wrap.
   This is where Chapter VI's "one class, standalone module" requirement
   got addressed, plus validation and configurable seeds that the raw
   functions didn't have.
6. **`mazegen-0.1.0-py3-none-any.whl` — packaging.** Depends on step 5
   existing and being import-clean. Building and, critically, *installing
   it into a completely separate virtualenv* is what surfaced the
   `config.py` import bug in step 3's file — a bug that had been invisible
   the whole time because everything had only ever been run from inside
   the repo.
7. **`sys.argv` wiring in `a_maze_ing.py`.** Only possible once *both*
   step 1 (config parsing) and step 5 (the class to hand parsed values to)
   exist. This is the point the mandatory `python3 a_maze_ing.py config.txt`
   usage from the subject became real, replacing the manual step-4 test
   harness.
8. **Project-wide lint cleanup (flake8 + the mypy package-root fix).**
   Deliberately last, not first — fixing whitespace/comment-style issues
   file by file *before* the pipeline existed would have meant redoing it
   every time new code landed. Once the whole pipeline in step 7 was
   working, one clean sweep caught everything at once, plus the mypy
   `src`/`mazegen` naming conflict that only becomes visible once you
   actually run `mypy .` (the mandatory lint command) across the *whole*
   project rather than file by file.

---

## Part 3 — Teaching the maze to draw itself in a window (the "MLX" branch)

This section is written for absolutely anyone — including someone who has never written
a line of code — who ends up with a link to this repository and wants to understand what
we're doing and why, one plain-language step at a time. It gets updated every time we
take a new step, in the order we actually did them (not cleaned up afterwards), including
the dead ends and the "wait, why do we need that?" moments.

### 3.0 So what are we actually trying to do here?

Right now this program already draws the maze — but only as text, in the terminal,
using `+`, `-`, and `|` characters (that's `ascii_display()` from Part 1 above; go run
`python3 a_maze_ing.py config.txt` and you'll see it). It works, and it's honestly all
the school project *requires* — the assignment (`en.subject.pdf`, Chapter V) explicitly
says you're allowed to show the maze either as text in the terminal, **or** as an actual
graphical picture in its own window, and either one counts as "done". So nothing below is
fixing something broken — it's us choosing to also build the fancier, optional version:
a real window, with colors, that you can interact with (regenerate the maze, show/hide
the solution path, change colors) using your mouse and keyboard instead of just reading
text.

### 3.1 What is this "MLX" thing?

The tool the school points students toward for this kind of graphics is called
**MiniLibX**, nicknamed "MLX". Think of it as a very small, bare-bones toolbox that
knows how to do exactly three things: open a blank window on screen, let a program color
in individual dots (pixels) inside that window, and tell the program when someone presses
a key or clicks the mouse. It doesn't know anything about mazes, buttons, menus, or
anything fancy — it's the graphics equivalent of a blank canvas and a box of crayons, and
everything maze-shaped that appears in that window will be *our* code deciding "color
this dot black, this dot white, this dot blue for the path," one dot at a time.

MiniLibX itself is written in a different programming language than our project (C,
whereas we're writing this project in Python), and it was written specifically for
students at 42/Epitech schools — it's not something ordinary developers reach for
outside this context. That mismatch (our project's language vs. the toolbox's language)
is the whole reason the next few steps look more involved than "just install a package."

**One trap worth flagging**: if you ever try to install something by typing
`pip install mlx`, you will *not* get this graphics toolbox — you'll get a completely
unrelated product, also confusingly named "MLX", made by Apple for machine-learning
number-crunching on Apple computers. It has nothing to do with drawing windows. We are
not using that one.

### 3.2 Why "which computer this runs on" matters so much here

This toolbox (MiniLibX) doesn't come in one universal version — it comes in different
builds depending on which operating system it's running on, and those builds are not
interchangeable:
- One build is made for **Linux** (the operating system running on the school's own lab
  computers in Berlin, where this project will actually be tested/graded).
- A different build is made for **Mac** (what this development laptop runs), built on
  completely different Apple-only foundations.

Code written to talk to the Mac build simply would not work at all on the school's Linux
machines, and vice versa. Since this project absolutely must run correctly on the
school's Linux machines (that's where it counts), but we're currently building it on a
Mac, we made a decision: use **the Linux build of MiniLibX everywhere**, including here
on the Mac. The trick that makes that possible is that the Linux build of MiniLibX talks
to something called "X11" (a very old, very standard way for programs to draw windows on
screen, originally a Linux/Unix thing) — and Macs can *also* speak X11, just not out of
the box. That's what the next step was about.

### 3.3 What we just installed on this Mac, and why (XQuartz)

To let this Mac understand X11 (the "language" the Linux graphics toolbox speaks), we
installed a free Apple-approved app called **XQuartz**. In plain terms: XQuartz is a
translator/middleman app that runs quietly in the background and lets X11-based programs
(like the Linux version of MiniLibX) open real windows on a Mac's screen, the same way
they would on a Linux machine. Without it, the Linux build of the graphics toolbox simply
has nobody on this Mac to talk to.

We installed it with a command-line tool called Homebrew (a very common "app store from
the terminal" for developer tools on Mac), using:
```
brew install --cask xquartz
```
Installing it required typing the Mac's account password directly in a terminal window —
that's normal and expected for anything that installs a real application system-wide
(rather than just a file inside this project folder); it's the same permission prompt
you'd get installing any desktop app. Once installed, we confirmed it landed in the usual
place (`/opt/X11`), with its files ready to be used for compiling.

One practical note for anyone repeating this on their own Mac: XQuartz sometimes needs
you to **log out and log back in** (or restart) once, the very first time, before it's
fully ready — the app is installed immediately, but the background piece that actually
draws windows doesn't fully start until then.

**Nothing above this point had anything to do with Linux**, by the way — this whole
XQuartz step is a Mac-only, development-convenience detour, purely so whoever is coding
this on a Mac can actually see a window pop up while working. On the school's real Linux
lab machines, none of this XQuartz business is needed at all — Linux already speaks X11
natively, so the exact same MiniLibX source code will simply work there directly.

### 3.4 What comes next

Nothing maze-shaped yet, on purpose — first we prove the entire chain works at all, with
the simplest possible test (just get *any* window to appear with *any* color in it),
before touching anything maze-specific:
1. Bring a copy of the Linux MiniLibX source code into this project (this is normal —
   MiniLibX isn't a thing you download as a ready-made package; you get its source code
   and build it yourself, specific to your own computer).
2. "Build" that source code — this means turning the human-readable source files into a
   compiled, ready-to-use library file the computer can actually run, using a compiler
   (a standard developer tool that translates code into something a computer can execute
   directly). This step is identical in spirit on Linux and on this Mac.
3. Write the smallest possible bit of Python that talks to that compiled library, opens a
   blank window, and colors in a few pixels — just to prove, end to end, "yes, Python can
   successfully ask MiniLibX to draw something, and it shows up on screen."

Only once that bare-bones test is working do we move on to drawing the actual maze walls,
colors, and interactions inside that window. This section will keep growing, step by
step, as each of those pieces gets built and proven to work.

### 3.5 The real thing: drawing the actual maze (`src/mazegen/visualizer.py`)

With the plain "does a window even open" test working, the next step was drawing the
*actual* maze — the same `Grid`/`Cell`/`Walls` data Casie's code already builds and
already prints as ASCII text (`output_maze.ascii_display`, Part 1, section 1.3). All of
this new code lives in exactly **one new file**, `src/mazegen/visualizer.py`, on purpose:
so anyone reviewing this project can see the entire graphical layer in one place, without
it being scattered across files that already work and are already understood. The *only*
change made to any existing file is a single new method at the bottom of
`src/mazegen/generator.py`:

```python
def visualize(self, cell_size: int = 20) -> None:
    """Open an interactive MLX window showing the generated maze."""
    from .visualizer import MlxVisualizer
    MlxVisualizer(self, cell_size=cell_size).run()
```

That's it — one method, one call. Nothing about how mazes are generated, solved, or
written to file changed at all.

**How a `Grid` becomes pixels on screen** — the mapping, plainly:
- Pick a size in pixels for one cell (`cell_size`, default 20 — so a 20×15 maze becomes a
  400×300-pixel picture, plus a thin strip at the bottom for on-screen instructions).
- Walk the grid exactly the same way the ASCII printer already does —
  `for row in grid.cells: for cell in row` — so there's no second, competing way of
  reading the maze; both renderers (text and graphical) look at the data identically.
- For each cell, look at its `walls` number (the same North=1/East=2/South=4/West=8 value
  from `structure.py` that gets written to the hex output file) and draw a short line on
  whichever of the cell's four edges has a wall bit set.
- Before drawing walls, a cell gets its whole square filled with a color first if it's
  special: magenta for the entry cell, red for the exit cell, gray for any cell marked
  `blocked` (reserved for the future "42" pattern — nothing sets `blocked` yet, so no
  cells are gray right now; that's expected, not a bug).
- All of that gets painted into one offscreen image (`mlx_new_image`), and only that
  finished image gets shown to the window in one shot (`mlx_put_image_to_window`) — this
  is the standard/recommended MiniLibX approach; the alternative, `mlx_pixel_put`,
  redraws and locks the real window pixel by pixel and is noticeably slower and
  flickery for anything bigger than a few pixels.

**The four required keyboard controls** (subject Chapter V), all wired through
`mlx_key_hook`:
- **1** — regenerate: asks the same `MazeGenerator` to build a brand-new maze (or the
  exact same one again, if a seed was set — that's the reproducibility rule working as
  intended, not a glitch) and redraws.
- **2** — toggle show/hide path: flips a flag and prints a note to the console. It
  doesn't draw an actual path yet because nobody has written the solver
  (`solve_perfect_maze.solve`) yet — Casie's `solve_floodfill.py` is still just a
  dated comment stub. Wiring the *key* now means plugging in real path drawing later is a
  small, contained change instead of a new feature.
- **3** — rotate wall color: cycles through a small fixed list of colors for the wall
  lines only (entry/exit/blocked colors stay fixed, so they're always identifiable).
- **4** or **Esc** — cleanly quits (`mlx_loop_end`), instead of force-closing the window.

**Two environment traps hit while testing this, worth knowing about:**
1. XQuartz (the translator app from section 3.3) **quits its background X server when
   it's been idle for a while with no windows open**. When that happens, any MiniLibX
   program's very first call (`mlx_init`) fails silently instead of giving a clear error
   (a known rough edge of this old C library, not something introduced here) and the
   *next* call after it crashes the whole program outright (a segfault, Python's most
   unhelpful kind of crash — no Python error message at all). If a previously-working
   MLX program suddenly crashes instantly with no message, the fix is almost always:
   reopen XQuartz (`open -a XQuartz` in a terminal, or just launch it from Spotlight) and
   try again.
2. **This Mac's plain `python3` command is version 3.9.6** (Apple's built-in system
   Python) — one version too old for this project, which needs 3.10+ (it already uses
   `int | None`-style type hints throughout, a 3.10 feature). Running
   `python3 a_maze_ing.py config.txt` on this particular Mac fails immediately with a
   `TypeError` that has nothing to do with anything in this branch — it's a pre-existing
   fact about this one machine's setup, not a bug in the project. A newer interpreter
   (`python3.11`, found here at `~/.local/bin/python3.11`) runs it correctly. Anyone
   picking up this repo on their own machine should first confirm with
   `python3 --version` that they're actually on 3.10 or later before assuming something
   is broken.

**How to actually run the interactive maze window right now**, from the repo root:
```bash
# one-time, only needed again if XQuartz has been closed/idle:
open -a XQuartz

DISPLAY=:0 python3.11 -c "
from src.mazegen.generator import MazeGenerator
g = MazeGenerator(width=20, height=15, seed=42)
g.generate()
g.visualize()
"
```
A window titled "A-maze-ing" appears with the maze drawn in white walls on black, a
magenta entry cell, a red exit cell, and a one-line control reminder at the bottom.
Press **1** to regenerate, **3** to change the wall color, **2** to see the (currently
inert) path-toggle message on the console, and **4** or **Esc** to quit.

**Important: click the maze window before pressing any key.** The maze window and the
Terminal window it was launched from are two separate windows, exactly like any two
apps on your Mac — keys typed while the Terminal is focused go to the Terminal, not to
the maze. Click directly on the "A-maze-ing" window first, *then* press a key.

### 3.6 A real bug found while testing this live: "regenerate" looked like it did nothing

While actually testing this interactively, pressing **1** appeared to do absolutely
nothing — the maze on screen never changed. It turned out to not be a broken key at
all: every other key (`2`, `3`, `4`) was confirmed working (their console messages
printed correctly), which meant keypresses genuinely were reaching the program. The real
cause was the demo command above using `seed=42` — a fixed seed. A seed's entire job is
to make maze generation **100% reproducible**: calling `generate()` again with the same
seed produces the exact same maze, bit for bit, every single time (`tests/test_generator.py`
already has a test asserting exactly this). So "regenerate" was working perfectly — it
was just regenerating an identical maze on top of itself, which is visually
indistinguishable from doing nothing at all.

That's correct behavior for the subject's reproducibility requirement, but it's the
wrong behavior for a "regenerate" *button* someone is actively pressing to see something
new — the subject's own example screenshots show two visibly different mazes,
captioned "different maze, shortest path and wall colours", specifically to illustrate
what pressing regenerate should produce. The fix, entirely inside
`MlxVisualizer.process_keyboard_input` (still no other file touched): pressing **1** now picks a
brand-new random seed, assigns it to the generator, and *then* calls `generate()` — so a
manual regenerate always visibly changes the maze, while the reproducibility guarantee
itself (same seed in the config file always reproduces the same first maze) is
untouched. Every keypress now also prints `[visualizer] key received: keycode=N` to the
console, so it's directly visible (not just inferred) that a key actually arrived and
which one it was — verified end-to-end with a real window: two consecutive presses of
**1** produced two different wall layouts each time.

### 3.7 A real solver, finally: `solve_floodfill.py` (flood-fill / BFS)

With the maze itself, the "42" pattern, and the interactive window all working, the last
missing piece for a genuinely functional "show the path" button was an actual solver.
`get_solution()` (in `generator.py`) had always been trying to import a `solve()`
function from a module called `solve_perfect_maze` — but re-checking the repo turned up
**two different, both-still-stub solver files**: `solve_perfect_maze.py` (Casie's
"starting BFS" commit — still just a comment) and `solve_floodfill.py` (an older,
seemingly abandoned stub from before the team split, also just a comment). Since
`get_solution()` only ever looked at `solve_perfect_maze`, `solve_floodfill.py` was
effectively dead code nobody was importing from anywhere.

The actual algorithm now lives in `solve_floodfill.py`, as a flood fill (a breadth-first
search, "BFS" — spreading outward one ring of neighboring cells at a time, like water
filling a maze from the entrance, until it reaches the exit). Because a **perfect** maze
is a spanning tree (Chapter IV.4 of the subject: exactly one path between any two
cells — see section 1.2 above for why the generation algorithm guarantees this), a flood
fill from the entry finds *the* path, and it is automatically also the shortest one the
subject asks for, since there is only one to find. It walks the same `cell.walls`
bitmask everything else in this project reads, so a step is only allowed where a wall bit
is actually open — never straight through a wall. The result comes back as a list of
single letters (`"N"`, `"E"`, `"S"`, `"W"`), exactly the format the subject's own output
file example uses.

**One wiring fix needed to actually connect it**: `generator.py`'s `get_solution()` was
changed to import from `solve_floodfill` instead of the never-implemented
`solve_perfect_maze` — a one-line fix, otherwise the new solver would sit there
correctly written but never actually called by anything. (`solve_perfect_maze.py` itself
was left alone — it's Casie's file, still just a planning comment, worth reconciling with
her directly rather than deleting unilaterally.)

**Verified two ways**: first, mechanically — replayed the returned path step by step
against the real wall data and confirmed it never crosses a closed wall and lands exactly
on the exit cell. Second, visually — `MlxVisualizer` now actually uses this solver: with
`show_path` toggled on (key **2**), every non-entry/non-exit cell the path passes through
gets filled in blue underneath the wall lines, using the exact same `get_solution()` call
`generator.py` exposes (no separate/duplicate path logic in the visualizer). Toggling key
**2** now immediately redraws with or without that blue trail, confirmed with a real
window.

### 3.8 Making the build genuinely portable: `vendor/build_mlx.sh`

Until this script existed, `build/libmlx.dylib` only existed because of a one-off command
typed directly into a terminal during testing — nowhere in the repository was that
command actually saved, which meant there was no real guarantee this would work on any
machine other than this exact Mac, let alone 42 Berlin's Linux lab machines, which is the
one that actually matters for evaluation. That's what `vendor/build_mlx.sh` fixes: a
small, deliberately simple script that:
- Detects whether it's running on Linux or macOS (`uname`), and compiles into
  `build/libmlx.so` or `build/libmlx.dylib` accordingly (on macOS, against XQuartz's X11
  headers at `/usr/X11/include` — same idea as section 3.4, just saved as a repeatable
  script now instead of a one-off command).
- Uses the *exact* source file list minilibx-linux's own `Makefile.mk` builds — not
  "every `.c` file in the folder". This was a real bug caught while first writing this
  script: a naive `ls mlx_*.c` also grabs `mlx_lib_xpm.c` and `mlx_ext_randr.c`, two
  alternate files that need an extra system library (`libXpm`) this project doesn't
  vendor or use, and the build failed with a wall of undeclared-identifier errors until
  the file list was narrowed to match the official one exactly.

The script has since been simplified further (its own author's pass over it, favoring the
same plain, linear readability as the rest of this project over defensive
error-checking): it now assumes it's always run from the repository root, using plain
relative paths (`vendor/minilibx-linux`, `build`) instead of calculating its own location
first, and it no longer pre-checks whether the vendored source folder or the right X11
developer headers exist before trying to compile — if either is missing, the build simply
fails with the compiler's own error message rather than a custom, friendlier one. That's
a deliberate simplicity-over-robustness tradeoff, not an oversight: the *only* documented
way to run it (`sh vendor/build_mlx.sh`, from the repository root) still works perfectly;
it just no longer holds your hand if you ignore that and run it some other way.

Run it with `sh vendor/build_mlx.sh` from the repository root — re-tested from a clean
`build/` directory on this Mac afterward (after the simplification pass too), producing
an identical, working `libmlx.dylib`, and confirmed the maze window still draws correctly
using that freshly rebuilt file. It hasn't been tested on an actual Linux machine yet
(nothing here is Linux), so that remains an open item — see below.

### 3.9 Making `make run`/`make lint` actually usable on this Mac: a project venv

Testing the Makefile (below) surfaced a real environment problem: this Mac's plain
`python3` command is version 3.9.6 (Apple's built-in system Python) — one version too old
for this project, which needs 3.10+ and already uses 3.10-only syntax throughout
(`config.py`, `generator.py`). So `make run` failed immediately with a `TypeError`, not
because of anything wrong with the Makefile, but because of *which* `python3` this
particular machine's PATH happens to point at.

The fix, exactly as the subject itself recommends (Chapter III.3: *"It is recommended to
use virtual environments (e.g., venv or conda) for dependency isolation during
development"*): a project-local virtual environment, created once with
`python3.11 -m venv venv` (using the newer interpreter that already exists on this
machine at `~/.local/bin/python3.11`). Once created, activating it
(`source venv/bin/activate`) makes plain `python3` correctly mean 3.11 for the rest of
that terminal session — no changes to the Makefile itself were needed, since it already
just calls plain `python3`; the venv fixes *which* `python3` that resolves to, globally
for that shell, without touching anything system-wide. `venv/` was added to `.gitignore`
— a venv is a local, machine-specific folder, never something to commit.

Activating the venv exposed one more real bug: `flake8 .` now also linted every
third-party package installed *inside* the venv itself (`venv/lib/python3.11/site-
packages/...`), producing thousands of irrelevant findings that have nothing to do with
this project's own code. Fixed with a small `.flake8` config file at the repository root
telling flake8 to skip `venv`, `build`, `dist`, `vendor`, `.mypy_cache`, `__pycache__`,
and `.git` — none of which are code this project owns or could fix anyway. (`mypy`
already skipped the venv correctly on its own, no fix needed there.)

Re-tested every Makefile target through the activated venv afterward: `install`, `run`,
`debug`, `clean`, `lint`, and `lint-strict` all confirmed working correctly (`lint`
correctly reports real, pre-existing style issues in a few of Casie's files — not new
problems, and not venv noise anymore).

### 3.10 Two new Makefile targets: `visualize` and `package`

The subject's six mandatory Makefile targets (`install`, `run`, `debug`, `clean`, `lint`,
`lint-strict`) say nothing about the MLX window at all — which meant, until now, the
*only* way to actually see it was typing a Python snippet by hand into a terminal, every
single time, exactly like this whole conversation had been doing. That's not something an
evaluator is going to do unprompted. Two small, optional additions fixed this:

- **`visualize_maze.py`** (new file, repository root): a second, small entry point that
  reads the same config file the same way `a_maze_ing.py` does, generates the maze the
  same way, but then opens the interactive MLX window instead of printing ASCII. Kept
  deliberately separate from `a_maze_ing.py` rather than merged into it, so the subject's
  own mandated command (`python3 a_maze_ing.py config.txt`) stays exactly as specified —
  fast, text-only, no graphical dependency. That separation matters concretely: if the
  mandated command *always* opened a blocking graphical window, an automated grading
  script expecting it to run and exit normally would hang forever waiting on a window
  nobody is there to close.
- **`make visualize`** (new Makefile target): runs `visualize_maze.py config.txt`. On a
  Mac, it also starts XQuartz and points `DISPLAY` at it first, using the same
  `case "$(uname)"` style already used in `vendor/build_mlx.sh`, for consistency; on
  Linux, neither of those is needed at all (see section 3.2), so nothing extra happens
  there.
- **`make package`** (new Makefile target): reruns `python -m build` and copies the
  freshly built `.whl` over the one at the repository root — the same manual process
  section 2.3 already documented, just made repeatable with one command. Deliberately
  kept separate from `make run`: the `.whl` is the standalone reusable *library*
  (Chapter VI), unrelated to actually running the maze generator, so it should not
  silently rebuild every time someone just wants to run the program. This target is also
  what regenerated `mazegen-0.1.0-py3-none-any.whl` after it went missing from the
  working tree (noticed via `git status` showing it deleted, unrelated to anything from
  this session — already stale anyway, since the package's source had changed since it
  was last built).

One shared-directory risk worth flagging: `build/` is used for *two* unrelated things —
the compiled `libmlx.dylib`/`.so`, and Python's own packaging tool's intermediate output
during `make package`. They didn't collide in testing (the packaging tool cleans up its
own subfolder afterward), but if that library ever mysteriously "disappears" right after
running `make package`, that's almost certainly why — the fix is just re-running
`sh vendor/build_mlx.sh`.

Both new targets were tested directly: `make package` successfully rebuilt the missing
wheel from current source, and `make visualize` was confirmed to launch XQuartz and stay
alive, stable, in the real MLX event loop before being stopped manually.

**What's left, in the order it would naturally get tackled next:**
9. **Not yet tested on a real Linux machine** — `vendor/build_mlx.sh`'s Linux branch has
   only been read/reasoned about, never actually run on Linux (this whole session has
   been on a Mac). First thing to do on a 42 Berlin machine: run
   `sh vendor/build_mlx.sh`, confirm `build/libmlx.so` appears, then run the same
   `MazeGenerator(...).visualize()` snippet from section 3.5 (no `DISPLAY=:0` or XQuartz
   needed there — Linux already has its own X server running).
10. The subject's mandatory **output file format** (Chapter IV.5) still isn't fully
    implemented: after the hex grid and a blank line, the file must also contain the
    entry coordinates, exit coordinates, and the solution path (N/E/S/W) on three more
    lines. `put_hex_maze()` (`output_maze.py`) currently only writes the hex grid. Now
    that a real solver exists, this is unblocked — flagged here rather than changed
    without asking, since it wasn't part of what was asked for in this session.
11. Non-perfect/braided maze support + corridor-width validation — independent of
    solving, layered on top of generation (step 3 in the chronological list above).
12. Makefile rules, `README.md` per the subject's required format — last, since they
    document/automate a pipeline that needs to already work.

---

# Visualization

Everything above (Part 3) is a running, chronological log — written as things were being
figured out, in the order they happened. This section is different: it's a single,
self-contained explanation of the *whole* visualization system as it stands right now,
written for anyone — teammate or total stranger to code — who opens this repo and asks
"okay, but how does the maze actually end up drawn on screen, and how hard would it be for
me to change something in it?"

## The one-sentence version

A small, separate piece of graphics software (not written by this team) draws a window
and colors in dots on it; our own Python code decides *which* dots to color, based on the
maze data Casie's code already builds; and a short Python translation layer in the middle
is what lets our Python code talk to that separate, non-Python software at all.

## The big picture: four layers, stacked on top of each other

Think of it as four layers, each one only trusting the layer directly below it to do its
one job:

```
 [4] MlxVisualizer (src/mazegen/visualizer.py)
       "Given a maze, decide what color every dot on screen should be."
       This is where all the maze-specific thinking happens: walls, entry,
       exit, the solution path, key presses. 100% ordinary Python.
             |
             |  calls plain Python functions like mlx.lib.mlx_pixel_put(...)
             v
 [3] The ctypes translation layer (also inside visualizer.py, the "MlxBridge" class)
       "Describe the shape of each C function so Python is allowed to call it."
       Still 100% Python -- but its only job is bookkeeping: it doesn't
       know anything about mazes at all.
             |
             |  ctypes hands the call down into compiled machine code
             v
 [2] libmlx.dylib / libmlx.so (build/ -- compiled, not source-controlled)
       Actual C code, written by someone else, that knows how to open a
       window and set pixels. We did not write a single line in this
       layer -- we only compiled it.
             |
             |  talks to the operating system's graphics stack
             v
 [1] X11 (native on Linux; via the XQuartz app on this Mac)
       The actual thing that draws pixels on your physical screen.
       Older than this entire project by about three decades.
```

Every arrow above is a real, separate boundary. Nothing skips a layer.

## Did we write any C code? Is it all Python?

**We wrote zero new lines of C.** All of the *new* code added for this feature —
`src/mazegen/visualizer.py` (layers 3 and 4 above) and `src/mazegen/solve_floodfill.py`
(the solver) — is ordinary Python, the same language as the rest of this project.

The only C involved is `vendor/minilibx-linux/`, which is someone else's existing,
publicly available library (written years ago by people at 42, for exactly this kind of
school project) that we copied into this repo unmodified and compiled ourselves. "Compiled"
here just means: turned their `.c` source files into one ready-to-run file,
`build/libmlx.dylib` (on this Mac) or `build/libmlx.so` (on Linux), using the script at
`vendor/build_mlx.sh`. We never opened one of those `.c` files and changed a single
character in it.

So, to directly answer it: **yes, everything we personally authored is Python.** The one
non-Python ingredient is a small, borrowed, unmodified C library that our Python talks to
through a translator (see next section).

## What is this "ctypes translation layer" actually doing?

Python and C are different languages that don't know how to talk to each other by
default. `ctypes` is a tool built into Python itself (nothing extra to install) whose
entire job is bridging that gap: you tell it "here is a compiled library file, and here
is exactly what each function inside it expects as input and returns as output," and
after that, calling a C function from Python looks just like calling any other Python
function.

That description work happens once, in the small `MlxBridge` class near the top of
`visualizer.py`. For example, this block:
```python
self.compiled_library.mlx_put_image_to_window.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_int, ctypes.c_int,
]
```
is Python saying "the C function `mlx_put_image_to_window` takes five arguments: three
raw memory addresses (`c_void_p`) and two whole numbers (`c_int`)." Once that's declared,
anywhere else in the file can just write
`self.mlx_bridge.compiled_library.mlx_put_image_to_window(mlx, window, image, x, y)` and
it works exactly like a normal Python call — all the translation is hidden after this
one-time setup. This is the *only* place in the whole project that has to know anything
about how C functions are shaped; everything else, including all the actual maze-drawing
logic, is unaware that C is involved at all.

## How is this wired to the solving algorithm?

This is a short chain, and every link in it already existed for another reason — nothing
new had to be invented just to connect them:

1. `MlxVisualizer` never talks to the solver directly. When the path needs to be shown
   (key **2**), it calls `self.generator.get_solution()` — the exact same method
   `generator.py` already exposed as its public "give me the solution" API, the one any
   future project reusing this package would also call.
2. `get_solution()` (in `generator.py`) imports `solve()` from `solve_floodfill.py` (see
   section 3.7 above for the story of that import once pointing at the wrong file) and
   hands it the maze's `Grid` plus the entry/exit coordinates.
3. `solve()` returns a plain list of letters, like `["N", "N", "E", "S", ...]` — no
   mention of pixels, colors, or windows anywhere in that file. It has never heard of MLX.
4. Back in the visualizer, `compute_solution_path_cells()` walks that list of letters
   starting from the entry coordinates, turning each letter back into an `(x, y)` cell
   position, building up the full set of cells the path passes through.
5. `draw()` then simply checks, for every cell it's about to draw anyway: "is this
   cell's `(x, y)` in that path set? If so, paint it blue before drawing its walls on
   top."

The important design point: the solver (`solve_floodfill.py`) has zero knowledge that a
graphical window even exists, and the visualizer has zero knowledge of *how* the path was
found — it only knows how to ask for it and how to draw whatever comes back. Either half
could be completely rewritten (a smarter solver, a totally different rendering approach)
without the other half needing to change at all.

## If this gets pushed to Casie, how easy is it for her to touch the MLX code?

Honestly, split into two very different answers depending on *what* she'd want to change:

**Genuinely easy — no C or ctypes knowledge required at all:**
- Changing colors (entry, exit, the "42" pattern, the path, the wall-color rotation list)
  — these are all just plain tuples of numbers near the top of `visualizer.py`
  (`ENTRY_COLOR = (255, 0, 255)`, etc.), the same as changing a color in any Python
  project.
- Changing `cell_size` (how many pixels wide one maze cell is) — one constant.
- Adding a new keyboard shortcut for something the maze data *already* has (say, a key
  that jumps straight to showing only the "42" pattern cells) — she'd copy the pattern
  already used for keys `1`–`4` in `process_keyboard_input`, which is plain `if`/`elif`
  Python.
- Anything about *what* gets drawn, using drawing tools that already exist in the file
  (`paint_solid_rectangle` is already there and reusable) — this is the large majority of
  believable future changes, and all of it is ordinary, readable Python with no C
  involved at all.

**Genuinely more tedious — does require understanding a little bit of C-to-Python
translation:**
- Anything that needs an MLX capability *not already wrapped* in the `MlxBridge` class —
  for example, reacting to mouse clicks, loading an image from a file, or resizing the
  window live. MiniLibX has a C function for each of these already (documented in
  `vendor/minilibx-linux/mlx.h`), but none of them have a `ctypes` description written
  for them yet in this project. Adding one means: opening `mlx.h`, finding the function's
  C signature, and writing a new `argtypes =` block for it in `MlxBridge.__init__`,
  following the exact pattern already used for the ten functions we do use. It's genuinely
  copy-paste-and-adjust rather than "figure it out from nothing" — but it does require
  being comfortable reading a C function signature well enough to translate it, which is
  a real, separate skill from writing the Python around it.
- One environment step has to succeed *before any of this Python runs at all*: the
  compiled library (`build/libmlx.so` on her Linux machine) has to exist first, by running
  `sh vendor/build_mlx.sh` **from the repository root** once (see section 3.8 — the
  script uses plain relative paths, so it only finds things correctly if run from there).
  On a normal Linux desktop with X11 developer headers already installed this should
  "just work"; if they're missing, or the script is run from somewhere else, it fails
  with the compiler's own error message rather than a friendly custom one — recoverable,
  but she'd need to recognize a raw compiler/shell error as "install libx11-dev and
  libxext-dev, then try again from the repo root" rather than something the script tells
  her directly.

**Bottom line**: reading and tweaking *what the maze looks like* is exactly as easy as
any other Python file in this repo — nothing about it requires knowing C. Extending *what
MLX itself can do* is a small, well-contained, learnable skill (reading a C header and
mirroring an existing pattern), not a wall — but it is a real skill she'd be picking up
for the first time if she's never used `ctypes` before, so budget a little extra time for
that specific kind of change versus a plain Python one.

---

# Comparison against a reference 100%-scoring repo

Cloned and read through `r3dBust3r/42-a-maze-ing` (a repo from students who scored 100%
on this exact project) for a sanity check on whether we're on track. Kept out of this
repo's own git history entirely — it's another team's submission, not something to fold
into ours, just something to read. Findings, most important first:

- **🔴 Biggest gap, by far: our `README.md`.** It's still the original brainstorming
  notes from before any code existed ("what I understand so far... don't know yet
  how..."). It has none of the subject's mandatory sections (Chapter VII): no italicized
  first-line credit, no "Description", no "Instructions", no config-file docs, no chosen
  algorithm + why, no reusability explanation, no team/roles/planning section, and no
  disclosure of how AI was used. Their README has essentially all of this. This is being
  fixed right now on its own branch (`fix/readme_fix`).
- **🟡 Real correctness gap**: their `maze_init()` explicitly rejects a config where
  `ENTRY` or `EXIT` lands on one of the "42" pattern's blocked cells (prints an error and
  exits). We have no equivalent check anywhere — nothing currently stops an entry/exit
  coordinate from silently coinciding with a cell that's supposed to stay permanently
  sealed. Worth a small fix later.
- **✅ MLX is confirmed genuinely optional, from their own commit history.** Their
  `TODO.md` literally reads *"Maze representation (MiniLibX) -> Switched to ASCII"* —
  they planned it, dropped it for ASCII + a text-based menu instead, and still scored
  100%. Doesn't waste our MLX work (it's a real bonus feature they don't have), just
  confirms it was never required.
- **✅ Our solver scales better.** Theirs is exhaustive recursive backtracking that
  enumerates every possible path between entry and exit and keeps the shortest; ours
  (`solve_floodfill.py`) is a proper BFS, always linear in the number of cells.
- **✅ Our error handling is more reusable.** Their config parser calls `exit(0)` directly
  from deep inside parsing logic, which would kill any program that imports it; ours
  raises catchable custom exceptions instead.
- **✅ Our "42 too small" behavior matches the subject more closely.** Theirs calls
  `exit(0)` (kills the whole program) if the maze is too small for the pattern; the
  subject says the pattern should just be *omitted* with an error printed instead, which
  is exactly what our `forty_two_pattern()` already does.
- **Everything else is a different valid style, not a gap**: `configparser` vs. manual
  line-splitting, storing `x`/`y` on each `Cell` vs. relying on list position, arbitrary
  WIDTH/HEIGHT bounds (9-45) they impose that the subject never requires. Their package's
  own pip name (`mazegen`) and actual Python import name (`a_maze_ing`) don't even match
  each other, which ours doesn't have a problem with (`from mazegen import ...` genuinely
  works for us) — one more small point in our favor, not theirs.
