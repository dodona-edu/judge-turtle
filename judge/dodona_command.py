"""Report judge's results to Dodona using Dodona commands (partial JSON output)."""

import json
import sys
from abc import ABC
from enum import Enum
from types import SimpleNamespace, TracebackType
from typing import Any, Optional, Union


class ErrorType(str, Enum):
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

    def __str__(self) -> str:  # noqa: E0307
        """Convert enum to string.

        Returns:
            string representation of enum
        """
        return self


class MessagePermission(str, Enum):
    """Dodona permission for a message."""

    STUDENT = "student"
    STAFF = "staff"
    ZEUS = "zeus"

    def __str__(self) -> str:  # noqa: E0307
        """Convert enum to string.

        Returns:
            string representation of enum
        """
        return self


class MessageFormat(str, Enum):
    """Dodona format for a message."""

    PLAIN = "plain"
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    CALLOUT = "callout"
    CALLOUT_INFO = "callout-info"
    CALLOUT_WARNING = "callout-warning"
    CALLOUT_DANGER = "callout-danger"
    CODE = "code"
    PYTHON = "python"

    def __str__(self) -> str:  # noqa: E0307
        """Convert enum to string.

        Returns:
            string representation of enum
        """
        return self


class AnnotationSeverity(str, Enum):
    """Dodona severity of an annotation."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    def __str__(self) -> str:  # noqa: E0307
        """Convert enum to string.

        Returns:
            string representation of enum
        """
        return self


class DodonaException(Exception):
    """Exception that will automatically create a message and set the correct status when thrown.

    When thrown inside a Dodona 'with' block, an error message will be created on the current
    Dodona object (eg. Test, Context ...). Blocks that extend the DodonaCommandWithAccepted class
    will have their accepted field set to True (if CORRECT or CORRECT_ANSWER) and to False otherwise.
    If the block also extends DodonaCommandWithStatus, its status is updated with this exception's
    status. A with block with a type that matches recover_at will silently catch the exception; and
    if the class is not Judgement, an escalate status message will be sent.
    """

    def __init__(
        self,
        status: dict[str, str],
        recover_at: type = None,
        **kwargs: Any,
    ) -> None:
        """Create DodonaException.

        Args:
            status: a status object
            recover_at: the type of the 'with' block to recover at
            **kwargs: named parameters used to create the error message
        """
        super().__init__()
        self.status = status
        if recover_at is None:
            # class Judgement is not yet defined, use this hack to retrieve the class at runtime
            self.recover_at = globals()["Judgement"]
            self.escalate_status = False
        else:
            self.recover_at = recover_at
            self.escalate_status = True
        self.message = Message(**kwargs) if len(kwargs) > 0 else None


class DodonaCommand(ABC):
    """Abstract class, parent of all Dodona commands.

    This class provides all shared functionality for the Dodona commands. These commands
    should be used in a Python 'with' block.

    Example:
        >>> with Judgement() as judgement:
        ...     with Tab():
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

    def close_msg(self) -> Optional[dict]:
        """Create close message that is printed as JSON to stdout when exiting the 'with' block.

        Returns:
            close message
        """
        return {"command": f"close-{self.name()}", **self.close_args.__dict__}

    @staticmethod
    def __print_command(result: Optional[dict]) -> None:
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
        """Handle a DodonaException.

        This function returns a boolean that is True if the exception should
        not get propagated to parent codeblocks. This should only be True
        if the current with block's type matches the type defined in recover_at,
        this means that all higher levels of Dodona objects can update their
        status and success parameters.

        This function can be overwritten by child classes, these overwrites
        should still call this function.

        This function prints a Dodona message and removes the message from
        the exception, so it is not also printed by the parent 'with' blocks.
        The function return True if self is of the type recover_at.

        Args:
            exception: exception thrown in the enclosed 'with' block

        Returns:
            if True, the exception is not propagated
        """
        # Add an error message
        if exception.message is not None:
            with exception.message:
                pass

            exception.message = None

        if isinstance(self, exception.recover_at):
            if exception.escalate_status:
                self.__print_command(
                    {
                        "command": "escalate-status",
                        "status": exception.status,
                    }
                )

            return True

        return False

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
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
        if isinstance(exc_val, DodonaException):
            handled = self.handle_dodona_exception(exc_val)
        else:
            handled = False

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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create TestCase.

        If a single positional argument is passed, this is assumed to be the message.

        Example:
            >>> with TestCase("This is the message"):
            ...     pass
            >>> with TestCase({
            ...     "format": MessageFormat.SQL,
            ...     "description": "This is the message"
            ... }):
            ...     pass

        If keyword arguments are passed, these are assumed to be the message's content.

        Example:
            >>> with TestCase(
            ...     format=MessageFormat.SQL,
            ...     description="This is the message"
            ... ):
            ...     pass

        Args:
            *args: positional args (if length == 1, is assumed to be the description)
            **kwargs: dict is assumed to be the description object
        """
        if len(args) == 1:
            super().__init__(description=args[0])
        else:
            super().__init__(description=kwargs)


class Test(DodonaCommandWithStatus):
    """Dodona Test."""

    def __init__(self, description: Union[str, dict], expected: str, **kwargs: Any) -> None:
        """Create Test.

        Args:
            description: a description string or object
            expected: the expected output
            **kwargs: dict that provides additional start message properties
        """
        super().__init__(description=description, expected=expected, **kwargs)


class Message(DodonaCommand):
    """Dodona Message."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create Message.

        If a single positional argument is passed, this is assumed to be the message.

        Example:
        >>> with Message("This is the message"):
        ...     pass
        >>> with Message({
        ...     "format": MessageFormat.SQL,
        ...     "description": "This is the message"
        ... }):
        ...     pass

        If keyword arguments are passed, these are assumed to be the message's content.

        Example:
        >>> with Message(
        ...     format=MessageFormat.SQL,
        ...     description="This is the message"
        ... ):
        ...     pass

        Args:
            *args: positional args (if length == 1, is assumed to be message)
            **kwargs: dict is assumed to be the message object
        """
        if len(args) == 1:
            super().__init__(message=args[0])
        else:
            super().__init__(message=kwargs)

    def start_msg(self) -> dict:
        """Print the "append-message" command and parameters when entering the 'with' block.

        Returns:
            start message that will be JSON encoded and printed to stdout
        """
        return {"command": "append-message", **self.start_args.__dict__}

    def close_msg(self) -> None:
        """Don't print anything when exiting the 'with' block."""


class Annotation(DodonaCommand):
    """Dodona Annotation."""

    def __init__(self, row: int, text: str, **kwargs: Any) -> None:
        """Create Annotation.

        Args:
            row: row number to annotate
            text: text to add in annotation
            **kwargs: additional named arguments
        """
        super().__init__(row=row, text=text, **kwargs)

    def start_msg(self) -> dict:
        """Print the "annotate-code" command and parameters when entering the 'with' block.

        Returns:
            start message that will be JSON encoded and printed to stdout
        """
        return {"command": "annotate-code", **self.start_args.__dict__}

    def close_msg(self) -> None:
        """Don't print anything when exiting the 'with' block."""
