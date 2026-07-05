#!/usr/bin/env python3

# Self-contained MLX (minilibx-linux) visualizer for the maze structures
# Casie's code already builds (Grid/Cell/Walls in structure.py) and already
# renders as ASCII (output_maze.ascii_display, which walks the exact same
# `for row in grid.cells: for cell in row` list this file reuses). Nothing
# else in the repo is touched by this file; the only wiring point is the one
# `MazeGenerator.visualize()` call added in generator.py.
#
# Background on what MLX is, why minilibx-linux specifically, and how
# libmlx.dylib/.so gets built is documented in WALKTHROUGH.md, Part 3 and
# in the "Visualization" section at the very end of that same file.

from __future__ import annotations

import ctypes
import pathlib
import random
from typing import TYPE_CHECKING, Any

from .generator import MazeGenerationError
from .structure import Cell, Grid, Walls

if TYPE_CHECKING:
    from .generator import MazeGenerator

DEFAULT_CELL_SIZE = 20
WALL_THICKNESS = 2
CONTROL_BAR_HEIGHT = 20

RGB = tuple[int, int, int]

BACKGROUND_COLOR: RGB = (0, 0, 0)
ENTRY_COLOR: RGB = (255, 0, 255)
EXIT_COLOR: RGB = (255, 0, 0)
BLOCKED_COLOR: RGB = (150, 150, 150)
PATH_COLOR: RGB = (50, 120, 255)
TEXT_COLOR = 0xFFFFFF

# (change_in_x, change_in_y) step for each solve_floodfill.solve() direction
# letter, used to turn its N/E/S/W path back into a set of (x, y) cells to
# highlight on screen.
PATH_STEP_DELTAS: dict[str, tuple[int, int]] = {
    "N": (0, -1),
    "E": (1, 0),
    "S": (0, 1),
    "W": (-1, 0),
}

WALL_COLOR_PALETTE: list[RGB] = [
    (255, 255, 255),
    (255, 215, 0),
    (0, 255, 0),
    (0, 200, 255),
]

CONTROLS_TEXT = b"1: regen   2: path   3: color   4/ESC: quit"
KEYCODE_ESCAPE = 0xFF1B
KEYCODE_REGENERATE = ord("1")
KEYCODE_TOGGLE_PATH = ord("2")
KEYCODE_ROTATE_COLOR = ord("3")
KEYCODE_QUIT = ord("4")


def locate_compiled_mlx_library() -> pathlib.Path:
    """Find the compiled minilibx shared library file for this repo.

    minilibx-linux does not come as a ready-made download -- it is C
    source code that has to be compiled, once, into one finished file
    before Python can use it at all (see vendor/build_mlx.sh). This
    function simply looks in the one place that finished file is
    expected to live, on either operating system this project supports.
    """
    repository_root_folder = pathlib.Path(__file__).resolve().parents[2]

    for compiled_file_name in ("libmlx.dylib", "libmlx.so"):
        candidate_path = repository_root_folder / "build" / compiled_file_name
        if candidate_path.exists():
            return candidate_path

    raise RuntimeError(
        "Could not find build/libmlx.dylib or build/libmlx.so. Build "
        "minilibx-linux first by running: sh vendor/build_mlx.sh "
        "(see WALKTHROUGH.md, Part 3)."
    )


class MlxBridge:
    """Translates between Python and the compiled MiniLibX C library.

    Python cannot call a C library's functions without first being told,
    function by function, what kind of inputs it expects and what kind
    of output it gives back. That one-time description is everything
    this class does -- it has no idea what a maze even is. Every other
    piece of maze-drawing logic lives in `MlxVisualizer` below instead.
    """

    def __init__(self) -> None:
        """Load the compiled library and describe each function we use."""
        # Step 1: locate and load the compiled C file built by
        # vendor/build_mlx.sh (libmlx.dylib on macOS, libmlx.so on Linux).
        self.compiled_library = ctypes.CDLL(str(locate_compiled_mlx_library()))

        # Step 2: tell Python exactly how to talk to the C library safely.
        # For every MiniLibX function we plan to call, we declare its
        # "argtypes" (the kind of value each argument must be) and its
        # "restype" (the kind of value it hands back). Skipping this
        # step is what would let Python send the wrong kind of data into
        # C and crash the whole program with no helpful error message.

        self.compiled_library.mlx_init.restype = ctypes.c_void_p

        self.compiled_library.mlx_new_window.restype = ctypes.c_void_p
        self.compiled_library.mlx_new_window.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_char_p,
        ]

        self.compiled_library.mlx_new_image.restype = ctypes.c_void_p
        self.compiled_library.mlx_new_image.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
        ]

        self.compiled_library.mlx_get_data_addr.restype = ctypes.POINTER(
            ctypes.c_char
        )
        self.compiled_library.mlx_get_data_addr.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        ]

        self.compiled_library.mlx_put_image_to_window.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_int, ctypes.c_int,
        ]

        self.compiled_library.mlx_destroy_image.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p,
        ]

        self.compiled_library.mlx_string_put.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_char_p,
        ]

        self.compiled_library.mlx_key_hook.argtypes = [
            ctypes.c_void_p,
            ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_void_p),
            ctypes.c_void_p,
        ]

        self.compiled_library.mlx_loop_end.argtypes = [ctypes.c_void_p]
        self.compiled_library.mlx_loop.argtypes = [ctypes.c_void_p]


