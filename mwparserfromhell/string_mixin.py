# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2016 Ben Kurtovic <ben.kurtovic@gmail.com>
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
interface for the ``unicode`` type (``str`` on py3k) in a dynamic manner.
"""

from __future__ import unicode_literals
from sys import getdefaultencoding

from .compat import bytes, py26, py3k, str

__all__ = ["StringMixIn"]

def inheritdoc(method):
    """Set __doc__ of *method* to __doc__ of *method* in its parent class.

    Since this is used on :class:`.StringMixIn`, the "parent class" used is
    ``str``. This function can be used as a decorator.
    """
    method.__doc__ = getattr(str, method.__name__).__doc__
    return method

class StringMixIn(object):
    """Implement the interface for ``unicode``/``str`` in a dynamic manner.

    To use this class, inherit from it and override the :meth:`__unicode__`
    method (same on py3k) to return the string representation of the object.
    The various string methods will operate on the value of :meth:`__unicode__`
    instead of the immutable ``self`` like the regular ``str`` type.
    """

    if py3k:
        def __str__(self):
            return self.__unicode__()

        def __bytes__(self):
            return bytes(self.__unicode__(), getdefaultencoding())
    else:
        def __str__(self):
            return bytes(self.__unicode__())

    def __unicode__(self):
        raise NotImplementedError()

    def __repr__(self):
        return repr(self.__unicode__())

    def __lt__(self, other):
        return self.__unicode__() < other

    def __le__(self, other):
        return self.__unicode__() <= other

    def __eq__(self, other):
        return self.__unicode__() == other

    def __ne__(self, other):
        return self.__unicode__() != other

    def __gt__(self, other):
        return self.__unicode__() > other

    def __ge__(self, other):
        return self.__unicode__() >= other

    if py3k:
        def __bool__(self):
            return bool(self.__unicode__())
    else:
        def __nonzero__(self):
            return bool(self.__unicode__())

    def __len__(self):
        return len(self.__unicode__())

    def __iter__(self):
        for char in self.__unicode__():
            yield char

    def __getitem__(self, key):
        return self.__unicode__()[key]

    def __reversed__(self):
        return reversed(self.__unicode__())

    def __contains__(self, item):
        return str(item) in self.__unicode__()

    def __getattr__(self, attr):
        return getattr(self.__unicode__(), attr)

    if py3k:
        maketrans = str.maketrans  # Static method can't rely on __getattr__

    if py26:
        @inheritdoc
        def encode(self, encoding=None, errors=None):
            if encoding is None:
                encoding = getdefaultencoding()
            if errors is not None:
                return self.__unicode__().encode(encoding, errors)
            return self.__unicode__().encode(encoding)


del inheritdoc
