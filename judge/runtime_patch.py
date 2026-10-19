"""Turtle runtime patches."""

import builtins
import sys
from contextlib import contextmanager
from io import StringIO
lazy from collections.abc import Iterator

from svg_turtle import SvgTurtle
from svg_turtle.canvas import Canvas


@contextmanager
def turtle_patch(width: int, height: int) -> Iterator[SvgTurtle]:
    """Patch the turtle module with the provided canvas size, yielding the shared turtle."""
    turtle_mod = sys.modules["turtle"]

    old_mainloop = turtle_mod.mainloop
    old_done = turtle_mod.done
    old_turtle = turtle_mod.Turtle
    try:
        screen = SvgTurtle._Screen(Canvas(width, height))  # noqa: SLF001
        screen.cv.config(bg="")
        screen.setworldcoordinates(
            -(screen.window_width() / 2) + 0.5,
            -(screen.window_height() / 2) - 0.5,
            +(screen.window_width() / 2) + 0.5,
            +(screen.window_height() / 2) - 0.5,
        )

        class CustomTurtle(SvgTurtle):
            """Custom Turtle class, of which each instance shares the same screen."""

            def __init__(self) -> None:
                super().__init__(screen=screen)

        SvgTurtle._screen = screen  # noqa: SLF001
        SvgTurtle._pen = CustomTurtle()  # noqa: SLF001

        turtle_mod.mainloop = lambda: None
        turtle_mod.done = lambda: None
        turtle_mod.Turtle = CustomTurtle

        yield SvgTurtle._pen  # noqa: SLF001
    finally:
        turtle_mod.mainloop = old_mainloop
        turtle_mod.done = old_done
        turtle_mod.Turtle = old_turtle


@contextmanager
def time_patch() -> Iterator[None]:
    """Patch the time module."""
    time_module = sys.modules["time"]
    old_sleep = time_module.sleep
    try:
        time_module.sleep = lambda _seconds: None
        yield
    finally:
        time_module.sleep = old_sleep


@contextmanager
def in_out_patch(stdin_data: str = "") -> Iterator[None]:
    """Patch stdin, stdout, stderr, with optional stdin data."""
    old_in, old_out, old_err = sys.stdin, sys.stdout, sys.stderr
    try:
        sys.stdin, sys.stdout, sys.stderr = StringIO(stdin_data), StringIO(), StringIO()
        yield
    finally:
        sys.stdin, sys.stdout, sys.stderr = old_in, old_out, old_err


@contextmanager
def runtime_patch(name: str) -> Iterator[None]:
    """Patch the python runtime, naming the script `name`."""
    old_os = sys.modules["os"]
    old_io = sys.modules["io"]
    old_open = builtins.open
    old_eval = builtins.eval
    old_exec = builtins.exec
    old_argv = sys.argv
    try:
        sys.modules["os"] = None
        sys.modules["io"] = None
        builtins.open = None
        builtins.eval = None
        builtins.exec = None
        sys.argv = [name]
        yield
    finally:
        sys.modules["os"] = old_os
        sys.modules["io"] = old_io
        builtins.open = old_open
        builtins.eval = old_eval
        builtins.exec = old_exec
        sys.argv = old_argv
