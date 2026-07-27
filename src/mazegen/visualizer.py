#!/usr/bin/env python3

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from mlx import Mlx

from .generator import MazeGenerationError
from .structure import Cell, Grid, Walls

if TYPE_CHECKING:
    from .generator import MazeGenerator

DEFAULT_CELL_SIZE = 20
WALL_THICKNESS = 2
CONTROL_BAR_HEIGHT = 20

RGB = tuple[int, int, int]

BACKGROUND_COLOR: RGB = (0, 0, 0)
ENTRY_COLOR: RGB = (4, 32, 207)
EXIT_COLOR: RGB = (255, 0, 0)
BLOCKED_COLOR: RGB = (150, 150, 150)
PATH_COLOR: RGB = (50, 120, 255)
TEXT_COLOR = 0xFFFFFF

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

CONTROLS_TEXT = "1: regen   2: path   3: color   4/ESC: quit"
KEYCODE_ESCAPE = 0xFF1B
KEYCODE_REGENERATE = ord("1")
KEYCODE_TOGGLE_PATH = ord("2")
KEYCODE_ROTATE_COLOR = ord("3")
KEYCODE_QUIT = ord("4")

XEVENT_CLIENT_MESSAGE = 33


class MlxVisualizer:
    """Interactive MiniLibX window rendering a mazegen Grid."""

    def __init__(
        self,
        generator: "MazeGenerator",
        cell_size: int = DEFAULT_CELL_SIZE,
    ) -> None:
        """Open the MLX window sized for this generator's current maze."""
        self.generator = generator
        self.cell_size = cell_size
        self.grid: Grid = generator.get_structure()
        self.show_path = False
        self.wall_color_index = 0
        self.current_image_pointer: int | None = None

        self.window_width_in_pixels = self.grid.width * cell_size
        self.window_height_in_pixels = (
            self.grid.height * cell_size + CONTROL_BAR_HEIGHT
        )

        self.mlx = Mlx()
        self.mlx_pointer = self.mlx.mlx_init()
        self.window_pointer = self.mlx.mlx_new_window(
            self.mlx_pointer,
            self.window_width_in_pixels,
            self.window_height_in_pixels,
            "A-maze-ing",
        )

    def run(self) -> None:
        """Draw the maze, turn on the keyboard controls, and wait for input."""
        self.draw()
        self.mlx.mlx_key_hook(
            self.window_pointer, self.on_key_press, None,
        )
        self.mlx.mlx_hook(
            self.window_pointer, XEVENT_CLIENT_MESSAGE, 0,
            self.on_close_button, None,
        )
        print("MLX visualizer running:", CONTROLS_TEXT)
        self.mlx.mlx_loop(self.mlx_pointer)

    def draw(self) -> None:
        """Render the whole maze into a new image and show it."""
        new_image_pointer = self.mlx.mlx_new_image(
            self.mlx_pointer,
            self.window_width_in_pixels,
            self.window_height_in_pixels,
        )
        pixel_memory_array, bits_per_pixel, bytes_per_image_row, _fmt = (
            self.mlx.mlx_get_data_addr(new_image_pointer)
        )
        bytes_per_pixel = bits_per_pixel // 8

        self.paint_solid_rectangle(
            pixel_memory_array, bytes_per_image_row, bytes_per_pixel,
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
                    pixel_memory_array, bytes_per_image_row,
                    bytes_per_pixel, cell, current_wall_color,
                    solution_path_cells,
                )

        previous_image_pointer = self.current_image_pointer
        if previous_image_pointer is not None:
            self.mlx.mlx_destroy_image(
                self.mlx_pointer, previous_image_pointer,
            )
        self.current_image_pointer = new_image_pointer

        self.mlx.mlx_put_image_to_window(
            self.mlx_pointer, self.window_pointer, new_image_pointer, 0, 0,
        )
        self.mlx.mlx_string_put(
            self.mlx_pointer, self.window_pointer,
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
        pixel_memory_array: memoryview,
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
        pixel_memory_array: memoryview,
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
                pixel_memory_array[exact_byte_offset] = blue
                pixel_memory_array[exact_byte_offset + 1] = green
                pixel_memory_array[exact_byte_offset + 2] = red
                pixel_memory_array[exact_byte_offset + 3] = 255

    def on_key_press(self, keycode: int, _param: object) -> None:
        """Run the action bound to a keycode (regen/path/color/quit)."""
        print(f"[visualizer] key received: keycode={keycode}")

        if keycode == KEYCODE_REGENERATE:
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
            self.mlx.mlx_loop_exit(self.mlx_pointer)

    def on_close_button(self, _param: object) -> None:
        """Quit when the window's own close ([X]) button is clicked."""
        print("[visualizer] close button clicked")
        self.mlx.mlx_loop_exit(self.mlx_pointer)
