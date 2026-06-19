what I understand so far:

* core dileverable --> a python program 
* this program reads an input file --> config file
* generates a maze
* then writes to a file in hex format
* so if a cell has 3 walls for example we might do smth like this --> 1110 --> meaning there is a wall
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


suggested workflow:

1- parsing config file, handling its errors etc..

2- creating the actual class that will reprsent the whole grid for example class Grid, inside we can implement a 2d Array, width, size, directions, etc..

3- finding a way to create the 42 pattern? should we do it before the actual maze generation or shape it in afterwards ? still not sure.

4- now we have the maze done, we solve it using any algorithm, BFS, floodfill (from exam rank 02) etc..
also there is smth called perfectmode here? not sure yet.

5- we must then validate the maze using the hex format mentioned earlier.

6- visualizing, either in terminal or using MLX

7- merge everything (Makefile)

8- create the .whl file to create an installable library.

9- cleanup, readme, flake8 mypy etc../ finally pushing.