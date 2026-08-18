"""translate judge output towards Dodona."""

from enum import Enum, auto
from typing import Any

from .dodona_command import ErrorType


class Translator:
    """a class for translating all user feedback.

    The Translator class provides translations for a set of Text
    messages and for the Dodona error types.
    """

    class Language(Enum):
        """Language."""

        EN = auto()
        NL = auto()

    class Text(Enum):
        """Text message content enum."""

        COMPARING_IMAGES = auto()
        RENDERING = auto()
        SOLUTION_EXECUTION_ERROR = auto()
        SUBMISSION_EXECUTION_ERROR = auto()
        SOLUTION_TITLE = auto()
        SUBMISSION_TITLE = auto()
        FOREGROUND_PIXELS_CORRECT = auto()

    def __init__(self, language: Language) -> None:
        """Create Translator.

        Args:
            language: language enum to use for translations
        """
        self.language = language

    @classmethod
    def from_str(cls: type["Translator"], language: str) -> "Translator":
        """Create a Translator instance.

        If the language is not detected correctly or not supported
        the translator defaults to English (EN).

        Args:
            language: Dodona language string "nl" or "en"

        Returns:
            translator
        """
        if language == "nl":
            return cls(cls.Language.NL)

        # default value is EN
        return cls(cls.Language.EN)

    def human_error(self, error: ErrorType) -> str:
        """Translate an ErrorType enum into a human-readable string.

        Args:
            error: ErrorType enum

        Returns:
            translated human-readable string
        """
        return self.error_translations[self.language][error]

    def error_status(self, error: ErrorType) -> dict[str, str]:
        """Translate an ErrorType enum into a status object.

        Args:
            error: ErrorType enum

        Returns:
            Dodona status object
        """
        return {
            "enum": error,
            "human": self.human_error(error),
        }

    def translate(self, message: Text, **kwargs: Any) -> str:
        """Translate a Text enum into a string.

        Args:
            message: Text enum
            kwargs: parameters for message

        Returns:
            translated text
        """
        return self.text_translations[self.language][message].format(**kwargs)

    error_translations = {
        Language.EN: {
            ErrorType.INTERNAL_ERROR: "Internal error",
            ErrorType.COMPILATION_ERROR: "The query is not valid",
            ErrorType.MEMORY_LIMIT_EXCEEDED: "Memory limit exceeded",
            ErrorType.TIME_LIMIT_EXCEEDED: "Time limit exceeded",
            ErrorType.OUTPUT_LIMIT_EXCEEDED: "Output limit exceeded",
            ErrorType.RUNTIME_ERROR: "Crashed while testing",
            ErrorType.WRONG: "Test failed",
            ErrorType.WRONG_ANSWER: "Test failed",
            ErrorType.CORRECT: "All tests succeeded",
            ErrorType.CORRECT_ANSWER: "All tests succeeded",
        },
        Language.NL: {
            ErrorType.INTERNAL_ERROR: "Interne fout",
            ErrorType.COMPILATION_ERROR: "Ongeldige query",
            ErrorType.MEMORY_LIMIT_EXCEEDED: "Geheugenlimiet overschreden",
            ErrorType.TIME_LIMIT_EXCEEDED: "Tijdslimiet overschreden",
            ErrorType.OUTPUT_LIMIT_EXCEEDED: "Outputlimiet overschreden",
            ErrorType.RUNTIME_ERROR: "Gecrasht bij testen",
            ErrorType.WRONG: "Test gefaald",
            ErrorType.WRONG_ANSWER: "Test gefaald",
            ErrorType.CORRECT: "Alle testen geslaagd",
            ErrorType.CORRECT_ANSWER: "Alle testen geslaagd",
        },
    }

    text_translations = {
        Language.EN: {
            Text.COMPARING_IMAGES: "Comparing images",
            Text.RENDERING: "Rendering",
            Text.SOLUTION_EXECUTION_ERROR: "Error executing solution script:\n    {error}",
            Text.SUBMISSION_EXECUTION_ERROR: "Error executing submission script:\n    {error}",
            Text.SOLUTION_TITLE: "Solution:",
            Text.SUBMISSION_TITLE: "Submission:",
            Text.FOREGROUND_PIXELS_CORRECT: "{correct_pixels}/{total_pixels} ({fraction:.1%}) visible pixels correct",
        },
        Language.NL: {
            Text.COMPARING_IMAGES: "Afbeeldingen vergelijken",
            Text.RENDERING: "Weergave",
            Text.SOLUTION_EXECUTION_ERROR: "Error bij het uitvoeren van het oplossingsscript:\n    {error}",
            Text.SUBMISSION_EXECUTION_ERROR: "Error bij het uitvoeren van het ingediende script:\n    {error}",
            Text.SOLUTION_TITLE: "Oplossing:",
            Text.SUBMISSION_TITLE: "Indiening:",
            Text.FOREGROUND_PIXELS_CORRECT: "{correct_pixels}/{total_pixels} ({fraction:.1%}) zichtbare pixels correct",
        },
    }
