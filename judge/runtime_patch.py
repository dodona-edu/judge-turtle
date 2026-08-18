"""Turtle runtime patches."""

import sys
from abc import ABC
from io import StringIO
from types import TracebackType
from typing import Any, Literal

from svg_turtle import SvgTurtle
from svg_turtle.canvas import Canvas


class Patch(ABC):
    """A patch helper class that allows to enter and exit a patch."""

    def __init__(self):
        """Base class for patches, each patch is fully defined by a generator function."""
        self.generator = self.patch()

    def patch(self):
        """Patch generator."""
        yield

    def __enter__(self) -> Any:
        """Start generator when entering the 'with' block.

        Returns:
            Value yielded by the generator
        """
        return next(self.generator)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Drop generator when leaving the 'with' block. This invokes the finally block in the generator.

        Returns:
            False: the patch 'with' block should not do any error handling.
        """
        self.generator = None

        return False  # don't handle any errors


class TurtlePatch(Patch):  # noqa: R0903
    """Patch the turtle module."""

    def __init__(self, width: int, height: int):
        """Create Turtle patch with provided canvas size."""
        self.width, self.height = width, height
        super().__init__()

    def patch(self):
        """Patch generator."""
        turtle_mod = sys.modules["turtle"]

        old_mainloop = turtle_mod.mainloop
        old_done = turtle_mod.done
        old_turtle = turtle_mod.Turtle
        try:
            screen = SvgTurtle._Screen(Canvas(self.width, self.height))  # noqa: W0212
            screen.cv.config(bg="")
            screen.setworldcoordinates(
                -(screen.window_width() / 2) + 0.5,
                -(screen.window_height() / 2) - 0.5,
                +(screen.window_width() / 2) + 0.5,
                +(screen.window_height() / 2) - 0.5,
            )

            class CustomTurtle(SvgTurtle):
                """Custom Turtle class, of which each instance shares the same screen."""

                def __init__(self):
                    super().__init__(screen=screen)

            SvgTurtle._screen = screen  # noqa: W0212
            SvgTurtle._pen = CustomTurtle()  # noqa: W0212

            turtle_mod.mainloop = lambda: None
            turtle_mod.done = lambda: None
            turtle_mod.Turtle = CustomTurtle

            yield SvgTurtle._pen  # noqa: W0212
        finally:
            turtle_mod.mainloop = old_mainloop
            turtle_mod.done = old_done
            turtle_mod.Turtle = old_turtle


class TimePatch(Patch):  # noqa: R0903
    """Patch the time module."""

    def patch(self):
        """Patch generator."""
        time_module = sys.modules["time"]
        old_sleep = time_module.sleep
        try:
            time_module.sleep = lambda x: None
            yield
        finally:
            time_module.sleep = old_sleep


class InOutPatch(Patch):  # noqa: R0903
    """Patch stdin, stdout, stderr."""

    def __init__(self, stdin_data: str = ""):
        """Create InOut patch with optional stdin data."""
        self.stdin_data = stdin_data
        super().__init__()

    def patch(self):
        """Patch generator."""
        old_in, old_out, old_err = sys.stdin, sys.stdout, sys.stderr
        __old_in__, __old_out__, __old_err__ = sys.__stdin__, sys.__stdout__, sys.__stderr__
        try:
            sys.stdin, sys.stdout, sys.stderr = StringIO(self.stdin_data), StringIO(), StringIO()
            __old_in__, __old_out__, __old_err__ = sys.stdin, sys.stdout, sys.stderr
            yield sys.stdin, sys.stdout, sys.stderr
        finally:
            sys.stdin, sys.stdout, sys.stderr = old_in, old_out, old_err
            sys.__stdin__, sys.__stdout__, sys.__stderr__ = __old_in__, __old_out__, __old_err__  # type: ignore[misc]


class RuntimePatch(Patch):  # noqa: R0903
    """Patch the python runtime."""

    def __init__(self, name: str):
        """Create runtime patch with provided name."""
        self.name = name
        super().__init__()

    def patch(self):
        """Patch generator."""
        old_os = sys.modules["os"]
        old_io = sys.modules["io"]
        old_open = __builtins__["open"]
        old_eval = __builtins__["eval"]
        old_exec = __builtins__["exec"]
        old_argv = sys.argv
        try:
            sys.modules["os"] = None
            sys.modules["io"] = None
            __builtins__["open"] = None
            __builtins__["eval"] = None
            __builtins__["exec"] = None
            sys.argv = [self.name]
            yield
        finally:
            sys.modules["os"] = old_os
            sys.modules["io"] = old_io
            __builtins__["open"] = old_open
            __builtins__["eval"] = old_eval
            __builtins__["exec"] = old_exec
            sys.argv = old_argv
