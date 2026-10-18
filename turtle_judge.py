"""turtle judge main script."""

import sys
from pathlib import Path

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


def generate_svg(
    file_path: str | Path,
    stdin_data: str,
    translator: Translator,
    canvas_size: tuple[int, int],
    *,
    is_reference: bool = False,
) -> bytes:
    """Run a script and return its drawing, or raise a DodonaException describing why it failed."""
    try:
        return generate_svg_byte_stream(file_path, *canvas_size, stdin_data)
    except BaseException as error:
        # BaseException: a submission calling exit() raises SystemExit, which must be reported too.
        if is_reference:
            raise DodonaException(
                translator.error_status(ErrorType.INTERNAL_ERROR),
                permission=MessagePermission.EDUCATOR,
                description=translator.translate(Translator.Text.SOLUTION_EXECUTION_ERROR, error=error),
                format=MessageFormat.CODE,
            ) from error

        raise DodonaException(
            translator.error_status(
                ErrorType.COMPILATION_ERROR if isinstance(error, SyntaxError) else ErrorType.RUNTIME_ERROR
            ),
            description=translator.translate(Translator.Text.SUBMISSION_EXECUTION_ERROR, error=error),
            format=MessageFormat.CODE,
        ) from error


def main(config: DodonaConfig) -> None:
    """Judge the submission described by the exercise configuration."""
    with Judgement():
        config.sanity_check()

        # Initiate translator
        translator = Translator.from_str(config.natural_language)

        # Set 'canvas_width' to 400 if not set
        canvas_width = int(getattr(config, "canvas_width", "400"))
        # Set 'canvas_height' to 250 if not set
        canvas_height = int(getattr(config, "canvas_height", "250"))
        canvas_size = (canvas_width, canvas_height)

        # Set 'solution_file' to "./solution.py" if not set
        solution_file = Path(config.resources) / str(getattr(config, "solution_file", "./solution.py"))

        # Read optional input file
        input_file = Path(config.resources) / str(getattr(config, "input_file", "./input.txt"))
        stdin_data = ""
        if input_file.exists():
            stdin_data = input_file.read_text(encoding="utf-8")

        if not solution_file.exists():
            with (
                Tab(translator.translate(Translator.Text.RENDERING)),
                Context(),
                TestCase(
                    format=MessageFormat.PYTHON,
                    description="",
                ),
            ):
                svg_submission = generate_svg(config.source, stdin_data, translator, canvas_size)

                svg_submission_str = svg_submission.decode("utf-8")

                html = f"""
                    <div style="background-color:#fff">{svg_submission_str}</div>
                    """

                with Test(
                    {
                        "format": MessageFormat.HTML,
                        "description": " ".join(html.split()),
                    },
                    "",
                ) as test:
                    test.generated = ""
                    test.status = translator.error_status(ErrorType.CORRECT)
        else:
            with (
                Tab(translator.translate(Translator.Text.COMPARING_IMAGES)),
                Context(),
                TestCase(
                    format=MessageFormat.PYTHON,
                    description="",
                ),
            ):
                svg_submission = generate_svg(config.source, stdin_data, translator, canvas_size)
                svg_solution = generate_svg(solution_file, stdin_data, translator, canvas_size, is_reference=True)

                png_submission = generate_png_image(svg_submission, canvas_width, canvas_height)
                png_solution = generate_png_image(svg_solution, canvas_width, canvas_height)

                correct_pixels, total_pixels, expected_total = diff_images(png_submission, png_solution)

                svg_submission_str = svg_submission.decode("utf-8")
                svg_solution_str = svg_solution.decode("utf-8")

                html = f"""
                    <div style="display:inline-block;width:50%;">
                        <p style="padding:10px">{translator.translate(Translator.Text.SUBMISSION_TITLE)}</p>
                        <div style="width:98%;background-color:#fff">{svg_submission_str}</div>
                    </div>
                    <div style="display:inline-block;float:right;width:50%;">
                        <p style="padding:10px">{translator.translate(Translator.Text.SOLUTION_TITLE)}</p>
                        <div style="width:98%;background-color:#fff">{svg_solution_str}</div>
                    </div>
                    """

                with Test(
                    {
                        "format": MessageFormat.HTML,
                        "description": " ".join(html.split()),
                    },
                    translator.translate(
                        Translator.Text.FOREGROUND_PIXELS_CORRECT,
                        correct_pixels=expected_total,
                        total_pixels=expected_total,
                        fraction=1,
                    ),
                ) as test:
                    test.generated = translator.translate(
                        Translator.Text.FOREGROUND_PIXELS_CORRECT,
                        correct_pixels=correct_pixels,
                        total_pixels=total_pixels,
                        fraction=correct_pixels / total_pixels,
                    )

                    if correct_pixels < total_pixels:
                        test.status = translator.error_status(ErrorType.WRONG)
                    else:
                        test.status = translator.error_status(ErrorType.CORRECT)


if __name__ == "__main__":
    main(DodonaConfig.from_json(sys.stdin.read()))
