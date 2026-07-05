# Tells `make` that these words are actions to run, not real files it
# might find lying around with these same names.
.PHONY: install run debug clean lint lint-strict visualize package

# Installs the tools needed to lint this project and build its .whl package.
install:
	python3 -m pip install flake8 mypy build

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
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

# just a stronger check.
lint-strict:
	flake8 .
	mypy . --strict

# Opens the interactive MLX graphical window instead of the ASCII
# display. Needs libmlx built first (sh vendor/build_mlx.sh). On a
# Mac this also needs XQuartz running, so this target starts it and
# points DISPLAY at it; on Linux none of that is needed, the OS
# already has its own display ready to go.
visualize:
	@case "$$(uname)" in \
		Darwin) open -a XQuartz; DISPLAY=:0 python3 visualize_maze.py config.txt ;; \
		*) python3 visualize_maze.py config.txt ;; \
	esac

# Rebuilds mazegen-0.1.0-py3-none-any.whl at the repository root from
# the current source in src/mazegen/. Separate from `run` on purpose:
# this is the reusable package (Chapter VI), not the maze generator
# itself, so it should not silently rebuild every time you just want
# to run the program.
package:
	python3 -m build
	cp dist/mazegen-0.1.0-py3-none-any.whl .
