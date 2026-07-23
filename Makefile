# Tells `make` that these words are actions to run, not real files it
# might find lying around with these same names.
.PHONY: install run debug clean lint lint-strict visualize package

# Where the dev tools (flake8, mypy, build, mlx) get installed. A venv,
# not the system Python, because modern Debian/Ubuntu (including WSL)
# refuse plain `pip install` outside one (PEP 668, "externally-managed-
# environment"). a_maze_ing.py itself needs none of this -- it only
# uses Python's standard library -- so `run`/`debug` below still use
# plain `python3` directly, exactly as the subject's mandated command.
VENV = venv
VENV_PYTHON = $(VENV)/bin/python3

# Creates the venv above and installs flake8, mypy, build into it, plus
# the official mlx package (vendor/mlx-2.2.tgz) for MLX visualization.
install:
	python3 -m venv $(VENV)
	$(VENV_PYTHON) -m pip install flake8 mypy build
	PATH="$(VENV)/bin:$$PATH" sh vendor/install_mlx.sh

# Runs the actual program 'python3 a_maze_ing.py config.txt'
run:
	python3 a_maze_ing.py config.txt

# Same as `run` above, but started inside Python's own built-in debugger
debug:
	python3 -m pdb a_maze_ing.py config.txt

# Deletes the temporary files Python leaves behind while running.
clean:
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf src/mazegen/__pycache__
	rm -rf .mypy_cache

# Runs the two mandatory checks the subject requires
lint:
	$(VENV_PYTHON) -m flake8 .
	$(VENV_PYTHON) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

# just a stronger check.
lint-strict:
	$(VENV_PYTHON) -m flake8 .
	$(VENV_PYTHON) -m mypy . --strict

# Opens the interactive MLX graphical window instead of the ASCII
# display. Needs the mlx package installed first (make install) --
# Linux only, no macOS build.
visualize:
	$(VENV_PYTHON) visualize_maze.py config.txt

# Rebuilds mazegen-0.1.0-py3-none-any.whl at the repository root from
# the current source in src/mazegen/. Separate from `run` on purpose:
# this is the reusable package (Chapter VI), not the maze generator
# itself, so it should not silently rebuild every time you just want
# to run the program.
package:
	$(VENV_PYTHON) -m build
	cp dist/mazegen-0.1.0-py3-none-any.whl .
