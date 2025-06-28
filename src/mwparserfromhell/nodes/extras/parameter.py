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

import re
from typing import TYPE_CHECKING, Any

from ...string_mixin import StringMixIn
from ...utils import parse_anything

if TYPE_CHECKING:
    from ...wikicode import Wikicode

__all__ = ["Parameter"]


class Parameter(StringMixIn):
    """Represents a parameter of a template.

    For example, the template ``{{foo|bar|spam=eggs}}`` contains two
    Parameters: one whose name is ``"1"``, value is ``"bar"``, and ``showkey``
    is ``False``, and one whose name is ``"spam"``, value is ``"eggs"``, and
    ``showkey`` is ``True``.
    """

    def __init__(self, name: Any, value: Any, showkey: bool = True) -> None:
        super().__init__()
        self.name = name
        self.value = value
        self.showkey = showkey

    def __str__(self) -> str:
        if self.showkey:
            return str(self.name) + "=" + str(self.value)
        return str(self.value)

    @staticmethod
    def can_hide_key(key: Any) -> re.Match | None:
        """Return whether or not the given key can be hidden."""
        return re.match(r"[1-9][0-9]*$", str(key).strip())

    @property
    def name(self) -> Wikicode:
        """The name of the parameter as a :class:`.Wikicode` object."""
        return self._name

    @name.setter
    def name(self, newval: Any) -> None:
        self._name = parse_anything(newval)

    @property
    def value(self) -> Wikicode:
        """The value of the parameter as a :class:`.Wikicode` object."""
        return self._value

    @value.setter
    def value(self, newval: Any) -> None:
        self._value = parse_anything(newval)

    @property
    def showkey(self) -> bool:
        """Whether to show the parameter's key (i.e., its "name")."""
        return self._showkey

    @showkey.setter
    def showkey(self, newval: Any) -> None:
        newval = bool(newval)
        if not newval and not self.can_hide_key(self.name):
            raise ValueError(f"parameter key {self.name!r} cannot be hidden")
        self._showkey = newval
