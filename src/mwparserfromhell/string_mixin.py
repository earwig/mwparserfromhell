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

"""
This module contains the :class:`.StringMixIn` type, which implements the
interface for the ``str`` type in a dynamic manner.
"""

from sys import getdefaultencoding

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

    def __str__(self):
        raise NotImplementedError()

    def __bytes__(self):
        return bytes(self.__str__(), getdefaultencoding())

    def __repr__(self):
        return repr(self.__str__())

    def __lt__(self, other):
        return self.__str__() < other

    def __le__(self, other):
        return self.__str__() <= other

    def __eq__(self, other):
        return self.__str__() == other

    def __ne__(self, other):
        return self.__str__() != other

    def __gt__(self, other):
        return self.__str__() > other

    def __ge__(self, other):
        return self.__str__() >= other

    def __bool__(self):
        return bool(self.__str__())

    def __len__(self):
        return len(self.__str__())

    def __iter__(self):
        yield from self.__str__()

    def __getitem__(self, key):
        return self.__str__()[key]

    def __reversed__(self):
        return reversed(self.__str__())

    def __contains__(self, item):
        return str(item) in self.__str__()

    def __getattr__(self, attr):
        if not hasattr(str, attr):
            raise AttributeError(
                "{!r} object has no attribute {!r}".format(type(self).__name__, attr)
            )
        return getattr(self.__str__(), attr)

    maketrans = str.maketrans  # Static method can't rely on __getattr__


del inheritdoc
