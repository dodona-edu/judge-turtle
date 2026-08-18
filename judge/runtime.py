"""Turtle runtime."""

import io
import os
from io import BytesIO

import numpy as np
from cairosvg import svg2png  # noqa
from PIL import Image, ImageChops  # noqa

from .runtime_patch import InOutPatch, RuntimePatch, TimePatch, TurtlePatch


def run_file(file_path: str, width: int, height: int, stdin_data: str = ""):
    """Run the submission file."""
    script_name = "<solution>"
    code = None

    decoded_path = os.path.abspath(os.fsdecode(file_path))
    with io.open_code(decoded_path) as code_file:
        code = compile(code_file.read(), script_name, "exec")

    run_code = __builtins__["exec"]  # noqa

    with (
        TurtlePatch(width, height) as turtle,
        InOutPatch(stdin_data),
        TimePatch(),
        RuntimePatch(script_name),
    ):
        run_globals = {
            "__name__": script_name,
            "__file__": script_name,
            "__cached__": None,
            "__doc__": None,
            "__loader__": None,
            "__package__": script_name,
            "__spec__": None,
        }

        run_code(code, run_globals)

        return turtle


def generate_svg_byte_stream(file_path: str, width: int, height: int, stdin_data: str = "") -> bytes:
    """Generate SVG byte stream from file."""
    turtle_instance = run_file(file_path, width, height, stdin_data)
    return turtle_instance.to_svg().encode()


def generate_png_image(svg_bytes: bytes, width: int, height: int) -> Image.Image:
    """Generate PNG image from SVG bytes."""
    png_bytes = BytesIO()
    svg2png(bytestring=svg_bytes, write_to=png_bytes, output_width=width, output_height=height)
    return Image.open(png_bytes).convert("RGBA")


def diff_images(submission: Image.Image, solution: Image.Image) -> tuple[int, int, int]:
    """Generate difference between two images, and return the number differing pixels."""
    # int(): np.count_nonzero returns an np.int64, which json.dumps refuses. These values only
    # ever reach the feedback as interpolated text today, so nothing breaks, but the annotation
    # below says int and a caller that puts one straight into a command would fail at runtime.
    wrong_pixels = int(np.count_nonzero(np.array(ImageChops.difference(submission, solution)).any(axis=-1)))
    total_non_transparent_pixels = int(
        np.count_nonzero(np.array(submission).any(axis=-1) | np.array(solution).any(axis=-1))
    )
    correct_non_transparent_pixels = total_non_transparent_pixels - wrong_pixels
    expected_non_transparent_pixels = int(np.count_nonzero(np.array(solution).any(axis=-1)))

    return correct_non_transparent_pixels, total_non_transparent_pixels, expected_non_transparent_pixels
