#!/usr/bin/env python3

# Interactive MLX (minilibx-linux) window for a mazegen Grid.

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

# Step for each solve_floodfill.solve() direction letter, used to turn a
# path of letters back into (x, y) cells.
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
    """Find the compiled minilibx shared library (see vendor/build_mlx.sh)."""
    repository_root_folder = pathlib.Path(__file__).resolve().parents[2]

    for compiled_file_name in ("libmlx.dylib", "libmlx.so"):
        candidate_path = repository_root_folder / "build" / compiled_file_name
        if candidate_path.exists():
            return candidate_path

    raise RuntimeError(
        "Could not find build/libmlx.dylib or build/libmlx.so. Build "
        "minilibx-linux first by running: sh vendor/build_mlx.sh"
    )


class MlxBridge:
    """ctypes binding for the MiniLibX C functions this file calls."""

    def __init__(self) -> None:
        self.compiled_library = ctypes.CDLL(str(locate_compiled_mlx_library()))

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


KeyPressCallback = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
)

PixelMemoryArray = ctypes.Array[ctypes.c_uint8]


class MlxVisualizer:
    """Interactive MiniLibX window rendering a mazegen Grid."""

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
        self.current_image_pointer: int | None = None
        self.key_press_callback: Any = None

        self.window_width_in_pixels = self.grid.width * cell_size
        self.window_height_in_pixels = (
            self.grid.height * cell_size + CONTROL_BAR_HEIGHT
        )

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
        """Render the whole maze into a new image and show it."""
        library = self.mlx_bridge.compiled_library

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

        self.paint_solid_rectangle(
            pixel_memory_array, bytes_per_image_row.value, bytes_per_pixel,
            0, 0, self.window_width_in_pixels, self.window_height_in_pixels,
            BACKGROUND_COLOR,
        )

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

        # drop the previous frame's image now that the new one is ready
        previous_image_pointer = self.current_image_pointer
        if previous_image_pointer is not None:
            library.mlx_destroy_image(
                self.current_mlx_pointer, previous_image_pointer,
            )
        self.current_image_pointer = new_image_pointer

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

        # priority: blocked > entry > exit > path
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

        if fill_color is not None:
            self.paint_solid_rectangle(
                pixel_memory_array, bytes_per_image_row, bytes_per_pixel,
                pixel_x, pixel_y, cell_size_in_pixels, cell_size_in_pixels,
                fill_color,
            )

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
        """Write one solid-color rectangle directly into the image memory."""
        red, green, blue = color

        for pixel_row in range(y, y + height):
            row_start_offset = pixel_row * bytes_per_image_row

            for pixel_column in range(x, x + width):
                exact_byte_offset = (
                    row_start_offset + pixel_column * bytes_per_pixel
                )
                # MiniLibX pixel byte order is blue, green, red
                pixel_memory_array[exact_byte_offset] = blue
                pixel_memory_array[exact_byte_offset + 1] = green
                pixel_memory_array[exact_byte_offset + 2] = red

    def setup_keyboard_controls(self) -> None:
        """Register the MLX key callback that dispatches to our handler."""
        @KeyPressCallback
        def handle_key_press_event(
            keycode: int, unused_extra_data: int,
        ) -> int:
            self.process_keyboard_input(keycode)
            return 0

        # kept as an attribute so ctypes doesn't garbage-collect it
        self.key_press_callback = handle_key_press_event
        self.mlx_bridge.compiled_library.mlx_key_hook(
            self.current_window_pointer, handle_key_press_event, None,
        )

    def process_keyboard_input(self, keycode: int) -> None:
        """Run the action bound to a keycode (regen/path/color/quit)."""
        print(f"[visualizer] key received: keycode={keycode}")

        if keycode == KEYCODE_REGENERATE:
            # force a fresh seed so a manual regenerate is visibly different
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
