"""Test DodonaCommand."""

import contextlib
import io
import json
import unittest

import pytest

from judge.dodona_command import Context, DodonaException, ErrorType, Judgement, MessageFormat, MessagePermission
from judge.dodona_command import Message as CommandMessage
from judge.dodona_command import TestCase as CommandTestCase


class TestDodonaCommand(unittest.TestCase):
    """DodonaCommand TestCase."""

    def test_string_values(self):
        self.assertEqual(ErrorType.COMPILATION_ERROR, "compilation error")
        self.assertEqual(MessagePermission.EDUCATOR, "educator")
        self.assertEqual(MessageFormat.HTML, "html")

        self.assertEqual(str(ErrorType.COMPILATION_ERROR), "compilation error")
        self.assertEqual(str(MessagePermission.EDUCATOR), "educator")
        self.assertEqual(str(MessageFormat.HTML), "html")

    def test_constructors(self):
        self.assertDictEqual(
            CommandTestCase(format=MessageFormat.PYTHON, description="test").start_msg(),
            {
                "command": "start-testcase",
                "description": {"format": "python", "description": "test"},
            },
        )
        self.assertDictEqual(
            CommandMessage(format=MessageFormat.PYTHON, description="test").start_msg(),
            {
                "command": "append-message",
                "message": {"format": "python", "description": "test"},
            },
        )

    def test_positional_argument_rejected(self):
        args = ("test",)
        with pytest.raises(TypeError):
            CommandTestCase(*args)
        with pytest.raises(TypeError):
            CommandMessage(*args)


class TestDodonaException(unittest.TestCase):
    """DodonaException TestCase."""

    def test_swallowed_by_judgement(self):
        status = {"enum": ErrorType.COMPILATION_ERROR, "human": "Compilation error"}
        out = io.StringIO()
        with (
            contextlib.redirect_stdout(out),
            Judgement(),
            Context(),
            CommandTestCase(format=MessageFormat.PYTHON, description="t"),
        ):
            raise DodonaException(
                status,
                permission=MessagePermission.EDUCATOR,
                description="boom",
                format=MessageFormat.CODE,
            )

        commands = [json.loads(chunk) for chunk in out.getvalue().replace("}\n{", "}\x00{").split("\x00")]
        self.assertListEqual(
            commands,
            [
                {"command": "start-judgement"},
                {"command": "start-context"},
                {"command": "start-testcase", "description": {"format": "python", "description": "t"}},
                {
                    "command": "append-message",
                    "message": {"permission": "educator", "description": "boom", "format": "code"},
                },
                {"command": "close-testcase", "accepted": False},
                {"command": "close-context", "accepted": False},
                {
                    "command": "close-judgement",
                    "accepted": False,
                    "status": {"enum": "compilation error", "human": "Compilation error"},
                },
            ],
        )

    def test_accepted_for_correct_status(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), Judgement(), Context():
            raise DodonaException({"enum": ErrorType.CORRECT, "human": "Correct"})

        self.assertNotIn("append-message", out.getvalue())
        self.assertIn('"accepted": true', out.getvalue())

    def test_not_swallowed_below_judgement(self):
        with contextlib.redirect_stdout(io.StringIO()), pytest.raises(DodonaException), Context():
            raise DodonaException({"enum": ErrorType.WRONG, "human": "Wrong"})
