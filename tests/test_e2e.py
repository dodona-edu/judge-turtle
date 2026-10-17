"""Test E2E."""

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path

import turtle_judge
from judge.dodona_config import DodonaConfig


class TestEndToEnd(unittest.TestCase):
    """E2E TestCase."""

    def __init__(self, methodName: str) -> None:  # noqa: N803
        # methodName is unittest.TestCase's own parameter name, so it can't be renamed here.
        super().__init__(methodName=methodName)
        self.maxDiff = None
        self.root_path = Path(__file__).resolve().parent.parent

    def build_config(self, exercise_path: Path, submission_path: Path, cwd_path: str) -> dict:
        """Build the Dodona config JSON for one exercise and submission."""
        config = {}

        with (exercise_path / "config.json").open(encoding="utf-8") as config_file:
            config.update(json.load(config_file).get("evaluation", {}))

        # str(): these go through json.dumps, which has no idea what a Path is.
        config.update(
            {
                "memory_limit": "99999999",
                "time_limit": "99999999",
                "programming_language": "python",
                "natural_language": "nl",
                "resources": str(exercise_path / "evaluation"),
                "source": str(submission_path),
                "judge": str(self.root_path),
                "workdir": cwd_path,
            }
        )
        return config

    def run_turtle_judge(
        self,
        exercise_path: Path,
        submission_path: Path,
        stdout_path: Path,
        learning_mode: bool = False,
    ):
        original_cwd = Path.cwd()

        with tempfile.TemporaryDirectory() as cwd_path:
            config = self.build_config(exercise_path, submission_path, cwd_path)

            os.chdir(cwd_path)
            try:
                out, err = StringIO(), StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    turtle_judge.main(DodonaConfig.from_json(json.dumps(config)))
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

    def test_example_exercises(self):
        self.run_all_repo_tests("example-exercises")

    def test_script_entry_point(self):
        """Run `python turtle_judge.py` with the config on stdin, as Dodona does."""
        exercise_path = self.root_path / "tests" / "e2e_repos" / "example-exercises" / "house"
        stdout_path = self.root_path / "tests" / "e2e_stdout" / "example-exercises" / "house_solution.stdout"

        with tempfile.TemporaryDirectory() as cwd_path:
            config = self.build_config(exercise_path, exercise_path / "solution" / "solution.py", cwd_path)
            # sys.executable, not the `run` script: macOS /bin/sh strips DYLD_* and breaks cairo loading.
            result = subprocess.run(  # noqa: S603
                [sys.executable, str(self.root_path / "turtle_judge.py")],
                input=json.dumps(config),
                capture_output=True,
                text=True,
                cwd=cwd_path,
                check=False,
            )

        self.assertMultiLineEqual(result.stderr.strip(), "")
        self.assertEqual(result.returncode, 0)
        actual = result.stdout.strip().replace(str(exercise_path), "<exercise_path>")
        self.assertMultiLineEqual(actual, stdout_path.read_text(encoding="utf-8"))
