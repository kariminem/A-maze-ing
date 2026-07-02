#! /usr/bin/env python3

## This is phase 1 of the A-maze-ing project, in this branch I am trying to configure, parse and validate the input file which is considered the starting point to the whole project, as simple as it may sound, I discovered we need to handle **CRAZY** edgecases !!
## so I'd say this file is a _HUGE minefield cleanser_.



## here all I want to do is to read a file
## parse its **input** --> checking for errors
## split each line from the '='
## create a dictioanry to hold the input
## numbers are numbers, strings are strings
## handle the point conversion of (0,0)
## when all is done and clear for takeoff, we 
## return the dict for the next phase!


## some questions that I have while developing
## 1- is the config file ordered in this exact way !?
## subject citation -> "Your program must handle all errors gracefully:
# invalid configuration, 
# file not found, bad syntax,
# impossible maze parameters, etc."
#  2- do we really need to handle all weird edge cases ??
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
    """Exception raised for invalid number of config inputs values in the config."""
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

def dict_validate(config_dict: dict) -> dict:
    input_params = ["WIDTH", "HEIGHT", "ENTRY", "EXIT",
                "OUTPUT_FILE", "PERFECT"]
    final_dict = {}
    for i in input_params:
        if i in config_dict.keys():
            continue
        else:
            raise MissingConfigInputs
    for key, value in config_dict.items():
        if key == "WIDTH":
            if int(value) <= 0:
                raise InvalidWidthInput
            else:
                final_dict[key] = int(value)
        if key == "HEIGHT":
            if int(value) <= 0:
                raise InvalidHeightInput
            else:
                final_dict[key] = int(value)
        if key == "ENTRY":
            try:
                x_entry, y_entry = value.strip().split(",")
                x_entry = int(x_entry)
                y_entry = int(y_entry)
                final_dict[key] = [x_entry,y_entry]
            except:
                raise InvalidEntryInput
        if key == "EXIT":
            try:
                x_exit, y_exit = value.strip().split(",")
                x_exit = int(x_exit)
                y_exit = int(y_exit)
                final_dict[key] = [x_exit,y_exit]
            except:
                raise InvalidExitInput
        if key == "OUTPUT_FILE":
            if (value != ""):
                output_file = value
                final_dict[key] = output_file
            else:
                raise EmptyFileName
        if key == "PERFECT":
            if value == "True" or value == 1:
                final_dict[key] = True
            elif value == "False" or value == 0:
                final_dict[key] = False
            else:
                raise InvalidPerfectPathInput
    if final_dict["EXIT"][0] >= final_dict["WIDTH"] or final_dict["EXIT"][1] >= final_dict["HEIGHT"] or final_dict["ENTRY"][0] >= final_dict["WIDTH"] or final_dict["ENTRY"][1] >= final_dict["HEIGHT"]:
        raise   ExceedingMazeLimit
    return final_dict


if __name__ == "__main__":
    config_dict = {}
    config_file = "default_config.txt"
    try:
        with open(config_file, "r") as f:
            text_list_unedited = [i.strip() for i in f if i.strip() != "" and i.strip()[0] != '#' ]
            for line in text_list_unedited:
                key, value = line.split("=", 1)
                config_dict[key.strip()] = value.strip()
    except FileNotFoundError:
        print("File Not Found!.")
        exit()






    try:
        final_dict:dict = dict_validate(config_dict)
    except ValueError:
        print("Input values should only contain int values")
        exit()
    except (InvalidWidthInput):
        print("Invalid Width Input")
        exit()
    except (InvalidHeightInput):
        print("Invalid Height Input")
        exit()
    except (MissingConfigInputs):
        print("Missing Config Parameters")
        exit()
    except (InvalidExitInput):
        print("Invalid Exit Input in config file")
        exit()
    except (InvalidEntryInput):
        print("Invalid Entry Input in config file")
        exit()
    except (EmptyFileName):
        print("Empty Output File Name")
        exit()
    except (InvalidPerfectPathInput):
        print("Invalid perfect path specifier, set to True or False")
        exit()
    except (ExceedingMazeLimit):
        print("Exceeding Maze Limit")
        exit()
    print("valdiation finished...")
    print(final_dict)