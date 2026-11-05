"""Report judge's results to Dodona using Dodona commands (partial JSON output)."""

import json
import sys
from abc import ABC
from enum import StrEnum
from types import SimpleNamespace, TracebackType
from typing import Any


class ErrorType(StrEnum):
    """Dodona error type."""

    INTERNAL_ERROR = "internal error"
    COMPILATION_ERROR = "compilation error"
    MEMORY_LIMIT_EXCEEDED = "memory limit exceeded"
    TIME_LIMIT_EXCEEDED = "time limit exceeded"
    OUTPUT_LIMIT_EXCEEDED = "output limit exceeded"
    RUNTIME_ERROR = "runtime error"
    WRONG = "wrong"
    WRONG_ANSWER = "wrong answer"
    CORRECT = "correct"
    CORRECT_ANSWER = "correct answer"


class MessagePermission(StrEnum):
    """Dodona permission for a message."""

    EDUCATOR = "educator"


class MessageFormat(StrEnum):
    """Dodona format for a message."""

    HTML = "html"
    CODE = "code"
    PYTHON = "python"


class DodonaException(Exception):
    """Exception that creates a message and sets the status of the enclosing 'with' blocks.

    When thrown inside a Dodona 'with' block, the message is printed once, by the innermost block.
    Blocks that extend DodonaCommandWithAccepted get their accepted field set (True if CORRECT or
    CORRECT_ANSWER, False otherwise), blocks that extend DodonaCommandWithStatus also get their status
    set. Judgement catches the exception.
    """

    def __init__(self, status: dict[str, str], **kwargs: Any) -> None:
        """Create DodonaException.

        Args:
            status: a status object
            **kwargs: named parameters used to create the error message
        """
        super().__init__()
        self.status = status
        self.message = Message(**kwargs) if len(kwargs) > 0 else None


# B024: no abstract members. Every method here has a usable default, so there is nothing to
# declare abstract. ABC stays to say it is only ever subclassed, never instantiated directly.
class DodonaCommand(ABC):  # noqa: B024
    """Abstract class, parent of all Dodona commands.

    This class provides all shared functionality for the Dodona commands. These commands
    should be used in a Python 'with' block.

    Example:
        >>> with Judgement() as judgement:
        ...     with Tab("example tab"):
        ...         pass

    A JSON message will be printed to stdout when entering the 'with' block. The contents of
    the message are the parameters passed to the constructor to the class.
    When exiting the 'with' block, a close JSON message will be printed to stdout. The contents
    of that message are set dynamically on the object that was returned when entering.

    Example:
        >>> with Tab(
        ...     title="example tab",
        ... ) as tab:
        ...     tab.badgeCount = 43

    When entering the 'with' block, prints:
    {
        "command": "start-tab",
        "title": "example tab"
    }

    When exiting the 'with' block, prints:
    {
        "command": "close-tab",
        "badgeCount": 43
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        """Create DodonaCommand.

        Args:
            **kwargs: dict that is JSON encoded and printed when entering the 'with' block
        """
        self.start_args = SimpleNamespace(**kwargs)
        self.close_args = SimpleNamespace()

    def name(self) -> str:
        """Get name used in start and close messages, defaults to the lowercase version of the classname.

        Returns:
            name
        """
        return self.__class__.__name__.lower()

    def start_msg(self) -> dict:
        """Create start message that is printed as JSON to stdout when entering the 'with' block.

        Returns:
            start message
        """
        return {"command": f"start-{self.name()}", **self.start_args.__dict__}

    def close_msg(self) -> dict | None:
        """Create close message that is printed as JSON to stdout when exiting the 'with' block.

        Returns:
            close message
        """
        return {"command": f"close-{self.name()}", **self.close_args.__dict__}

    @staticmethod
    def __print_command(result: dict | None) -> None:
        """Print the provided to stdout as JSON.

        Args:
            result: dict that will be JSON encoded and printed to stdout
        """
        if result is None:
            return
        json.dump(result, sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write("\n")  # Next JSON fragment should be on new line

    def __enter__(self) -> SimpleNamespace:
        """Print the start message when entering the 'with' block.

        Returns:
            SimpleNamespace object that can be used to dynamically create the
            close message
        """
        self.__print_command(self.start_msg())
        return self.close_args

    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        """Print the exception's message, unless an inner block already did.

        Child classes can overwrite this, but should still call it.

        Args:
            exception: exception thrown in the enclosed 'with' block

        Returns:
            if True, the exception is not propagated
        """
        if exception.message is not None:
            with exception.message:
                pass

            exception.message = None

        return False

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Print the close message when exiting the 'with' block & handle enclosed exceptions.

        If a DodonaException was thrown in the enclosed 'with' block, the 'handle_dodona_exception'
        function is called. This function can be overwritten by child classes. If 'handle_dodona_exception'
        returns True, this function also returns True and the error is not propagated.

        Args:
            exc_type: exception type
            exc_val: exception value
            exc_tb: exception traceback

        Returns:
            if True, the exception is not propagated
        """
        handled = self.handle_dodona_exception(exc_val) if isinstance(exc_val, DodonaException) else False

        self.__print_command(self.close_msg())
        return handled


