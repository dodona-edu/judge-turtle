"""Test Translator."""

import unittest

from judge.dodona_command import ErrorType
from judge.translator import Translator


class TestTranslator(unittest.TestCase):
    """Translator TestCase."""

    def test_translate(self):
        self.assertEqual(
            Translator.from_str("nl").translate(Translator.Text.COMPARING_IMAGES),
            "Afbeeldingen vergelijken",
        )

        self.assertEqual(
            Translator.from_str("en").translate(Translator.Text.COMPARING_IMAGES),
            "Comparing images",
        )

    def test_human_error(self):
        self.assertEqual(
            Translator.from_str("nl").human_error(ErrorType.CORRECT),
            "Alle testen geslaagd",
        )

        self.assertEqual(
            Translator.from_str("en").human_error(ErrorType.CORRECT),
            "All tests succeeded",
        )

    def test_error_status(self):
        self.assertDictEqual(
            Translator.from_str("nl").error_status(ErrorType.CORRECT),
            {
                "enum": ErrorType.CORRECT,
                "human": "Alle testen geslaagd",
            },
        )

        self.assertDictEqual(
            Translator.from_str("en").error_status(ErrorType.CORRECT),
            {
                "enum": ErrorType.CORRECT,
                "human": "All tests succeeded",
            },
        )

    def test_turtle_error_headlines(self):
        self.assertEqual(
            Translator.from_str("en").human_error(ErrorType.COMPILATION_ERROR),
            "The code contains a syntax error",
        )

        self.assertEqual(
            Translator.from_str("nl").human_error(ErrorType.COMPILATION_ERROR),
            "De code bevat een syntaxfout",
        )
