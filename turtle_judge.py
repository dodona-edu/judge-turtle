"""turtle judge main script."""

import sys

from judge.dodona_command import (
    Context,
    ErrorType,
    Judgement,
    MessageFormat,
    Tab,
    Test,
    TestCase,
)
from judge.dodona_config import DodonaConfig
from judge.translator import Translator
from judge.runtime import generate_svg_byte_stream, generate_png_image, diff_images

# extract info from exercise configuration
config = DodonaConfig.from_json(sys.stdin.read())

with Judgement():
    config.sanity_check()

    # Initiate translator
    config.translator = Translator.from_str(config.natural_language)

    # Set 'solution_file' to "./solution.py" if not set
    config.solution_file = str(getattr(config, "solution_file", "./solution.py"))

    with Tab(f"Comparing PNGs"):
        with Context(), TestCase(
            format=MessageFormat.PYTHON,
            description=config.raw_submission_file,
        ) as testcase:
            svg_submission = generate_svg_byte_stream(config.source)
            png_submission = generate_png_image(svg_submission)

            svg_solution = generate_svg_byte_stream(config.solution_file)
            png_solution = generate_png_image(svg_solution)

            diff = diff_images(png_submission, png_solution)

            with Test(
                f"test1 {diff}",
                svg_submission.decode("utf-8"),
            ) as test:
                test.generated = svg_solution.decode("utf-8")
