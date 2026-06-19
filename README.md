what I understand so far:

* core dileverable --> a python program 
* this program reads an input file --> config file
* geenrates a maze
* then writes to a file in hex format
* so if a cell has 3 walls for example we might do smth lik this --> 1110 --> meaning there is a wall
in NES, North East South and there is no wall in West.
* then we need to display it somehow (don't know yet how! but probably smth graphically we will import a library or smth)
* we also find the solution to the maze?
* the maze must contain te shape '42' made of walls?
does it mean full cells? or just thin walls?
* path width --> max 2 cells' width

All of this in addition to the base requirements of compiance with:
* flake8
* mypy
* no docstrings
* error handling
* Makefile
* mazegen-*.whl --> installable package through pip (did it before so I know this part)
* and ofc a README.md