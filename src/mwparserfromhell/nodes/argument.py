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

__all__ = ["Argument"]


class Argument(Node):
    """Represents a template argument substitution, like ``{{{foo}}}``."""

    def __init__(self, name: Any, default: Any = None):
        super().__init__()
        self.name = name
        self.default = default

    def __str__(self) -> str:
        start = "{{{" + str(self.name)
        if self.default is not None:
            return start + "|" + str(self.default) + "}}}"
        return start + "}}}"

    def __children__(self) -> Generator[Wikicode, None, None]:
        yield self.name
        if self.default is not None:
            yield self.default

    def __strip__(self, **kwargs: Any) -> str | None:
        if self.default is not None:
            return self.default.strip_code(**kwargs)
        return None

    def __showtree__(
        self,
        write: Callable[[str], None],
        get: Callable[[Wikicode], None],
        mark: Callable[[], None],
    ) -> None:
        write("{{{")
        get(self.name)
        if self.default is not None:
            write("    | ")
            mark()
            get(self.default)
        write("}}}")

    @property
    def name(self) -> Wikicode:
        """The name of the argument to substitute."""
        return self._name

    @name.setter
    def name(self, value: Any) -> None:
        self._name = parse_anything(value)

    @property
    def default(self) -> Wikicode | None:
        """The default value to substitute if none is passed.

        This will be ``None`` if the argument wasn't defined with one. The
        MediaWiki parser handles this by rendering the argument itself in the
        result, complete braces. To have the argument render as nothing, set
        default to ``""`` (``{{{arg}}}`` vs. ``{{{arg|}}}``).
        """
        return self._default

    @default.setter
    def default(self, default: Any) -> None:
        if default is None:
            self._default = None
        else:
            self._default = parse_anything(default)
