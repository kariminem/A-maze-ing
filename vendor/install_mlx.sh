#!/usr/bin/env sh
# Installs the official mlx (MiniLibX) Python package from the prebuilt
# wheel bundled with the subject (vendor/mlx-2.2.tgz), picking the wheel
# that matches the current Linux distro. Only Ubuntu and Fedora wheels are
# provided, and only for Linux -- there is no macOS build.
#
# Usage, from the repository root:
#   sh vendor/install_mlx.sh

set -e

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
ARCHIVE="$SCRIPT_DIR/mlx-2.2.tgz"
EXTRACT_DIR="$SCRIPT_DIR/mlx-2.2"

if [ ! -f "$ARCHIVE" ]; then
	echo "error: $ARCHIVE not found." >&2
	exit 1
fi

if [ "$(uname)" != "Linux" ]; then
	echo "Skipping MLX install: prebuilt wheels are Linux-only (Ubuntu/Fedora)." >&2
	echo "See vendor/mlx-2.2.tgz (src/) to build it from source instead." >&2
	exit 0
fi

DISTRO_ID=$(. /etc/os-release && echo "$ID")

case "$DISTRO_ID" in
	ubuntu | debian)
		WHEEL_DIR="ubuntu"
		;;
	fedora | rhel | centos)
		WHEEL_DIR="fedora"
		;;
	*)
		echo "error: unrecognized Linux distro '$DISTRO_ID'." >&2
		echo "Only ubuntu/ and fedora/ wheels are provided in $ARCHIVE." >&2
		exit 1
		;;
esac

rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"
tar -xzf "$ARCHIVE" -C "$EXTRACT_DIR"

python3 -m pip install "$EXTRACT_DIR/$WHEEL_DIR"/mlx-*.whl

echo "Installed mlx from $WHEEL_DIR wheel."
