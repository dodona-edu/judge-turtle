"""Turtle runtime."""

import builtins
import io
from pathlib import Path
from typing import Any

from cairosvg import svg2png
from PIL import Image, ImageChops

from .runtime_patch import in_out_patch, runtime_patch, time_patch, turtle_patch


def run_file(file_path: str | Path, width: int, height: int, stdin_data: str = "") -> Any:
    """Run the submission file."""
    script_name = "<solution>"

    with io.open_code(str(Path(file_path).resolve())) as code_file:
        code = compile(code_file.read(), script_name, "exec")

    # Grabbed before the patches below null out builtins.exec for the submission.
    run_code = builtins.exec

    with (
        turtle_patch(width, height) as turtle,
        in_out_patch(stdin_data),
        time_patch(),
        runtime_patch(script_name),
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


def generate_svg_byte_stream(file_path: str | Path, width: int, height: int, stdin_data: str = "") -> bytes:
    """Generate SVG byte stream from file."""
    turtle_instance = run_file(file_path, width, height, stdin_data)
    return turtle_instance.to_svg().encode()


def generate_png_image(svg_bytes: bytes, width: int, height: int) -> Image.Image:
    """Generate PNG image from SVG bytes."""
    png_bytes = svg2png(bytestring=svg_bytes, output_width=width, output_height=height)
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def _any_channel_mask(image: Image.Image) -> Image.Image:
    """Collapse an image to one band that is non-zero where any channel is non-zero."""
    mask, *channels = image.split()
    for channel in channels:
        mask = ImageChops.lighter(mask, channel)
    return mask


def _count_non_zero(mask: Image.Image) -> int:
    """Count the non-zero pixels of a single-band image."""
    width, height = mask.size
    return width * height - mask.histogram()[0]


def diff_images(submission: Image.Image, solution: Image.Image) -> tuple[int, int, int]:
    """Generate difference between two images, and return the number differing pixels."""
    submission_mask = _any_channel_mask(submission)
    solution_mask = _any_channel_mask(solution)

    wrong_pixels = _count_non_zero(_any_channel_mask(ImageChops.difference(submission, solution)))
    total_non_transparent_pixels = _count_non_zero(ImageChops.lighter(submission_mask, solution_mask))
    correct_non_transparent_pixels = total_non_transparent_pixels - wrong_pixels
    expected_non_transparent_pixels = _count_non_zero(solution_mask)

    return correct_non_transparent_pixels, total_non_transparent_pixels, expected_non_transparent_pixels
