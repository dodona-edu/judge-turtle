"""Test DodonaCommand."""

import unittest

from judge.dodona_command import ErrorType, MessageFormat, MessagePermission


class TestDodonaCommand(unittest.TestCase):
    """DodonaCommand TestCase."""

    def test_string_values(self):
        self.assertEqual(ErrorType.COMPILATION_ERROR, "compilation error")
        self.assertEqual(MessagePermission.STUDENT, "student")
        self.assertEqual(MessageFormat.TEXT, "text")

        self.assertEqual(str(ErrorType.COMPILATION_ERROR), "compilation error")
        self.assertEqual(str(MessagePermission.STUDENT), "student")
        self.assertEqual(str(MessageFormat.TEXT), "text")
