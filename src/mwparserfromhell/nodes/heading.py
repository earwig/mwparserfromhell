# Copyright (C) 2012-2025 Ben Kurtovic <ben.kurtovic@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any, Callable

from ..utils import parse_anything
from ._base import Node

if TYPE_CHECKING:
    from ..wikicode import Wikicode


class Heading(Node):
    """Represents a section heading in wikicode, like ``== Foo ==``."""

    def __init__(self, title: Any, level: int):
        super().__init__()
        self.title = title  # pyright: ignore[reportIncompatibleMethodOverride]
        self.level = level

    def __str__(self) -> str:
        return ("=" * self.level) + str(self.title) + ("=" * self.level)

    def __children__(self) -> Generator[Wikicode, None, None]:
        yield self.title

    def __strip__(self, **kwargs: Any) -> str | None:
        return self.title.strip_code(**kwargs)

    def __showtree__(
        self,
        write: Callable[[str], None],
        get: Callable[[Wikicode], None],
        mark: Callable[[], None],
    ) -> None:
        write("=" * self.level)
        get(self.title)
        write("=" * self.level)

    @property
    def title(self) -> Wikicode:
        """The title of the heading, as a :class:`.Wikicode` object."""
        return self._title

    @title.setter
    def title(self, value: Any) -> None:
        self._title = parse_anything(value)

    @property
    def level(self) -> int:
        """The heading level, as an integer between 1 and 6, inclusive."""
        return self._level

    @level.setter
    def level(self, value: int) -> None:
        value = int(value)
        if value < 1 or value > 6:
            raise ValueError(value)
        self._level = value
