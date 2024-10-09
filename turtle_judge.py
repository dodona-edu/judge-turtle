"""turtle judge main script."""

import base64
import os
import sys

from judge.dodona_command import (
    Context,
    DodonaException,
    ErrorType,
    Judgement,
    MessageFormat,
    MessagePermission,
    Tab,
    Test,
    TestCase,
)
from judge.dodona_config import DodonaConfig
from judge.runtime import diff_images, generate_png_image, generate_svg_byte_stream
from judge.translator import Translator

# extract info from exercise configuration
config = DodonaConfig.from_json(sys.stdin.read())

with Judgement():
    config.sanity_check()

    # Initiate translator
    config.translator = Translator.from_str(config.natural_language)

    # Set 'canvas_width' to 400 if not set
    config.canvas_width = int(getattr(config, "canvas_width", "400"))
    # Set 'canvas_height' to 250 if not set
    config.canvas_height = int(getattr(config, "canvas_height", "250"))

    # Set 'solution_file' to "./solution.py" if not set
    config.solution_file = str(getattr(config, "solution_file", "./solution.py"))
    config.solution_file = os.path.join(config.resources, config.solution_file)

    if not os.path.exists(config.solution_file):
        raise DodonaException(
            config.translator.error_status(ErrorType.RUNTIME_ERROR),
            permission=MessagePermission.STAFF,
            description=f"Could not find solution file: '{config.solution_file}'.",
            format=MessageFormat.TEXT,
        )

    with Tab(config.translator.translate(Translator.Text.COMPARING_IMAGES)):
        with Context(), TestCase(
            format=MessageFormat.PYTHON,
            description="",
        ):
            try:
                svg_submission = generate_svg_byte_stream(config.source, config.canvas_width, config.canvas_height)
            except BaseException as error:
                raise DodonaException(
                    config.translator.error_status(ErrorType.COMPILATION_ERROR),
                    description=config.translator.translate(Translator.Text.SOLUTION_EXECUTION_ERROR, error=error),
                    format=MessageFormat.CODE,
                ) from error
            try:
                svg_solution = generate_svg_byte_stream(config.solution_file, config.canvas_width, config.canvas_height)
            except BaseException as error:
                raise DodonaException(
                    config.translator.error_status(ErrorType.COMPILATION_ERROR),
                    permission=MessagePermission.STAFF,
                    description=config.translator.translate(Translator.Text.SUBMISSION_EXECUTION_ERROR, error=error),
                    format=MessageFormat.CODE,
                ) from error

            png_submission = generate_png_image(svg_submission, config.canvas_width, config.canvas_height)
            png_solution = generate_png_image(svg_solution, config.canvas_width, config.canvas_height)

            correct_pixels, total_pixels, expected_total = diff_images(png_submission, png_solution)

            # base64_submission = base64.b64encode(svg_submission).decode("utf-8")
            # base64_solution = base64.b64encode(svg_solution).decode("utf-8")

            svg_submission_str = svg_submission.decode("utf-8")
            svg_solution_str = svg_solution.decode("utf-8")

            html = f"""
            <div style="display:inline-block;width:50%;">
                <p style="padding:10px">{config.translator.translate(Translator.Text.SUBMISSION_TITLE)}</p>
                <div style="width:98%;background-color:#fff">{svg_submission_str}</div>
            </div>
            <div style="display:inline-block;float:right;width:50%;">
                <p style="padding:10px">{config.translator.translate(Translator.Text.SOLUTION_TITLE)}</p>
                <div style="width:98%;background-color:#fff">{svg_solution_str}</div>
            </div>
            """

            with Test(
                {
                    "format": MessageFormat.HTML,
                    "description": " ".join(html.split()),
                },
                config.translator.translate(
                    Translator.Text.FOREGROUND_PIXELS_CORRECT,
                    correct_pixels=expected_total,
                    total_pixels=expected_total,
                    fraction=1,
                ),
            ) as test:
                test.generated = config.translator.translate(
                    Translator.Text.FOREGROUND_PIXELS_CORRECT,
                    correct_pixels=correct_pixels,
                    total_pixels=total_pixels,
                    fraction=correct_pixels / total_pixels,
                )

                if correct_pixels < total_pixels:
                    test.status = config.translator.error_status(ErrorType.WRONG)
                else:
                    test.status = config.translator.error_status(ErrorType.CORRECT)