class DodonaCommandWithAccepted(DodonaCommand):
    """abstract class, parent of all Dodona commands that have an accepted field."""

    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        """Update the accepted parameter based on the exception status.

        Args:
            exception: exception thrown in the enclosed 'with' block

        Returns:
            if True, the exception is not propagated
        """
        accepted = exception.status["enum"] == ErrorType.CORRECT or exception.status["enum"] == ErrorType.CORRECT_ANSWER
        self.close_args.accepted = accepted

        return super().handle_dodona_exception(exception)


class DodonaCommandWithStatus(DodonaCommandWithAccepted):
    """abstract class, parent of all Dodona commands that have a status field."""

    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        """Update the status of the object.

        Args:
            exception: exception thrown in the enclosed 'with' block

        Returns:
            if True, the exception is not propagated
        """
        self.close_args.status = exception.status

        return super().handle_dodona_exception(exception)


class Judgement(DodonaCommandWithStatus):
    """Dodona Judgement."""

    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        """Update the status and swallow the exception.

        Args:
            exception: exception thrown in the enclosed 'with' block

        Returns:
            True, the exception is not propagated
        """
        super().handle_dodona_exception(exception)
        return True


class Tab(DodonaCommand):
    """Dodona Tab."""

    def __init__(self, title: str, **kwargs: Any) -> None:
        """Create Tab.

        Args:
            title: title of the tab
            **kwargs: additional named arguments
        """
        super().__init__(title=title, **kwargs)


class Context(DodonaCommandWithAccepted):
    """Dodona Context."""


class TestCase(DodonaCommandWithAccepted):
    """Dodona TestCase."""

    def __init__(self, **kwargs: Any) -> None:
        """Create TestCase.

        The keyword arguments are the content of the test case's description.

        Example:
            >>> with TestCase(
            ...     format=MessageFormat.PYTHON,
            ...     description="This is the message"
            ... ):
            ...     pass

        Args:
            **kwargs: dict is assumed to be the description object
        """
        super().__init__(description=kwargs)


class Test(DodonaCommandWithStatus):
    """Dodona Test."""

    def __init__(self, description: str | dict, expected: str, **kwargs: Any) -> None:
        """Create Test.

        Args:
            description: a description string or object
            expected: the expected output
            **kwargs: dict that provides additional start message properties
        """
        super().__init__(description=description, expected=expected, **kwargs)


class Message(DodonaCommand):
    """Dodona Message."""

    def __init__(self, **kwargs: Any) -> None:
        """Create Message.

        The keyword arguments are the content of the message.

        Example:
            >>> with Message(
            ...     format=MessageFormat.CODE,
            ...     description="This is the message"
            ... ):
            ...     pass

        Args:
            **kwargs: dict is assumed to be the message object
        """
        super().__init__(message=kwargs)

    def start_msg(self) -> dict:
        """Print the "append-message" command and parameters when entering the 'with' block.

        Returns:
            start message that will be JSON encoded and printed to stdout
        """
        return {"command": "append-message", **self.start_args.__dict__}

    def close_msg(self) -> None:
        """Don't print anything when exiting the 'with' block."""
