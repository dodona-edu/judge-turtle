"""Test turtle_judge."""

import tempfile
import unittest
from pathlib import Path
from typing import Any

import turtle_judge
from judge.dodona_command import DodonaException, ErrorType
from judge.dodona_config import DodonaConfig
from judge.translator import Translator


class TestReadInputs(unittest.TestCase):
    """read_inputs TestCase."""

    def setUp(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        self.resources = Path(tempdir.name)
        self.translator = Translator.from_str("en")

    def write(self, name: str, text: str):
        (self.resources / name).write_text(text, encoding="utf-8")

    def read(self, **settings: Any):
        config = DodonaConfig(
            memory_limit="99999999",
            time_limit="99999999",
            programming_language="python",
            natural_language="en",
            resources=str(self.resources),
            source="[source]",
            judge="[judge]",
            workdir="[workdir]",
            **settings,
        )
        return turtle_judge.read_inputs(config, self.translator)

    def test_default_without_input_file(self):
        self.assertEqual(self.read(), [""])

    def test_default_input_file(self):
        self.write("input.txt", "hello\n")
        self.assertEqual(self.read(), ["hello\n"])

    def test_input_file(self):
        self.write("other.txt", "other\n")
        self.assertEqual(self.read(input_file="./other.txt"), ["other\n"])

    def test_input_files_in_order(self):
        self.write("a.txt", "a\n")
        self.write("b.txt", "b\n")
        self.assertEqual(self.read(input_files=["b.txt", "a.txt"]), ["b\n", "a\n"])

    def test_discovers_txt_files_in_natural_order(self):
        for name in ["10.txt", "2.txt", "1.txt", "b.txt", "a.txt"]:
            self.write(name, f"{name}\n")
        self.assertEqual(self.read(), ["1.txt\n", "2.txt\n", "10.txt\n", "a.txt\n", "b.txt\n"])

    def test_input_file_ignores_other_txt_files(self):
        self.write("input.txt", "input\n")
        self.write("other.txt", "other\n")
        self.assertEqual(self.read(input_file="other.txt"), ["other\n"])

    def test_input_files_ignores_unlisted_txt_files(self):
        self.write("a.txt", "a\n")
        self.write("b.txt", "b\n")
        self.assertEqual(self.read(input_files=["b.txt"]), ["b\n"])

    def test_no_txt_files(self):
        self.write("solution.py", "pass\n")
        self.assertEqual(self.read(), [""])

    def test_txt_in_subfolder_ignored(self):
        (self.resources / "sub").mkdir()
        self.write("sub/a.txt", "a\n")
        self.write("b.txt", "b\n")
        self.assertEqual(self.read(), ["b\n"])

    def test_both_keys_set(self):
        self.write("a.txt", "a\n")
        with self.assertRaises(DodonaException) as context:
            self.read(input_file="a.txt", input_files=["a.txt"])
        self.assertEqual(context.exception.status["enum"], ErrorType.INTERNAL_ERROR)

    def test_missing_listed_file(self):
        self.write("a.txt", "a\n")
        with self.assertRaises(DodonaException) as context:
            self.read(input_files=["a.txt", "missing.txt"])
        self.assertEqual(context.exception.status["enum"], ErrorType.INTERNAL_ERROR)
