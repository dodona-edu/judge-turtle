"""Test E2E."""

import json
import os
import runpy
import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path

from .fake_in_out import fake_in_out


class TestEndToEnd(unittest.TestCase):
    """E2E TestCase."""

    def __init__(self, methodName: str) -> None:  # noqa: N803
        # methodName is unittest.TestCase's own parameter name, so it can't be renamed here.
        super().__init__(methodName=methodName)
        self.maxDiff = None
        self.root_path = Path(__file__).resolve().parent.parent

    def run_turtle_judge(
        self,
        exercise_path: Path,
        submission_path: Path,
        stdout_path: Path,
        learning_mode: bool = False,
    ):
        evaluation_path = exercise_path / "evaluation"
        config_path = exercise_path / "config.json"

        config = {}
        original_cwd = Path.cwd()

        with config_path.open(encoding="utf-8") as config_file:
            config.update(json.load(config_file).get("evaluation", {}))

        with tempfile.TemporaryDirectory() as cwd_path:
            # str(): these go through json.dumps, which has no idea what a Path is.
            config.update(
                {
                    "memory_limit": "99999999",
                    "time_limit": "99999999",
                    "programming_language": "python",
                    "natural_language": "nl",
                    "resources": str(evaluation_path),
                    "source": str(submission_path),
                    "judge": str(self.root_path),
                    "workdir": cwd_path,
                }
            )

            os.chdir(cwd_path)
            try:
                with fake_in_out(StringIO(json.dumps(config))) as (out, err):
                    runpy.run_path(str(self.root_path / "turtle_judge.py"))
            finally:
                # Back out before TemporaryDirectory deletes it. Without this the process is left
                # sitting in a directory that no longer exists, so os.getcwd() raises for whatever
                # runs next, and the judge's own sanity check calls Path.cwd().
                os.chdir(original_cwd)

        self.assertMultiLineEqual(err.getvalue().strip(), "")

        actual = out.getvalue().strip().replace(str(exercise_path), "<exercise_path>")

        if learning_mode:
            stdout_path.write_text(actual, encoding="utf-8")
        else:
            if not stdout_path.exists():
                raise FileNotFoundError(f"Missing stdout file: {stdout_path}")

            self.assertMultiLineEqual(actual, stdout_path.read_text(encoding="utf-8"))

    def run_all_repo_tests(self, repo_path: str):
        test_exercises_path = self.root_path / "tests" / "e2e_repos" / repo_path
        test_stdout_path = self.root_path / "tests" / "e2e_stdout" / repo_path

        learning_mode = os.environ.get("LEARN_OUTPUT", "NO") == "YES"
        if learning_mode:
            print("\n------------------------------------------")
            print("WARNING: LEARN_OUTPUT is enabled")
            print("> 'stdout' and 'stderr' files will get updated to match the execution output")
            print("------------------------------------------")

            shutil.rmtree(test_stdout_path)

        test_stdout_path.mkdir(parents=True, exist_ok=True)

        # sorted(): iterdir yields in directory order, so without it the subtests run in whatever
        # order the filesystem hands back, which differs between machines.
        for exercise_path in sorted(test_exercises_path.iterdir()):
            if exercise_path.name.startswith("_") or not exercise_path.is_dir():
                continue

            solution_path = exercise_path / "solution"

            for submission_path in sorted(solution_path.iterdir()):
                if submission_path.suffix != ".py":
                    continue

                stdout_path = test_stdout_path / f"{exercise_path.name}_{submission_path.stem}.stdout"

                with self.subTest(exercise=exercise_path.name, submission=submission_path.name):
                    self.run_turtle_judge(
                        exercise_path,
                        submission_path,
                        stdout_path,
                        learning_mode,
                    )

    def test_e2e(self):
        self.run_all_repo_tests("test-turtle-judge")
