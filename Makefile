NAME=
HEADER=
CC=
CFLAGS=
SRCS=

install: # Install project dependencies using pip, uv, pipx, or any other package manager of your choice.

run:  # Execute the main script of your project (e.g., via Python interpreter).

debug: # Run the main script in debug mode using Python’s built-in debugger (e.g., pdb).

clean: # Remove temporary files or caches (e.g., __pycache__, .mypy_cache) to keep the project environment clean.

lint: # Execute the commands flake8 . and mypy . --warn-return-any --warn-unused-ignores--ignore-missing-imports--disallow-untyped-defs --check-untyped-defs

lint-strict: #  (optional): Execute the commands flake8 . and mypy . --strict

.PHONY: install run debug clean lint lint-strict
