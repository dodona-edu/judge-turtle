import sys
from io import BytesIO
from PIL import Image, ImageChops
from svg_turtle import SvgTurtle
from svg_turtle.canvas import Canvas
from cairosvg import svg2png
from typing import Any
import runpy


def monkey_patch():
    cls: Any = SvgTurtle
    cls._screen = SvgTurtle._Screen(Canvas(1000, 500))
    cls._pen = SvgTurtle()

    turtle_module: Any = sys.modules["turtle"]
    turtle_module.mainloop = turtle_module.done = lambda: None
    turtle_module.Turtle = SvgTurtle

    return cls._pen


def run_file(file_path: str):
    t = monkey_patch()

    runpy.run_path(file_path)

    return t


def generate_svg_byte_stream(file_path: str) -> bytes:
    t = run_file(file_path)

    svg_text = t.to_svg()
    return svg_text.encode()


def generate_png_image(svg_bytes: bytes) -> Image.Image:
    png_bytes = BytesIO()
    svg2png(bytestring=svg_bytes, write_to=png_bytes)
    return Image.open(png_bytes)


def diff_images(image1: Image.Image, image2: Image.Image) -> int:
    diff = ImageChops.difference(image1, image2)

    return sum(diff.histogram())