# A reusable "shape" for the function we hand to MiniLibX to run every time
# a key is pressed: it takes a keycode number and one extra raw pointer
# MiniLibX always passes along (which we never need to use), and returns a
# whole number MiniLibX ignores.
KeyPressCallback = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
)

# The finished image lives in memory as one giant list of individual color
# bytes -- this is the type of that list once ctypes hands it back to us.
PixelMemoryArray = ctypes.Array[ctypes.c_uint8]


class MlxVisualizer:
    """Interactive MiniLibX window rendering a mazegen `Grid`.

    Maps each `Cell` to a `cell_size`-pixel square: `cell.walls` (the same
    North/East/South/West bitmask `output_maze.ascii_display` reads) draws
    the four edge lines, and entry/exit/blocked/path cells get a filled
    color underneath those lines.
    """

    def __init__(
        self,
        generator: "MazeGenerator",
        cell_size: int = DEFAULT_CELL_SIZE,
    ) -> None:
        self.generator = generator
        self.cell_size = cell_size
        self.grid: Grid = generator.get_structure()
        self.show_path = False
        self.wall_color_index = 0

        # These start out empty because nothing has been drawn or bound
        # to a key yet -- they get filled in the very first time draw()
        # and setup_keyboard_controls() run.
        self.current_image_pointer: int | None = None
        self.key_press_callback: Any = None

        self.window_width_in_pixels = self.grid.width * cell_size
        self.window_height_in_pixels = (
            self.grid.height * cell_size + CONTROL_BAR_HEIGHT
        )

        # Open the actual connection to MiniLibX and create one real,
        # visible window sized exactly to fit this maze.
        self.mlx_bridge = MlxBridge()
        self.current_mlx_pointer = self.mlx_bridge.compiled_library.mlx_init()
        self.current_window_pointer = (
            self.mlx_bridge.compiled_library.mlx_new_window(
                self.current_mlx_pointer,
                self.window_width_in_pixels,
                self.window_height_in_pixels,
                b"A-maze-ing",
            )
        )

    def run(self) -> None:
        """Draw the maze, turn on the keyboard controls, and wait for input."""
        self.draw()
        self.setup_keyboard_controls()
        print("MLX visualizer running:", CONTROLS_TEXT.decode())
        self.mlx_bridge.compiled_library.mlx_loop(self.current_mlx_pointer)

    def draw(self) -> None:
        """Render the whole maze into a brand-new image and show it."""
        library = self.mlx_bridge.compiled_library

        # Step 1: ask MiniLibX for a blank image exactly the size of our
        # window, and ask for direct access to its raw pixel memory so we
        # can paint into it ourselves, one color at a time.
        new_image_pointer = library.mlx_new_image(
            self.current_mlx_pointer,
            self.window_width_in_pixels,
            self.window_height_in_pixels,
        )

        bits_per_pixel_result = ctypes.c_int()
        bytes_per_image_row = ctypes.c_int()
        byte_order_flag = ctypes.c_int()
        raw_pixel_data_pointer = library.mlx_get_data_addr(
            new_image_pointer,
            ctypes.byref(bits_per_pixel_result),
            ctypes.byref(bytes_per_image_row),
            ctypes.byref(byte_order_flag),
        )

        bytes_per_pixel = bits_per_pixel_result.value // 8
        pixel_memory_array_size = (
            bytes_per_image_row.value * self.window_height_in_pixels
        )
        pixel_memory_array = ctypes.cast(
            raw_pixel_data_pointer,
            ctypes.POINTER(ctypes.c_uint8 * pixel_memory_array_size),
        ).contents

        # Step 2: paint the whole image black first, as a clean canvas
        # underneath everything else we are about to draw.
        self.paint_solid_rectangle(
            pixel_memory_array, bytes_per_image_row.value, bytes_per_pixel,
            0, 0, self.window_width_in_pixels, self.window_height_in_pixels,
            BACKGROUND_COLOR,
        )

        # Step 3: work out which color the walls should currently be, and
        # which cells (if any) belong to the solution path, then draw
        # every single cell of the maze, one at a time, row by row -- the
        # exact same `for row in grid.cells: for cell in row` order Casie's
        # ascii_display() already uses.
        current_wall_color = WALL_COLOR_PALETTE[self.wall_color_index]
        solution_path_cells = (
            self.compute_solution_path_cells() if self.show_path else set()
        )
        for row_of_cells in self.grid.cells:
            for cell in row_of_cells:
                self.draw_individual_cell(
                    pixel_memory_array, bytes_per_image_row.value,
                    bytes_per_pixel, cell, current_wall_color,
                    solution_path_cells,
                )

        # Step 4: throw away the previous frame's image (if there was
        # one) now that the new one is ready, so we never build up an
        # ever-growing pile of unused images in memory across repeated
        # regenerate/toggle/color-change presses.
        previous_image_pointer = self.current_image_pointer
        if previous_image_pointer is not None:
            library.mlx_destroy_image(
                self.current_mlx_pointer, previous_image_pointer,
            )
        self.current_image_pointer = new_image_pointer

        # Step 5: hand the finished picture to MiniLibX so it actually
        # appears in the window, then draw the one-line control reminder
        # text on top of it.
        library.mlx_put_image_to_window(
            self.current_mlx_pointer, self.current_window_pointer,
            new_image_pointer, 0, 0,
        )
        library.mlx_string_put(
            self.current_mlx_pointer, self.current_window_pointer,
            5, self.window_height_in_pixels - 6,
            TEXT_COLOR, CONTROLS_TEXT,
        )

    def compute_solution_path_cells(self) -> set[tuple[int, int]]:
        """Return the (x, y) cells on the solution path, if one exists."""
        try:
            path_directions = self.generator.get_solution()
        except (NotImplementedError, ValueError, MazeGenerationError) as exc:
            print(f"[visualizer] could not compute solution path: {exc}")
            return set()

        current_x, current_y = self.generator.entry
        cells_on_the_path = {(current_x, current_y)}

        for direction_letter in path_directions:
            change_in_x, change_in_y = PATH_STEP_DELTAS[direction_letter]
            current_x = current_x + change_in_x
            current_y = current_y + change_in_y
            cells_on_the_path.add((current_x, current_y))

        return cells_on_the_path

    def draw_individual_cell(
        self,
        pixel_memory_array: PixelMemoryArray,
        bytes_per_image_row: int,
        bytes_per_pixel: int,
        cell: Cell,
        wall_color: RGB,
        solution_path_cells: set[tuple[int, int]],
    ) -> None:
        """Paint one cell's special color (if any), then draw its walls."""
        cell_size_in_pixels = self.cell_size
        pixel_x = cell.x * cell_size_in_pixels
        pixel_y = cell.y * cell_size_in_pixels
        entry_x, entry_y = self.generator.entry
        exit_x, exit_y = self.generator.exit

        # Step 1: decide whether this particular cell needs a solid
        # color pad underneath its walls -- and if several reasons could
        # apply at once, this priority order decides which one wins.
        if cell.blocked:
            fill_color: RGB | None = BLOCKED_COLOR
        elif (cell.x, cell.y) == (entry_x, entry_y):
            fill_color = ENTRY_COLOR
        elif (cell.x, cell.y) == (exit_x, exit_y):
            fill_color = EXIT_COLOR
        elif (cell.x, cell.y) in solution_path_cells:
            fill_color = PATH_COLOR
        else:
            fill_color = None

        # Step 2: paint the entry/exit/blocked/path pad first, before any
        # wall lines go on top of it, so the walls stay clearly visible
        # even over a colored cell.
        if fill_color is not None:
            self.paint_solid_rectangle(
                pixel_memory_array, bytes_per_image_row, bytes_per_pixel,
                pixel_x, pixel_y, cell_size_in_pixels, cell_size_in_pixels,
                fill_color,
            )

        # Step 3: draw a short line on whichever of the four edges this
        # cell has a closed wall on -- reading the exact same North/East/
        # South/West bits `output_maze.ascii_display` already reads.
        wall_thickness_in_pixels = WALL_THICKNESS

        if cell.walls & Walls.NORTH:
            self.paint_solid_rectangle(
                pixel_memory_array, bytes_per_image_row, bytes_per_pixel,
                pixel_x, pixel_y,
                cell_size_in_pixels, wall_thickness_in_pixels,
                wall_color,
            )

        if cell.walls & Walls.SOUTH:
            self.paint_solid_rectangle(
                pixel_memory_array, bytes_per_image_row, bytes_per_pixel,
                pixel_x, pixel_y + cell_size_in_pixels
                - wall_thickness_in_pixels,
                cell_size_in_pixels, wall_thickness_in_pixels,
                wall_color,
            )

        if cell.walls & Walls.WEST:
            self.paint_solid_rectangle(
                pixel_memory_array, bytes_per_image_row, bytes_per_pixel,
                pixel_x, pixel_y,
                wall_thickness_in_pixels, cell_size_in_pixels,
                wall_color,
            )

        if cell.walls & Walls.EAST:
            self.paint_solid_rectangle(
                pixel_memory_array, bytes_per_image_row, bytes_per_pixel,
                pixel_x + cell_size_in_pixels - wall_thickness_in_pixels,
                pixel_y,
                wall_thickness_in_pixels, cell_size_in_pixels,
                wall_color,
            )

    @staticmethod
    def paint_solid_rectangle(
        pixel_memory_array: PixelMemoryArray,
        bytes_per_image_row: int,
        bytes_per_pixel: int,
        x: int,
        y: int,
        width: int,
        height: int,
        color: RGB,
    ) -> None:
        """Write one solid-color rectangle directly into the image memory.

        This writes color bytes one at a time, in a plain, easy-to-follow
        double loop (every row, then every column in that row) rather
        than a clever shortcut -- clarity here matters more than shaving
        off a fraction of a second.
        """
        red, green, blue = color

        for pixel_row in range(y, y + height):
            row_start_offset = pixel_row * bytes_per_image_row

            for pixel_column in range(x, x + width):
                exact_byte_offset = (
                    row_start_offset + pixel_column * bytes_per_pixel
                )
                # MiniLibX stores each pixel's color as three consecutive
                # bytes in this exact order: blue, then green, then red.
                pixel_memory_array[exact_byte_offset] = blue
                pixel_memory_array[exact_byte_offset + 1] = green
                pixel_memory_array[exact_byte_offset + 2] = red

    def setup_keyboard_controls(self) -> None:
        """Tell MiniLibX which function to call whenever a key is pressed."""
        @KeyPressCallback
        def handle_key_press_event(
            keycode: int, unused_extra_data: int,
        ) -> int:
            """Forward the raw keycode MiniLibX reports to our own logic."""
            self.process_keyboard_input(keycode)
            return 0

        # This callback is kept as an attribute on purpose: if we let
        # Python forget about it, it could be garbage-collected while
        # MiniLibX still holds a raw pointer to it, which would crash the
        # program the next time any key is pressed.
        self.key_press_callback = handle_key_press_event
        self.mlx_bridge.compiled_library.mlx_key_hook(
            self.current_window_pointer, handle_key_press_event, None,
        )

    def process_keyboard_input(self, keycode: int) -> None:
        """Carry out whichever action is bound to the key just pressed."""
        print(f"[visualizer] key received: keycode={keycode}")

        if keycode == KEYCODE_REGENERATE:
            # A fixed seed makes generate() reproduce the identical maze
            # on every call (that is the whole point of a seed) -- which
            # would look exactly like "regenerate did nothing". A manual,
            # user-triggered regenerate should visibly produce a new
            # maze, so we pick a brand-new random seed for it every time.
            new_random_seed = random.randrange(2**32)
            self.generator.seed = new_random_seed
            self.generator.generate()
            self.grid = self.generator.get_structure()
            print(f"[visualizer] regenerated maze with seed={new_random_seed}")
            self.draw()

        elif keycode == KEYCODE_TOGGLE_PATH:
            self.show_path = not self.show_path
            path_visibility_state = "ON" if self.show_path else "OFF"
            print(f"[visualizer] path toggle: {path_visibility_state}")
            self.draw()

        elif keycode == KEYCODE_ROTATE_COLOR:
            self.wall_color_index = (
                self.wall_color_index + 1
            ) % len(WALL_COLOR_PALETTE)
            self.draw()

        elif keycode in (KEYCODE_QUIT, KEYCODE_ESCAPE):
            self.mlx_bridge.compiled_library.mlx_loop_end(
                self.current_mlx_pointer
            )
