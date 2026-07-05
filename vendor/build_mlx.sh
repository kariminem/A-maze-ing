#!/usr/bin/env sh
# Quick compile script for minilibx-linux to shared library

# 1. Stop immediately if any compilation command fails
set -e

# 2. Get the folder paths
MLX_DIR="vendor/minilibx-linux"
OUTPUT_DIR="build"

mkdir -p $OUTPUT_DIR

# 3. The exact list of C source files we need to build
SRC_FILES="mlx_init.c mlx_new_window.c mlx_pixel_put.c mlx_loop.c \
mlx_mouse_hook.c mlx_key_hook.c mlx_expose_hook.c mlx_loop_hook.c \
mlx_int_anti_resize_win.c mlx_int_do_nothing.c \
mlx_int_wait_first_expose.c mlx_int_get_visual.c \
mlx_flush_event.c mlx_string_put.c mlx_set_font.c \
mlx_new_image.c mlx_get_data_addr.c \
mlx_put_image_to_window.c mlx_get_color_value.c mlx_clear_window.c \
mlx_xpm.c mlx_int_str_to_wordtab.c mlx_destroy_window.c \
mlx_int_param_event.c mlx_int_set_win_event_mask.c mlx_hook.c \
mlx_rgb.c mlx_destroy_image.c mlx_mouse.c mlx_screen_size.c \
mlx_destroy_display.c"

# 4. Check the OS and compile standard dynamic flags
OS_NAME=$(uname)

cd $MLX_DIR

if [ "$OS_NAME" = "Darwin" ]; then
    echo "Building for macOS (requires XQuartz)..."
    cc -dynamiclib -O2 -I/usr/X11/include \
        $SRC_FILES -L/usr/X11/lib -lXext -lX11 -lm \
        -o "../../$OUTPUT_DIR/libmlx.dylib"
elif [ "$OS_NAME" = "Linux" ]; then
    echo "Building for Linux..."
    cc -shared -fPIC -O2 \
        $SRC_FILES -lXext -lX11 -lm \
        -o "../../$OUTPUT_DIR/libmlx.so"
else
    echo "Error: Unknown OS"
    exit 1
fi

echo "Compilation successful!"