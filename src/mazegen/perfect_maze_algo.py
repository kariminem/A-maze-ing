#!/usr/bin/env python3

import random
from .structure import Grid, Cell, Walls, OPPOSITE
from config import AmazingExceptions


class InvalidCoordinates(AmazingExceptions):
    """Exception raised when there is a coordinates missmatch"""
    pass


# Defining seed to make maze reproducable
myseed = 42
# the "rndm" is now our own random-instance, based on the seed,
# to reproduce mazes, so instead of random.choice() we have
# to use random_instance.choice()
random_instance = random.Random(myseed)


# call it with the cell where we begin so: x, y = entry and call
# perfect_algo(grid, grid.cells[y][x])
def perfect_algo(grid: Grid, cell: Cell) -> None:
    cell.visited = True

    unvisited_neighbors = get_unvisited_neighbors(grid, cell)

    while unvisited_neighbors:  # if we have an unvisited neighbor
        next_cell = random_instance.choice(unvisited_neighbors)  # choose one randomly
        remove_wall_between(cell, next_cell)  # remove the wall between them
        perfect_algo(grid, next_cell)

        unvisited_neighbors = get_unvisited_neighbors(grid, cell)

    return


def get_neighbor(grid: Grid, x: int, y: int) -> Cell | None:
    """helper fuction for checking if cell coordinates are out of bounds"""
    if x < 0 or x >= grid.width or y < 0 or y >= grid.height:
        return None
    else:
        return grid.cells[y][x]


def get_unvisited_neighbors(grid: Grid, current: Cell):
    """get a list of all unvisited neighbours of the input Cell"""
    # defining each neighbor as the direction they're in
    north = get_neighbor(grid, current.x, current.y - 1)
    east = get_neighbor(grid, current.x + 1, current.y)
    south = get_neighbor(grid, current.x, current.y + 1)
    west = get_neighbor(grid, current.x - 1, current.y)

    # creating a list for all the unvisited neighbors
    unvisited_neighbors: list[Cell] = []
    if north and not north.visited:  # the if <destination> part checks if you
        # have a neighbor in that direction.
        # If not the variable is None so if nort is false
        unvisited_neighbors.append(north)
    if east and not east.visited:
        unvisited_neighbors.append(east)
    if south and not south.visited:
        unvisited_neighbors.append(south)
    if west and not west.visited:
        unvisited_neighbors.append(west)

    return unvisited_neighbors


############ FUNCTION SHOULD FIGURE ITSELF OUT WHICH WALLS TO BREAK ############
def remove_wall_between(current: Cell, neighbor: Cell):
    """remove the wall (set it to 0) of a cell and its neighbor"""
    # get the directions of both cells walls to remove
    if current.y == neighbor.y:
        if neighbor.x == current.x + 1:
            # neighbor is to our right
            direction_neighbor_wall = Walls.WEST
        elif neighbor.x == current.x - 1:
            # neighbor is to our left
            direction_neighbor_wall = Walls.EAST
        else:
            # y == y and x == x ???? -> our neighbor is us
            print(f"current is: x: {current.x} y: {current.y}\nneighbor is x: {neighbor.x} y: {neighbor.y}") ### for testing ###
            print(f"neighbor.x == current.x + 1 is: {neighbor.x == current.x + 1}")
            print(f"neighbor.x == current.x - 1 is: {neighbor.x == current.x - 1}")
            raise InvalidCoordinates
    else:
        if neighbor.y == current.y - 1:
            # neighbor is above us
            direction_neighbor_wall = Walls.SOUTH
        elif neighbor.y == current.y + 1:
            # neighbor is below us
            direction_neighbor_wall = Walls.NORTH
        else:
            # x == x and y == y ???? -> our neighbor is us
            raise InvalidCoordinates

    direction_current_wall = OPPOSITE[direction_neighbor_wall]
    # we do a bit operation by inverting the bits of the direction (with ~)
    # and using the & which will only set bits to 1 if both bits (current
    # wall and direction) are 1. Since we inverted direction bits, the only 1
    # bit of that direction, will be zero and only this bit will be deducted
    # So it is simply the way of setting that wall to "open"
    current.walls &= ~direction_current_wall
    neighbor.walls &= ~direction_neighbor_wall
