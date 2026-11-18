"""turtle judge main script."""

import sys
from dataclasses import dataclass
from pathlib import Path
lazy from types import CodeType

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
from judge.runtime import compile_script, diff_images, generate_png_image, generate_svg_byte_stream
from judge.translator import Translator

FULL_SIMILARITY_PERCENTAGE = 100


@dataclass(frozen=True)
class Settings:
    """Settings shared by all testcases."""

    translator: Translator
    canvas_size: tuple[int, int]
    minimum_similarity_percentage: float


def educator_error(translator: Translator, description: str) -> DodonaException:
    """Create an internal error that only educators see."""
    return DodonaException(
        translator.error_status(ErrorType.INTERNAL_ERROR),
        permission=MessagePermission.EDUCATOR,
        description=description,
        format=MessageFormat.CODE,
    )


def read_inputs(config: DodonaConfig, translator: Translator) -> list[str]:
    """Read the stdin contents to judge, one per testcase."""
    resources = Path(config.resources)
    input_files = getattr(config, "input_files", None)

    if input_files is None:
        input_file = resources / str(getattr(config, "input_file", "./input.txt"))
        return [input_file.read_text(encoding="utf-8") if input_file.exists() else ""]

    if hasattr(config, "input_file"):
        raise educator_error(translator, translator.translate(Translator.Text.INPUT_FILE_CONFLICT))

    inputs = []
    for name in input_files:
        path = resources / str(name)
        if not path.is_file():
            raise educator_error(translator, translator.translate(Translator.Text.INPUT_FILE_MISSING, path=name))
        inputs.append(path.read_text(encoding="utf-8"))
    return inputs


def submission_error(error: BaseException, translator: Translator, error_type: ErrorType) -> DodonaException:
    """Describe a failure of the submission."""
    return DodonaException(
        translator.error_status(error_type),
        description=translator.translate(Translator.Text.SUBMISSION_EXECUTION_ERROR, error=error),
        format=MessageFormat.CODE,
    )


def solution_error(error: BaseException, translator: Translator) -> DodonaException:
    """Describe a failure of the reference solution for educators only."""
    return educator_error(translator, translator.translate(Translator.Text.SOLUTION_EXECUTION_ERROR, error=error))


def compile_code(file_path: str | Path, translator: Translator, *, is_reference: bool = False) -> CodeType:
    """Compile a script, or raise a DodonaException describing why it failed."""
    try:
        return compile_script(file_path)
    except BaseException as error:
        if is_reference:
            raise solution_error(error, translator) from error

        raise submission_error(error, translator, ErrorType.COMPILATION_ERROR) from error


def generate_svg(
    code: CodeType,
    stdin_data: str,
    translator: Translator,
    canvas_size: tuple[int, int],
    *,
    is_reference: bool = False,
) -> bytes:
    """Run compiled code and return its drawing, or raise a DodonaException describing why it failed."""
    try:
        return generate_svg_byte_stream(code, *canvas_size, stdin_data)
    except BaseException as error:
        # BaseException: a submission calling exit() raises SystemExit, which must be reported too.
        if is_reference:
            raise solution_error(error, translator) from error

        raise submission_error(error, translator, ErrorType.RUNTIME_ERROR) from error


def render_input(submission: CodeType, stdin_data: str, settings: Settings) -> None:
    """Render the submission for one input as a correct testcase."""
    translator = settings.translator
    with Context(), TestCase(format=MessageFormat.CODE, description=stdin_data):
        svg_submission = generate_svg(submission, stdin_data, translator, settings.canvas_size)

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


def judge_input(submission: CodeType, svg_solution: bytes, stdin_data: str, settings: Settings) -> None:
    """Compare the submission with the solution's drawing for one input as a testcase."""
    translator = settings.translator
    with Context(), TestCase(format=MessageFormat.CODE, description=stdin_data):
        svg_submission = generate_svg(submission, stdin_data, translator, settings.canvas_size)

        png_submission = generate_png_image(svg_submission, *settings.canvas_size)
        png_solution = generate_png_image(svg_solution, *settings.canvas_size)

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

        if settings.minimum_similarity_percentage >= FULL_SIMILARITY_PERCENTAGE:
            expected = translator.translate(
                Translator.Text.FOREGROUND_PIXELS_CORRECT,
                correct_pixels=expected_total,
                total_pixels=expected_total,
                fraction=1,
            )
        else:
            expected = translator.translate(
                Translator.Text.MINIMUM_PIXELS_CORRECT,
                minimum=settings.minimum_similarity_percentage / 100,
            )

        with Test(
            {
                "format": MessageFormat.HTML,
                "description": " ".join(html.split()),
            },
            expected,
        ) as test:
            test.generated = translator.translate(
                Translator.Text.FOREGROUND_PIXELS_CORRECT,
                correct_pixels=correct_pixels,
                total_pixels=total_pixels,
                fraction=correct_pixels / total_pixels if total_pixels else 1,
            )

            # Multiplying avoids float rounding at the threshold (29 / 100 * 100 < 29).
            if correct_pixels * 100 < settings.minimum_similarity_percentage * total_pixels:
                test.status = translator.error_status(ErrorType.WRONG)
            else:
                test.status = translator.error_status(ErrorType.CORRECT)


def main(config: DodonaConfig) -> None:
    """Judge the submission described by the exercise configuration."""
    with Judgement() as judgement:
        config.sanity_check()

        # Initiate translator
        translator = Translator.from_str(config.natural_language)

        # Set 'canvas_width' to 400 if not set
        canvas_width = int(getattr(config, "canvas_width", "400"))
        # Set 'canvas_height' to 250 if not set
        canvas_height = int(getattr(config, "canvas_height", "250"))
        minimum_similarity_percentage = float(
            getattr(config, "minimum_similarity_percentage", FULL_SIMILARITY_PERCENTAGE)
        )
        settings = Settings(translator, (canvas_width, canvas_height), minimum_similarity_percentage)

        # Set 'solution_file' to "./solution.py" if not set
        solution_file = Path(config.resources) / str(getattr(config, "solution_file", "./solution.py"))

        inputs = read_inputs(config, translator)

        comparing = solution_file.exists()
        crash = None
        with Tab(translator.translate(Translator.Text.COMPARING_IMAGES if comparing else Translator.Text.RENDERING)):
            submission = compile_code(config.source, translator)
            if comparing:
                solution = compile_code(solution_file, translator, is_reference=True)
                svg_solutions = [
                    generate_svg(solution, stdin_data, translator, settings.canvas_size, is_reference=True)
                    for stdin_data in inputs
                ]

            for index, stdin_data in enumerate(inputs):
                try:
                    if comparing:
                        judge_input(submission, svg_solutions[index], stdin_data, settings)
                    else:
                        render_input(submission, stdin_data, settings)
                except DodonaException as error:
                    # The crash is already reported in its testcase; keep the first one for the judgement status.
                    crash = crash or error

        if crash is not None:
            judgement.accepted = False
            judgement.status = crash.status


if __name__ == "__main__":
    main(DodonaConfig.from_json(sys.stdin.read()))
