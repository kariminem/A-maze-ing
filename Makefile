.PHONY: install run debug clean lint lint-strict visualize package


VENV = venv
VENV_PYTHON = $(VENV)/bin/python3


install:
	python3 -m venv $(VENV)
	$(VENV_PYTHON) -m pip install flake8 mypy build
	PATH="$(VENV)/bin:$$PATH" sh vendor/install_mlx.sh

run:
	python3 a_maze_ing.py config.txt

debug:
	python3 -m pdb a_maze_ing.py config.txt

clean:
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf src/mazegen/__pycache__
	rm -rf .mypy_cache

lint:
	$(VENV_PYTHON) -m flake8 .
	$(VENV_PYTHON) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs


lint-strict:
	$(VENV_PYTHON) -m flake8 .
	$(VENV_PYTHON) -m mypy . --strict


visualize:
	$(VENV_PYTHON) visualize_maze.py config.txt


package:
	$(VENV_PYTHON) -m build
	cp dist/mazegen-0.1.0-py3-none-any.whl .
