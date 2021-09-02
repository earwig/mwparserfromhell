# Copyright (C) 2012-2020 Ben Kurtovic <ben.kurtovic@gmail.com>
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

from ..string_mixin import StringMixIn

__all__ = ["Node"]


class Node(StringMixIn):
    """Represents the base Node type, demonstrating the methods to override.

    :meth:`__str__` must be overridden. It should return a ``str``
    representation of the node. If the node contains :class:`.Wikicode`
    objects inside of it, :meth:`__children__` should be a generator that
    iterates over them. If the node is printable (shown when the page is
    rendered), :meth:`__strip__` should return its printable version,
    stripping out any formatting marks. It does not have to return a string,
    but something that can be converted to a string with ``str()``. Finally,
    :meth:`__showtree__` can be overridden to build a nice tree representation
    of the node, if desired, for :meth:`~.Wikicode.get_tree`.
    """

    def __str__(self):
        raise NotImplementedError()

    def __children__(self):
        return
        # pylint: disable=unreachable
        yield  # pragma: no cover (this is a generator that yields nothing)

    def __strip__(self, **kwargs):
        return None

    def __showtree__(self, write, get, mark):
        write(str(self))
