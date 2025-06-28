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

from typing import TYPE_CHECKING, Any

from ._base import Node

if TYPE_CHECKING:
    from ..wikicode import Wikicode

__all__ = ["Comment"]


class Comment(Node):
    """Represents a hidden HTML comment, like ``<!-- foobar -->``."""

    def __init__(self, contents: Wikicode | str):
        super().__init__()
        self.contents = contents

    def __str__(self) -> str:
        return "<!--" + self.contents + "-->"

    @property
    def contents(self) -> str:
        """The hidden text contained between ``<!--`` and ``-->``."""
        return self._contents

    @contents.setter
    def contents(self, value: Any) -> None:
        self._contents = str(value)
