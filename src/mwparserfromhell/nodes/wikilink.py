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

__all__ = ["Wikilink"]


class Wikilink(Node):
    """Represents an internal wikilink, like ``[[Foo|Bar]]``."""

    def __init__(self, title: Any, text: Any = None):
        super().__init__()
        self.title = title  # pyright: ignore[reportIncompatibleMethodOverride]
        self.text = text

    def __str__(self) -> str:
        if self.text is not None:
            return "[[" + str(self.title) + "|" + str(self.text) + "]]"
        return "[[" + str(self.title) + "]]"

    def __children__(self) -> Generator[Wikicode, None, None]:
        yield self.title
        if self.text is not None:
            yield self.text

    def __strip__(self, **kwargs: Any) -> str | None:
        if self.text is not None:
            return self.text.strip_code(**kwargs)
        return self.title.strip_code(**kwargs)

    def __showtree__(
        self,
        write: Callable[[str], None],
        get: Callable[[Wikicode], None],
        mark: Callable[[], None],
    ) -> None:
        write("[[")
        get(self.title)
        if self.text is not None:
            write("    | ")
            mark()
            get(self.text)
        write("]]")

    @property
    def title(self) -> Wikicode:
        """The title of the linked page, as a :class:`.Wikicode` object."""
        return self._title

    @title.setter
    def title(self, value: Any) -> None:
        self._title = parse_anything(value)

    @property
    def text(self) -> Wikicode | None:
        """The text to display (if any), as a :class:`.Wikicode` object."""
        return self._text

    @text.setter
    def text(self, value: Any) -> None:
        if value is None:
            self._text = None
        else:
            self._text = parse_anything(value)
