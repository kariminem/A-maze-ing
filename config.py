#! /usr/bin/env python3

# This is phase 1 of the A-maze-ing project, in this branch I am trying to
# configure, parse and validate the input file which is considered the
# starting point to the whole project, as simple as it may sound, I
# discovered we need to handle **CRAZY** edgecases !!
# so I'd say this file is a _HUGE minefield cleanser_.

# here all I want to do is to read a file
# parse its **input** --> checking for errors
# split each line from the '='
# create a dictioanry to hold the input
# numbers are numbers, strings are strings
# handle the point conversion of (0,0)
# when all is done and clear for takeoff, we
# return the dict for the next phase!

# some questions that I have while developing
# 1- is the config file ordered in this exact way !?
# subject citation -> "Your program must handle all errors gracefully:
# invalid configuration,
# file not found, bad syntax,
# impossible maze parameters, etc."
# 2- do we really need to handle all weird edge cases ??
# cause omg I can already think of 100 edge cases !!!


class AmazingExceptions(Exception):
    """base class for handling all exceptions"""
    pass


class InvalidWidthInput(AmazingExceptions):
    """Exception raised for invalid width values in the config."""
    pass


class InvalidHeightInput(AmazingExceptions):
    """Exception raised for invalid height values in the config."""
    pass


class MissingConfigInputs(AmazingExceptions):
    """Exception raised for invalid number of config inputs values in the
    config."""
    pass


class InvalidEntryInput(AmazingExceptions):
    """Exception raised for invalid Entry input."""
    pass


class InvalidExitInput(AmazingExceptions):
    """Exception raised for invalid Exit input."""
    pass


class InvalidPerfectPathInput(AmazingExceptions):
    """Exception raised for invalid perfect path specifier in config."""
    pass


class EmptyFileName(AmazingExceptions):
    """Exception raised for empty output file."""
    pass


class ExceedingMazeLimit(AmazingExceptions):
    """Exception raised for exceeding maze limit"""
    pass


class MalformedConfigLine(AmazingExceptions):
    """Exception raised for a config line that is not KEY=VALUE."""
    pass


class InvalidSeedInput(AmazingExceptions):
    """Exception raised for an invalid seed value in the config."""
    pass


class UnknownInputParam(AmazingExceptions):
    """Exception raised for an invalid input parameter in the config."""
    pass


ConfigValue = int | str | list[int] | bool | None


def dict_validate(config_dict: dict[str, str]) -> dict[str, ConfigValue]:
    """Validate a raw KEY=VALUE config dict and convert it to typed values.

    Args:
        config_dict: Raw string values keyed by config key, as read from
            the config file.

    Returns:
        A dict with the same keys, values converted to their proper types
        (int, list[int], str, bool).

    Raises:
        MissingConfigInputs: A mandatory key is missing.
        InvalidWidthInput: WIDTH is not a positive int.
        InvalidHeightInput: HEIGHT is not a positive int.
        InvalidEntryInput: ENTRY is not a valid "x,y" pair of ints.
        InvalidExitInput: EXIT is not a valid "x,y" pair of ints.
        EmptyFileName: OUTPUT_FILE is empty.
        InvalidPerfectPathInput: PERFECT is not True or False.
        ExceedingMazeLimit: ENTRY or EXIT falls outside WIDTH x HEIGHT.
    """
    input_params = [
        "WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT",
    ]
    for i in input_params:
        if i in config_dict.keys():
            continue
        else:
            raise MissingConfigInputs("Missing Config Parameters")

    final_dict: dict[str, ConfigValue] = {}
    width = height = 0
    entry = exit_ = [0, 0]

    for key, value in config_dict.items():
        if key == "WIDTH":
            try:
                width = int(value)
            except ValueError:
                raise InvalidWidthInput("Invalid Width Input")
            if width <= 0:
                raise InvalidWidthInput("Invalid Width Input")
            final_dict[key] = width
        elif key == "HEIGHT":
            try:
                height = int(value)
            except ValueError:
                raise InvalidHeightInput("Invalid Height Input")
            if height <= 0:
                raise InvalidHeightInput("Invalid Height Input")
            final_dict[key] = height
        elif key == "ENTRY":
            try:
                x_entry, y_entry = value.strip().split(",")
                entry = [int(x_entry), int(y_entry)]
            except ValueError:
                raise InvalidEntryInput("Invalid Entry Input in config file")
            final_dict[key] = entry
        elif key == "EXIT":
            try:
                x_exit, y_exit = value.strip().split(",")
                exit_ = [int(x_exit), int(y_exit)]
            except ValueError:
                raise InvalidExitInput("Invalid Exit Input in config file")
            final_dict[key] = exit_
        elif key == "OUTPUT_FILE":
            if value == "":
                raise EmptyFileName("Empty Output File Name")
            final_dict[key] = value
        elif key == "PERFECT":
            if value == "True":
                final_dict[key] = True
            elif value == "False":
                final_dict[key] = False
            else:
                raise InvalidPerfectPathInput(
                    "Invalid perfect path specifier, set to True or False"
                )
        elif key == "SEED":
            try:
                final_dict[key] = int(value)
            except ValueError:
                raise InvalidSeedInput("Invalid Seed Input")
        elif key not in input_params:
            if key != "SEED":
                raise UnknownInputParam(f"Unknown input -> {key}")

    if "SEED" not in final_dict:
        final_dict["SEED"] = None

    if (exit_[0] >= width or exit_[1] >= height
            or entry[0] >= width or entry[1] >= height):
        raise ExceedingMazeLimit("Exceeding Maze Limit")
    return final_dict


def load_config(config_file: str) -> dict[str, ConfigValue]:
    """Read and validate a KEY=VALUE config file.

    Args:
        config_file: Path to the config file to read.

    Returns:
        The validated, typed config values (see dict_validate).
    """
    config_dict: dict[str, str] = {}
    with open(config_file, "r") as f:
        lines = [
            line.strip() for line in f
            if line.strip() != "" and line.strip()[0] != "#"
        ]
        for line in lines:
            if "=" not in line:
                raise MalformedConfigLine(f"Line is not KEY=VALUE: {line!r}")
            key, value = line.split("=", 1)
            config_dict[key.strip()] = value.strip()
    return dict_validate(config_dict)


if __name__ == "__main__":
    config_file = "config.txt"
    try:
        final_dict = load_config(config_file)
    except FileNotFoundError:
        print("File Not Found!.")
        exit()
    except AmazingExceptions as exc:
        print(exc)
        exit()
    print("validation finished...")
    print(final_dict)
