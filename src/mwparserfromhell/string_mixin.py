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

"""
This module contains the :class:`.StringMixIn` type, which implements the
interface for the ``str`` type in a dynamic manner.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, SupportsIndex

__all__ = ["StringMixIn"]


def inheritdoc(method):
    """Set __doc__ of *method* to __doc__ of *method* in its parent class.

    Since this is used on :class:`.StringMixIn`, the "parent class" used is
    ``str``. This function can be used as a decorator.
    """
    method.__doc__ = getattr(str, method.__name__).__doc__
    return method


class StringMixIn:
    """Implement the interface for ``str`` in a dynamic manner.

    To use this class, inherit from it and override the :meth:`__str__` method
    to return the string representation of the object. The various string
    methods will operate on the value of :meth:`__str__` instead of the
    immutable ``self`` like the regular ``str`` type.
    """

    # This is based on collections.UserString, but:
    # - Requires overriding __str__ instead of setting .data
    # - Returns new strings as strs instead of StringMixIns

    __slots__ = ()

    def __str__(self) -> str:
        raise NotImplementedError()

    def __bytes__(self) -> bytes:
        return bytes(str(self), sys.getdefaultencoding())

    def __repr__(self) -> str:
        return repr(str(self))

    def __lt__(self, other: str | StringMixIn) -> bool:
        return str(self) < other

    def __le__(self, other: str | StringMixIn) -> bool:
        return str(self) <= other

    def __eq__(self, other: Any) -> bool:
        return str(self) == other

    def __ne__(self, other: Any) -> bool:
        return str(self) != other

    def __gt__(self, other: str | StringMixIn) -> bool:
        return str(self) > other

    def __ge__(self, other: str | StringMixIn) -> bool:
        return str(self) >= other

    def __bool__(self) -> bool:
        return bool(str(self))

    def __len__(self) -> int:
        return len(str(self))

    def __iter__(self) -> Iterator[str]:
        yield from str(self)

    def __getitem__(self, key: SupportsIndex | slice) -> str:
        return str(self)[key]

    def __reversed__(self) -> Iterator[str]:
        return reversed(str(self))

    def __contains__(self, item: Any) -> bool:
        return str(item) in str(self)

    @inheritdoc
    def capitalize(self) -> str:
        return str(self).capitalize()

    @inheritdoc
    def casefold(self) -> str:
        return str(self).casefold()

    @inheritdoc
    def center(self, width: int, fillchar: str = " ") -> str:
        return str(self).center(width, fillchar)

    @inheritdoc
    def count(
        self,
        sub: str | StringMixIn,
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
    ) -> int:
        if isinstance(sub, StringMixIn):
            sub = str(sub)
        return str(self).count(sub, start, end)

    @inheritdoc
    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        return str(self).encode(encoding, errors)

    @inheritdoc
    def endswith(
        self,
        suffix: str | tuple[str, ...],
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
    ) -> bool:
        return str(self).endswith(suffix, start, end)

    @inheritdoc
    def expandtabs(self, tabsize: int = 8) -> str:
        return str(self).expandtabs(tabsize)

    @inheritdoc
    def find(
        self,
        sub: str | StringMixIn,
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
    ) -> int:
        if isinstance(sub, StringMixIn):
            sub = str(sub)
        return str(self).find(sub, start, end)

    @inheritdoc
    def format(self, /, *args: Any, **kwds: Any) -> str:
        return str(self).format(*args, **kwds)

    @inheritdoc
    def format_map(self, mapping: Mapping[str, Any]) -> str:
        return str(self).format_map(mapping)

    @inheritdoc
    def index(
        self,
        sub: str,
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
    ) -> int:
        return str(self).index(sub, start, end)

    @inheritdoc
    def isalpha(self) -> bool:
        return str(self).isalpha()

    @inheritdoc
    def isalnum(self) -> bool:
        return str(self).isalnum()

    @inheritdoc
    def isascii(self) -> bool:
        return str(self).isascii()

    @inheritdoc
    def isdecimal(self) -> bool:
        return str(self).isdecimal()

    @inheritdoc
    def isdigit(self) -> bool:
        return str(self).isdigit()

    @inheritdoc
    def isidentifier(self) -> bool:
        return str(self).isidentifier()

    @inheritdoc
    def islower(self) -> bool:
        return str(self).islower()

    @inheritdoc
    def isnumeric(self) -> bool:
        return str(self).isnumeric()

    @inheritdoc
    def isprintable(self) -> bool:
        return str(self).isprintable()

    @inheritdoc
    def isspace(self) -> bool:
        return str(self).isspace()

    @inheritdoc
    def istitle(self) -> bool:
        return str(self).istitle()

    @inheritdoc
    def isupper(self) -> bool:
        return str(self).isupper()

    @inheritdoc
    def join(self, seq: Iterable[str]) -> str:
        return str(self).join(seq)

    @inheritdoc
    def ljust(self, width: int, fillchar: str = " ") -> str:
        return str(self).ljust(width, fillchar)

    @inheritdoc
    def lower(self) -> str:
        return str(self).lower()

    @inheritdoc
    def lstrip(self, chars: str | None = None) -> str:
        return str(self).lstrip(chars)

    maketrans = str.maketrans

    @inheritdoc
    def partition(self, sep: str) -> tuple[str, str, str]:
        return str(self).partition(sep)

    @inheritdoc
    def removeprefix(self, prefix: str | StringMixIn, /) -> str:
        if isinstance(prefix, StringMixIn):
            prefix = str(prefix)
        return str(self).removeprefix(prefix)

    @inheritdoc
    def removesuffix(self, suffix: str | StringMixIn, /) -> str:
        if isinstance(suffix, StringMixIn):
            suffix = str(suffix)
        return str(self).removesuffix(suffix)

    @inheritdoc
    def replace(
        self,
        old: str | StringMixIn,
        new: str | StringMixIn,
        /,
        count: SupportsIndex = -1,
    ):
        if isinstance(old, StringMixIn):
            old = str(old)
        if isinstance(new, StringMixIn):
            new = str(new)
        return str(self).replace(old, new, count)

    @inheritdoc
    def rfind(
        self,
        sub: str | StringMixIn,
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
    ) -> int:
        if isinstance(sub, StringMixIn):
            sub = str(sub)
        return str(self).rfind(sub, start, end)

    @inheritdoc
    def rindex(
        self,
        sub: str,
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
    ) -> int:
        return str(self).rindex(sub, start, end)

    @inheritdoc
    def rjust(self, width: int, fillchar: str = " ") -> str:
        return str(self).rjust(width, fillchar)

    @inheritdoc
    def rpartition(self, sep: str) -> tuple[str, str, str]:
        return str(self).rpartition(sep)

    @inheritdoc
    def rstrip(self, chars: str | None = None) -> str:
        return str(self).rstrip(chars)

    @inheritdoc
    def split(self, sep: str | None = None, maxsplit: SupportsIndex = -1) -> list[str]:
        return str(self).split(sep, maxsplit)

    @inheritdoc
    def rsplit(self, sep: str | None = None, maxsplit: SupportsIndex = -1) -> list[str]:
        return str(self).rsplit(sep, maxsplit)

    @inheritdoc
    def splitlines(self, keepends: bool = False) -> list[str]:
        return str(self).splitlines(keepends)

    @inheritdoc
    def startswith(
        self,
        prefix: str | tuple[str, ...],
        start: SupportsIndex | None = None,
        end: SupportsIndex | None = None,
    ) -> bool:
        return str(self).startswith(prefix, start, end)

    @inheritdoc
    def strip(self, chars: str | None = None) -> str:
        return str(self).strip(chars)

    @inheritdoc
    def swapcase(self) -> str:
        return str(self).swapcase()

    @inheritdoc
    def title(self) -> str:
        return str(self).title()

    @inheritdoc
    def translate(self, *args: Any) -> str:
        return str(self).translate(*args)

    @inheritdoc
    def upper(self) -> str:
        return str(self).upper()

    @inheritdoc
    def zfill(self, width: int) -> str:
        return str(self).zfill(width)
