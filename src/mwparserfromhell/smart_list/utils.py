# Copyright (C) 2012-2023 Ben Kurtovic <ben.kurtovic@gmail.com>
# Copyright (C) 2019-2020 Yuri Astrakhan <YuriAstrakhan@gmail.com>
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

from sys import maxsize

__all__ = []


def inheritdoc(method):
    """Set __doc__ of *method* to __doc__ of *method* in its parent class.

    Since this is used on :class:`.SmartList`, the "parent class" used is
    ``list``. This function can be used as a decorator.
    """
    method.__doc__ = getattr(list, method.__name__).__doc__
    return method


class _SliceNormalizerMixIn:
    """MixIn that provides a private method to normalize slices."""

    __slots__ = ()

    def _normalize_slice(self, key, clamp=False):
        """Return a slice equivalent to the input *key*, standardized."""
        if key.start is None:
            start = 0
        else:
            start = (len(self) + key.start) if key.start < 0 else key.start
        if key.stop is None or key.stop == maxsize:
            stop = len(self) if clamp else None
        else:
            stop = (len(self) + key.stop) if key.stop < 0 else key.stop
        return slice(start, stop, key.step or 1)
